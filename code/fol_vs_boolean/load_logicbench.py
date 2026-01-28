#!/usr/bin/env python3
"""
Reusable LogicBench dataset loader.

Loads LogicBench dataset directly from GitHub repository.
Can be imported by any script that needs LogicBench data.

Usage:
    from load_logicbench import load_logicbench

    examples = load_logicbench(
        logic_type='propositional_logic',
        reasoning_patterns=['modus_tollens', 'disjunctive_syllogism'],
        max_examples_per_pattern=10
    )
"""

import json
import urllib.request
import urllib.error


def load_logicbench(logic_type='propositional_logic', reasoning_patterns=None, max_examples_per_pattern=None):
    """
    Load LogicBench dataset directly from GitHub repository.

    Args:
        logic_type: str, 'propositional_logic', 'first_order_logic', or 'nm_logic'
        reasoning_patterns: list of str, specific patterns to load
                           (e.g., ['modus_tollens', 'disjunctive_syllogism'])
                           If None, loads all available patterns for the logic type
        max_examples_per_pattern: int, optional limit on number of examples to load per pattern

    Returns:
        List[dict], each with:
            - 'id': str, unique identifier
            - 'text': str, context/premises
            - 'query': str, question
            - 'ground_truth': bool/str, answer
            - 'pattern': str, reasoning pattern name
            - 'logic_type': str, type of logic

    Example:
        >>> examples = load_logicbench('propositional_logic', ['modus_tollens'], 5)
        >>> print(f"Loaded {len(examples)} examples")
        >>> print(examples[0]['text'])
    """
    print(f"Loading LogicBench from GitHub (logic_type={logic_type})...")

    # Default reasoning patterns for each logic type
    default_patterns = {
        'propositional_logic': [
            'modus_tollens',
            'disjunctive_syllogism',
            'hypothetical_syllogism',
            'constructive_dilemma',
            'destructive_dilemma',
            'bidirectional_dilemma',
            'commutation',
            'material_implication'
        ],
        'first_order_logic': [
            'universal_instantiation',
            'existential_generalization',
            'existential_instantiation',
            'universal_generalization'
        ],
        'nm_logic': [
            # Non-monotonic logic patterns (add as needed)
        ]
    }

    if reasoning_patterns is None:
        reasoning_patterns = default_patterns.get(logic_type, ['modus_tollens'])
        print(f"  Using default patterns: {reasoning_patterns}")

    base_url = "https://raw.githubusercontent.com/Mihir3009/LogicBench/main/data/LogicBench(Eval)/BQA"

    examples = []
    for pattern in reasoning_patterns:
        print(f"  Loading pattern: {pattern}")

        # LogicBench uses data_instances.json (not numbered files)
        url = f"{base_url}/{logic_type}/{pattern}/data_instances.json"
        pattern_examples = 0

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())

                # Extract samples from LogicBench format
                for sample in data.get('samples', []):
                    if max_examples_per_pattern and pattern_examples >= max_examples_per_pattern:
                        break

                    sample_id = sample.get('id', f"{pattern}_{len(examples)}")
                    context = sample.get('context', '')

                    # LogicBench has qa_pairs (question-answer pairs)
                    qa_pairs = sample.get('qa_pairs', [])
                    if qa_pairs:
                        # Use first QA pair
                        qa = qa_pairs[0]
                        query = qa.get('question', '')
                        ground_truth = qa.get('answer', None)
                    else:
                        query = ''
                        ground_truth = None

                    examples.append({
                        'id': sample_id,
                        'text': context,
                        'query': query,
                        'ground_truth': ground_truth,
                        'pattern': pattern,
                        'logic_type': logic_type
                    })
                    pattern_examples += 1

        except urllib.error.HTTPError as e:
            print(f"    Error loading {url}: HTTP {e.code}")
        except Exception as e:
            print(f"    Error processing {url}: {e}")

        print(f"    Loaded {pattern_examples} examples from {pattern}")

    print(f"Total loaded: {len(examples)} examples from LogicBench")
    return examples


def load_all_propositional(max_examples_per_pattern=None):
    """
    Convenience function to load all propositional logic patterns.

    Args:
        max_examples_per_pattern: int, optional limit per pattern

    Returns:
        List[dict], all propositional logic examples
    """
    return load_logicbench(
        logic_type='propositional_logic',
        reasoning_patterns=None,  # Load all patterns
        max_examples_per_pattern=max_examples_per_pattern
    )


def load_all_fol(max_examples_per_pattern=None):
    """
    Convenience function to load all first-order logic patterns.

    Args:
        max_examples_per_pattern: int, optional limit per pattern

    Returns:
        List[dict], all FOL examples
    """
    return load_logicbench(
        logic_type='first_order_logic',
        reasoning_patterns=None,  # Load all patterns
        max_examples_per_pattern=max_examples_per_pattern
    )


if __name__ == '__main__':
    # Test the loader
    print("Testing LogicBench loader...\n")

    # Load a small sample
    examples = load_logicbench(
        logic_type='propositional_logic',
        reasoning_patterns=['modus_tollens'],
        max_examples_per_pattern=2
    )

    print("\n" + "="*60)
    print("Sample Example:")
    print("="*60)
    if examples:
        ex = examples[0]
        print(f"ID: {ex['id']}")
        print(f"Pattern: {ex['pattern']}")
        print(f"Logic Type: {ex['logic_type']}")
        print(f"\nContext:\n{ex['text']}")
        print(f"\nQuery: {ex['query']}")
        print(f"Answer: {ex['ground_truth']}")
    else:
        print("No examples loaded!")
