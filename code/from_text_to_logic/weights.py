#!/usr/bin/env python3
"""
Assign weights to logical constraints and split them into hard and soft constraints.

Purpose:
- Scores constraints using retrieval/NLI-based support from extracted propositions.
- Enriches the logic structure and produces a weighted reasoning-ready JSON file.

Inputs:
- Path to the original document.
- Path to a logified JSON file.
- Threshold and retrieval/model configuration.

Outputs:
- A dictionary with primitive propositions, hard constraints, and soft constraints.
- A saved *_weighted.json file.
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
from experiments.baseline_rag.chunker import chunk_document
from experiments.baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    compute_cosine_similarity
)
from experiments.baseline_rag.nli_reranker import load_nli_model, score_nli_pairs

from config.retrieval_config import HARDNESS_CONSTANT, SBERT_TOP_K, SBERT_MODEL, NLI_MODEL, USE_ENRICHMENT 
from from_text_to_logic.check_logic_structure import enrich_logic_structure

################

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


# def retrieve_top_k_chunks(
#     query: str,
#     chunks: List[Dict],
#     chunk_embeddings: np.ndarray,
#     sbert_model,
#     k: int = 10
# ) -> List[Dict]:
#     """Retrieve top-k chunks most similar to query using SBERT."""
#     query_embedding = encode_query(query, sbert_model)
#     similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

#     k = min(k, len(chunks))
#     top_k_indices = np.argsort(similarities)[::-1][:k]

#     retrieved = []
#     for idx in top_k_indices:
#         chunk = chunks[idx].copy()
#         chunk['similarity'] = float(similarities[idx])
#         retrieved.append(chunk)

#     return retrieved


# def compute_nli_entailment(
#     constraint_text: str,
#     chunks: List[Dict],
#     chunk_embeddings: np.ndarray,
#     sbert_model,
#     nli_model,
#     k: int = 10
# ) -> float:
#     """
#     Compute max NLI entailment score for constraint against top-k chunks.
    
#     Returns the maximum P(entailment) across all retrieved chunks.
#     """
#     retrieved = retrieve_top_k_chunks(
#         query=constraint_text,
#         chunks=chunks,
#         chunk_embeddings=chunk_embeddings,
#         sbert_model=sbert_model,
#         k=k
#     )

#     if not retrieved:
#         return 0.0

#     # Build (premise, hypothesis) pairs: premise=chunk, hypothesis=constraint
#     pairs = [(chunk['text'], constraint_text) for chunk in retrieved]

#     # Score with NLI: returns array of shape (n_pairs, 3) with [P(contra), P(neutral), P(entail)]
#     probs = score_nli_pairs(nli_model, pairs)
    
#     # Return max entailment score
#     return float(np.max(probs[:, 2]))

def compute_nli_entailment(
    constraint_text: str,
    propositions_from_text: List[Dict],
    nli_model,
    k: int = 10,
    sbert_model=None,
    prop_embeddings=None,
    sbert_model_name=SBERT_MODEL
):
    """
    Compute NLI entailment scores for a constraint against proposition texts.

    Returns tuple:
        - max_entailment: float - maximum P(entailment) across top-k candidates
        - top_3_probs: list - top 3 NLI probability distributions [contra, neutral, entail]
    
    NOTE: If prop_embeddings is provided, propositions_from_text should already be
          filtered (only dicts with "translation" key) to match the embeddings.
    """
    # If embeddings provided, assume propositions are pre-filtered
    if prop_embeddings is not None:
        filtered_props = propositions_from_text
    else:
        # Filter to propositions that actually have a translation
        filtered_props = [p for p in propositions_from_text if isinstance(p, dict) and p.get("translation")]
    
    if not filtered_props:
        return 0.0, []

    prop_texts = [p["translation"] for p in filtered_props]

    # Use provided model or load (for backward compatibility)
    if sbert_model is None:
        sbert_model = load_sbert_model(sbert_model_name)
    
    # Use provided embeddings or compute
    if prop_embeddings is None:
        prop_embeddings = sbert_model.encode(prop_texts, convert_to_numpy=True)

    # SBERT ranking by cosine similarity
    query_embedding = encode_query(constraint_text, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, prop_embeddings)

    k = min(k, len(prop_texts)) if k else len(prop_texts)
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Select top-k propositions by SBERT similarity
    candidates = [filtered_props[i] for i in top_k_indices]

    # Build (premise, hypothesis) pairs
    pairs = [(prop["translation"], constraint_text) for prop in candidates]

    if not pairs:
        return 0.0, []

    # Score with NLI: returns array [P(contra), P(neutral), P(entail)]
    probs = score_nli_pairs(nli_model, pairs)

    # Compute both return values
    max_entailment = float(np.max(probs[:, 2]))
    top_3 = sorted(probs, key=lambda x: x[2], reverse=True)[:3]
    top_3_list = [row.tolist() for row in top_3]

    return max_entailment, top_3_list





def assign_weights(
    pathfile: str,
    json_path: str,
    hardness_criterion: float = HARDNESS_CONSTANT,
    k: int = 10,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    sbert_model_name: str = SBERT_MODEL,
    nli_model_name: str = NLI_MODEL,
    verbose: bool = True
    ) -> Dict[str, Any]:
    """
    Assign weights to logical constraints and split them into hard and soft constraints.
    """
    
    # Step 1: Load logified JSON
    if verbose:
        print(f"Loading logified JSON from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        logified = json.load(f)

    # Step 1.5: ENRICH the logic structure (modal pairs, finite domains, etc.)
    if USE_ENRICHMENT:
        if verbose:
            print("Enriching logic structure...")

        logified = enrich_logic_structure(
            logified_path=json_path,
            source_path=pathfile,
            output_path=None,  # Don't save intermediate file
            verbose=verbose
        )
    else:
        if verbose:
            print("Skipping enrichment (USE_ENRICHMENT=False)")
    
    # Now continue with enriched structure
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

    # Step 2: Get propositions (premise candidates)
    propositions = logified.get("primitive_props", [])
    if verbose:
        print(f"  Found {len(propositions)} propositions")

    # Step 3: Load models ONCE
    if verbose:
        print(f"Loading SBERT model: {sbert_model_name}")
    sbert_model = load_sbert_model(sbert_model_name)
    
    if verbose:
        print(f"Loading NLI model: {nli_model_name}")
    nli_model = load_nli_model(nli_model_name)

    # Step 4: Process each constraint
    if verbose:
        print(f"\nClassifying {len(constraints)} constraints (hardness_criterion={hardness_criterion})...")

    hard_constraints = []
    soft_constraints = []

    required_fields = {"id", "translation", "formula", "llm_weight"}
    missing = [c for c in constraints if not required_fields.issubset(c.keys())]
    if missing:
        raise ValueError("[Weights] constraints missing required fields: id, translation, formula, llm_weight")

    # Pre-compute proposition embeddings ONCE
    filtered_props = [p for p in propositions if isinstance(p, dict) and p.get("translation")]
    prop_texts = [p["translation"] for p in filtered_props]
    prop_embeddings = sbert_model.encode(prop_texts, convert_to_numpy=True) if prop_texts else None

    for i, constraint in enumerate(constraints):
        constraint_id = constraint.get('id', f'C_{i+1}')
        constraint_text = constraint.get('translation', '')
        llm_weight = constraint.get('llm_weight', 0)

        if not constraint_text:
            if verbose:
                print(f"  [{i+1}/{len(constraints)}] {constraint_id}: SKIPPED (no translation)")
            continue

        # Single call returns both values
        nli_entailment, list_nli_entailment = compute_nli_entailment(
            constraint_text=constraint_text,
            propositions_from_text=filtered_props,  
            nli_model=nli_model,
            k=k,
            sbert_model=sbert_model,
            prop_embeddings=prop_embeddings
        )
    
        # Compute combined score
        combined = llm_weight * nli_entailment

        if verbose:
            print(f"  [{i+1}/{len(constraints)}] {constraint_id}: "
                  f"llm={llm_weight:.2f} × nli={nli_entailment:.2f} = {combined:.2f}", end="")

        # Build output constraint
        output_constraint = {
            "llm-weight": llm_weight,
            "nli_entailment": nli_entailment,
            "combined=(llm)*(nli)": combined,
            "hardness_constant": hardness_criterion,
            "id": constraint_id,
            "formula": constraint.get('formula', ''),
            "translation": constraint_text,
            "evidence": constraint.get('evidence', ''),
            "reasoning": constraint.get('reasoning', ''),
            "list nli": list_nli_entailment
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
    parser.add_argument("--hardness-criterion", type=float, default= HARDNESS_CONSTANT,
                        help="Threshold for hard classification")
    parser.add_argument("--k", type=int, default = SBERT_TOP_K,
                        help="Number of top chunks to retrieve")
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
