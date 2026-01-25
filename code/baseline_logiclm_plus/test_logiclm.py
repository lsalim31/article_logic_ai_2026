"""
Unit tests for LOGIC-LM++ baseline implementation.

This module provides unit tests for each component of the LOGIC-LM++ pipeline,
ensuring correctness before running on full datasets (FOLIO, ProofWriter, AR-LSAT).

Test categories:
1. Solver tests: FOL theorem proving with Prover9/Z3
2. Formalization tests: NL → FOL translation, output format
3. Refinement tests: Candidate generation, pairwise comparison, BACKTRACKING
4. Integration tests: End-to-end pipeline on toy examples
5. Evaluation tests: Metrics computation (Er, Ea, backtracking stats)

Key test functions:

Solver tests (Prover9/Z3):
- test_prover9_basic(): Test on simple FOL problem
- test_z3_fallback(): Verify Z3 works as fallback
- test_entailment_checking(): Verify Proved/Disproved/Unknown logic
- test_solver_timeout(): Check timeout handling
- test_malformed_fol(): Error handling for invalid FOL syntax
- test_error_message_parsing(): Extract actionable errors for refinement

Formalization tests (NL → FOL):
- test_formalization_output_format(): Validate FOL structure (predicates, premises, conclusion)
- test_malformed_json_handling(): Malformed LLM output (should fail gracefully)
- test_predicate_extraction(): Check predicate definitions
- test_quantifier_handling(): ∀/∃ in premises
- test_fol_syntax_validation(): Reject invalid FOL syntax

Refinement tests (with backtracking):
- test_refinement_generates_alternatives(): N=2 candidates produced
- test_pairwise_comparison_output(): Returns 'A' or 'B'
- test_backtracking_decision(): Returns 'IMPROVED' or 'REVERT'
- test_refinement_loop_with_backtracking(): Track REVERT decisions
- test_early_stopping_consecutive_backtracks(): Stop after threshold REVERTs
- test_refinement_with_solver_error(): Error feedback passed to refinement prompt
- test_context_rich_prompt(): Verify problem statement included in refinement
- test_semantic_vs_syntactic_comparison(): Backtracking catches semantic errors

Integration tests:
- test_end_to_end_folio_example(): Full pipeline on FOLIO-like problem
- test_end_to_end_proofwriter_example(): Full pipeline on ProofWriter-like problem
- test_formalization_failure_handling(): Pipeline continues on failure
- test_solver_failure_handling(): Error recorded in results
- test_backtracking_prevents_degradation(): Verify semantic improvement tracking
- test_early_termination_on_success(): Solver success before max iterations

Evaluation tests (Tables 1-2, Figure 4):
- test_accuracy_metrics(): Standard classification metrics (Table 1)
- test_execution_rate_Er(): % formulations that execute
- test_execution_accuracy_Ea(): % correct among executed (NOT among all)
- test_backtracking_stats(): Figure 4 metrics (corrected per iteration)
- test_efficiency_metrics(): Time, LLM calls tracking
- test_comparison_to_logic_lm(): Verify improvement over baseline

Test data:
- Toy examples: Simple FOL reasoning problems
- Edge cases: Empty text, contradictory premises, tautologies
- Failure cases: Malformed formulations, solver timeouts, semantic errors
- Backtracking cases: Syntactically correct but semantically wrong refinements

Design decisions:
- Unit tests for each module (formalizer, refiner, solver)
- Integration tests for full pipeline with backtracking
- Mock LLM calls for deterministic testing (where possible)
- Real Prover9/Z3 calls (if available, otherwise skip with warning)
- Test semantic improvement tracking (paper's key innovation)
- Verify Er vs. Ea distinction (Table 2 metrics)
"""
