"""
SAT solver interface module.

This module provides a clean interface to SAT solvers (python-sat or Z3),
handling formulation validation, solving, and result interpretation.

Core responsibilities:
1. Solve SAT problems in CNF/DIMACS format
2. Test entailment via unsatisfiability checking
3. Validate formulations (syntax, solvability)
4. Handle solver timeouts and errors

Key functions:
- solve_sat(clauses, query_literal, timeout=30) -> dict
  Main SAT solving entry point, returns answer + diagnostics

- validate_formulation(clauses) -> dict
  Quick validation: check if formulation is well-formed and solvable

- test_entailment(clauses, query_literal) -> str
  Determine if query is entailed/contradicted/unknown

Entailment logic:
The solver determines logical consequence through unsatisfiability testing:
- Query is ENTAILED if: clauses ∧ ¬query is UNSAT
  (i.e., negating the query makes the theory inconsistent)
- Query is CONTRADICTED if: clauses ∧ query is UNSAT
  (i.e., asserting the query makes the theory inconsistent)
- Query is UNKNOWN if: both clauses ∧ query and clauses ∧ ¬query are SAT
  (i.e., query is consistent with theory but not required)

Output format from solve_sat():
{
    'answer': str,                      # 'Entailed' | 'Contradicted' | 'Unknown'
    'satisfiable': bool | None,         # Is base theory satisfiable?
    'model': Dict[int, bool] | None,    # Satisfying assignment if SAT
    'solver_time': float,               # Time spent in solver (seconds)
    'error': str | None,                # Error message if solver failed
    'timeout': bool                     # True if solver timed out
}

Output format from validate_formulation():
{
    'valid': bool,                      # Is formulation well-formed?
    'error_message': str | None,        # Description of error if invalid
    'num_variables': int,               # Number of unique variables
    'num_clauses': int                  # Number of clauses
}

Solver choice:
- Primary: python-sat (lightweight, pure Python, easy install)
- Fallback: Z3 (if python-sat unavailable, more powerful but heavier)

Design decisions:
- DIMACS CNF format (standard, solver-agnostic)
- Timeout handling (prevent infinite solving)
- Entailment via UNSAT testing (sound and complete)
- Error messages preserved for refinement feedback
"""
