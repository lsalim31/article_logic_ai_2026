#!/usr/bin/env python3
"""
download_sample.py

Download and filter 100 examples from DocNLI test set.

Filtering criteria:
- Premise length: 200-500 words
- Balanced: 50 entailment, 50 not-entailment
- Priority: FEVER/SQuAD sources if metadata available

Output:
- doc-nli/sample_100.json

Usage:
    python download_sample.py
    python download_sample.py --output doc-nli/sample_100.json
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Try tensorflow_datasets, fall back to manual instructions
try:
    import tensorflow_datasets as tfds
    HAS_TFDS = True
except ImportError:
    HAS_TFDS = False


# Paths
_script_dir = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = _script_dir / "doc-nli" / "sample_100.json"

# Filtering criteria
MIN_PREMISE_WORDS = 200
MAX_PREMISE_WORDS = 500
NUM_ENTAILMENT = 50
NUM_NOT_ENTAILMENT = 50


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def filter_by_word_count(examples: List[Dict], min_words: int, max_words: int) -> List[Dict]:
    """Filter examples by premise word count."""
    filtered = []
    for ex in examples:
        word_count = count_words(ex["premise"])
        if min_words <= word_count <= max_words:
            ex["premise_word_count"] = word_count
            filtered.append(ex)
    return filtered


def download_with_tfds() -> List[Dict[str, Any]]:
    """Download DocNLI test set using TensorFlow Datasets."""
    print("Loading DocNLI test set from TensorFlow Datasets...")

    # Load test split
    dataset = tfds.load("doc_nli", split="test")

    examples = []
    for idx, example in enumerate(dataset):
        examples.append({
            "original_idx": idx,
            "premise": example["premise"].numpy().decode("utf-8"),
            "hypothesis": example["hypothesis"].numpy().decode("utf-8"),
            "label": "entailment" if example["label"].numpy() == 1 else "not_entailment"
        })

    print(f"  Loaded {len(examples)} examples from test set")
    return examples


def sample_balanced(
    examples: List[Dict],
    num_entailment: int,
    num_not_entailment: int,
    seed: int = 42
) -> List[Dict]:
    """Sample balanced examples from filtered pool."""
    random.seed(seed)

    # Separate by label
    entailment = [ex for ex in examples if ex["label"] == "entailment"]
    not_entailment = [ex for ex in examples if ex["label"] == "not_entailment"]

    print(f"  Filtered pool: {len(entailment)} entailment, {len(not_entailment)} not_entailment")

    # Check if we have enough
    if len(entailment) < num_entailment:
        print(f"  Warning: Only {len(entailment)} entailment examples available")
        num_entailment = len(entailment)
    if len(not_entailment) < num_not_entailment:
        print(f"  Warning: Only {len(not_entailment)} not_entailment examples available")
        num_not_entailment = len(not_entailment)

    # Sample
    sampled_entailment = random.sample(entailment, num_entailment)
    sampled_not_entailment = random.sample(not_entailment, num_not_entailment)

    # Combine and shuffle
    sampled = sampled_entailment + sampled_not_entailment
    random.shuffle(sampled)

    # Assign example_id
    for i, ex in enumerate(sampled):
        ex["example_id"] = i

    return sampled


def save_sample(examples: List[Dict], output_path: Path) -> None:
    """Save sampled examples to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "metadata": {
            "source": "DocNLI test split (TensorFlow Datasets)",
            "filter_criteria": {
                "min_premise_words": MIN_PREMISE_WORDS,
                "max_premise_words": MAX_PREMISE_WORDS,
                "num_entailment": NUM_ENTAILMENT,
                "num_not_entailment": NUM_NOT_ENTAILMENT
            },
            "download_timestamp": datetime.now().isoformat(),
            "num_examples": len(examples)
        },
        "examples": examples
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved {len(examples)} examples to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and filter 100 examples from DocNLI test set"
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

    if not HAS_TFDS:
        print("Error: tensorflow_datasets not installed.")
        print("Install with: pip install tensorflow_datasets tensorflow")
        return 1

    # Download
    examples = download_with_tfds()

    # Filter by word count
    print(f"Filtering by premise word count ({MIN_PREMISE_WORDS}-{MAX_PREMISE_WORDS})...")
    filtered = filter_by_word_count(examples, MIN_PREMISE_WORDS, MAX_PREMISE_WORDS)
    print(f"  {len(filtered)} examples match word count criteria")

    # Sample balanced
    print(f"Sampling {NUM_ENTAILMENT} entailment + {NUM_NOT_ENTAILMENT} not_entailment...")
    sampled = sample_balanced(filtered, NUM_ENTAILMENT, NUM_NOT_ENTAILMENT, seed=args.seed)

    # Save
    print(f"Saving to {args.output}...")
    save_sample(sampled, args.output)

    print("Done!")
    return 0


if __name__ == "__main__":
    exit(main())
