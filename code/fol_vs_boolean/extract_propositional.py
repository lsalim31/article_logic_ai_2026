#!/usr/bin/env python3
"""
Wrapper for propositional extraction with unified output format.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'from_text_to_logic'))

from logify import logify_text


def extract_propositional(text, query=None):
    """
    Extract propositional logic with error handling.

    Args:
        text: Natural language text
        query: Optional query (not used by logify)

    Returns:
        dict with: id, extraction_mode, extraction, raw_response, success, error_message
    """
    try:
        result = logify_text(text)
        success = True
        error_message = None
        raw_response = result.get('raw_response', '')
    except Exception as e:
        result = {}
        success = False
        error_message = str(e)
        raw_response = ''

    return {
        'id': None,  # Set by caller
        'extraction_mode': 'propositional',
        'extraction': result,
        'raw_response': raw_response,
        'success': success,
        'error_message': error_message
    }


if __name__ == '__main__':
    # Test
    test_text = "Alice is a student. All students are human."
    result = extract_propositional(test_text)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Propositions: {len(result['extraction'].get('primitive_props', []))}")
    else:
        print(f"Error: {result['error_message']}")
