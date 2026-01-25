"""
FOL solver interface module for Logic-LM++.

This module provides a clean interface to first-order logic theorem provers
(Prover9) and SMT solvers (Z3), as specified in the Logic-LM++ paper.

From paper (page 3, line 309): "Symbolic Reasoning, where we use a symbolic
solver like Prover9 and Z3 theorem prover to solve the formulations generated earlier."

Core responsibilities:
1. Solve FOL problems using Prover9 (theorem prover) or Z3 (SMT solver)
2. Test entailment/contradiction via theorem proving
3. Validate formulations (syntax, well-formedness)
4. Handle solver timeouts and errors
5. Parse solver output and error messages for refinement feedback

Key functions:
- solve_fol(premises, conclusion, solver='prover9', timeout=30) -> dict
  Main FOL solving entry point, returns answer + diagnostics

- validate_formulation(premises, conclusion) -> dict
  Quick validation: check if formulation is well-formed FOL

- test_entailment_prover9(premises, conclusion) -> dict
  Use Prover9 to test if premises ⊢ conclusion

- test_entailment_z3(premises, conclusion) -> dict
  Use Z3 SMT solver to test entailment

- parse_solver_error(error_output, solver) -> str
  Extract actionable error messages for refinement feedback

Entailment logic (theorem proving):
The solver determines logical consequence through proof search:
- Query is PROVED if: premises ⊢ conclusion (proof found)
- Query is DISPROVED if: premises ⊢ ¬conclusion (counterproof found)
- Query is UNKNOWN if: no proof found within timeout (open-world assumption for ProofWriter)

Error types passed to refinement:
1. Syntax errors: malformed FOL formulas
2. Type errors: wrong predicate arity, variable scoping issues
3. Unsatisfiable premises: contradictory axioms
4. Timeout: proof search exceeded time limit

Output format from solve_fol():
{
    'answer': str,                      # 'Proved' | 'Disproved' | 'Unknown' | 'Error'
    'proof': str | None,                # Proof trace if available (for debugging)
    'solver_time': float,               # Time spent in solver (seconds)
    'error': str | None,                # Error message if solver failed (sent to refinement)
    'timeout': bool,                    # True if solver timed out
    'solver_used': str                  # 'prover9' | 'z3'
}

Output format from validate_formulation():
{
    'valid': bool,                      # Is formulation well-formed FOL?
    'error_message': str | None,        # Description of error if invalid
    'num_predicates': int,              # Number of unique predicates
    'num_premises': int                 # Number of premises
}

Solver choice (from Logic-LM++ paper):
- Primary: Prover9 (first-order logic theorem prover, Robinson 1965)
- Fallback: Z3 (SMT solver with FOL support, de Moura & Bjørner 2008)

Design decisions:
- FOL syntax compatible with Prover9 and Z3
- Timeout handling (prevent infinite proof search)
- Detailed error messages for refinement (semantic feedback critical)
- Execution success tracked separately from correctness (Table 2 in paper)
"""
