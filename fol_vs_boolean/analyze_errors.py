#!/usr/bin/env python3
"""
Analyze extraction errors from dual extraction.

Usage:
    python analyze_errors.py
"""

import json
import os
from collections import Counter


def load_results(filepath):
    """Load JSONL results."""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def analyze_errors(results, mode):
    """Analyze error patterns."""
    failures = [r for r in results if not r['success']]

    print(f"\n=== {mode.upper()} Error Analysis ===")
    print(f"Total examples: {len(results)}")
    print(f"Failures: {len(failures)} ({100*len(failures)/len(results):.1f}%)")

    if failures:
        print(f"\nError messages:")
        error_types = Counter([r['error_message'][:80] if r['error_message'] else 'Unknown' for r in failures])
        for error, count in error_types.most_common():
            print(f"  [{count}x] {error}")

    return len(failures)


def main():
    # Load results
    prop_file = 'data/extractions/propositional.jsonl'
    fol_file = 'data/extractions/fol.jsonl'

    if not os.path.exists(prop_file) or not os.path.exists(fol_file):
        print("ERROR: Run run_dual_extraction.py first!")
        return

    print("Loading results...")
    prop_results = load_results(prop_file)
    fol_results = load_results(fol_file)

    if len(prop_results) != len(fol_results):
        print("WARNING: Different number of results!")

    # Analyze each mode
    prop_failures = analyze_errors(prop_results, 'propositional')
    fol_failures = analyze_errors(fol_results, 'fol')

    # Overall comparison
    total = len(prop_results)
    print("\n" + "="*50)
    print("=== OVERALL COMPARISON ===")
    print("="*50)
    print(f"Total examples: {total}")
    print(f"Propositional error rate: {100*prop_failures/total:.1f}%")
    print(f"FOL error rate: {100*fol_failures/total:.1f}%")
    print(f"Difference: {fol_failures - prop_failures} more FOL failures")
    print(f"           ({100*(fol_failures - prop_failures)/total:.1f} percentage points)")

    # Save results
    output_dir = 'data/results'
    os.makedirs(output_dir, exist_ok=True)

    results = {
        'total_examples': total,
        'propositional': {
            'failures': prop_failures,
            'error_rate': prop_failures / total if total > 0 else 0
        },
        'fol': {
            'failures': fol_failures,
            'error_rate': fol_failures / total if total > 0 else 0
        },
        'comparison': {
            'absolute_difference': fol_failures - prop_failures,
            'percentage_point_difference': (fol_failures - prop_failures) / total if total > 0 else 0,
            'conclusion': 'FOL has more errors' if fol_failures > prop_failures else 'Propositional has more errors'
        }
    }

    output_file = os.path.join(output_dir, 'error_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")


if __name__ == '__main__':
    main()
