"""
Create a DocNLI dataset with single-sentence hypotheses.

This script:
1. Selects diverse premises (100-400 words) from DocNLI
2. Uses an LLM to generate single-sentence hypotheses:
   - N entailment (facts directly verifiable from premise)
   - N not_entailment (contradictions or unverifiable claims)
3. Saves the dataset in the same format as other DocNLI experiments
"""
import argparse
import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path
from openai import OpenAI


# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent.parent  # Go up 3 levels: dataset -> claude_constructed -> experiments -> code
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))    

from config.retrieval_config import REASONING_MODEL

# Configuration
NUM_PREMISES = 15  # Number of premises to include
HYPOTHESES_PER_LABEL = 5  # entailment + not_entailment per premise
MIN_PREMISE_WORDS = 100
MAX_PREMISE_WORDS = 400
SEED = 42

OUTPUT_DIR = _script_dir
LOCAL_DATA_PATH = _code_dir / "experiments" / "DocNLI" / "docnli-long_100_400" / "sample_10.json"


def get_diverse_premises(num_premises: int) -> list:
    """Load DocNLI from local JSON file and select diverse premises."""
    
    print(f"Loading DocNLI from local file: {LOCAL_DATA_PATH}")
    
    with open(LOCAL_DATA_PATH, 'r') as f:
        data = json.load(f)

    print(f"Filtering premises ({MIN_PREMISE_WORDS}-{MAX_PREMISE_WORDS} words)...")

    premises = []
    seen_starts = set()

    for premise_data in data['premises']:
        premise = premise_data['premise']
        premise_words = len(premise.split())

        if MIN_PREMISE_WORDS <= premise_words <= MAX_PREMISE_WORDS:
            # Skip similar premises (same start)
            start = premise[:100].lower()
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


def generate_hypotheses(premise: str, api_key: str, model: str = REASONING_MODEL) -> dict:
    """Generate single-sentence hypotheses for a premise using LLM."""

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"  # For OpenRouter
    )

    prompt = f"""You are generating test data for a Natural Language Inference (NLI) system that uses formal propositional logic.

The system works by:
1. Extracting atomic propositions from the premise (simple declarative statements like "X said Y", "X did Y", "X is Y")
2. Stripping modal words (should, must, typically, sometimes) from propositions
3. Matching hypothesis text to these propositions using semantic similarity
4. Using a logic solver to check entailment

Given the following premise, generate exactly {HYPOTHESES_PER_LABEL * 2} single-sentence hypotheses:
- {HYPOTHESES_PER_LABEL} ENTAILMENT hypotheses: Statements that can be verified as TRUE by combining 1-3 facts from the premise
- {HYPOTHESES_PER_LABEL} NOT_ENTAILMENT hypotheses: Statements that are FALSE or UNVERIFIABLE from the premise

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR ENTAILMENT HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

1. USE EXPLICIT FACTS ONLY
   ✓ Good: "Huey said she knew Francis since 1980"
   ✓ Good: "Francis told Huey that Johnson feared the drug test"
   ✓ Good: "The amendment was approved by voters in November 1987"
   ✗ Bad: "Huey recalls Francis implying..." (inference, not stated)
   ✗ Bad: "The text suggests that..." (meta-commentary)

2. REFERENCE WHAT WAS SAID, DONE, OR REPORTED
   ✓ Good: "X said that Y", "X testified that Y", "X stated that Y"
   ✓ Good: "X did Y", "X went to Y", "X worked at Y"
   ✗ Bad: "X implied that Y", "X suggested that Y", "X believed that Y" (unless explicitly stated)

3. COMBINE FACTS FROM DIFFERENT PARTS OF THE PREMISE
   ✓ Good: "Because [FACT from sentence 2], [FACT from sentence 5]"
   ✓ Good: "[Person] did [action1] and also [action2]"
   This tests the system's ability to combine multiple propositions.

4. USE NAMES, DATES, AND NUMBERS EXACTLY AS STATED
   ✓ Good: Use "NBC-TV" if the text says "NBC-TV"
   ✗ Bad: Paraphrase "NBC-TV" as "a television network"

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR NOT_ENTAILMENT HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

1. USE LEXICALLY DISTINGUISHABLE ERRORS (the system uses word matching)
   ✓ Good: Wrong proper nouns: "CBC-TV" instead of "NBC-TV"
   ✓ Good: Wrong numbers/dates: "1985" instead of "1980", "3 minutes" instead of "5 minutes"
   ✓ Good: Wrong names: "Johnson" instead of "Lewis", "Smith" instead of "Francis"
   ✓ Good: Negated actions: "rejected" instead of "approved", "denied" instead of "confirmed"
   
2. AVOID SUBTLE SEMANTIC SHIFTS
   ✗ Bad: "injected into the sample" vs "slipped into the beverage" (too similar lexically)
   ✗ Bad: Changing only one adjective or adverb
   The system uses semantic similarity, so lexically similar phrases get matched incorrectly.

3. TYPES OF NOT_ENTAILMENT TO INCLUDE:
   - CONTRADICTIONS: Directly negate or reverse a stated fact
   - WRONG ENTITIES: Swap names, organizations, locations
   - WRONG VALUES: Change dates, numbers, quantities
   - FABRICATIONS: Add claims or outcomes not mentioned at all
   - WRONG ATTRIBUTIONS: Attribute statements to the wrong person

4. MAKE ERRORS OBVIOUS AT THE WORD LEVEL
   ✓ Good: "Lewis said he used steroids" (wrong person - it was Johnson who admitted it)
   ✓ Good: "The legislation was signed into law" (fabrication - it was only introduced)
   ✓ Good: "Huey worked for CBS" (wrong organization - she worked for NBC)

═══════════════════════════════════════════════════════════════════════════════
FORMATTING REQUIREMENTS:
═══════════════════════════════════════════════════════════════════════════════

- Each hypothesis must be ONE SINGLE SENTENCE (10-30 words)
- No periods except at the end
- Cover DIFFERENT aspects of the premise (don't cluster around one fact)
- Use simple, direct language

═══════════════════════════════════════════════════════════════════════════════
PREMISE:
═══════════════════════════════════════════════════════════════════════════════
{premise}

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT (respond with this exact JSON structure):
═══════════════════════════════════════════════════════════════════════════════
{{
    "entailment": [
        "First entailment hypothesis that combines or restates explicit facts.",
        "Second entailment hypothesis using different facts from the premise.",
        "Third entailment hypothesis covering another aspect of the premise.",
        "Fourth entailment hypothesis with exact names/dates/numbers from text.",
        "Fifth entailment hypothesis combining facts from different sentences."
    ],
    "not_entailment": [
        "First not_entailment with wrong proper noun (person, org, or place).",
        "Second not_entailment with wrong date, number, or quantity.",
        "Third not_entailment that negates or reverses a stated fact.",
        "Fourth not_entailment with fabricated claim not in the premise.",
        "Fifth not_entailment attributing a statement to the wrong person."
    ]
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return result


def create_dataset(num_premises: int, api_key: str) -> dict:
    """Create the full dataset."""

    premises = get_diverse_premises(num_premises)

    dataset = {
        "metadata": {
            "source": "DocNLI (premises) + LLM generated single-sentence hypotheses",
            "original_source": str(LOCAL_DATA_PATH),
            "generation_method": "LLM-generated single-sentence hypotheses for NLI testing (pipeline-aware prompt v2)",
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
            hyps = generate_hypotheses(p['premise'], api_key)

            premise_data = {
                "premise_id": i,
                "premise": p['premise'],
                "premise_word_count": p['premise_words'],
                "num_entailment": len(hyps['entailment']),
                "num_not_entailment": len(hyps['not_entailment']),
                "hypotheses": []
            }

            # Add entailment hypotheses
            for j, h in enumerate(hyps['entailment']):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "entailment",
                    "original_idx": i * (HYPOTHESES_PER_LABEL * 2) + j
                })
                print(f"  ✅ Entailment: {h[:60]}...")

            # Add not_entailment hypotheses
            for j, h in enumerate(hyps['not_entailment']):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "not_entailment",
                    "original_idx": i * (HYPOTHESES_PER_LABEL * 2) + len(hyps['entailment']) + j
                })
                print(f"  ❌ Not_entailment: {h[:60]}...")

            dataset['premises'].append(premise_data)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Update metadata
    dataset['metadata']['num_premises'] = len(dataset['premises'])
    dataset['metadata']['num_examples'] = sum(len(p['hypotheses']) for p in dataset['premises'])

    return dataset


def main():
    parser = argparse.ArgumentParser(description="Create single-sentence hypothesis dataset")
    parser.add_argument("--num-premises", type=int, default=NUM_PREMISES, help="Number of premises")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--output-name",
        default="gold_balanced.json",
        help="Output filename (default: gold_balanced.json)",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate dataset
    print("=" * 80)
    print("CREATING SINGLE-SENTENCE HYPOTHESIS DATASET (Pipeline-Aware v2)")
    print("=" * 80)

    dataset = create_dataset(args.num_premises, args.api_key)

    # Save dataset
    output_path = OUTPUT_DIR / args.output_name
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\n{'=' * 80}")
    print("DATASET CREATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output: {output_path}")
    print(f"Premises: {dataset['metadata']['num_premises']}")
    print(f"Total examples: {dataset['metadata']['num_examples']}")
    print(f"Entailment: {dataset['metadata']['label_distribution']['entailment']}")
    print(f"Not_entailment: {dataset['metadata']['label_distribution']['not_entailment']}")


if __name__ == "__main__":
    main()
