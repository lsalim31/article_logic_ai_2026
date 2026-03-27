#!/usr/bin/env python3
"""
Temporary script to run logify2 Stage 2 with Claude instead of OpenAI.
This is needed because we have an Anthropic API key but not OpenAI.
"""

import sys
import os
import json
from anthropic import Anthropic

# Read the prompt
prompt_path = "/workspace/repo/code/prompts/prompt_logify2"
with open(prompt_path, 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Read the LLM input
input_path = "/workspace/repo/artifacts/few_shot_examples/outputs/example_03_student_assessment_llm_input.txt"
with open(input_path, 'r', encoding='utf-8') as f:
    user_input = f.read()

print("=" * 80)
print("Running Stage 2 with Claude (Anthropic)")
print("=" * 80)
print(f"\nSystem prompt length: {len(system_prompt)} characters")
print(f"User input length: {len(user_input)} characters")

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

print("\nSending to Claude Sonnet 3.5...")

# Call Claude
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=8000,
    temperature=0.1,
    system=system_prompt,
    messages=[
        {"role": "user", "content": user_input}
    ]
)

response_text = response.content[0].text.strip()
print(f"\nResponse received. Length: {len(response_text)} characters")

# Parse JSON
try:
    # Try direct parse
    logic_structure = json.loads(response_text)
except json.JSONDecodeError:
    # Try to extract JSON from response
    if "{" in response_text and "}" in response_text:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        json_text = response_text[json_start:json_end]
        logic_structure = json.loads(json_text)
    else:
        print("ERROR: Could not parse JSON from response")
        print("Raw response:")
        print(response_text)
        sys.exit(1)

# Save output
output_path = "/workspace/repo/artifacts/few_shot_examples/outputs/example_03_student_assessment_output.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(logic_structure, f, indent=2, ensure_ascii=False)

print(f"\n✓ Output saved to: {output_path}")
print(f"  - Primitive propositions: {len(logic_structure.get('primitive_props', []))}")
print(f"  - Hard constraints: {len(logic_structure.get('hard_constraints', []))}")
print(f"  - Soft constraints: {len(logic_structure.get('soft_constraints', []))}")

print("\n" + "=" * 80)
print("STAGE 2 COMPLETED SUCCESSFULLY")
print("=" * 80)
