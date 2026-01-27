#!/usr/bin/env python3
"""
Wrapper for propositional extraction with unified output format.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'from_text_to_logic'))

from logify import LogifyConverter

# Global converter instance (lazy initialization)
_logify_converter = None

def get_logify_converter():
    """Get or create the LogifyConverter instance."""
    global _logify_converter
    if _logify_converter is None:
        # Get API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set.\n"
                "Set it with: export OPENAI_API_KEY='your-key-here'"
            )
        _logify_converter = LogifyConverter(api_key=api_key)
    return _logify_converter


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
