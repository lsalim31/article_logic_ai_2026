"""
Create a DocNLI dataset with single-sentence hypotheses (4-way classification).

This script:
1. Loads premises (100-500 words) from multiple DocNLI source files
2. Deduplicates and selects diverse premises (≤10)
3. Uses an LLM to generate single-sentence hypotheses per premise:
   - 4 entailment (facts directly verifiable from premise)
   - 4 contradiction (statements that contradict the premise)
   - 4 uncertain (statements consistent with premise but not entailed)
   - 4 not_mentioned (2 same-domain hard distractors + 2 off-topic)
4. Validates LLM output and retries on malformed responses
5. Saves the dataset with 4-way labels for fine-grained evaluation
"""
import argparse
import json
import os
import sys
import random
import traceback
from datetime import datetime
from pathlib import Path
from openai import OpenAI


# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent.parent / "code"
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

# ── Hardcoded model configuration ──────────────────────────────────────────────
REASONING_MODEL = "openai/gpt-4.1"
REASONING_EFFORT = "medium"

# ── Dataset configuration ──────────────────────────────────────────────────────
NUM_PREMISES = 10                # Target number of premises
HYPOTHESES_PER_LABEL = 4         # Per category (entailment, contradiction, uncertain, not_mentioned)
MIN_PREMISE_WORDS = 100
MAX_PREMISE_WORDS = 500
SEED = 42
MAX_RETRIES = 2                  # Retries per premise on LLM generation failure

OUTPUT_DIR = _script_dir

# ── Source data paths (merged from multiple DocNLI splits) ─────────────────────
_experiments_dir = _script_dir.parent.parent.parent / "experiments" / "DocNLI"
LOCAL_DATA_PATHS = [
    _experiments_dir / "docnli-long_100_400" / "sample_10.json",   # 3 premises, 100-400 words
    _experiments_dir / "doc-nli" / "sample_100.json",              # 10 premises, 200-500 words
]


def get_diverse_premises(num_premises: int) -> list:
    """Load premises from multiple DocNLI source files and select diverse ones.

    Deduplication strategy:
      - Skip premises whose first 100 characters (lowercased) match one already seen.
      - This avoids selecting near-duplicate passages that sometimes appear across splits.
    """
    all_premises = []
    seen_starts = set()

    for path in LOCAL_DATA_PATHS:
        if not path.exists():
            print(f"  WARNING: Source file not found, skipping: {path}")
            continue

        print(f"Loading premises from: {path}")
        with open(path, 'r') as f:
            data = json.load(f)

        for premise_data in data['premises']:
            premise = premise_data['premise']
            premise_words = len(premise.split())

            if not (MIN_PREMISE_WORDS <= premise_words <= MAX_PREMISE_WORDS):
                continue

            # Dedup by first 100 chars
            start = premise[:100].lower()
            if start in seen_starts:
                continue
            seen_starts.add(start)

            all_premises.append({
                'premise': premise,
                'premise_words': premise_words,
                'source_file': str(path.name),
            })

    print(f"Found {len(all_premises)} unique premises in {MIN_PREMISE_WORDS}-{MAX_PREMISE_WORDS} word range")

    # Sample randomly
    random.seed(SEED)
    selected = random.sample(all_premises, min(num_premises, len(all_premises)))

    print(f"Selected {len(selected)} diverse premises")
    return selected


def validate_hypotheses(hyps: dict, expected_per_label: int) -> tuple[bool, str]:
    """Validate that LLM output has the right structure and counts.

    Returns:
        (is_valid, error_message)
    """
    required_keys = ['entailment', 'contradiction', 'uncertain', 'not_mentioned']
    for key in required_keys:
        if key not in hyps:
            return False, f"Missing key '{key}' in LLM response"
        if not isinstance(hyps[key], list):
            return False, f"Key '{key}' is not a list"
        if len(hyps[key]) != expected_per_label:
            return False, f"Key '{key}' has {len(hyps[key])} items, expected {expected_per_label}"
        for item in hyps[key]:
            if not isinstance(item, str) or len(item.strip()) < 5:
                return False, f"Key '{key}' contains invalid hypothesis: {repr(item)}"
    return True, ""


def generate_hypotheses(premise: str, client: OpenAI, model: str = REASONING_MODEL) -> dict:
    """Generate single-sentence hypotheses for a premise using LLM.

    Args:
        premise: The source text to generate hypotheses about.
        client: Reusable OpenAI client instance.
        model: Model identifier for OpenRouter.

    Returns:
        Dict with keys: entailment, contradiction, uncertain, not_mentioned.
        Each is a list of HYPOTHESES_PER_LABEL strings.
    """

    prompt = f"""You are generating test data for a logical inference system that uses formal propositional logic.

The system works by:
1. Extracting atomic propositions from the premise (simple statements without logical connectives)
2. Matching hypothesis text to these propositions using semantic similarity
3. Using a logic solver to check entailment
4. You generate statements built out of these propositions with varying degrees of complexity — usually simple but occasionally involving up to 5 connectives. Mix it up.

Given the following premise, generate exactly {HYPOTHESES_PER_LABEL * 4} single-sentence hypotheses:
- {HYPOTHESES_PER_LABEL} ENTAILMENT hypotheses: Statements that are definitely TRUE based on the premise
- {HYPOTHESES_PER_LABEL} CONTRADICTION hypotheses: Statements that are definitely FALSE based on the premise
- {HYPOTHESES_PER_LABEL} UNCERTAIN hypotheses: Statements that COULD be true or false — the premise is consistent with both
- {HYPOTHESES_PER_LABEL} NOT_MENTIONED hypotheses: See special rules below

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
   ✓ Good: "X and Y" — both facts stated
   ✓ Good: "X, who did Y" — relative clause combining facts
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

Generate TWO types of not_mentioned hypotheses:

TYPE A — HARD (same broad domain, but different entities/events):
Generate {HYPOTHESES_PER_LABEL // 2} hypotheses that are in the SAME DOMAIN as the premise
but about DIFFERENT specific entities, events, or facts NOT mentioned in the premise.
   ✓ Good (sports premise): "Roger Federer withdrew from the French Open due to a knee injury."
     (same domain: sports/tennis, but different people and events)
   ✓ Good (legal premise): "The California Supreme Court overturned a ruling on eminent domain."
     (same domain: law, but different court, state, and issue)
   The key: shares general topic vocabulary but NO overlap with specific premise entities.

TYPE B — EASY (completely different domain):
Generate {HYPOTHESES_PER_LABEL - HYPOTHESES_PER_LABEL // 2} hypotheses about COMPLETELY DIFFERENT topics.
   ✓ Good: "The European Central Bank raised interest rates in March."
   ✓ Good: "Toyota announced a recall of 500,000 vehicles."
   Ensure ZERO lexical overlap with key premise terms.

ALL not_mentioned hypotheses must be realistic standalone statements.

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
OUTPUT FORMAT (respond with this exact JSON structure, {HYPOTHESES_PER_LABEL} items per list):
═══════════════════════════════════════════════════════════════════════════════
{{
    "entailment": [
        "First entailment combining explicit facts naturally.",
        "Second entailment using different facts from the premise.",
        "Third entailment covering another aspect of the premise.",
        "Fourth entailment with exact names/dates/numbers from text."
    ],
    "contradiction": [
        "First contradiction with wrong proper noun.",
        "Second contradiction with wrong date or number.",
        "Third contradiction that negates a stated fact.",
        "Fourth contradiction with wrong attribution."
    ],
    "uncertain": [
        "First uncertain: known event with unspecified detail.",
        "Second uncertain: plausible extension of stated facts.",
        "Third uncertain: combines known entities in unconfirmed way.",
        "Fourth uncertain: reasonable detail not explicitly stated."
    ],
    "not_mentioned": [
        "TYPE A (hard): same-domain statement about different entities.",
        "TYPE A (hard): same-domain statement about different events.",
        "TYPE B (easy): entirely different domain and topic.",
        "TYPE B (easy): no lexical overlap with premise."
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

    # Create a single reusable client
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    dataset = {
        "metadata": {
            "source": "DocNLI (premises) + LLM generated single-sentence hypotheses",
            "original_sources": [str(p) for p in LOCAL_DATA_PATHS],
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
            "is_4way_classification": True,
            "not_mentioned_split": f"{HYPOTHESES_PER_LABEL // 2} hard (same-domain) + {HYPOTHESES_PER_LABEL - HYPOTHESES_PER_LABEL // 2} easy (off-topic)"
        },
        "premises": []
    }

    for i, p in enumerate(premises):
        print(f"\nProcessing premise {i+1}/{len(premises)}...")
        print(f"  Words: {p['premise_words']}, Source: {p['source_file']}")
        print(f"  Preview: {p['premise'][:100]}...")

        # Generate hypotheses with retry
        success = False
        for attempt in range(MAX_RETRIES + 1):
            try:
                hyps = generate_hypotheses(p['premise'], client)

                # Validate output
                is_valid, error_msg = validate_hypotheses(hyps, HYPOTHESES_PER_LABEL)
                if not is_valid:
                    print(f"  VALIDATION FAILED (attempt {attempt+1}/{MAX_RETRIES+1}): {error_msg}")
                    if attempt < MAX_RETRIES:
                        continue
                    else:
                        print(f"  SKIPPING premise after {MAX_RETRIES+1} failed attempts")
                        break

                premise_data = {
                    "premise_id": i,
                    "premise": p['premise'],
                    "premise_word_count": p['premise_words'],
                    "source_file": p['source_file'],
                    "num_entailment": len(hyps['entailment']),
                    "num_contradiction": len(hyps['contradiction']),
                    "num_uncertain": len(hyps['uncertain']),
                    "num_not_mentioned": len(hyps['not_mentioned']),
                    "hypotheses": []
                }

                # Add hypotheses with their 4-way labels
                idx_offset = i * (HYPOTHESES_PER_LABEL * 4)
                current_idx = 0

                for label_name, emoji in [
                    ('entailment', '✅'),
                    ('contradiction', '❌'),
                    ('uncertain', '❓'),
                    ('not_mentioned', '⬜'),
                ]:
                    for h in hyps[label_name]:
                        premise_data['hypotheses'].append({
                            "hypothesis": h,
                            "label": label_name,
                            "original_idx": idx_offset + current_idx
                        })
                        print(f"  {emoji} {label_name}: {h[:60]}...")
                        current_idx += 1

                dataset['premises'].append(premise_data)
                success = True
                break

            except json.JSONDecodeError as e:
                print(f"  JSON PARSE ERROR (attempt {attempt+1}/{MAX_RETRIES+1}): {e}")
                if attempt >= MAX_RETRIES:
                    print(f"  SKIPPING premise after {MAX_RETRIES+1} failed attempts")
            except Exception as e:
                print(f"  ERROR (attempt {attempt+1}/{MAX_RETRIES+1}): {e}")
                traceback.print_exc()
                if attempt >= MAX_RETRIES:
                    print(f"  SKIPPING premise after {MAX_RETRIES+1} failed attempts")

    # Update metadata with actual counts
    dataset['metadata']['num_premises'] = len(dataset['premises'])
    dataset['metadata']['num_examples'] = sum(len(p['hypotheses']) for p in dataset['premises'])
    dataset['metadata']['label_distribution'] = {
        "entailment": sum(1 for p in dataset['premises'] for h in p['hypotheses'] if h['label'] == 'entailment'),
        "contradiction": sum(1 for p in dataset['premises'] for h in p['hypotheses'] if h['label'] == 'contradiction'),
        "uncertain": sum(1 for p in dataset['premises'] for h in p['hypotheses'] if h['label'] == 'uncertain'),
        "not_mentioned": sum(1 for p in dataset['premises'] for h in p['hypotheses'] if h['label'] == 'not_mentioned'),
    }

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
        default="data_constructed_march30.json",
        help="Output filename)",
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
    print(f"Sources: {[str(p) for p in LOCAL_DATA_PATHS]}")
    print(f"Target: {NUM_PREMISES} premises × {HYPOTHESES_PER_LABEL} hypotheses/label × 4 labels")
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
