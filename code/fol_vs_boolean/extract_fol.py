#!/usr/bin/env python3
"""
Wrapper for FOL extraction with unified output format.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'baseline_logiclm_plus'))

from formalizer import formalize_to_fol


def extract_fol(text, query):
    """
    Extract FOL with error handling.

    Args:
        text: Natural language text (premises)
        query: Natural language query (conclusion)

    Returns:
        dict with: id, extraction_mode, extraction, raw_response, success, error_message
    """
    result = formalize_to_fol(text, query)

    success = (result.get('formalization_error') is None)
    error_message = result.get('formalization_error')
    raw_response = result.get('raw_response', '')

    return {
        'id': None,  # Set by caller
        'extraction_mode': 'fol',
        'extraction': result,
        'raw_response': raw_response,
        'success': success,
        'error_message': error_message
    }


if __name__ == '__main__':
    # Test
    test_text = "Alice is a student. All students are human."
    test_query = "Is Alice human?"
    result = extract_fol(test_text, test_query)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Predicates: {len(result['extraction'].get('predicates', {}))}")
        print(f"Premises: {len(result['extraction'].get('premises', []))}")
    else:
        print(f"Error: {result['error_message']}")
