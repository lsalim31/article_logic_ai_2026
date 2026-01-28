#!/usr/bin/env python3
"""
Single-file LogicBench FOL experiment comparing FOL vs Propositional extraction.

This script uses FIRST-ORDER LOGIC patterns from LogicBench to test extraction quality.
FOL patterns involve quantifiers (∀, ∃) and should reveal differences between extractors.

This script:
1. Loads LogicBench FOL dataset from GitHub
2. Runs both propositional and FOL extraction on same examples
3. Analyzes and compares formalization error rates
4. Saves results to JSON

Usage:
    python run_logicbench_fol_experiment.py

Requirements:
    - OPENROUTER_API_KEY or OPENAI_API_KEY environment variable set
"""

import json
import os
import sys
from collections import Counter

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'from_text_to_logic'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'baseline_logiclm_plus'))

from logify import LogifyConverter
from formalizer import formalize_to_fol
from load_logicbench import load_logicbench

# Initialize the propositional logic converter (needs API key)
# We'll initialize it lazily in the extraction function
_logify_converter = None

def get_logify_converter():
    """Get or create the LogifyConverter instance."""
    global _logify_converter
    if _logify_converter is None:
        # Get API key from environment (try OPENROUTER_API_KEY first, then OPENAI_API_KEY)
        api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set.\n"
                "Set it with: export OPENROUTER_API_KEY='your-key-here'"
            )
        _logify_converter = LogifyConverter(api_key=api_key)
    return _logify_converter


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_propositional(text, query=None):
    """
    Extract propositional logic with error handling.

    Args:
        text: Natural language text
        query: Optional query (not used by logify)

    Returns:
        dict with: extraction_mode, extraction, raw_response, success, error_message
    """
    try:
        converter = get_logify_converter()
        result = converter.convert_text_to_logic(text)
        success = True
        error_message = None
        raw_response = ''  # LogifyConverter doesn't expose raw response
    except Exception as e:
        result = {}
        success = False
        error_message = str(e)
        raw_response = ''

    return {
        'extraction_mode': 'propositional',
        'extraction': result,
        'raw_response': raw_response,
        'success': success,
        'error_message': error_message
    }


def extract_fol(text, query):
    """
    Extract FOL with error handling.

    Args:
        text: Natural language text (premises)
        query: Natural language query (conclusion)

    Returns:
        dict with: extraction_mode, extraction, raw_response, success, error_message
    """
    result = formalize_to_fol(text, query)

    success = (result.get('formalization_error') is None)
    error_message = result.get('formalization_error')
    raw_response = result.get('raw_response', '')

    return {
        'extraction_mode': 'fol',
        'extraction': result,
        'raw_response': raw_response,
        'success': success,
        'error_message': error_message
    }


# Dataset loading is now handled by load_logicbench.py module
# Import with: from load_logicbench import load_logicbench


# ============================================================================
# DUAL EXTRACTION
# ============================================================================

def run_dual_extraction(examples, verbose=True):
    """
    Run both propositional and FOL extraction on same examples.

    Args:
        examples: List[dict], each with 'id', 'text', 'query'
        verbose: bool, print progress

    Returns:
        tuple: (prop_results, fol_results)
    """
    prop_results = []
    fol_results = []

    for i, example in enumerate(examples):
        if verbose:
            print(f"\nProcessing {i+1}/{len(examples)}: {example['id']}")

        text = example['text']
        query = example.get('query', '')

        # Extract propositional
        if verbose:
            print("  Running propositional extraction...")
        prop_result = extract_propositional(text=text, query=query)
        prop_result['id'] = example['id']
        prop_result['original_text'] = text
        prop_result['original_query'] = query
        prop_result['ground_truth'] = example.get('ground_truth')
        prop_results.append(prop_result)
        if verbose:
            print(f"    Success: {prop_result['success']}")

        # Extract FOL
        if verbose:
            print("  Running FOL extraction...")
        fol_result = extract_fol(text=text, query=query)
        fol_result['id'] = example['id']
        fol_result['original_text'] = text
        fol_result['original_query'] = query
        fol_result['ground_truth'] = example.get('ground_truth')
        fol_results.append(fol_result)
        if verbose:
            print(f"    Success: {fol_result['success']}")

    return prop_results, fol_results


# ============================================================================
# ERROR ANALYSIS
# ============================================================================

def analyze_errors(prop_results, fol_results, verbose=True):
    """
    Analyze extraction errors and compare both modes.

    Args:
        prop_results: List[dict], propositional extraction results
        fol_results: List[dict], FOL extraction results
        verbose: bool, print detailed analysis

    Returns:
        dict with complete analysis results
    """
    # Count failures
    prop_failures = [r for r in prop_results if not r['success']]
    fol_failures = [r for r in fol_results if not r['success']]

    total = len(prop_results)

    if verbose:
        # Propositional analysis
        print("\n" + "="*60)
        print("=== PROPOSITIONAL Error Analysis ===")
        print("="*60)
        print(f"Total examples: {total}")
        print(f"Failures: {len(prop_failures)} ({100*len(prop_failures)/total:.1f}%)")

        if prop_failures:
            print(f"\nError messages:")
            error_types = Counter([r['error_message'][:80] if r['error_message'] else 'Unknown'
                                  for r in prop_failures])
            for error, count in error_types.most_common():
                print(f"  [{count}x] {error}")

        # FOL analysis
        print("\n" + "="*60)
        print("=== FOL Error Analysis ===")
        print("="*60)
        print(f"Total examples: {total}")
        print(f"Failures: {len(fol_failures)} ({100*len(fol_failures)/total:.1f}%)")

        if fol_failures:
            print(f"\nError messages:")
            error_types = Counter([r['error_message'][:80] if r['error_message'] else 'Unknown'
                                  for r in fol_failures])
            for error, count in error_types.most_common():
                print(f"  [{count}x] {error}")

        # Overall comparison
        print("\n" + "="*60)
        print("=== OVERALL COMPARISON ===")
        print("="*60)
        print(f"Total examples: {total}")
        print(f"Propositional error rate: {100*len(prop_failures)/total:.1f}%")
        print(f"FOL error rate: {100*len(fol_failures)/total:.1f}%")
        print(f"Difference: {len(fol_failures) - len(prop_failures)} more FOL failures")
        print(f"           ({100*(len(fol_failures) - len(prop_failures))/total:.1f} percentage points)")

    # Compile results
    results = {
        'total_examples': total,
        'propositional': {
            'failures': len(prop_failures),
            'error_rate': len(prop_failures) / total if total > 0 else 0
        },
        'fol': {
            'failures': len(fol_failures),
            'error_rate': len(fol_failures) / total if total > 0 else 0
        },
        'comparison': {
            'absolute_difference': len(fol_failures) - len(prop_failures),
            'percentage_point_difference': (len(fol_failures) - len(prop_failures)) / total if total > 0 else 0,
            'conclusion': 'FOL has more errors' if len(fol_failures) > len(prop_failures) else 'Propositional has more errors'
        }
    }

    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.
    """
    # Configuration - FOL PATTERNS (quantified logic)
    LOGIC_TYPE = 'first_order_logic'  # Testing FOL patterns with quantifiers
    PATTERNS = ['modus_tollens', 'disjunctive_syllogism', 'hypothetical_syllogism']  # Same patterns but with FOL quantifiers
    MAX_EXAMPLES_PER_PATTERN = 20  # More examples to better see differences
    OUTPUT_DIR = 'data/logicbench_fol_results'

    print("="*60)
    print("LogicBench FOL Patterns Extraction Experiment")
    print("Testing on First-Order Logic examples with quantifiers")
    print("="*60)

    # Step 1: Load dataset from GitHub
    print("\n[Step 1] Loading LogicBench FOL dataset from GitHub...")
    try:
        examples = load_logicbench(
            logic_type=LOGIC_TYPE,
            reasoning_patterns=PATTERNS,
            max_examples_per_pattern=MAX_EXAMPLES_PER_PATTERN
        )
    except Exception as e:
        print(f"ERROR loading dataset: {e}")
        print("\nMake sure you have internet connection to access GitHub.")
        import traceback
        traceback.print_exc()
        return

    if not examples:
        print("ERROR: No examples loaded!")
        return

    # Step 2: Run dual extraction
    print(f"\n[Step 2] Running dual extraction on {len(examples)} FOL examples...")
    prop_results, fol_results = run_dual_extraction(examples, verbose=True)

    # Step 3: Analyze errors
    print("\n[Step 3] Analyzing errors...")
    analysis = analyze_errors(prop_results, fol_results, verbose=True)

    # Step 4: Save results
    print(f"\n[Step 4] Saving results to {OUTPUT_DIR}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save extraction results
    prop_output = os.path.join(OUTPUT_DIR, 'propositional_results.jsonl')
    with open(prop_output, 'w') as f:
        for r in prop_results:
            f.write(json.dumps(r) + '\n')
    print(f"  Saved propositional results to {prop_output}")

    fol_output = os.path.join(OUTPUT_DIR, 'fol_results.jsonl')
    with open(fol_output, 'w') as f:
        for r in fol_results:
            f.write(json.dumps(r) + '\n')
    print(f"  Saved FOL results to {fol_output}")

    # Save analysis
    analysis_output = os.path.join(OUTPUT_DIR, 'error_analysis.json')
    with open(analysis_output, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"  Saved error analysis to {analysis_output}")

    # Final summary
    print("\n" + "="*60)
    print("=== EXPERIMENT COMPLETE ===")
    print("="*60)
    print(f"Results saved to: {OUTPUT_DIR}")
    print(f"\nConclusion: {analysis['comparison']['conclusion']}")
    print(f"  Propositional error rate: {100*analysis['propositional']['error_rate']:.1f}%")
    print(f"  FOL error rate: {100*analysis['fol']['error_rate']:.1f}%")
    print(f"  Difference: {analysis['comparison']['percentage_point_difference']:.2%}")


if __name__ == '__main__':
    main()
