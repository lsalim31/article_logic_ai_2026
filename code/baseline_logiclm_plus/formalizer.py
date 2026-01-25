"""
Natural language to symbolic formalization module.

This module handles the initial translation from natural language text + query
into propositional logic (SAT) formulation.

Core responsibilities:
1. Call LLM with formalization prompt
2. Parse JSON response into structured format
3. Validate output structure
4. Handle malformed outputs (count as formalization failure)

Key functions:
- formalize_to_sat(text, query, model_name, temperature=0) -> dict
  Main entry point for NL → SAT translation

- parse_formalization_response(raw_response) -> dict
  Parse LLM JSON output, handle malformed responses

- validate_formalization(formalization) -> bool
  Check if formalization structure is valid (has required fields)

Output format:
{
    'variables': Dict[str, str],        # e.g., {'P1': 'John is home', 'P2': '...'}
    'clauses': List[List[int]],         # CNF in DIMACS format: [[1, -2], [2, 3]]
    'query_literal': int,               # Integer literal representing query
    'variable_map': Dict[str, int],     # String name to integer ID mapping
    'raw_response': str,                # Full LLM output for debugging
    'formalization_error': str | None   # Error message if formalization failed
}

Design decisions:
- SAT only (propositional logic, matches main system)
- JSON output from LLM (reliable parsing)
- Malformed outputs → formalization failure (no retry)
- DIMACS CNF format (standard, solver-agnostic)
"""
