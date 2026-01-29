#!/usr/bin/env python3
"""
download_sample.py

Download and sample premises from DocNLI test set with ALL their hypotheses.

This script groups examples by premise (document), filters by word count,
and samples N unique premises with all their associated hypotheses.

Filtering criteria:
- Premise length: 200-500 words
- Sample N unique premises (default: 10)

Output:
- doc-nli/sample_100.json (contains premises list and flattened examples)

Usage:
    pip install datasets
    python download_sample.py
    python download_sample.py --num-premises 10
    python download_sample.py --num-premises 20 --output doc-nli/sample_20_premises.json
"""

import json
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


# Paths
_script_dir = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = _script_dir / "doc-nli" / "sample_100.json"

# Filtering criteria
MIN_PREMISE_WORDS = 200
MAX_PREMISE_WORDS = 500
DEFAULT_NUM_PREMISES = 10


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def download_and_group_by_premise() -> Dict[str, Dict[str, Any]]:
    """
    Download DocNLI test set and group examples by premise.

    Returns:
        Dict mapping premise_text -> {
            "hypotheses": [{"hypothesis": str, "label": str, "original_idx": int}, ...],
            "first_original_idx": int
        }
    """
    print("Loading DocNLI test set from HuggingFace Datasets...")

    dataset = load_dataset("saattrupdan/doc-nli", split="test")

    # Group by premise text
    premises_dict = defaultdict(lambda: {"hypotheses": [], "first_original_idx": None})

    for idx, example in enumerate(dataset):
        premise_text = example["premise"]

        if premises_dict[premise_text]["first_original_idx"] is None:
            premises_dict[premise_text]["first_original_idx"] = idx

        premises_dict[premise_text]["hypotheses"].append({
            "hypothesis": example["hypothesis"],
            "label": example["label"],  # "entailment" or "not_entailment"
            "original_idx": idx
        })

    print(f"  Loaded {len(dataset)} examples from test set")
    print(f"  Found {len(premises_dict)} unique premises")

    return dict(premises_dict)


def filter_premises(
    premises_dict: Dict[str, Dict[str, Any]],
    min_words: int,
    max_words: int
) -> List[Tuple[str, Dict[str, Any], int]]:
    """
    Filter premises by word count.

    Returns:
        List of (premise_text, premise_data, word_count) tuples
    """
    filtered = []
    for premise_text, premise_data in premises_dict.items():
        word_count = count_words(premise_text)
        if min_words <= word_count <= max_words:
            filtered.append((premise_text, premise_data, word_count))

    return filtered


def sample_premises(
    filtered_premises: List[Tuple[str, Dict[str, Any], int]],
    num_premises: int,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Sample N premises with all their hypotheses.

    Returns:
        List of premise dicts with structure:
        {
            "premise_id": int,
            "premise": str,
            "premise_word_count": int,
            "first_original_idx": int,
            "hypotheses": [{"hypothesis": str, "label": str, "original_idx": int}, ...]
        }
    """
    random.seed(seed)

    if len(filtered_premises) < num_premises:
        print(f"  Warning: Only {len(filtered_premises)} premises available, using all")
        num_premises = len(filtered_premises)

    sampled = random.sample(filtered_premises, num_premises)

    # Build output structure
    premises_list = []
    for i, (premise_text, premise_data, word_count) in enumerate(sampled):
        premises_list.append({
            "premise_id": i,
            "premise": premise_text,
            "premise_word_count": word_count,
            "first_original_idx": premise_data["first_original_idx"],
            "hypotheses": premise_data["hypotheses"]
        })

    return premises_list


def flatten_to_examples(premises_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten premises to individual examples for compatibility.

    Returns:
        List of example dicts with structure:
        {
            "example_id": int,
            "premise_id": int,
            "original_idx": int,
            "premise": str,
            "hypothesis": str,
            "label": str
        }
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


def save_sample(
    premises_list: List[Dict[str, Any]],
    examples: List[Dict[str, Any]],
    output_path: Path,
    num_premises: int
) -> None:
    """Save sampled premises and examples to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count label distribution
    label_counts = {"entailment": 0, "not_entailment": 0}
    for ex in examples:
        label_counts[ex["label"]] = label_counts.get(ex["label"], 0) + 1

    data = {
        "metadata": {
            "source": "DocNLI test split (HuggingFace: saattrupdan/doc-nli)",
            "filter_criteria": {
                "min_premise_words": MIN_PREMISE_WORDS,
                "max_premise_words": MAX_PREMISE_WORDS,
                "num_premises_requested": num_premises
            },
            "download_timestamp": datetime.now().isoformat(),
            "num_premises": len(premises_list),
            "num_examples": len(examples),
            "label_distribution": label_counts,
            "avg_hypotheses_per_premise": len(examples) / len(premises_list) if premises_list else 0
        },
        "premises": premises_list,
        "examples": examples
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved {len(premises_list)} premises with {len(examples)} total examples to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and sample premises from DocNLI test set with all hypotheses"
    )
    parser.add_argument(
        "--num-premises",
        type=int,
        default=DEFAULT_NUM_PREMISES,
        help=f"Number of unique premises to sample (default: {DEFAULT_NUM_PREMISES})"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output path (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)"
    )

    args = parser.parse_args()

    if not HAS_DATASETS:
        print("Error: datasets library import failed.")
        print(f"Error details: {DATASETS_ERROR}")
        print("Install with: pip install datasets")
        return 1

    # Download and group by premise
    premises_dict = download_and_group_by_premise()

    # Filter by word count
    print(f"Filtering by premise word count ({MIN_PREMISE_WORDS}-{MAX_PREMISE_WORDS})...")
    filtered = filter_premises(premises_dict, MIN_PREMISE_WORDS, MAX_PREMISE_WORDS)
    print(f"  {len(filtered)} premises match word count criteria")

    # Calculate avg hypotheses per premise
    total_hyps = sum(len(p[1]["hypotheses"]) for p in filtered)
    avg_hyps = total_hyps / len(filtered) if filtered else 0
    print(f"  Average hypotheses per premise: {avg_hyps:.1f}")

    # Sample premises
    print(f"Sampling {args.num_premises} premises with all their hypotheses...")
    premises_list = sample_premises(filtered, args.num_premises, seed=args.seed)

    # Flatten to examples
    examples = flatten_to_examples(premises_list)

    # Report
    print(f"  Sampled {len(premises_list)} premises with {len(examples)} total hypotheses")

    # Save
    print(f"Saving to {args.output}...")
    save_sample(premises_list, examples, args.output, args.num_premises)

    print("Done!")
    return 0


if __name__ == "__main__":
    exit(main())
