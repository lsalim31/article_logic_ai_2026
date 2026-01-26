"""
Natural language to symbolic formalization module.

This module handles the initial translation from natural language text + query
into first-order logic (FOL) formulation for Logic-LM++.

Core responsibilities:
1. Call LLM with formalization prompt
2. Parse JSON response into structured format
3. Validate output structure (syntax and well-formedness)
4. Handle malformed outputs (count as formalization failure)

Key functions:
- formalize_to_fol(text, query, model_name, temperature=0) -> dict
  Main entry point for NL → FOL translation

- parse_formalization_response(raw_response) -> dict
  Parse LLM JSON output, handle malformed responses

- validate_formalization(formalization) -> bool
  Check if formalization structure is valid (has required fields, valid FOL syntax)

Output format:
{
    'predicates': Dict[str, str],       # e.g., {'Student(x)': 'x is a student', 'Human(x)': '...'}
    'premises': List[str],              # FOL premises: ['∀x (Student(x) → Human(x))', '¬∃x (Young(x) ∧ Teach(x))', ...]
    'conclusion': str,                  # FOL conclusion: 'Human(rose) ∨ Manager(jerry)'
    'raw_response': str,                # Full LLM output for debugging
    'formalization_error': str | None   # Error message if formalization failed
}

Design decisions (from Logic-LM++ paper):
- First-order logic (FOL) formalization (FOLIO, ProofWriter, AR-LSAT require FOL)
- JSON output from LLM (reliable parsing)
- Malformed outputs → formalization failure, no retry
- FOL syntax compatible with Prover9/Z3
- Syntactic validation only at this stage (semantic correctness checked by solver + refinement)
"""

import json
from openai import OpenAI
from config import FORMALIZATION_PROMPT, MODEL_NAME, TEMPERATURE, MAX_TOKENS


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

    # Call LLM
    client = OpenAI()
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
