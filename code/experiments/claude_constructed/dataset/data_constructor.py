"""
Create a DocNLI dataset with single-sentence hypotheses.

This script:
1. Selects diverse premises (100-400 words) from DocNLI
2. Uses an LLM to generate single-sentence hypotheses:
   - 3 entailment (facts directly verifiable from premise)
   - 3 not_entailment (contradictions or unverifiable claims)
3. Saves the dataset in the same format as other DocNLI experiments
"""

import json
import os
import random
from datetime import datetime
from datasets import load_dataset
from openai import OpenAI

# Configuration
NUM_PREMISES = 10  # Number of premises to include
HYPOTHESES_PER_LABEL = 3  # 3 entailment + 3 not_entailment per premise
MIN_PREMISE_WORDS = 150
MAX_PREMISE_WORDS = 350
SEED = 42

OUTPUT_DIR = "/workspace/repo/code/experiments/DocNLI/docnli-single-sentence"


def get_diverse_premises(num_premises: int) -> list: """Load DocNLI and select diverse premises."""
    print("Loading DocNLI from HuggingFace...")
    ds = load_dataset("saattrupdan/doc-nli", split="train")

    print(f"Filtering premises ({MIN_PREMISE_WORDS}-{MAX_PREMISE_WORDS} words)...")

    premises = []
    seen_starts = set()

    for item in ds:
        premise = item['premise'
]
        premise_words = len(premise.split())

        if MIN_PREMISE_WORDS <= premise_words <= MAX_PREMISE_WORDS:
            # Skip similar premises (same start)
            start = premise[
    : 100
].lower()
            if start in seen_starts:
                continue
            seen_starts.add(start)

            premises.append({
                'premise': premise,
                'premise_words': premise_words
})

            if len(premises) >= num_premises * 3:  # Get extra for filtering
                break

    # Sample randomly
    random.seed(SEED)
    selected = random.sample(premises, min(num_premises, len(premises)))

    print(f"Selected {len(selected)} diverse premises")
    return selected


def generate_hypotheses(premise: str, api_key: str) -> dict: """Generate single-sentence hypotheses for a premise using LLM."""

    client = OpenAI(api_key=api_key)

    prompt = f"""You are generating test data for a Natural Language Inference (NLI) system.

Given the following premise, generate exactly 6 single-sentence hypotheses:
- 3 ENTAILMENT hypotheses: Facts that are DIRECTLY stated or clearly implied by the premise
- 3 NOT_ENTAILMENT hypotheses: Claims that either contradict the premise OR contain information not verifiable from the premise

IMPORTANT RULES:
1. Each hypothesis must be a SINGLE SENTENCE (no periods except at the end)
2. Keep hypotheses between 10-25 words
3. Entailment hypotheses should be verifiable directly from the premise text
4. Not_entailment hypotheses should have subtle but clear issues (wrong dates, names, numbers, or added facts)
5. Make hypotheses diverse - cover different aspects of the premise

PREMISE: {premise
}

Respond in this exact JSON format: {
    {
        "entailment": [
            "First entailment hypothesis.",
            "Second entailment hypothesis.",
            "Third entailment hypothesis."
        ],
        "not_entailment": [
            "First not_entailment hypothesis (contains error or unverifiable claim).",
            "Second not_entailment hypothesis (contains error or unverifiable claim).",
            "Third not_entailment hypothesis (contains error or unverifiable claim)."
        ]
    }
}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
    {
        "role": "user",
        "content": prompt
    }
],
        temperature=0.3,
        response_format={
    "type": "json_object"
}
    )

    result = json.loads(response.choices[
    0
].message.content)
    return result


def create_dataset(num_premises: int, api_key: str) -> dict: """Create the full dataset."""

    premises = get_diverse_premises(num_premises)

    dataset = {
    "metadata": {
        "source": "DocNLI (premises) + GPT-4 generated single-sentence hypotheses",
        "original_source": "HuggingFace: saattrupdan/doc-nli (train split)",
        "generation_method": "LLM-generated single-sentence hypotheses for NLI testing",
        "filter_criteria": {
            "min_words": MIN_PREMISE_WORDS,
            "max_words": MAX_PREMISE_WORDS,
            "hypotheses_per_label": HYPOTHESES_PER_LABEL
        },
        "download_timestamp": datetime.now().isoformat(),
        "num_premises": len(premises),
        "num_examples": len(premises) * HYPOTHESES_PER_LABEL * 2,
        "label_distribution": {
            "entailment": len(premises) * HYPOTHESES_PER_LABEL,
            "not_entailment": len(premises) * HYPOTHESES_PER_LABEL
        },
        "entailment_percentage": 50.0,
        "avg_hypotheses_per_premise": HYPOTHESES_PER_LABEL * 2,
        "is_single_sentence": True
    },
    "premises": []
}

    for i, p in enumerate(premises):
        print(f"\nProcessing premise {i+1}/{len(premises)}...")
        print(f"  Words: {p['premise_words']}")
        print(f"  Preview: {p['premise'][:100]}...")

        # Generate hypotheses
        try:
            hyps = generate_hypotheses(p['premise'
], api_key)

            premise_data = {
    "premise_id": i,
    "premise": p['premise'
    ],
    "premise_word_count": p['premise_words'
    ],
    "num_entailment": len(hyps['entailment'
    ]),
    "num_not_entailment": len(hyps['not_entailment'
    ]),
    "hypotheses": []
}

            # Add entailment hypotheses
            for j, h in enumerate(hyps['entailment'
]):
                premise_data['hypotheses'
].append({
    "hypothesis": h,
    "label": "entailment",
    "original_idx": i * 6 + j
})
                print(f"  ✅ Entailment: {h[:60]}...")

            # Add not_entailment hypotheses
            for j, h in enumerate(hyps['not_entailment'
]):
                premise_data['hypotheses'
].append({
    "hypothesis": h,
    "label": "not_entailment",
    "original_idx": i * 6 + len(hyps['entailment'
    ]) + j
})
                print(f"  ❌ Not_entailment: {h[:60]}...")

            dataset['premises'
].append(premise_data)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Update metadata
    dataset['metadata'
]['num_premises'
] = len(dataset['premises'
])
    dataset['metadata'
]['num_examples'
] = sum(len(p['hypotheses'
]) for p in dataset['premises'
])

    return dataset


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create single-sentence hypothesis dataset")
    parser.add_argument("--num-premises", type=int, default=NUM_PREMISES, help="Number of premises")
    parser.add_argument("--api-key", type=str, default=os.environ.get("OPENAI_API_KEY"), help="OpenAI API key")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: No API key provided. Set OPENAI_API_KEY or use --api-key")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate dataset
    print("=" * 80)
    print("CREATING SINGLE-SENTENCE HYPOTHESIS DATASET")
    print("=" * 80)

    dataset = create_dataset(args.num_premises, args.api_key)

    # Save dataset
    output_path = os.path.join(OUTPUT_DIR,
"gold_balanced.json")
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\n{'=' * 80}")
    print(f"DATASET CREATED SUCCESSFULLY")
    print(f"{'=' * 80}")
    print(f"Output: {output_path}")
    print(f"Premises: {dataset['metadata']['num_premises']}")
    print(f"Total examples: {dataset['metadata']['num_examples']}")
    print(f"Entailment: {dataset['metadata']['label_distribution']['entailment']}")
    print(f"Not_entailment: {dataset['metadata']['label_distribution']['not_entailment']}")


if __name__ == "__main__":
    main()
