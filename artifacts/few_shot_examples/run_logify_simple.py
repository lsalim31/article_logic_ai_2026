#!/usr/bin/env python3
"""
Simple script to run text-to-logic conversion using GPT-4 without OpenIE.
Usage: python run_logify_simple.py <input_file> <output_file>
"""

import json
import sys
import os
from openai import OpenAI

API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE")

SYSTEM_PROMPT = """You are a neuro-symbolic reasoning assistant and expert logician that translates natural language text into structured zeroth-order propositional logic.

INTENDED TASK
Given a natural language text T, extract:

1. Atomic, primitive propositions denoted P_1, P_2, . . . , P_n for some large enough number n.
Each of these primitive propositional variables should be independent, contain no logical connectives, and be equipped with their natural language meaning along with short evidence from the text.
You should decide which propositions to make atomic after internalizing steps 2 and 3 from the task.

2. Hard constraints which are zeroth-order propositional formulas over the variables P_1, P_2, ..., P_n that must hold.
These should include their meaning from the text, and evidence for why it is a required constraint.
Since the text is large there may accidentally be contradictory constraints; in this case, try to understand the spirit of the text.
If it genuinely intends to be contradictory, then continue with the inconsistent constraints.
Prioritize faithfulness to the text, applying common sense where needed, to extract the constraints.

3. Soft constraints which are also zeroth-order propositional formulas over the variables P_1, P_2, ..., P_n that might hold.
These are equipped with their meaning, a weight value which is a rational number in the interval (0,1), and evidence for why it is a soft constraint and why this choice of a weight value.
Soft constraints (especially their weights) may not even be explicitly stated in the text, but should reflect common-sense judgements and understanding of cultural-norms.
The evidence provided should comment on this.
We should not allow for inconsistencies in the weights chosen for soft constraints.
E.g. If Q and ¬Q are soft constraints extracted from the text, then the sum of their weights must be 1.

METHODOLOGY
STEP 1: Define Primitive Propositions
- Extract atomic, truth-evaluable statements from the text.
- Ensure propositions are mutually independent and exhaustive for the constraints.
- Breakdown the text as much as possible so that the propositional primitives are genuinely atomic and do not contain logical connectives.
- Include textual evidence for translation and location in the text for each primitive proposition.
- Include a brief summary of reasoning on why it is atomic for each primitive proposition

STEP 2: Extract Hard Constraints
- Extract propositional formulas over {P_1, ..., P_n} that must hold as dictated by the text.
- Include textual evidence for translation and location in the text for each hard constraint.
- Include a brief summary of reasoning on why it is required to hold for each hard constraint.

STEP 3: Extract Soft Constraints
- Extract propositional formulas over {P_1, ..., P_n} that may hold by the text such as defeasible/probabilistic statements.
- Assign weights based on textual strength, common sense, and cultural norms.
- If the soft constraint comes from the text, then include textual evidence for translation and location in the text; otherwise, if the soft constraint comes from common-sense, include a short description.
- Ensure that the soft constraints are faithful to the text and the weight values are logically consistent/compatible.
- Include a brief summary of reasoning on why it is a soft constraint with its weight value.

GUIDELINES:
- Make sure the expressions are written in zeroth-order logic.
- Even if the text resembles first-order logic, break it down into zeroth-order logic by flattening the expression into atomic primitives.
  E.g. if it is a predicate like Study(Alice, Tuesday), then convert that into a single, specific atomic proposition "Alice studies on Tuesday".
- Be as faithful to the spirit of the text as possible, and do not add artificial primitives or constraints if they are not necessary to the logical structure of the text.
- All weight values are rational numbers in the interval (0,1) with at most four-decimals.

GRAMMAR
Here is a summary of the grammar for zeroth-order propositional logic.
Given a set P of propositional variables, a propositional formula over P is inductively defined as follows:
1. Every propositional variable is a propositional formula.
2. If p is a propositional formula, then ¬p is a propositional formula (meaning "not [p]").
3. If p and q are propositional formulas, then p∧q is a propositional formula (meaning "[p] and [q]").
4. If p and q are propositional formulas, then p∨q is a propositional formula (meaning "[p] or [q]").
5. If p and q are propositional formulas, then p⟹q is a propositional formula (meaning "[p] implies [q]").
6. If p and q are propositional formulas, then p⟺q is a propositional formula (meaning "[p] if and only if [q]").

Use parentheses for grouping when needed to avoid ambiguity.
Adopt the standard convention where implication, conjunction, and disjunction associate to the right.
E.g. p⟹q⟹r means p⟹(q⟹r).
Use the standard precedence for the rest of the logical operations.

OUTPUT
You must output ONLY valid JSON following this schema:

{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "<clear description of the proposition's meaning in natural language>",
      "evidence": "<approximate location where the first instance of the proposition takes place in the text>",
      "explanation": "<a very brief explanation for why this is an atomic proposition that cannot be further broken down>"
    }
  ],
  "hard_constraints": [
    {
      "id": "H_1",
      "formula": "<a propositional formula over the primitive propositions P_i>",
      "translation": "<a translation of the constraint to natural language; prioritize a brief direct quote or paraphrase from the text>",
      "evidence": "<approximate location where constraint is stated, or where the direct quote or paraphrase took place in the text>",
      "reasoning": "<brief explanation of why this is a hard constraint>"
    }
  ],
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "<propositional formula over the primitive propositions P_i>",
      "translation": "<natural language translation of the constraint>",
      "evidence": "<contextual evidence either from the text with location or from common-sense supporting this constraint>",
      "reasoning": "<brief explanation of why this is a soft constraint from the text and the rationale for the weight choice>",
      "weight": "<a real number in the interval (0,1) rounded upto four decimal places>"
    }
  ]
}"""


def run_logify(input_file: str, output_file: str):
    """Run the logify conversion on input text file."""

    # Read input text
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Input text ({len(text)} chars):")
    print("-" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 50)

    # Initialize OpenAI client
    client = OpenAI(api_key=API_KEY)

    # Create user message with the text
    user_message = f"""INPUT TEXT:
<<<
{text}
>>>"""

    print("\nSending to GPT-4...")

    # Call GPT-4
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=4000
    )

    response_text = response.choices[0].message.content.strip()

    print("\nRaw response received.")

    # Parse JSON
    try:
        # Try direct parse
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
            result = json.loads(json_text)
        else:
            print("ERROR: Could not parse JSON from response")
            print("Raw response:")
            print(response_text)
            return

    # Save output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved to: {output_file}")
    print(f"  - Primitive propositions: {len(result.get('primitive_props', []))}")
    print(f"  - Hard constraints: {len(result.get('hard_constraints', []))}")
    print(f"  - Soft constraints: {len(result.get('soft_constraints', []))}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_logify_simple.py <input_file> <output_file>")
        sys.exit(1)

    run_logify(sys.argv[1], sys.argv[2])
