"""
Create a LogiQA dataset with binary yes/no hypotheses for the Logify pipeline.

This script:
1. Loads LogiQA2 test data (multiple choice questions)
2. Converts each question to binary yes/no format:
   - The correct answer option becomes an "entailment" (yes) hypothesis
   - Incorrect answer options become "not_entailment" (no) hypotheses
3. Saves the dataset in a format compatible with the Logify experiment pipeline

The LogiQA dataset contains logical reasoning questions with:
- A context/premise (text)
- A question
- 4 answer options (one correct)
- Reasoning type tags

We transform this to:
- premise: context + question combined
- hypotheses: answer options as statements with yes/no labels
"""
import argparse
import json
import os
import random
from datetime import datetime
from pathlib import Path


# Configuration
NUM_SAMPLES = 15  # Number of LogiQA samples to include
MIN_CONTEXT_WORDS = 30
MAX_CONTEXT_WORDS = 300
SEED = 42

_script_dir = Path(__file__).resolve().parent
OUTPUT_DIR = _script_dir
LOGIQA_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "logiqa2" / "test.txt"


def load_logiqa_data(data_path: Path) -> list:
    """Load LogiQA data from JSONL file."""
    print(f"Loading LogiQA data from: {data_path}")

    samples = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sample = json.loads(line)
                    samples.append(sample)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line: {e}")
                    continue

    print(f"Loaded {len(samples)} total samples")
    return samples


def filter_samples(samples: list, num_samples: int) -> list:
    """Filter and select diverse samples from LogiQA."""
    print(f"Filtering samples ({MIN_CONTEXT_WORDS}-{MAX_CONTEXT_WORDS} words)...")

    filtered = []
    seen_starts = set()

    for sample in samples:
        text = sample.get('text', '')
        word_count = len(text.split())

        # Check word count
        if not (MIN_CONTEXT_WORDS <= word_count <= MAX_CONTEXT_WORDS):
            continue

        # Check for valid answer and options
        if 'answer' not in sample or 'options' not in sample:
            continue
        if len(sample['options']) != 4:
            continue
        if not isinstance(sample['answer'], int) or sample['answer'] not in [0, 1, 2, 3]:
            continue

        # Skip similar contexts (same start)
        start = text[:80].lower()
        if start in seen_starts:
            continue
        seen_starts.add(start)

        filtered.append({
            'id': sample.get('id', len(filtered)),
            'text': text,
            'question': sample.get('question', ''),
            'options': sample['options'],
            'answer': sample['answer'],
            'type': sample.get('type', {}),
            'word_count': word_count
        })

        if len(filtered) >= num_samples * 3:  # Get extra for random selection
            break

    # Random sample
    random.seed(SEED)
    selected = random.sample(filtered, min(num_samples, len(filtered)))

    print(f"Selected {len(selected)} diverse samples")
    return selected


def convert_to_binary_format(samples: list) -> dict:
    """
    Convert LogiQA multiple choice to balanced binary yes/no format.

    For each sample:
    - premise = context + question
    - correct option -> hypothesis with label "yes"
    - ONE randomly selected incorrect option -> hypothesis with label "no"

    This creates a balanced dataset with equal yes/no distribution.
    """
    random.seed(SEED)

    dataset = {
        "metadata": {
            "source": "LogiQA2 (converted to balanced binary yes/no format)",
            "original_source": str(LOGIQA_DATA_PATH),
            "generation_method": "Multiple choice to balanced binary conversion (1 yes + 1 no per sample)",
            "conversion_rules": {
                "correct_answer": "yes",
                "one_random_incorrect": "no"
            },
            "filter_criteria": {
                "min_words": MIN_CONTEXT_WORDS,
                "max_words": MAX_CONTEXT_WORDS
            },
            "creation_timestamp": datetime.now().isoformat(),
            "num_samples": len(samples),
            "num_hypotheses": len(samples) * 2,  # 2 options per sample (1 yes + 1 no)
            "label_distribution": {
                "yes": len(samples),       # 1 correct per sample
                "no": len(samples)         # 1 incorrect per sample (balanced)
            }
        },
        "samples": []
    }

    for i, sample in enumerate(samples):
        # Combine context and question as the premise
        context = sample['text'].strip()
        question = sample['question'].strip()

        # Create combined premise
        if question:
            premise = f"{context}\n\nQuestion: {question}"
        else:
            premise = context

        correct_idx = sample['answer']
        options = sample['options']

        sample_data = {
            "sample_id": i,
            "original_id": sample['id'],
            "context": premise,
            "context_word_count": len(premise.split()),
            "reasoning_types": list(sample['type'].keys()) if sample['type'] else [],
            "qa_pairs": []
        }

        # Add the correct answer (yes)
        correct_option = options[correct_idx]
        hypothesis_text = f"The answer is: {correct_option}"
        sample_data["qa_pairs"].append({
            "question": hypothesis_text,
            "answer": "yes",
            "option_index": correct_idx,
            "is_correct_answer": True
        })

        # Select ONE random incorrect option (no)
        incorrect_indices = [idx for idx in range(len(options)) if idx != correct_idx]
        selected_incorrect_idx = random.choice(incorrect_indices)
        incorrect_option = options[selected_incorrect_idx]
        hypothesis_text = f"The answer is: {incorrect_option}"
        sample_data["qa_pairs"].append({
            "question": hypothesis_text,
            "answer": "no",
            "option_index": selected_incorrect_idx,
            "is_correct_answer": False
        })

        dataset["samples"].append(sample_data)

        print(f"  Sample {i}: 2 hypotheses (1 yes, 1 no) - balanced")

    return dataset


def create_dataset(num_samples: int) -> dict:
    """Create the full dataset."""

    # Load LogiQA data
    samples = load_logiqa_data(LOGIQA_DATA_PATH)

    # Filter and select samples
    selected = filter_samples(samples, num_samples)

    # Convert to binary format
    dataset = convert_to_binary_format(selected)

    return dataset


def main():
    parser = argparse.ArgumentParser(description="Create LogiQA binary hypothesis dataset")
    parser.add_argument("--num-samples", type=int, default=NUM_SAMPLES, help="Number of samples")
    parser.add_argument(
        "--output-name",
        default="logiqa_binary.json",
        help="Output filename (default: logiqa_binary.json)",
    )
    args = parser.parse_args()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate dataset
    print("=" * 80)
    print("CREATING LOGIQA BINARY HYPOTHESIS DATASET")
    print("=" * 80)

    dataset = create_dataset(args.num_samples)

    # Save dataset
    output_path = OUTPUT_DIR / args.output_name
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 80}")
    print("DATASET CREATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output: {output_path}")
    print(f"Samples: {dataset['metadata']['num_samples']}")
    print(f"Total hypotheses: {dataset['metadata']['num_hypotheses']}")
    print(f"Yes (correct): {dataset['metadata']['label_distribution']['yes']}")
    print(f"No (incorrect): {dataset['metadata']['label_distribution']['no']}")


if __name__ == "__main__":
    main()
