#!/usr/bin/env python3
"""
updated_load_logicbench.py - Complete LogicBench dataset loader.

Loads LogicBench dataset directly from GitHub with full pattern coverage.

Usage:
    from updated_load_logicbench import load_logicbench

    examples = load_logicbench(
        dataset_type='eval',
        task_type='BQA',
        logic_type='propositional_logic',
        patterns=['modus_tollens'],
        max_examples_per_pattern=10
    )
"""

import json
import urllib.request
import urllib.error

# Complete pattern definitions for LogicBench
PATTERNS = {
    'propositional_logic': [
        'bidirectional_dilemma',
        'commutation',
        'constructive_dilemma',
        'destructive_dilemma',
        'disjunctive_syllogism',
        'hypothetical_syllogism',
        'material_implication',
        'modus_tollens'
    ],
    'first_order_logic': [
        'bidirectional_dilemma',
        'constructive_dilemma',
        'destructive_dilemma',
        'disjunctive_syllogism',
        'existential_generalization',
        'hypothetical_syllogism',
        'modus_ponens',
        'modus_tollens',
        'universal_instantiation'
    ],
    'nm_logic': [
        'default_reasoning_default',
        'default_reasoning_irr',
        'default_reasoning_open',
        'default_reasoning_several',
        'reasoning_about_exceptions_1',
        'reasoning_about_exceptions_2',
        'reasoning_about_exceptions_3',
        'reasoning_about_priority'
    ]
}

BASE_URL = "https://raw.githubusercontent.com/Mihir3009/LogicBench/main/data"


def load_logicbench(dataset_type='eval', task_type='BQA', logic_type='all',
                    patterns=None, max_examples_per_pattern=None, all_qa_pairs=False):
    """
    Load LogicBench dataset from GitHub.

    Args:
        dataset_type: 'eval' or 'aug'
        task_type: 'BQA' or 'MCQA' (only for eval)
        logic_type: 'propositional_logic', 'first_order_logic', 'nm_logic', or 'all'
        patterns: list of pattern names, or None for all patterns in logic_type
        max_examples_per_pattern: optional limit per pattern
        all_qa_pairs: if True, return all QA pairs per sample; if False, only first

    Returns:
        List[dict] with keys:
            - id: unique identifier
            - text: context/premises
            - query: question
            - ground_truth: expected answer
            - pattern: reasoning pattern name
            - logic_type: 'propositional_logic', 'first_order_logic', or 'nm_logic'
            - folder_name: exact folder path
            - type: 'eval' or 'aug'
    """
    # Build dataset folder name
    if dataset_type == 'eval':
        dataset_folder = f"LogicBench(Eval)/{task_type}"
    else:
        dataset_folder = "LogicBench(Aug)/BQA"

    # Determine logic types to load
    if logic_type == 'all':
        logic_types = list(PATTERNS.keys())
    else:
        logic_types = [logic_type]

    examples = []

    for lt in logic_types:
        available_patterns = PATTERNS.get(lt, [])

        # Filter patterns if specified
        if patterns:
            target_patterns = [p for p in patterns if p in available_patterns]
        else:
            target_patterns = available_patterns

        for pattern in target_patterns:
            folder_name = f"{dataset_folder}/{lt}/{pattern}"
            url = f"{BASE_URL}/{folder_name}/data_instances.json"

            pattern_examples = _fetch_pattern(
                url=url,
                pattern=pattern,
                logic_type=lt,
                folder_name=folder_name,
                dataset_type=dataset_type,
                max_examples=max_examples_per_pattern,
                all_qa_pairs=all_qa_pairs
            )
            examples.extend(pattern_examples)

    print(f"Total loaded: {len(examples)} examples")
    return examples


def _fetch_pattern(url, pattern, logic_type, folder_name, dataset_type,
                   max_examples=None, all_qa_pairs=False):
    """Fetch examples for a single pattern."""
    examples = []

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        samples = data.get('samples', [])
        count = 0

        for sample in samples:
            if max_examples and count >= max_examples:
                break

            sample_id = sample.get('id', f"{pattern}_{count}")
            context = sample.get('context', '')
            qa_pairs = sample.get('qa_pairs', [])

            if not qa_pairs:
                continue

            # Get QA pairs
            pairs_to_process = qa_pairs if all_qa_pairs else [qa_pairs[0]]

            for i, qa in enumerate(pairs_to_process):
                example_id = f"{sample_id}_q{i}" if all_qa_pairs else sample_id

                examples.append({
                    'id': example_id,
                    'text': context,
                    'query': qa.get('question', ''),
                    'ground_truth': qa.get('answer', None),
                    'pattern': pattern,
                    'logic_type': logic_type,
                    'folder_name': folder_name,
                    'type': dataset_type
                })

            count += 1

        print(f"  Loaded {len(examples)} from {logic_type}/{pattern}")

    except urllib.error.HTTPError as e:
        print(f"  Error loading {pattern}: HTTP {e.code}")
    except Exception as e:
        print(f"  Error loading {pattern}: {e}")

    return examples


def get_available_patterns(logic_type='all'):
    """Return available patterns for a logic type."""
    if logic_type == 'all':
        return PATTERNS.copy()
    return PATTERNS.get(logic_type, [])


if __name__ == '__main__':
    print("Testing updated LogicBench loader...\n")

    # Test: load 2 examples from modus_tollens (propositional)
    examples = load_logicbench(
        dataset_type='eval',
        task_type='BQA',
        logic_type='propositional_logic',
        patterns=['modus_tollens'],
        max_examples_per_pattern=2
    )

    print("\n" + "=" * 60)
    print("Sample Example:")
    print("=" * 60)

    if examples:
        ex = examples[0]
        print(f"ID: {ex['id']}")
        print(f"Pattern: {ex['pattern']}")
        print(f"Logic Type: {ex['logic_type']}")
        print(f"Folder: {ex['folder_name']}")
        print(f"Type: {ex['type']}")
        print(f"\nContext:\n{ex['text']}")
        print(f"\nQuery: {ex['query']}")
        print(f"Answer: {ex['ground_truth']}")
    else:
        print("No examples loaded!")
