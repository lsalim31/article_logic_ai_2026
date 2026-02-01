#!/usr/bin/env python3
"""
Patricio's edits: Jan 31
weights.py - Constraint Classification via NLI

Classifies constraints from a logified JSON file into hard and soft constraints
using NLI cross-encoder scores combined with LLM-assigned weights.

Pipeline:
1. Load {primitive_props, constraints} from logified JSON
2. For each constraint, retrieve top-k document chunks via SBERT
3. Score (chunk, constraint) pairs using NLI cross-encoder
4. Compute combined_score = llm_weight × max(nli_entailment)
5. Classify: combined >= hardness_criterion → hard, else → soft

Usage:
    python weights.py document.pdf logified.json

Usage (Python):
    from from_text_to_logic.weights import assign_weights
    result = assign_weights(pathfile="doc.pdf", json_path="logified.json")
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import numpy as np

# Reuse existing infrastructure
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    compute_cosine_similarity
)
from baseline_rag.nli_reranker import load_nli_model, score_nli_pairs


def extract_text_from_document(file_path: str) -> str:
    """Extract text from PDF, DOCX, or TXT file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix in ['.txt', '.text']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif suffix == '.pdf':
        try:
            import fitz
        except ImportError:
            raise ImportError("PyMuPDF required. Install with: pip install PyMuPDF")
        doc = fitz.open(file_path)
        text_parts = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(text_parts)

    elif suffix in ['.docx', '.doc']:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx required. Install with: pip install python-docx")
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError(f"Unsupported format: {suffix}. Supported: .txt, .pdf, .docx")


def retrieve_top_k_chunks(
    query: str,
    chunks: List[Dict],
    chunk_embeddings: np.ndarray,
    sbert_model,
    k: int = 10
) -> List[Dict]:
    """Retrieve top-k chunks most similar to query using SBERT."""
    query_embedding = encode_query(query, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    k = min(k, len(chunks))
    top_k_indices = np.argsort(similarities)[::-1][:k]

    retrieved = []
    for idx in top_k_indices:
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
        retrieved.append(chunk)

    return retrieved


def compute_nli_entailment(
    constraint_text: str,
    chunks: List[Dict],
    chunk_embeddings: np.ndarray,
    sbert_model,
    nli_model,
    k: int = 10
) -> float:
    """
    Compute max NLI entailment score for constraint against top-k chunks.
    
    Returns the maximum P(entailment) across all retrieved chunks.
    """
    retrieved = retrieve_top_k_chunks(
        query=constraint_text,
        chunks=chunks,
        chunk_embeddings=chunk_embeddings,
        sbert_model=sbert_model,
        k=k
    )

    if not retrieved:
        return 0.0

    # Build (premise, hypothesis) pairs: premise=chunk, hypothesis=constraint
    pairs = [(chunk['text'], constraint_text) for chunk in retrieved]

    # Score with NLI: returns array of shape (n_pairs, 3) with [P(contra), P(neutral), P(entail)]
    probs = score_nli_pairs(nli_model, pairs)
    
    # Return max entailment score
    return float(np.max(probs[:, 2]))


def assign_weights(
    pathfile: str,
    json_path: str,
    hardness_criterion: float = 0.85,
    k: int = 10,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Classify constraints into hard and soft using NLI scores.

    Args:
        pathfile: Path to document file (PDF, DOCX, TXT)
        json_path: Path to logified JSON file with {primitive_props, constraints}
        hardness_criterion: Threshold for hard classification (default: 0.85)
        k: Number of top chunks to retrieve per constraint (default: 10)
        chunk_size: Tokens per chunk (default: 512)
        chunk_overlap: Overlapping tokens between chunks (default: 50)
        sbert_model_name: SBERT model for retrieval
        nli_model_name: NLI model for scoring
        verbose: Print progress messages

    Returns:
        Dict with {primitive_props, hard_constraints, soft_constraints}
    """
    # Step 1: Load logified JSON
    if verbose:
        print(f"Loading logified JSON from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        logified = json.load(f)

    constraints = logified.get('constraints', [])
    primitive_props = logified.get('primitive_props', [])

    if not constraints:
        if verbose:
            print("No constraints found.")
        return {
            "primitive_props": primitive_props,
            "hard_constraints": [],
            "soft_constraints": []
        }

    if verbose:
        print(f"  Found {len(constraints)} constraints")

    # Step 2: Extract and chunk document
    if verbose:
        print(f"Extracting text from: {pathfile}")

    document_text = extract_text_from_document(pathfile)

    if verbose:
        print(f"  Extracted {len(document_text)} characters")
        print(f"Chunking document (size={chunk_size}, overlap={chunk_overlap})...")

    chunks = chunk_document(document_text, chunk_size=chunk_size, overlap=chunk_overlap)

    if verbose:
        print(f"  Created {len(chunks)} chunks")

    # Step 3: Load models
    if verbose:
        print(f"Loading SBERT model: {sbert_model_name}")
    sbert_model = load_sbert_model(sbert_model_name)

    if verbose:
        print("Pre-computing chunk embeddings...")
    chunk_embeddings = encode_chunks(chunks, sbert_model)

    if verbose:
        print(f"Loading NLI model: {nli_model_name}")
    nli_model = load_nli_model(nli_model_name)

    # Step 4: Process each constraint
    if verbose:
        print(f"\nClassifying {len(constraints)} constraints (hardness_criterion={hardness_criterion})...")

    hard_constraints = []
    soft_constraints = []

    for i, constraint in enumerate(constraints):
        constraint_id = constraint.get('id', f'C_{i+1}')
        constraint_text = constraint.get('translation', '')
        llm_weight = constraint.get('llm_weight', 0.5)

        if not constraint_text:
            if verbose:
                print(f"  [{i+1}/{len(constraints)}] {constraint_id}: SKIPPED (no translation)")
            continue

        # Compute NLI entailment score
        nli_entailment = compute_nli_entailment(
            constraint_text=constraint_text,
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            sbert_model=sbert_model,
            nli_model=nli_model,
            k=k
        )

        # Compute combined score
        combined = llm_weight * nli_entailment

        if verbose:
            print(f"  [{i+1}/{len(constraints)}] {constraint_id}: "
                  f"llm={llm_weight:.2f} × nli={nli_entailment:.2f} = {combined:.2f}", end="")

        # Build output constraint
        output_constraint = {
            "id": constraint_id,
            "formula": constraint.get('formula', ''),
            "translation": constraint_text,
            "evidence": constraint.get('evidence', ''),
            "reasoning": constraint.get('reasoning', '')
        }

        # Classify based on combined score
        if combined >= hardness_criterion:
            hard_constraints.append(output_constraint)
            if verbose:
                print(" → HARD")
        else:
            output_constraint['weight'] = combined
            soft_constraints.append(output_constraint)
            if verbose:
                print(" → SOFT")

    # Step 5: Build and save output
    output = {
        "primitive_props": primitive_props,
        "hard_constraints": hard_constraints,
        "soft_constraints": soft_constraints
    }

    json_path_obj = Path(json_path)
    output_path = json_path_obj.parent / (json_path_obj.stem + "_weighted.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"\n✓ Classification complete!")
        print(f"  Hard constraints: {len(hard_constraints)}")
        print(f"  Soft constraints: {len(soft_constraints)}")
        print(f"  Output saved to: {output_path}")

    return output


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Classify constraints into hard/soft using NLI scores"
    )
    parser.add_argument("pathfile", help="Path to document file (PDF, DOCX, TXT)")
    parser.add_argument("json_path", help="Path to logified JSON file")
    parser.add_argument("--hardness-criterion", type=float, default=0.85,
                        help="Threshold for hard classification (default: 0.85)")
    parser.add_argument("--k", type=int, default=10,
                        help="Number of top chunks to retrieve (default: 10)")
    parser.add_argument("--chunk-size", type=int, default=512,
                        help="Tokens per chunk (default: 512)")
    parser.add_argument("--chunk-overlap", type=int, default=50,
                        help="Overlapping tokens (default: 50)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress messages")

    args = parser.parse_args()

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
            hardness_criterion=args.hardness_criterion,
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