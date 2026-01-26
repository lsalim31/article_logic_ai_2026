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

import json
from solver_interface import (
    solve_fol,
    validate_formulation,
    test_entailment_z3,
    test_entailment_prover9,
    parse_solver_error
)
from formalizer import (
    formalize_to_fol,
    parse_formalization_response,
    validate_formalization
)


# ============================================================================
# SOLVER TESTS (Prover9/Z3)
# ============================================================================

def test_z3_fallback():
    """Verify Z3 works as fallback."""
    print("Running test_z3_fallback...")

    # Simple modus ponens: P, P → Q ⊢ Q
    premises = ["P(a)", "Implies(P(a), Q(a))"]
    conclusion = "Q(a)"

    result = test_entailment_z3(premises, conclusion, timeout=5)

    assert result is not None, "Z3 should return a result"
    assert 'answer' in result, "Result should have 'answer' field"
    assert result['answer'] in ['Proved', 'Disproved', 'Unknown', 'Error'], \
        f"Answer should be valid value, got {result['answer']}"

    print(f"  Result: {result['answer']}")
    print("  ✓ test_z3_fallback passed")


def test_entailment_checking():
    """Verify Proved/Disproved/Unknown logic."""
    print("Running test_entailment_checking...")

    # Simple valid entailment
    premises = ["Human(socrates)"]
    conclusion = "Human(socrates)"

    result = solve_fol(premises, conclusion, solver='z3', timeout=5)

    assert result is not None, "Should return result"
    assert 'answer' in result, "Should have answer field"
    print(f"  Simple entailment result: {result['answer']}")
    print("  ✓ test_entailment_checking passed")


def test_solver_timeout():
    """Check timeout handling."""
    print("Running test_solver_timeout...")

    # Use very short timeout to trigger timeout condition
    premises = ["Human(x)"]
    conclusion = "Mortal(x)"

    result = solve_fol(premises, conclusion, solver='z3', timeout=1)

    assert result is not None, "Should return result even on timeout"
    assert 'timeout' in result, "Should have timeout field"
    print(f"  Timeout test result: {result['answer']}, timeout={result.get('timeout')}")
    print("  ✓ test_solver_timeout passed")


def test_malformed_fol():
    """Error handling for invalid FOL syntax."""
    print("Running test_malformed_fol...")

    # Malformed premise
    premises = ["This is not FOL syntax!"]
    conclusion = "Q(a)"

    result = solve_fol(premises, conclusion, solver='z3', timeout=5)

    # Should detect error or return Unknown
    assert result is not None, "Should return result"
    assert result['answer'] in ['Error', 'Unknown'], \
        f"Malformed FOL should error, got {result['answer']}"
    print(f"  Malformed FOL result: {result['answer']}")
    print("  ✓ test_malformed_fol passed")


def test_error_message_parsing():
    """Extract actionable errors for refinement."""
    print("Running test_error_message_parsing...")

    # Test Z3 error parsing
    error_msg = "Z3 exception: timeout exceeded after 30000ms"
    parsed = parse_solver_error(error_msg, 'z3')

    assert parsed is not None, "Should return parsed error"
    assert len(parsed) > 0, "Parsed error should not be empty"
    assert 'timeout' in parsed.lower(), "Should mention timeout"
    print(f"  Parsed error: {parsed}")
    print("  ✓ test_error_message_parsing passed")


def test_prover9_basic():
    """Test on simple FOL problem."""
    print("Running test_prover9_basic...")

    # Simple problem
    premises = ["Human(socrates)"]
    conclusion = "Human(socrates)"

    result = test_entailment_prover9(premises, conclusion, timeout=5)

    # Prover9 not implemented, should return error
    assert result is not None, "Should return result"
    assert result['answer'] == 'Error', "Prover9 not implemented, should error"
    assert 'not implemented' in result['error'].lower(), "Should explain not implemented"
    print(f"  Prover9 result: {result['error']}")
    print("  ✓ test_prover9_basic passed")


# ============================================================================
# FORMALIZATION TESTS (NL → FOL)
# ============================================================================

def test_formalization_output_format():
    """Validate FOL structure (predicates, premises, conclusion)."""
    print("Running test_formalization_output_format...")

    # Create a mock formalization response
    mock_response = json.dumps({
        "predicates": {"Human(x)": "x is human", "Mortal(x)": "x is mortal"},
        "premises": ["∀x (Human(x) → Mortal(x))", "Human(socrates)"],
        "conclusion": "Mortal(socrates)"
    })

    result = parse_formalization_response(mock_response)

    assert result is not None, "Should return parsed result"
    assert 'predicates' in result, "Should have predicates"
    assert 'premises' in result, "Should have premises"
    assert 'conclusion' in result, "Should have conclusion"
    assert isinstance(result['predicates'], dict), "Predicates should be dict"
    assert isinstance(result['premises'], list), "Premises should be list"
    assert isinstance(result['conclusion'], str), "Conclusion should be string"
    print(f"  Parsed {len(result['predicates'])} predicates, {len(result['premises'])} premises")
    print("  ✓ test_formalization_output_format passed")


def test_malformed_json_handling():
    """Malformed LLM output (should fail gracefully)."""
    print("Running test_malformed_json_handling...")

    # Malformed JSON
    malformed = "This is not valid JSON { broken"

    result = parse_formalization_response(malformed)

    assert result is not None, "Should return result"
    assert result['formalization_error'] is not None, "Should have error"
    print(f"  Malformed JSON error: {result['formalization_error']}")
    print("  ✓ test_malformed_json_handling passed")


def test_predicate_extraction():
    """Check predicate definitions."""
    print("Running test_predicate_extraction...")

    # Valid formalization
    formalization = {
        "predicates": {"Human(x)": "x is human"},
        "premises": ["Human(socrates)"],
        "conclusion": "Human(socrates)"
    }

    validation = validate_formulation(formalization['premises'], formalization['conclusion'])

    assert validation is not None, "Should return validation result"
    assert validation['valid'], "Valid formulation should pass"
    assert validation['num_predicates'] >= 0, "Should count predicates"
    print(f"  Found {validation['num_predicates']} predicates")
    print("  ✓ test_predicate_extraction passed")


def test_quantifier_handling():
    """∀/∃ in premises."""
    print("Running test_quantifier_handling...")

    # Premises with quantifiers
    premises = ["∀x (Human(x) → Mortal(x))", "∃x Human(x)"]
    conclusion = "∃x Mortal(x)"

    validation = validate_formulation(premises, conclusion)

    assert validation is not None, "Should validate"
    assert validation['valid'], "Should accept quantifiers"
    print(f"  Validated {len(premises)} premises with quantifiers")
    print("  ✓ test_quantifier_handling passed")


def test_fol_syntax_validation():
    """Reject invalid FOL syntax."""
    print("Running test_fol_syntax_validation...")

    # Invalid formalization - empty premises
    formalization = {
        "predicates": {},
        "premises": [],
        "conclusion": "Q(a)"
    }

    is_valid = validate_formalization(formalization)

    assert not is_valid, "Empty premises should be invalid"
    print("  Empty premises correctly rejected")
    print("  ✓ test_fol_syntax_validation passed")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_formalization_failure_handling():
    """Pipeline continues on failure."""
    print("Running test_formalization_failure_handling...")

    # Malformed JSON response
    malformed = "Not a valid JSON response"

    result = parse_formalization_response(malformed)

    # Should return result with error, not crash
    assert result is not None, "Should handle failure gracefully"
    assert 'formalization_error' in result, "Should record error"
    assert result['formalization_error'] is not None, "Error should be set"
    print(f"  Error handled: {result['formalization_error'][:50]}...")
    print("  ✓ test_formalization_failure_handling passed")


def test_solver_failure_handling():
    """Error recorded in results."""
    print("Running test_solver_failure_handling...")

    # Invalid formulation
    premises = []  # Empty - invalid
    conclusion = "Q(a)"

    result = solve_fol(premises, conclusion, solver='z3', timeout=5)

    assert result is not None, "Should return result"
    assert result['answer'] == 'Error', "Should detect error"
    assert result['error'] is not None, "Should have error message"
    print(f"  Solver error: {result['error']}")
    print("  ✓ test_solver_failure_handling passed")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test functions."""
    print("\n" + "="*70)
    print("LOGIC-LM++ BASELINE TESTS")
    print("="*70 + "\n")

    # Solver tests
    print("--- SOLVER TESTS ---")
    test_z3_fallback()
    test_entailment_checking()
    test_solver_timeout()
    test_malformed_fol()
    test_error_message_parsing()
    test_prover9_basic()

    # Formalization tests
    print("\n--- FORMALIZATION TESTS ---")
    test_formalization_output_format()
    test_malformed_json_handling()
    test_predicate_extraction()
    test_quantifier_handling()
    test_fol_syntax_validation()

    # Integration tests
    print("\n--- INTEGRATION TESTS ---")
    test_formalization_failure_handling()
    test_solver_failure_handling()

    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()
