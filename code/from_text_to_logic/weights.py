#!/usr/bin/env python3
"""
weights.py - Soft Constraint Verification via LLM Logprobs

Verifies whether a document endorses each soft constraint from a logified JSON file.
Uses SBERT retrieval + LLM logprob extraction to compute probability scores.

See weights_how_it_works.md for detailed algorithm explanation.

Usage (CLI):
    python weights.py document.pdf logified.json --api-key sk-...

Usage (Python):
    from from_text_to_logic.weights import assign_weights

    result = assign_weights(
        pathfile="document.pdf",
        json_path="logified.json",
        api_key="sk-..."
    )
    # Outputs: logified_weighted.json
"""

import sys
import json
import math
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to Python path (for imports to work from anywhere)
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import numpy as np
from openai import OpenAI

# Reuse existing RAG infrastructure
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    compute_cosine_similarity
)


def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from various document formats.

    Args:
        file_path: Path to document file (PDF, DOCX, TXT)

    Returns:
        Extracted text content
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix in ['.txt', '.text']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF support. "
                "Install with: pip install PyMuPDF"
            )
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)

    elif suffix in ['.docx', '.doc']:
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install with: pip install python-docx"
            )
        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs]
        return "\n".join(text_parts)

    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: .txt, .pdf, .docx"
        )


def retrieve_top_k_chunks(
    constraint: str,
    chunks: List[Dict],
    chunk_embeddings: np.ndarray,
    sbert_model,
    k: int = 10
) -> List[Dict]:
    """
    Retrieve top-k chunks most similar to the constraint using SBERT.

    Args:
        constraint: The soft constraint text (query)
        chunks: List of chunk dicts from chunker
        chunk_embeddings: Pre-computed chunk embeddings
        sbert_model: Loaded SBERT model
        k: Number of chunks to retrieve

    Returns:
        List of top-k chunks sorted by similarity (highest first)
    """
    query_embedding = encode_query(constraint, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    # Get top-k indices
    k = min(k, len(chunks))
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Return chunks with similarity scores
    retrieved = []
    for idx in top_k_indices:
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
        retrieved.append(chunk)

    return retrieved


def build_verification_prompt(chunks: List[Dict], constraint: str) -> str:
    """
    Build the LLM prompt for YES/NO verification.

    Args:
        chunks: Retrieved chunks (top-k)
        constraint: The soft constraint to verify

    Returns:
        Formatted prompt string
    """
    chunk_texts = "\n\n".join([chunk['text'] for chunk in chunks])

    prompt = f"""You are a verifier that will answer with exactly one token: "YES" or "NO". Do not produce any other text.

[TEXT]
{chunk_texts}

[CONSTRAINT]
{constraint}

[QUESTION]
Does the text endorse this constraint as a general, necessary rule? Answer "YES" or "NO" with no other words."""

    return prompt


def extract_logprobs_for_yes_no(response) -> Dict[str, float]:
    """
    Extract logprobs for YES and NO tokens from API response.

    Args:
        response: OpenAI API response with logprobs

    Returns:
        Dict with logit_yes, logit_no, prob_yes, prob_no
    """
    logit_yes = -100.0
    logit_no = -100.0

    if (hasattr(response.choices[0], 'logprobs') and
        response.choices[0].logprobs is not None and
        hasattr(response.choices[0].logprobs, 'content') and
        response.choices[0].logprobs.content):

        first_token_logprobs = response.choices[0].logprobs.content[0]

        # Check the actual generated token first
        actual_token = first_token_logprobs.token.strip().upper()
        actual_logprob = first_token_logprobs.logprob

        if actual_token == "YES":
            logit_yes = actual_logprob
        elif actual_token == "NO":
            logit_no = actual_logprob

        # Search through top_logprobs for YES and NO
        if hasattr(first_token_logprobs, 'top_logprobs') and first_token_logprobs.top_logprobs:
            for candidate in first_token_logprobs.top_logprobs:
                token = candidate.token.strip().upper()
                logprob = candidate.logprob

                if token == "YES" and logit_yes == -100.0:
                    logit_yes = logprob
                elif token == "NO" and logit_no == -100.0:
                    logit_no = logprob

    prob_yes = math.exp(logit_yes) if logit_yes > -100.0 else 0.0
    prob_no = math.exp(logit_no) if logit_no > -100.0 else 0.0

    return {
        "logit_yes": logit_yes,
        "logit_no": logit_no,
        "prob_yes": prob_yes,
        "prob_no": prob_no
    }


def verify_single_constraint(
    constraint_text: str,
    chunks: List[Dict],
    chunk_embeddings: np.ndarray,
    sbert_model,
    client: OpenAI,
    model: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 5,
    k: int = 10
) -> Dict[str, float]:
    """
    Verify a single constraint against the document chunks.

    Args:
        constraint_text: The soft constraint translation (natural language)
        chunks: All document chunks
        chunk_embeddings: Pre-computed chunk embeddings
        sbert_model: Loaded SBERT model
        client: OpenAI client
        model: OpenAI model
        temperature: Sampling temperature
        max_tokens: Max response tokens
        k: Number of top chunks to retrieve

    Returns:
        Dict with logit_yes, logit_no, prob_yes, prob_no
    """
    # Retrieve top-k chunks for this constraint
    retrieved_chunks = retrieve_top_k_chunks(
        constraint_text, chunks, chunk_embeddings, sbert_model, k=k
    )

    # Build prompt
    prompt = build_verification_prompt(retrieved_chunks, constraint_text)

    # Debug output: show chunks and prompt
    print("\n" + "=" * 60)
    print("DEBUG: Retrieved Chunks")
    print("=" * 60)
    for j, chunk in enumerate(retrieved_chunks):
        print(f"\n--- Chunk {j+1} (similarity: {chunk['similarity']:.4f}) ---")
        print(chunk['text'][:500] + ("..." if len(chunk['text']) > 500 else ""))
    print("\n" + "=" * 60)
    print("DEBUG: Full Prompt to LLM")
    print("=" * 60)
    print(prompt)
    print("=" * 60 + "\n")

    # Call LLM with logprobs
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        logprobs=True,
        top_logprobs=20
    )

    # Extract logprobs
    return extract_logprobs_for_yes_no(response)


def assign_weights(
    pathfile: str,
    json_path: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 5,
    reasoning_effort: str = "low",
    k: int = 10,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Assign weights to all soft constraints in a logified JSON file.

    Args:
        pathfile: Path to document file (PDF, DOCX, TXT)
        json_path: Path to logified JSON file
        api_key: OpenAI API key
        model: OpenAI model (default: gpt-4o)
        temperature: Sampling temperature (default: 0.0)
        max_tokens: Max tokens in response (default: 5)
        reasoning_effort: For reasoning models (default: low)
        k: Number of top chunks to retrieve (default: 10)
        chunk_size: Tokens per chunk (default: 512)
        chunk_overlap: Overlapping tokens between chunks (default: 50)
        sbert_model_name: SBERT model for retrieval (default: all-MiniLM-L6-v2)
        verbose: Print progress messages (default: True)

    Returns:
        The logified structure with weights added to soft constraints
    """
    # Step 1: Load logified JSON
    if verbose:
        print(f"Loading logified JSON from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        logified = json.load(f)

    soft_constraints = logified.get('soft_constraints', [])

    if not soft_constraints:
        if verbose:
            print("No soft constraints found. Nothing to weight.")
        return logified

    if verbose:
        print(f"  Found {len(soft_constraints)} soft constraints")

    # Step 2: Extract text from document
    if verbose:
        print(f"Extracting text from: {pathfile}")

    document_text = extract_text_from_document(pathfile)

    if verbose:
        print(f"  Extracted {len(document_text)} characters")

    # Step 3: Chunk the document
    if verbose:
        print(f"Chunking document (size={chunk_size}, overlap={chunk_overlap})...")

    chunks = chunk_document(document_text, chunk_size=chunk_size, overlap=chunk_overlap)

    if verbose:
        print(f"  Created {len(chunks)} chunks")

    # Step 4: Load SBERT and pre-compute chunk embeddings (once for all constraints)
    if verbose:
        print(f"Loading SBERT model: {sbert_model_name}")

    sbert_model = load_sbert_model(sbert_model_name)

    if verbose:
        print("Pre-computing chunk embeddings...")

    chunk_embeddings = encode_chunks(chunks, sbert_model)

    if verbose:
        print(f"  Computed embeddings for {len(chunks)} chunks")

    # Step 5: Initialize OpenAI client (with OpenRouter support)
    is_openrouter = api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-')

    if is_openrouter:
        # OpenRouter API
        client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
        # Prefix model with openai/ for OpenRouter if not already prefixed
        if not model.startswith('openai/') and '/' not in model:
            model = f'openai/{model}'
        if verbose:
            print(f"  Using OpenRouter API with model: {model}")
    else:
        # Direct OpenAI API
        client = OpenAI(api_key=api_key)
        if verbose:
            print(f"  Using OpenAI API with model: {model}")

    # Check if this is a reasoning model
    base_model = model.replace('openai/', '')
    is_reasoning_model = any(base_model.startswith(prefix) for prefix in ["gpt-5", "o1", "o3"])
    if is_reasoning_model:
        print(f"  WARNING: Model {model} may not support logprobs. Consider using gpt-4o.")

    # Step 6: Process each soft constraint
    if verbose:
        print(f"\nProcessing {len(soft_constraints)} soft constraints...")

    for i, constraint in enumerate(soft_constraints):
        constraint_id = constraint.get('id', f'S_{i+1}')
        constraint_text = constraint.get('translation', '')

        if not constraint_text:
            if verbose:
                print(f"  [{i+1}/{len(soft_constraints)}] {constraint_id}: SKIPPED (no translation)")
            continue

        if verbose:
            print(f"  [{i+1}/{len(soft_constraints)}] {constraint_id}: {constraint_text[:60]}...")

        # Verify original constraint
        if verbose:
            print(f"      Verifying original...")
        result_original = verify_single_constraint(
            constraint_text=constraint_text,
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            sbert_model=sbert_model,
            client=client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            k=k
        )

        if verbose:
            print(f"      → logit_yes={result_original['logit_yes']:.4f}, logit_no={result_original['logit_no']:.4f}, "
                  f"P(YES)={result_original['prob_yes']:.4f}, P(NO)={result_original['prob_no']:.4f}")

        # Verify negated constraint
        negated_constraint_text = f"It is false that {constraint_text}"
        if verbose:
            print(f"      Verifying negation: {negated_constraint_text[:60]}...")
        result_negated = verify_single_constraint(
            constraint_text=negated_constraint_text,
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            sbert_model=sbert_model,
            client=client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            k=k
        )

        if verbose:
            print(f"      → neg_logit_yes={result_negated['logit_yes']:.4f}, neg_logit_no={result_negated['logit_no']:.4f}, "
                  f"neg_P(YES)={result_negated['prob_yes']:.4f}, neg_P(NO)={result_negated['prob_no']:.4f}")

        # Add weight field to constraint (8 values: original + negated)
        constraint['weight'] = [
            result_original['logit_yes'],
            result_original['logit_no'],
            result_original['prob_yes'],
            result_original['prob_no'],
            result_negated['logit_yes'],
            result_negated['logit_no'],
            result_negated['prob_yes'],
            result_negated['prob_no']
        ]

    # Step 7: Save output
    json_path_obj = Path(json_path)
    output_path = json_path_obj.parent / (json_path_obj.stem + "_weighted.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logified, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"\n✓ Weights assigned! Output saved to: {output_path}")

    return logified


def main():
    """Command-line interface for weight assignment."""
    parser = argparse.ArgumentParser(
        description="Assign weights to soft constraints using LLM logprobs",
        epilog="Example: python weights.py document.pdf logified.json --api-key sk-..."
    )
    parser.add_argument(
        "pathfile",
        help="Path to document file (PDF, DOCX, or TXT)"
    )
    parser.add_argument(
        "json_path",
        help="Path to logified JSON file"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="OpenAI API key"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model (default: gpt-4o)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature (default: 0.0)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=5,
        help="Maximum tokens in response (default: 5)"
    )
    parser.add_argument(
        "--reasoning-effort",
        default="low",
        choices=["none", "low", "medium", "high"],
        help="Reasoning effort for reasoning models (default: low)"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Number of top chunks to retrieve (default: 10)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Tokens per chunk (default: 512)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlapping tokens between chunks (default: 50)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    # Validate file paths
    if not Path(args.pathfile).exists():
        print(f"Error: Document not found: {args.pathfile}")
        return 1

    if not Path(args.json_path).exists():
        print(f"Error: JSON file not found: {args.json_path}")
        return 1

    try:
        assign_weights(
            pathfile=args.pathfile,
            json_path=args.json_path,
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            reasoning_effort=args.reasoning_effort,
            k=args.k,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            verbose=not args.quiet
        )
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
