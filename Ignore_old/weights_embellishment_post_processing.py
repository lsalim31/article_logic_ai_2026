#!/usr/bin/env python3
"""
weights.py

Assign hard/soft weights to the original logified structure.

Design intent:
- Keep preprocessing lightweight and deterministic.
- Defer embellishment (modal/auxiliary/negation expansions) to query time,
  and only for top-K retrieved propositions.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

import numpy as np

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# Reuse existing infrastructure
from baseline_rag.retriever import (
    load_sbert_model,
    encode_query,
    compute_cosine_similarity,
)
from baseline_rag.nli_reranker import load_nli_model, score_nli_pairs

from config.retrieval_config import HARDNESS_CONSTANT, SBERT_TOP_K, SBERT_MODEL


def _normalize_constraints(logified: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accept either:
      - canonical logified format: {"constraints": [...]}
      - already weighted format: {"hard_constraints": [...], "soft_constraints": [...]}
    Returns a unified list of constraints for reweighting.
    """
    if "constraints" in logified and isinstance(logified["constraints"], list):
        return logified["constraints"]

    hard = logified.get("hard_constraints", [])
    soft = logified.get("soft_constraints", [])
    return list(hard) + list(soft)


def compute_nli_entailment(
    constraint_text: str,
    propositions_from_text: List[Dict[str, Any]],
    nli_model,
    k: int = SBERT_TOP_K,
    sbert_model_name: str = SBERT_MODEL,
) -> float:
    """
    Compute max NLI entailment for one constraint against top-k proposition translations.
    Returns value in [0,1].
    """
    filtered_props = [
        p for p in propositions_from_text
        if isinstance(p, dict) and isinstance(p.get("translation"), str) and p["translation"].strip()
    ]
    if not filtered_props:
        return 0.0

    prop_texts = [p["translation"] for p in filtered_props]
    sbert_model = load_sbert_model(sbert_model_name)

    query_embedding = encode_query(constraint_text, sbert_model)
    prop_embeddings = sbert_model.encode(prop_texts, convert_to_numpy=True)

    similarities = compute_cosine_similarity(query_embedding, prop_embeddings)
    top_k = min(max(1, k), len(prop_texts))
    top_idx = np.argsort(similarities)[::-1][:top_k]
    candidates = [filtered_props[i] for i in top_idx]

    pairs = [(prop["translation"], constraint_text) for prop in candidates]
    if not pairs:
        return 0.0

    probs = score_nli_pairs(nli_model, pairs)  # [P(contra), P(neutral), P(entail)]
    return float(np.max(probs[:, 2]))


def compute_list_nli_entailment(
    constraint_text: str,
    propositions_from_text: List[Dict[str, Any]],
    nli_model,
    k: int = SBERT_TOP_K,
    sbert_model_name: str = SBERT_MODEL,
):
    """
    Return top-3 NLI rows by entailment probability for diagnostics.
    """
    filtered_props = [
        p for p in propositions_from_text
        if isinstance(p, dict) and isinstance(p.get("translation"), str) and p["translation"].strip()
    ]
    if not filtered_props:
        return []

    prop_texts = [p["translation"] for p in filtered_props]
    sbert_model = load_sbert_model(sbert_model_name)

    query_embedding = encode_query(constraint_text, sbert_model)
    prop_embeddings = sbert_model.encode(prop_texts, convert_to_numpy=True)

    similarities = compute_cosine_similarity(query_embedding, prop_embeddings)
    top_k = min(max(1, k), len(prop_texts))
    top_idx = np.argsort(similarities)[::-1][:top_k]
    candidates = [filtered_props[i] for i in top_idx]

    pairs = [(prop["translation"], constraint_text) for prop in candidates]
    if not pairs:
        return []

    probs = score_nli_pairs(nli_model, pairs)
    top = sorted(probs, key=lambda x: x[2], reverse=True)[:3]
    return [row.tolist() for row in top]


def assign_weights(
    pathfile: str,  # kept for interface compatibility (not used for enrichment anymore)
    json_path: str,
    hardness_criterion: float = HARDNESS_CONSTANT,
    k: int = 10,
    chunk_size: int = 512,     # retained for backward compatibility
    chunk_overlap: int = 50,   # retained for backward compatibility
    sbert_model_name: str = SBERT_MODEL,
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Classify constraints into hard/soft on the ORIGINAL structure only.

    IMPORTANT:
    - No call to enrich_logic_structure here.
    - Query-time embellishment should happen later, after top-K retrieval.
    """
    if verbose:
        print(f"Loading ORIGINAL logified JSON from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        logified = json.load(f)

    primitive_props = logified.get("primitive_props", [])
    constraints = _normalize_constraints(logified)

    if not constraints:
        if verbose:
            print("No constraints found.")
        output = {
            "primitive_props": primitive_props,
            "hard_constraints": [],
            "soft_constraints": [],
        }
        out_path = Path(json_path).parent / (Path(json_path).stem + "_weighted.json")
        with open(out_path, "w", encoding="utf-8") as wf:
            json.dump(output, wf, indent=2, ensure_ascii=False)
        return output

    if verbose:
        print(f"Found {len(primitive_props)} primitive propositions")
        print(f"Found {len(constraints)} constraints (pre-enrichment/original)")
        print(f"Loading NLI model: {nli_model_name}")

    nli_model = load_nli_model(nli_model_name)

    required_fields = {"id", "translation", "formula"}
    missing = [c for c in constraints if not required_fields.issubset(c.keys())]
    if missing:
        raise ValueError(
            "[weights] constraints missing required fields: id, translation, formula"
        )

    hard_constraints = []
    soft_constraints = []

    if verbose:
        print(
            f"\nClassifying {len(constraints)} constraints "
            f"(hardness_criterion={hardness_criterion})..."
        )

    for i, constraint in enumerate(constraints):
        cid = constraint.get("id", f"C_{i+1}")
        ctext = (constraint.get("translation") or "").strip()
        formula = constraint.get("formula", "")

        if not ctext:
            if verbose:
                print(f"  [{i+1}/{len(constraints)}] {cid}: SKIPPED (no translation)")
            continue

        # Keep upstream llm_weight if present; default conservative mid-confidence.
        llm_weight = float(constraint.get("llm_weight", constraint.get("weight", 0.5)))

        nli_entailment = compute_nli_entailment(
            constraint_text=ctext,
            propositions_from_text=primitive_props,
            nli_model=nli_model,
            k=k,
            sbert_model_name=sbert_model_name,
        )

        list_nli = compute_list_nli_entailment(
            constraint_text=ctext,
            propositions_from_text=primitive_props,
            nli_model=nli_model,
            k=k,
            sbert_model_name=sbert_model_name,
        )

        combined = llm_weight * nli_entailment

        out_c = {
            "id": cid,
            "formula": formula,
            "translation": ctext,
            "evidence": constraint.get("evidence", ""),
            "reasoning": constraint.get("reasoning", ""),
            "llm_weight": llm_weight,
            "nli_entailment": nli_entailment,
            "combined=(llm)*(nli)": combined,
            "hardness_constant": hardness_criterion,
            "list nli": list_nli,
        }

        if combined >= hardness_criterion:
            hard_constraints.append(out_c)
            if verbose:
                print(
                    f"  [{i+1}/{len(constraints)}] {cid}: "
                    f"llm={llm_weight:.2f} × nli={nli_entailment:.2f} = {combined:.2f} → HARD"
                )
        else:
            out_c["weight"] = combined
            soft_constraints.append(out_c)
            if verbose:
                print(
                    f"  [{i+1}/{len(constraints)}] {cid}: "
                    f"llm={llm_weight:.2f} × nli={nli_entailment:.2f} = {combined:.2f} → SOFT"
                )

    output = {
        "primitive_props": primitive_props,
        "hard_constraints": hard_constraints,
        "soft_constraints": soft_constraints,
    }

    out_path = Path(json_path).parent / (Path(json_path).stem + "_weighted.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    if verbose:
        print("\n✓ Weighting complete (ORIGINAL structure only, no enrichment)")
        print(f"  Hard constraints: {len(hard_constraints)}")
        print(f"  Soft constraints: {len(soft_constraints)}")
        print(f"  Output saved to: {out_path}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Assign hard/soft weights on original logified constraints only "
            "(query-time embellishment is handled downstream)."
        )
    )
    parser.add_argument("pathfile", help="Path to source document file (kept for compatibility)")
    parser.add_argument("json_path", help="Path to original logified JSON file")
    parser.add_argument(
        "--hardness-criterion",
        type=float,
        default=HARDNESS_CONSTANT,
        help="Threshold for hard classification",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=SBERT_TOP_K,
        help="Number of top propositions for NLI support scoring",
    )
    parser.add_argument("--chunk-size", type=int, default=512, help="Compatibility arg")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Compatibility arg")
    parser.add_argument("--quiet", action="store_true", help="Suppress logs")
    args = parser.parse_args()

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
            verbose=not args.quiet,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
