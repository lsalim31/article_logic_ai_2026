"""
Natural language to symbolic formalization module.

This module handles the initial translation from natural language text + query
into logical formulations for Logic-LM++.

Supports two logic types:
1. Propositional logic: Ground atoms (P, Q, R) without quantifiers
2. First-order logic (FOL): Predicates with arguments and quantifiers

Core responsibilities:
1. Call LLM with appropriate formalization prompt (propositional or FOL)
2. Parse JSON response into structured format
3. Validate output structure (syntax and well-formedness)
4. Handle malformed outputs (count as formalization failure)

Key functions:
- formalize(text, query, logic_type='propositional', ...) -> dict
  Main entry point supporting both propositional and FOL

- formalize_to_fol(text, query, ...) -> dict
  Legacy FOL-only entry point (for backward compatibility)

- parse_formalization_response(raw_response) -> dict
  Parse LLM JSON output, handle malformed responses

- validate_formalization(formalization) -> bool
  Check if formalization structure is valid

Output format:
{
    'predicates': Dict[str, str],       # e.g., {'P': 'Liam finished work early', ...}
    'premises': List[str],              # e.g., ['P → Q', '¬Q', ...]
    'conclusion': str,                  # e.g., '¬P'
    'raw_response': str,                # Full LLM output for debugging
    'formalization_error': str | None   # Error message if formalization failed
}

Design decisions:
- Propositional logic for LogicBench propositional tasks (better Z3 compatibility)
- FOL for FOLIO, AR-LSAT (requires Prover9 or proper FOL handling)
- JSON output from LLM (reliable parsing)
- Malformed outputs → formalization failure, no retry
"""

import json
import os
from openai import OpenAI
from config import (
    FORMALIZATION_PROMPT,
    PROPOSITIONAL_FORMALIZATION_PROMPT,
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS
)


def formalize_to_fol(text, query, model_name=MODEL_NAME, temperature=TEMPERATURE):
    """
    Main entry point for NL → FOL translation.

    Args:
        text: Natural language text (premises)
        query: Natural language query (conclusion to test)
        model_name: LLM model to use
        temperature: Sampling temperature

    Returns:
        dict with keys: predicates, premises, conclusion, raw_response, formalization_error
    """
    # Format the prompt with text and query
    prompt = FORMALIZATION_PROMPT.format(text=text, query=query)

    # Call LLM - auto-detect OpenRouter or OpenAI
    # If OPENROUTER_API_KEY is set, use it; otherwise use OPENAI_API_KEY
    api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
    base_url = None

    if os.environ.get('OPENROUTER_API_KEY'):
        base_url = "https://openrouter.ai/api/v1"
    elif os.environ.get('OPENAI_BASE_URL'):
        base_url = os.environ.get('OPENAI_BASE_URL')

    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a formal logician."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS
        )

        raw_response = response.choices[0].message.content

    except Exception as e:
        # LLM call failed
        return {
            'predicates': {},
            'premises': [],
            'conclusion': '',
            'raw_response': '',
            'formalization_error': f"LLM call failed: {str(e)}"
        }

    # Parse the response
    formalization = parse_formalization_response(raw_response)

    # Validate the formalization
    if validate_formalization(formalization):
        formalization['formalization_error'] = None
    else:
        formalization['formalization_error'] = "Validation failed: missing required fields or invalid structure"

    return formalization


def parse_formalization_response(raw_response):
    """
    Parse LLM JSON output, handle malformed responses.

    Args:
        raw_response: Raw LLM response string

    Returns:
        dict with keys: predicates, premises, conclusion, raw_response, formalization_error
    """
    result = {
        'predicates': {},
        'premises': [],
        'conclusion': '',
        'raw_response': raw_response,
        'formalization_error': None
    }

    # Try to parse JSON
    try:
        # Extract JSON if wrapped in markdown code blocks
        response_text = raw_response.strip()
        if response_text.startswith('```'):
            # Remove code block markers
            lines = response_text.split('\n')
            # Find start and end of JSON
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith('```'):
                    if in_json:
                        break
                    else:
                        in_json = True
                        continue
                if in_json:
                    json_lines.append(line)
            response_text = '\n'.join(json_lines)

        # Parse JSON
        parsed = json.loads(response_text)

        # Extract fields
        result['predicates'] = parsed.get('predicates', {})
        result['premises'] = parsed.get('premises', [])
        result['conclusion'] = parsed.get('conclusion', '')

    except json.JSONDecodeError as e:
        # Malformed JSON - count as formalization failure
        result['formalization_error'] = f"JSON parse error: {str(e)}"
    except Exception as e:
        result['formalization_error'] = f"Unexpected error during parsing: {str(e)}"

    return result


def validate_formalization(formalization):
    """
    Check if formalization structure is valid (has required fields, valid FOL syntax).

    Args:
        formalization: dict with predicates, premises, conclusion

    Returns:
        bool: True if valid, False otherwise
    """
    # Check if formalization failed during parsing
    if formalization.get('formalization_error') is not None:
        return False

    # Check required fields exist
    if 'predicates' not in formalization:
        return False
    if 'premises' not in formalization:
        return False
    if 'conclusion' not in formalization:
        return False

    # Check types
    if not isinstance(formalization['predicates'], dict):
        return False
    if not isinstance(formalization['premises'], list):
        return False
    if not isinstance(formalization['conclusion'], str):
        return False

    # Check not empty (at minimum need some premises)
    if len(formalization['premises']) == 0:
        return False

    # Syntactic validation only - semantic correctness checked by solver
    return True
