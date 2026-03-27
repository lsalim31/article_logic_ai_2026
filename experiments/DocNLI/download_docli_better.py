#!/usr/bin/env python3
"""
download_fever_nli.py

Download and filter binary-FEVER-NLI dataset for balanced NLI experiments.

This script:
1. Downloads all 10K examples from binary-FEVER-NLI
2. Groups by premise and computes balance scores
3. Filters to "gold" premises (≥5 hypotheses, score ≥0.8, mixed labels)
4. Saves gold_balanced.json (full filtered set) for future experiments
5. Optionally samples N premises for current experiment

Balance score: min(ent, not_ent) / max(ent, not_ent)
- 3:3 → 1.0 (perfect)
- 4:5 → 0.8 (good)
- 2:6 → 0.33 (poor)

Usage:
    python download_fever_nli.py                          # Create gold set + sample 10
    python download_fever_nli.py --num-premises 20        # Sample 20 from gold
    python download_fever_nli.py --min-score 0.6          # Lower balance threshold
    python download_fever_nli.py --min-hypotheses 8       # Require more hypotheses
"""

import copy
import json
import random
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict


# URL for binary-FEVER-NLI
FEVER_NLI_URL = "https://raw.githubusercontent.com/salesforce/DocNLI/main/Data/binary-FEVER-NLI/test.txt"

# Paths
_script_dir = Path(__file__).resolve().parent
FEVER_NLI_DIR = _script_dir / "fever-nli"
GOLD_OUTPUT_PATH = FEVER_NLI_DIR / "gold_balanced.json"

# Default filter criteria
DEFAULT_MIN_HYPOTHESES = 5
DEFAULT_MIN_BALANCE_SCORE = 0.8
DEFAULT_NUM_PREMISES = 10


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def compute_balance_score(num_entailment: int, num_not_entailment: int) -> float:
    """
    Compute balance score for a premise.
    
    Score = min(ent, not_ent) / max(ent, not_ent)
    - 1.0 = perfectly balanced
    - 0.0 = completely imbalanced (one class only)
    """
    if num_entailment == 0 or num_not_entailment == 0:
        return 0.0
    return min(num_entailment, num_not_entailment) / max(num_entailment, num_not_entailment)


def download_and_parse() -> List[Dict[str, Any]]:
    """
    Download binary-FEVER-NLI and parse TSV format.

    Returns:
        List of example dicts with keys: label, premise, hypothesis, original_idx
    """
    print(f"Downloading binary-FEVER-NLI from {FEVER_NLI_URL}...")

    with urllib.request.urlopen(FEVER_NLI_URL) as response:
        content = response.read().decode('utf-8')

    examples = []
    lines = content.strip().split('\n')

    for idx, line in enumerate(lines):
        parts = line.split('\t')
        if len(parts) != 3:
            print(f"  Warning: Skipping malformed line {idx}: {line[:50]}...")
            continue

        label, premise, hypothesis = parts
        examples.append({
            "original_idx": idx,
            "label": label.strip(),
            "premise": premise.strip(),
            "hypothesis": hypothesis.strip()
        })

    print(f"  Downloaded {len(examples)} examples")
    return examples


def group_by_premise(examples: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Group examples by premise text and compute statistics.

    Returns:
        Dict mapping premise_text -> {
            "hypotheses": [...],
            "first_original_idx": int,
            "num_entailment": int,
            "num_not_entailment": int,
            "balance_score": float
        }
    """
    premises_dict = defaultdict(lambda: {
        "hypotheses": [],
        "first_original_idx": None,
        "num_entailment": 0,
        "num_not_entailment": 0
    })

    for ex in examples:
        premise_text = ex["premise"]
        data = premises_dict[premise_text]

        if data["first_original_idx"] is None:
            data["first_original_idx"] = ex["original_idx"]

        data["hypotheses"].append({
            "hypothesis": ex["hypothesis"],
            "label": ex["label"],
            "original_idx": ex["original_idx"]
        })

        if ex["label"] == "entailment":
            data["num_entailment"] += 1
        else:
            data["num_not_entailment"] += 1

    # Compute balance scores
    for premise_text, data in premises_dict.items():
        data["balance_score"] = compute_balance_score(
            data["num_entailment"],
            data["num_not_entailment"]
        )

    print(f"  Found {len(premises_dict)} unique premises")
    return dict(premises_dict)


def filter_gold_premises(
    premises_dict: Dict[str, Dict[str, Any]],
    min_hypotheses: int,
    min_balance_score: float
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Filter to "gold" premises meeting quality criteria.

    Criteria:
    - At least min_hypotheses hypotheses
    - Balance score >= min_balance_score
    - Must have both entailment and not_entailment (mixed)

    Returns:
        List of (premise_text, premise_data) tuples, sorted by balance_score descending
    """
    filtered = []

    for premise_text, data in premises_dict.items():
        num_hyps = len(data["hypotheses"])
        score = data["balance_score"]
        is_mixed = data["num_entailment"] > 0 and data["num_not_entailment"] > 0

        if num_hyps >= min_hypotheses and score >= min_balance_score and is_mixed:
            filtered.append((premise_text, data))

    # Sort by balance score (best first), then by number of hypotheses
    filtered.sort(key=lambda x: (x[1]["balance_score"], len(x[1]["hypotheses"])), reverse=True)

    return filtered


def build_premises_list(
    filtered_premises: List[Tuple[str, Dict[str, Any]]],
    start_id: int = 0
) -> List[Dict[str, Any]]:
    """
    Build structured premises list for JSON output.
    """
    premises_list = []

    for i, (premise_text, data) in enumerate(filtered_premises):
        premises_list.append({
            "premise_id": start_id + i,
            "premise": premise_text,
            "premise_word_count": count_words(premise_text),
            "first_original_idx": data["first_original_idx"],
            "num_entailment": data["num_entailment"],
            "num_not_entailment": data["num_not_entailment"],
            "balance_score": round(data["balance_score"], 3),
            "hypotheses": data["hypotheses"]
        })

    return premises_list


def flatten_to_examples(premises_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten premises to individual examples for compatibility.
    """
    examples = []
    example_id = 0

    for premise_data in premises_list:
        for hyp in premise_data["hypotheses"]:
            examples.append({
                "example_id": example_id,
                "premise_id": premise_data["premise_id"],
                "original_idx": hyp["original_idx"],
                "premise": premise_data["premise"],
                "premise_word_count": premise_data["premise_word_count"],
                "hypothesis": hyp["hypothesis"],
                "label": hyp["label"]
            })
            example_id += 1

    return examples


def compute_statistics(premises_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute dataset statistics."""
    total_hypotheses = sum(len(p["hypotheses"]) for p in premises_list)
    total_entailment = sum(p["num_entailment"] for p in premises_list)
    total_not_entailment = sum(p["num_not_entailment"] for p in premises_list)
    
    avg_balance = sum(p["balance_score"] for p in premises_list) / len(premises_list) if premises_list else 0
    
    return {
        "num_premises": len(premises_list),
        "num_examples": total_hypotheses,
        "label_distribution": {
            "entailment": total_entailment,
            "not_entailment": total_not_entailment
        },
        "entailment_percentage": round(total_entailment / total_hypotheses * 100, 1) if total_hypotheses > 0 else 0,
        "avg_hypotheses_per_premise": round(total_hypotheses / len(premises_list), 1) if premises_list else 0,
        "avg_balance_score": round(avg_balance, 3),
        "min_balance_score": min(p["balance_score"] for p in premises_list) if premises_list else 0,
        "max_balance_score": max(p["balance_score"] for p in premises_list) if premises_list else 0
    }


def save_dataset(
    premises_list: List[Dict[str, Any]],
    output_path: Path,
    filter_criteria: Dict[str, Any],
    is_sample: bool = False,
    sampled_from: str = None
) -> None:
    """Save premises and examples to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    examples = flatten_to_examples(premises_list)
    stats = compute_statistics(premises_list)

    metadata = {
        "source": "binary-FEVER-NLI (https://github.com/salesforce/DocNLI)",
        "original_source": "FEVER dataset (Wikipedia passages)",
        "filter_criteria": filter_criteria,
        "download_timestamp": datetime.now().isoformat(),
        **stats
    }
    
    if is_sample:
        metadata["sampled_from"] = sampled_from
        metadata["is_sample"] = True
    else:
        metadata["is_gold_set"] = True

    data = {
        "metadata": metadata,
        "premises": premises_list,
        "examples": examples
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved to {output_path}")
    print(f"    Premises: {stats['num_premises']}")
    print(f"    Examples: {stats['num_examples']}")
    print(f"    Entailment: {stats['entailment_percentage']}%")
    print(f"    Avg balance score: {stats['avg_balance_score']}")


def sample_premises(
    premises_list: List[Dict[str, Any]],
    num_premises: int,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Sample N premises from the gold set.
    
    Samples from top-balanced premises to maintain quality.
    Uses deep copy to avoid mutating the original gold set.
    """
    random.seed(seed)

    if len(premises_list) <= num_premises:
        print(f"  Warning: Only {len(premises_list)} premises available, using all")
        sampled = copy.deepcopy(premises_list)
    else:
        # Sample from top 2x to maintain balance quality
        pool_size = min(len(premises_list), num_premises * 2)
        pool = premises_list[:pool_size]
        sampled = copy.deepcopy(random.sample(pool, num_premises))

    # Re-assign premise IDs for the sample (safe now with deep copy)
    for i, premise in enumerate(sampled):
        premise["premise_id"] = i

    return sampled


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and filter binary-FEVER-NLI for balanced NLI experiments"
    )
    parser.add_argument(
        "--min-hypotheses",
        type=int,
        default=DEFAULT_MIN_HYPOTHESES,
        help=f"Minimum hypotheses per premise (default: {DEFAULT_MIN_HYPOTHESES})"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_BALANCE_SCORE,
        help=f"Minimum balance score (default: {DEFAULT_MIN_BALANCE_SCORE})"
    )
    parser.add_argument(
        "--num-premises",
        type=int,
        default=DEFAULT_NUM_PREMISES,
        help=f"Number of premises to sample (default: {DEFAULT_NUM_PREMISES})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)"
    )
    parser.add_argument(
        "--gold-only",
        action="store_true",
        help="Only create gold set, don't sample"
    )
    parser.add_argument(
        "--sample-output",
        type=Path,
        default=None,
        help="Output path for sample (default: fever-nli/sample_{num_premises}.json)"
    )

    args = parser.parse_args()

    # Download and parse
    examples = download_and_parse()

    # Group by premise
    print("Grouping by premise and computing statistics...")
    premises_dict = group_by_premise(examples)

    # Show overall stats
    total_ent = sum(1 for ex in examples if ex["label"] == "entailment")
    print(f"  Overall: {total_ent} entailment ({total_ent/len(examples)*100:.1f}%), "
          f"{len(examples)-total_ent} not_entailment ({(len(examples)-total_ent)/len(examples)*100:.1f}%)")

    # Filter to gold premises
    print(f"Filtering to gold premises (≥{args.min_hypotheses} hyps, score ≥{args.min_score})...")
    filtered = filter_gold_premises(
        premises_dict,
        args.min_hypotheses,
        args.min_score
    )
    print(f"  {len(filtered)} premises meet gold criteria")

    if not filtered:
        print("ERROR: No premises meet the filter criteria. Try lowering thresholds.")
        return 1

    # Build gold premises list
    gold_premises = build_premises_list(filtered)

    # Save gold set
    filter_criteria = {
        "min_hypotheses": args.min_hypotheses,
        "min_balance_score": args.min_score,
        "require_mixed_labels": True
    }

    print("\nSaving gold set...")
    save_dataset(gold_premises, GOLD_OUTPUT_PATH, filter_criteria, is_sample=False)

    # Sample if requested
    if not args.gold_only:
        print(f"\nSampling {args.num_premises} premises...")
        sampled = sample_premises(gold_premises, args.num_premises, seed=args.seed)

        sample_output = args.sample_output
        if sample_output is None:
            sample_output = FEVER_NLI_DIR / f"sample_{args.num_premises}.json"

        sample_criteria = {
            **filter_criteria,
            "num_premises_sampled": args.num_premises,
            "seed": args.seed
        }

        print("Saving sample...")
        save_dataset(
            sampled,
            sample_output,
            sample_criteria,
            is_sample=True,
            sampled_from=str(GOLD_OUTPUT_PATH)
        )

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
