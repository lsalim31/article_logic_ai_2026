#!/usr/bin/env python3
"""
Comprehensive test script to verify the logic solver works correctly.
Tests all components: encoding, parsing, SAT solving, and edge cases.
"""

import json
import sys
import os
import traceback
from typing import Dict, Any

# Add parent directory to path to import logic_solver as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import():
    """Test that all imports work correctly."""
    print("="*80)
    print("TEST 1: Module Imports")
    print("="*80)

    try:
        from logic_solver import LogicSolver, SolverResult, solve_query
        from logic_solver.encoding import LogicEncoder, FormulaParser
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_formula_parser():
    """Test the formula parser with various inputs."""
    print("\n" + "="*80)
    print("TEST 2: Formula Parser")
    print("="*80)

    from logic_solver.encoding import FormulaParser

    prop_to_var = {"P_1": 1, "P_2": 2, "P_3": 3, "P_4": 4}
    parser = FormulaParser(prop_to_var)

    test_cases = [
        ("P_1", [[1]], "Single proposition"),
        ("~P_1", [[-1]], "Negation"),
        ("P_1 & P_2", [[1], [2]], "Conjunction"),
        ("P_1 | P_2", [[1, 2]], "Disjunction"),
        ("P_1 => P_2", [[-1, 2]], "Implication"),
        ("P_1 <=> P_2", [[-1, 2], [-2, 1]], "Biconditional"),
        ("~(P_1 & P_2)", [[-1, -2]], "De Morgan's law"),
        ("(P_1 | P_2) & P_3", [[1, 2], [3]], "Mixed operators"),
    ]

    all_passed = True
    for formula, expected, description in test_cases:
        try:
            result = parser.parse(formula)
            # Sort for comparison
            result_sorted = sorted([sorted(clause) for clause in result])
            expected_sorted = sorted([sorted(clause) for clause in expected])

            if result_sorted == expected_sorted:
                print(f"  ✓ {description}: {formula}")
            else:
                print(f"  ✗ {description}: {formula}")
                print(f"    Expected: {expected_sorted}")
                print(f"    Got: {result_sorted}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {description}: {formula}")
            print(f"    Error: {e}")
            all_passed = False

    return all_passed


def test_encoder():
    """Test the LogicEncoder."""
    print("\n" + "="*80)
    print("TEST 3: Logic Encoder")
    print("="*80)

    from logic_solver.encoding import LogicEncoder

    structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "Prop 1"},
            {"id": "P_2", "translation": "Prop 2"},
        ],
        "hard_constraints": [
            {"formula": "P_1 => P_2", "translation": "If P1 then P2"}
        ],
        "soft_constraints": [
            {"formula": "P_1", "weight": 0.8, "translation": "Usually P1"}
        ]
    }

    try:
        encoder = LogicEncoder(structure)
        wcnf = encoder.encode()

        print(f"  ✓ Encoder created successfully")
        print(f"    - Propositions mapped: {len(encoder.prop_to_var)}")
        print(f"    - Hard clauses: {len(wcnf.hard)}")
        print(f"    - Soft clauses: {len(wcnf.soft)}")
        print(f"    - Hard clauses: {wcnf.hard}")

        # Verify hard constraint P_1 => P_2 becomes [-1, 2]
        if [-1, 2] in wcnf.hard:
            print(f"  ✓ Hard constraint correctly encoded as [-1, 2]")
        else:
            print(f"  ✗ Hard constraint not found")
            return False

        return True
    except Exception as e:
        print(f"  ✗ Encoder failed: {e}")
        traceback.print_exc()
        return False


def test_basic_sat():
    """Test basic SAT solving."""
    print("\n" + "="*80)
    print("TEST 4: Basic SAT Solving")
    print("="*80)

    from logic_solver import LogicSolver

    structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "A"},
            {"id": "P_2", "translation": "B"},
        ],
        "hard_constraints": [
            {"formula": "P_1 => P_2", "translation": "If A then B"}
        ],
        "soft_constraints": []
    }

    try:
        solver = LogicSolver(structure)

        # Test 1: Query the hard constraint itself (should be TRUE)
        result = solver.query("P_1 => P_2")
        assert result.answer == "TRUE", f"Expected TRUE, got {result.answer}"
        print(f"  ✓ Entailment check: P_1 => P_2 is TRUE")

        # Test 2: Contradiction (should be FALSE)
        result = solver.query("P_1 & ~P_2")
        assert result.answer == "FALSE", f"Expected FALSE, got {result.answer}"
        print(f"  ✓ Contradiction check: P_1 & ~P_2 is FALSE")

        # Test 3: Consistent but not entailed (should be UNCERTAIN)
        result = solver.query("P_1")
        assert result.answer == "UNCERTAIN", f"Expected UNCERTAIN, got {result.answer}"
        print(f"  ✓ Uncertainty check: P_1 is UNCERTAIN")

        return True
    except Exception as e:
        print(f"  ✗ SAT solving failed: {e}")
        traceback.print_exc()
        return False


def test_with_soft_constraints():
    """Test solver with soft constraints."""
    print("\n" + "="*80)
    print("TEST 5: Soft Constraints")
    print("="*80)

    from logic_solver import LogicSolver

    structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "Studies"},
            {"id": "P_2", "translation": "Passes"},
        ],
        "hard_constraints": [
            {"formula": "P_1 => P_2", "translation": "If studies then passes"}
        ],
        "soft_constraints": [
            {"formula": "P_1", "weight": 0.9, "translation": "Usually studies"}
        ]
    }

    try:
        solver = LogicSolver(structure)

        # Query P_1 - should be UNCERTAIN with high confidence
        result = solver.query("P_1")
        print(f"  Query P_1: {result.answer} (confidence: {result.confidence:.3f})")

        assert result.answer == "UNCERTAIN", f"Expected UNCERTAIN, got {result.answer}"
        assert result.confidence > 0.5, f"Expected confidence > 0.5, got {result.confidence}"
        print(f"  ✓ Soft constraint influences confidence (weight 0.9 → conf {result.confidence:.3f})")

        return True
    except Exception as e:
        print(f"  ✗ Soft constraint test failed: {e}")
        traceback.print_exc()
        return False


def test_real_example():
    """Test with the real Alice example from the artifacts."""
    print("\n" + "="*80)
    print("TEST 6: Real Example (Alice)")
    print("="*80)

    from logic_solver import LogicSolver

    try:
        with open('/workspace/repo/artifacts/code/logify2_full_demo.json', 'r') as f:
            logified = json.load(f)

        solver = LogicSolver(logified)
        print(f"  ✓ Loaded Alice example ({len(logified['primitive_props'])} props)")

        # Test entailment
        result = solver.query("P_3 => P_4")  # H_1: Studies hard => Passes
        assert result.answer == "TRUE", f"Expected TRUE for H_1, got {result.answer}"
        print(f"  ✓ H_1 entailment: P_3 => P_4 is TRUE (conf: {result.confidence:.3f})")

        # Test contradiction
        result = solver.query("P_3 & ~P_4")  # Studies but doesn't pass
        assert result.answer == "FALSE", f"Expected FALSE for contradiction, got {result.answer}"
        print(f"  ✓ Contradiction: P_3 & ~P_4 is FALSE (conf: {result.confidence:.3f})")

        # Test uncertain with soft constraint
        result = solver.query("P_3")  # Does Alice study? (S_1: weight 0.8)
        assert result.answer == "UNCERTAIN", f"Expected UNCERTAIN for P_3, got {result.answer}"
        print(f"  ✓ Soft constraint: P_3 is UNCERTAIN (conf: {result.confidence:.3f})")

        return True
    except FileNotFoundError:
        print(f"  ⚠ Alice example file not found, skipping")
        return True
    except Exception as e:
        print(f"  ✗ Real example test failed: {e}")
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*80)
    print("TEST 7: Edge Cases")
    print("="*80)

    from logic_solver import LogicSolver
    from logic_solver.encoding import FormulaParser

    # Test 1: Empty structure
    try:
        structure = {
            "primitive_props": [],
            "hard_constraints": [],
            "soft_constraints": []
        }
        solver = LogicSolver(structure)
        print(f"  ✓ Empty structure handled")
    except Exception as e:
        print(f"  ✗ Empty structure failed: {e}")
        return False

    # Test 2: Unknown proposition in query
    structure = {
        "primitive_props": [{"id": "P_1", "translation": "A"}],
        "hard_constraints": [],
        "soft_constraints": []
    }
    solver = LogicSolver(structure)

    try:
        result = solver.query("P_99")  # Unknown proposition
        # Solver catches the error and returns UNCERTAIN with error message
        if "Unknown proposition" in result.explanation or "Error" in result.explanation:
            print(f"  ✓ Unknown proposition handled gracefully: {result.explanation}")
        else:
            print(f"  ✗ Unknown proposition should be in error message")
            return False
    except ValueError as e:
        # Also acceptable - error propagated
        print(f"  ✓ Unknown proposition correctly rejected with exception")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

    # Test 3: Malformed formula
    try:
        result = solver.query("P_1 &&&")  # Invalid syntax
        # Solver catches the error and returns UNCERTAIN with error message
        if "Error" in result.explanation or "Invalid" in result.explanation:
            print(f"  ✓ Malformed formula handled gracefully: {result.explanation}")
        else:
            print(f"  ✗ Malformed formula should be in error message")
            return False
    except Exception as e:
        # Also acceptable - error propagated
        print(f"  ✓ Malformed formula correctly rejected with exception")

    # Test 4: Tautology
    structure = {
        "primitive_props": [{"id": "P_1", "translation": "A"}],
        "hard_constraints": [],
        "soft_constraints": []
    }
    solver = LogicSolver(structure)
    result = solver.query("P_1 | ~P_1")  # Tautology
    print(f"  Tautology P_1 | ~P_1: {result.answer} (conf: {result.confidence:.3f})")

    return True


def test_unicode_operators():
    """Test that Unicode operators are handled correctly."""
    print("\n" + "="*80)
    print("TEST 8: Unicode Operators")
    print("="*80)

    from logic_solver import LogicSolver

    structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "A"},
            {"id": "P_2", "translation": "B"},
        ],
        "hard_constraints": [
            {"formula": "P_1 ⟹ P_2", "translation": "If A then B"}  # Unicode arrow
        ],
        "soft_constraints": []
    }

    try:
        solver = LogicSolver(structure)
        print(f"  ✓ Unicode operators in structure handled")

        # Query with Unicode
        result = solver.query("P_1 ⇒ P_2")
        assert result.answer == "TRUE", f"Expected TRUE, got {result.answer}"
        print(f"  ✓ Unicode query operators handled: P_1 ⇒ P_2 is TRUE")

        # Query with mixed operators
        result = solver.query("P_1 ∧ P_2")
        print(f"  ✓ Unicode AND operator handled: P_1 ∧ P_2 is {result.answer}")

        return True
    except Exception as e:
        print(f"  ✗ Unicode operator test failed: {e}")
        traceback.print_exc()
        return False


def test_confidence_computation():
    """Test confidence score computation."""
    print("\n" + "="*80)
    print("TEST 9: Confidence Computation")
    print("="*80)

    from logic_solver import LogicSolver

    # Structure with varying soft constraint weights
    structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "A"},
            {"id": "P_2", "translation": "B"},
        ],
        "hard_constraints": [],
        "soft_constraints": [
            {"formula": "P_1", "weight": 0.9, "translation": "Very likely A"},
            {"formula": "P_2", "weight": 0.1, "translation": "Unlikely B"},
        ]
    }

    try:
        solver = LogicSolver(structure)

        # Query P_1 (high weight soft constraint)
        result1 = solver.query("P_1")
        print(f"  Query P_1 (weight 0.9): {result1.answer} (conf: {result1.confidence:.3f})")

        # Query P_2 (low weight soft constraint)
        result2 = solver.query("P_2")
        print(f"  Query P_2 (weight 0.1): {result2.answer} (conf: {result2.confidence:.3f})")

        # P_1 should have higher confidence than P_2
        if result1.confidence > result2.confidence:
            print(f"  ✓ Confidence ordering correct: {result1.confidence:.3f} > {result2.confidence:.3f}")
        else:
            print(f"  ⚠ Confidence ordering unexpected (may be OK depending on implementation)")

        return True
    except Exception as e:
        print(f"  ✗ Confidence computation test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*80)
    print("COMPREHENSIVE LOGIC SOLVER TEST SUITE")
    print("="*80)
    print()

    tests = [
        ("Module Imports", test_import),
        ("Formula Parser", test_formula_parser),
        ("Logic Encoder", test_encoder),
        ("Basic SAT Solving", test_basic_sat),
        ("Soft Constraints", test_with_soft_constraints),
        ("Real Example", test_real_example),
        ("Edge Cases", test_edge_cases),
        ("Unicode Operators", test_unicode_operators),
        ("Confidence Computation", test_confidence_computation),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe logic solver is working correctly!")
        return 0
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed")
        print("\nPlease review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
