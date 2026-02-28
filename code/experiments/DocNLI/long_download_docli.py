#!/usr/bin/env python3
"""
download_docnli_long.py

Download and filter DocNLI dataset for balanced NLI experiments with LONG premises.

This script:
1. Downloads DocNLI test set from HuggingFace
2. Groups by premise and computes balance scores
3. Filters to "gold" premises (800-1200 words, ≥5 hypotheses, score ≥0.8, mixed labels)
4. Saves gold_balanced.json (full filtered set) for future experiments
5. Optionally samples N premises for current experiment

Balance score: min(ent, not_ent) / max(ent, not_ent)
- 3:3 → 1.0 (perfect)
- 4:5 → 0.8 (good)
- 2:6 → 0.33 (poor)

Usage:
    python download_docnli_long.py                          # Create gold set + sample 10
    python download_docnli_long.py --num-premises 20        # Sample 20 from gold
    python download_docnli_long.py --min-score 0.6          # Lower balance threshold
    python download_docnli_long.py --min-hypotheses 8       # Require more hypotheses
    python download_docnli_long.py --min-words 500 --max-words 800  # Different word range
"""

import copy
import json
import sys
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Try HuggingFace datasets
try:
    from datasets import load_dataset
    HAS_DATASETS = True
    DATASETS_ERROR = None
except ImportError as e:
    HAS_DATASETS = False
    DATASETS_ERROR = str(e)
except Exception as e:
    HAS_DATASETS = False
    DATASETS_ERROR = str(e)


# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from config.retrieval_config import DEFAULT_MIN_WORDS, DEFAULT_MAX_WORDS

# Default filter criteria

DEFAULT_MIN_HYPOTHESES = 5
DEFAULT_MIN_BALANCE_SCORE = 0.8
DEFAULT_NUM_PREMISES = 10

# Paths
_script_dir = Path(__file__).resolve().parent
DOCNLI_LONG_DIR = _script_dir / f"docnli-long_{DEFAULT_MIN_WORDS}_{DEFAULT_MAX_WORDS }"
GOLD_OUTPUT_PATH = DOCNLI_LONG_DIR / "gold_balanced.json"

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


def download_and_parse(min_words: int, max_words: int) -> List[Dict[str, Any]]:
    """
    Download DocNLI test set and parse, filtering by word count.

    Returns:
        List of example dicts with keys: label, premise, hypothesis, original_idx
    """
    print(f"Loading DocNLI test set from HuggingFace...")

    dataset = load_dataset("saattrupdan/doc-nli", split="test")
    print(f"  Loaded {len(dataset)} total examples")

    examples = []
    skipped_short = 0
    skipped_long = 0

    for idx, ex in enumerate(dataset):
        premise = ex["premise"]
        word_count = count_words(premise)

        if word_count < min_words:
            skipped_short += 1
            continue
        if word_count > max_words:
            skipped_long += 1
            continue

        examples.append({
            "original_idx": idx,
            "label": ex["label"],
            "premise": premise,
            "hypothesis": ex["hypothesis"],
            "word_count": word_count
        })

    print(f"  Filtered to {len(examples)} examples ({min_words}-{max_words} words)")
    print(f"  Skipped: {skipped_short} too short, {skipped_long} too long")
    return examples


def group_by_premise(examples: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Group examples by premise text and compute statistics.

    Returns:
        Dict mapping premise_text -> {
            "hypotheses": [...],
            "first_original_idx": int,
            "word_count": int,
            "num_entailment": int,
            "num_not_entailment": int,
            "balance_score": float
        }
    """
    premises_dict = defaultdict(lambda: {
        "hypotheses": [],
        "first_original_idx": None,
        "word_count": 0,
        "num_entailment": 0,
        "num_not_entailment": 0
    })

    for ex in examples:
        premise_text = ex["premise"]
        data = premises_dict[premise_text]

        if data["first_original_idx"] is None:
            data["first_original_idx"] = ex["original_idx"]
            data["word_count"] = ex["word_count"]

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

    print(f"  Found {len(premises_dict)} unique premises in word range")
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
            "premise_word_count": data["word_count"],
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
    if not premises_list:
        return {
            "num_premises": 0,
            "num_examples": 0,
            "label_distribution": {"entailment": 0, "not_entailment": 0},
            "entailment_percentage": 0,
            "avg_hypotheses_per_premise": 0,
            "avg_balance_score": 0,
            "min_balance_score": 0,
            "max_balance_score": 0,
            "avg_premise_words": 0,
            "min_premise_words": 0,
            "max_premise_words": 0
        }

    total_hypotheses = sum(len(p["hypotheses"]) for p in premises_list)
    total_entailment = sum(p["num_entailment"] for p in premises_list)
    total_not_entailment = sum(p["num_not_entailment"] for p in premises_list)

    avg_balance = sum(p["balance_score"] for p in premises_list) / len(premises_list)
    word_counts = [p["premise_word_count"] for p in premises_list]

    return {
        "num_premises": len(premises_list),
        "num_examples": total_hypotheses,
        "label_distribution": {
            "entailment": total_entailment,
            "not_entailment": total_not_entailment
        },
        "entailment_percentage": round(total_entailment / total_hypotheses * 100, 1) if total_hypotheses > 0 else 0,
        "avg_hypotheses_per_premise": round(total_hypotheses / len(premises_list), 1),
        "avg_balance_score": round(avg_balance, 3),
        "min_balance_score": min(p["balance_score"] for p in premises_list),
        "max_balance_score": max(p["balance_score"] for p in premises_list),
        "avg_premise_words": round(sum(word_counts) / len(word_counts), 1),
        "min_premise_words": min(word_counts),
        "max_premise_words": max(word_counts)
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
        "source": "DocNLI test split (HuggingFace: saattrupdan/doc-nli)",
        "original_source": "Various document sources (news, Wikipedia, etc.)",
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
    print(f"    Avg premise words: {stats['avg_premise_words']}")


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
        description="Download and filter DocNLI for balanced NLI experiments with long premises"
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=DEFAULT_MIN_WORDS,
        help=f"Minimum premise word count (default: {DEFAULT_MIN_WORDS})"
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=DEFAULT_MAX_WORDS,
        help=f"Maximum premise word count (default: {DEFAULT_MAX_WORDS})"
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
        help="Output path for sample (default: docnli-long/sample_{num_premises}.json)"
    )

    args = parser.parse_args()

    if not HAS_DATASETS:
        print("Error: datasets library import failed.")
        print(f"Error details: {DATASETS_ERROR}")
        print("Install with: pip install datasets")
        return 1

    # Download and parse
    examples = download_and_parse(args.min_words, args.max_words)

    if not examples:
        print("ERROR: No examples found in the specified word range.")
        return 1

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
        print("  Suggestions:")
        print("    --min-hypotheses 3")
        print("    --min-score 0.5")
        return 1

    # Build gold premises list
    gold_premises = build_premises_list(filtered)

    # Save gold set
    filter_criteria = {
        "min_words": args.min_words,
        "max_words": args.max_words,
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
            sample_output = DOCNLI_LONG_DIR / f"sample_{args.num_premises}.json"

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
