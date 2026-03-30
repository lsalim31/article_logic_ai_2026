"""
Create a DocNLI dataset with single-sentence hypotheses.

This script:
1. Selects diverse premises (100-400 words) from DocNLI
2. Uses an LLM to generate single-sentence hypotheses:
   - N entailment (facts directly verifiable from premise)
   - N contradiction (statements that contradict the premise)
   - N uncertain (statements consistent with premise but not entailed)
   - N not_mentioned (statements about unrelated topics)
3. Saves the dataset with 4-way labels for fine-grained evaluation
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
_code_dir = _script_dir.parent.parent.parent / "code"  # Go up 3 levels: dataset -> claude_constructed -> experiments -> code
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

# Hardcoded model configuration
REASONING_MODEL = "openai/gpt-4.1"
REASONING_EFFORT = "medium"

# Configuration
NUM_PREMISES = 15  # Number of premises to include
HYPOTHESES_PER_LABEL = 5  # per category (entailment, contradiction, uncertain, not_mentioned)
MIN_PREMISE_WORDS = 100
MAX_PREMISE_WORDS = 400
SEED = 42

OUTPUT_DIR = _script_dir
LOCAL_DATA_PATH = _script_dir.parent.parent.parent / "experiments" / "DocNLI" / "docnli-long_100_400" / "sample_10.json"


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

    prompt = f"""You are generating test data for a logical inference system that uses formal propositional logic.

The system works by:
1. Extracting atomic propositions from the premise (simple statements that do not have connectives in them)
2. Matching hypothesis text to these propositions using semantic similarity
3. Using a logic solver to check entailment
4. You generate statements built out of these propositions that are written in varying degrees of complexity although usually simple. It can be slightly logically involved (such as 5 connectives) but not always. Mix it up.

Given the following premise, generate exactly {HYPOTHESES_PER_LABEL * 4} single-sentence hypotheses:
- {HYPOTHESES_PER_LABEL} ENTAILMENT hypotheses: Statements that are definitely TRUE based on the premise
- {HYPOTHESES_PER_LABEL} CONTRADICTION hypotheses: Statements that are definitely FALSE based on the premise
- {HYPOTHESES_PER_LABEL} UNCERTAIN hypotheses: Statements that COULD be true or false - the premise is consistent with both
- {HYPOTHESES_PER_LABEL} NOT_MENTIONED hypotheses: Statements about topics completely UNRELATED to the premise

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR ENTAILMENT HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

1. USE EXPLICIT FACTS ONLY
   ✓ Good: "Huey said she knew Francis since 1980"
   ✓ Good: "Francis told Huey that Johnson feared the drug test"
   ✗ Bad: "Huey recalls Francis implying..." (inference, not stated)

2. REFERENCE WHAT WAS SAID, DONE, OR REPORTED
   ✓ Good: "X said that Y", "X testified that Y", "X did Y"
   ✗ Bad: "X implied that Y", "X believed that Y" (unless explicitly stated)

3. COMBINE FACTS NATURALLY
   ✓ Good: "X and Y" - both facts stated
   ✓ Good: "X, who did Y" - relative clause combining facts
   ✓ Good: "The [noun] that [fact1] also [fact2]"

4. USE NAMES, DATES, AND NUMBERS EXACTLY AS STATED
   ✓ Good: Use "NBC-TV" if the text says "NBC-TV"
   ✗ Bad: Paraphrase "NBC-TV" as "a television network"

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR CONTRADICTION HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

1. USE LEXICALLY DISTINGUISHABLE ERRORS (the system uses word matching)
   ✓ Good: Wrong proper nouns: "CBC-TV" instead of "NBC-TV"
   ✓ Good: Wrong numbers/dates: "1985" instead of "1980"
   ✓ Good: Wrong names: "Johnson" instead of "Lewis"
   ✓ Good: Negated actions: "rejected" instead of "approved"

2. AVOID SUBTLE SEMANTIC SHIFTS
   ✗ Bad: Changing only one adjective or adverb
   ✗ Bad: Synonyms that are lexically similar

3. TYPES OF CONTRADICTION TO INCLUDE:
   - Directly negate or reverse a stated fact
   - Swap names, organizations, locations
   - Change dates, numbers, quantities
   - Attribute statements to the wrong person

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR UNCERTAIN HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

The premise NEITHER confirms NOR denies these. Both true and false are possible.

1. USE UNDERSPECIFIED ASPECTS
   ✓ Good: "Huey met Francis at a restaurant" (they met, but location not specified)
   ✓ Good: "Johnson was nervous during the interview" (interview happened, emotion not stated)

2. COMBINE KNOWN FACTS WITH UNKNOWN DETAILS
   ✓ Good: "Francis warned Huey before the test" (both exist, warning not mentioned)
   ✓ Good: "The committee met twice before approving" (approval happened, count unknown)

3. WHAT MAKES IT UNCERTAIN (NOT CONTRADICTION):
   - The premise doesn't rule it out
   - It's plausible given what's stated
   - Adding this fact wouldn't create a logical contradiction

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR NOT_MENTIONED HYPOTHESES:
═══════════════════════════════════════════════════════════════════════════════

Statements about COMPLETELY DIFFERENT topics with no connection to the premise.

1. INTRODUCE ENTIRELY NEW ENTITIES
   ✓ Good: "The European Central Bank raised interest rates in March"
   ✓ Good: "Toyota announced a recall of 500,000 vehicles"

2. ENSURE ZERO LEXICAL OVERLAP WITH KEY PREMISE TERMS
   - Different people, organizations, places
   - Different domains entirely

3. MAKE THEM REALISTIC STANDALONE STATEMENTS
   ✓ Good: Sounds like a real news headline or fact

═══════════════════════════════════════════════════════════════════════════════
FORMATTING REQUIREMENTS:
═══════════════════════════════════════════════════════════════════════════════

- Each hypothesis must be ONE SINGLE SENTENCE (10-30 words)
- Cover DIFFERENT aspects of the premise
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
        "First entailment combining explicit facts naturally.",
        "Second entailment using different facts from the premise.",
        "Third entailment covering another aspect of the premise.",
        "Fourth entailment with exact names/dates/numbers from text.",
        "Fifth entailment combining facts about the same entity."
    ],
    "contradiction": [
        "First contradiction with wrong proper noun.",
        "Second contradiction with wrong date or number.",
        "Third contradiction that negates a stated fact.",
        "Fourth contradiction with wrong attribution.",
        "Fifth contradiction that reverses an outcome."
    ],
    "uncertain": [
        "First uncertain: known event with unspecified detail.",
        "Second uncertain: plausible extension of stated facts.",
        "Third uncertain: combines known entities in unconfirmed way.",
        "Fourth uncertain: reasonable detail not explicitly stated.",
        "Fifth uncertain: underspecified aspect of confirmed event."
    ],
    "not_mentioned": [
        "First not_mentioned: entirely different people and organizations.",
        "Second not_mentioned: unrelated domain or topic.",
        "Third not_mentioned: different events and places.",
        "Fourth not_mentioned: no lexical overlap with premise.",
        "Fifth not_mentioned: realistic but completely irrelevant fact."
    ]
}}
"""

    # Build request with reasoning effort
    request_params = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    # Add reasoning effort for supported models
    if "gpt-4" in model or "o1" in model or "o3" in model:
        request_params["extra_body"] = {"reasoning_effort": REASONING_EFFORT}

    response = client.chat.completions.create(**request_params)

    result = json.loads(response.choices[0].message.content)

    return result


def create_dataset(num_premises: int, api_key: str) -> dict:
    """Create the full dataset with 4-way classification."""

    premises = get_diverse_premises(num_premises)

    dataset = {
        "metadata": {
            "source": "DocNLI (premises) + LLM generated single-sentence hypotheses",
            "original_source": str(LOCAL_DATA_PATH),
            "generation_method": "LLM-generated single-sentence hypotheses for 4-way NLI testing",
            "generation_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "filter_criteria": {
                "min_words": MIN_PREMISE_WORDS,
                "max_words": MAX_PREMISE_WORDS,
                "hypotheses_per_label": HYPOTHESES_PER_LABEL
            },
            "download_timestamp": datetime.now().isoformat(),
            "num_premises": len(premises),
            "num_examples": len(premises) * HYPOTHESES_PER_LABEL * 4,
            "label_distribution": {
                "entailment": len(premises) * HYPOTHESES_PER_LABEL,
                "contradiction": len(premises) * HYPOTHESES_PER_LABEL,
                "uncertain": len(premises) * HYPOTHESES_PER_LABEL,
                "not_mentioned": len(premises) * HYPOTHESES_PER_LABEL
            },
            "label_set": ["entailment", "contradiction", "uncertain", "not_mentioned"],
            "avg_hypotheses_per_premise": HYPOTHESES_PER_LABEL * 4,
            "is_single_sentence": True,
            "is_4way_classification": True
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
                "num_entailment": len(hyps.get('entailment', [])),
                "num_contradiction": len(hyps.get('contradiction', [])),
                "num_uncertain": len(hyps.get('uncertain', [])),
                "num_not_mentioned": len(hyps.get('not_mentioned', [])),
                "hypotheses": []
            }

            # Add hypotheses with their 4-way labels
            idx_offset = i * (HYPOTHESES_PER_LABEL * 4)
            current_idx = 0

            # Entailment hypotheses
            for h in hyps.get('entailment', []):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "entailment",
                    "original_idx": idx_offset + current_idx
                })
                print(f"  ✅ Entailment: {h[:60]}...")
                current_idx += 1

            # Contradiction hypotheses
            for h in hyps.get('contradiction', []):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "contradiction",
                    "original_idx": idx_offset + current_idx
                })
                print(f"  ❌ Contradiction: {h[:60]}...")
                current_idx += 1

            # Uncertain hypotheses
            for h in hyps.get('uncertain', []):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "uncertain",
                    "original_idx": idx_offset + current_idx
                })
                print(f"  ❓ Uncertain: {h[:60]}...")
                current_idx += 1

            # Not mentioned hypotheses
            for h in hyps.get('not_mentioned', []):
                premise_data['hypotheses'].append({
                    "hypothesis": h,
                    "label": "not_mentioned",
                    "original_idx": idx_offset + current_idx
                })
                print(f"  ⬜ Not mentioned: {h[:60]}...")
                current_idx += 1

            dataset['premises'].append(premise_data)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Update metadata
    dataset['metadata']['num_premises'] = len(dataset['premises'])
    dataset['metadata']['num_examples'] = sum(len(p['hypotheses']) for p in dataset['premises'])

    return dataset


def main():
    parser = argparse.ArgumentParser(description="Create single-sentence hypothesis dataset (4-way)")
    parser.add_argument("--num-premises", type=int, default=NUM_PREMISES, help="Number of premises")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--output-name",
        default="data_claude_constructed_test.json",
        help="Output filename (default: data_claude_constructed_test.json)",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate dataset
    print("=" * 80)
    print("CREATING 4-WAY CLASSIFICATION DATASET")
    print(f"Model: {REASONING_MODEL} (reasoning_effort: {REASONING_EFFORT})")
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
    print(f"Label distribution (4-way):")
    for label, count in dataset['metadata']['label_distribution'].items():
        print(f"  - {label}: {count}")


if __name__ == "__main__":
    main()
