#!/usr/bin/env python3
"""
Run dual extraction (propositional and FOL) on the same examples.

Usage:
    python run_dual_extraction.py

Input:
    data/raw/source_examples.jsonl - each line: {"id": "001", "text": "...", "query": "..."}

Output:
    data/extractions/propositional.jsonl
    data/extractions/fol.jsonl
"""

import json
import os
from extract_propositional import extract_propositional
from extract_fol import extract_fol


def main():
    # Setup paths
    input_file = 'data/raw/source_examples.jsonl'
    output_dir = 'data/extractions'
    os.makedirs(output_dir, exist_ok=True)

    prop_output = os.path.join(output_dir, 'propositional.jsonl')
    fol_output = os.path.join(output_dir, 'fol.jsonl')

    # Check input exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        print("Please create data/raw/source_examples.jsonl with format:")
        print('{"id": "001", "text": "Alice is a student. All students are human.", "query": "Is Alice human?"}')
        return

    # Load examples
    print(f"Loading examples from {input_file}...")
    examples = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"Loaded {len(examples)} examples")

    # Process each example
    prop_results = []
    fol_results = []

    for i, example in enumerate(examples):
        print(f"\nProcessing {i+1}/{len(examples)}: {example['id']}")

        text = example['text']
        query = example.get('query', '')

        # Extract propositional
        print("  Running propositional extraction...")
        prop_result = extract_propositional(text=text, query=query)
        prop_result['id'] = example['id']
        prop_result['original_text'] = text
        prop_result['original_query'] = query
        prop_results.append(prop_result)
        print(f"    Success: {prop_result['success']}")

        # Extract FOL
        print("  Running FOL extraction...")
        fol_result = extract_fol(text=text, query=query)
        fol_result['id'] = example['id']
        fol_result['original_text'] = text
        fol_result['original_query'] = query
        fol_results.append(fol_result)
        print(f"    Success: {fol_result['success']}")

    # Save results
    print(f"\nSaving propositional results to {prop_output}...")
    with open(prop_output, 'w') as f:
        for r in prop_results:
            f.write(json.dumps(r) + '\n')

    print(f"Saving FOL results to {fol_output}...")
    with open(fol_output, 'w') as f:
        for r in fol_results:
            f.write(json.dumps(r) + '\n')

    # Quick summary
    prop_failures = sum(1 for r in prop_results if not r['success'])
    fol_failures = sum(1 for r in fol_results if not r['success'])

    print("\n=== Quick Summary ===")
    print(f"Total examples: {len(examples)}")
    print(f"Propositional failures: {prop_failures}/{len(examples)} ({100*prop_failures/len(examples):.1f}%)")
    print(f"FOL failures: {fol_failures}/{len(examples)} ({100*fol_failures/len(examples):.1f}%)")
    print(f"\nRun analyze_errors.py for detailed analysis.")


if __name__ == '__main__':
    main()
