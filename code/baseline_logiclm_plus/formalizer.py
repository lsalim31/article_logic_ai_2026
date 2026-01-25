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
