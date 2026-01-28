#!/usr/bin/env python3
"""
Test script for the logic solver module.

This script tests the logic solver with the example logified structure.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import logic_solver as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Compute paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
REPO_DIR = CODE_DIR.parent
ARTIFACTS_DIR = REPO_DIR / "artifacts" / "code"

from logic_solver import LogicSolver, solve_query


def test_basic_queries():
    """Test basic queries with the Alice example."""

    # Load the example logified structure
    demo_file = ARTIFACTS_DIR / "logify2_full_demo.json"
    with open(demo_file, 'r') as f:
        logified = json.load(f)

    print("=" * 80)
    print("LOGIC SOLVER TEST")
    print("=" * 80)
    print()

    # Display the structure
    print("Loaded logified structure:")
    print(f"  - {len(logified['primitive_props'])} primitive propositions")
    print(f"  - {len(logified['hard_constraints'])} hard constraints")
    print(f"  - {len(logified['soft_constraints'])} soft constraints")
    print()

    # Create solver
    solver = LogicSolver(logified)
    print("Solver initialized successfully!")
    print()

    # Test queries
    test_cases = [
        # Query 1: Entailed by hard constraint (H_1: P_3 => P_4)
        {
            "description": "If Alice studies hard (P_3), does she pass the exam (P_4)?",
            "query": "P_3 => P_4",
            "expected": "TRUE"
        },

        # Query 2: Check if P_3 is true (soft constraint S_1 says usually true)
        {
            "description": "Does Alice study hard (P_3)?",
            "query": "P_3",
            "expected": "UNCERTAIN"
        },

        # Query 3: Check consistency of studying hard AND passing exam
        {
            "description": "Is it consistent that Alice studies hard AND passes?",
            "query": "P_3 & P_4",
            "expected": "TRUE or UNCERTAIN"
        },

        # Query 4: Contradiction check
        {
            "description": "Does Alice study hard AND NOT pass? (should contradict H_1)",
            "query": "P_3 & ~P_4",
            "expected": "FALSE"
        },

        # Query 5: Simple proposition check
        {
            "description": "Is Alice a student (P_1)?",
            "query": "P_1",
            "expected": "UNCERTAIN (no hard constraint forces this)"
        },

        # Query 6: Another hard constraint (H_2: P_6 => P_7)
        {
            "description": "If Alice is focused (P_6), does she complete homework (P_7)?",
            "query": "P_6 => P_7",
            "expected": "TRUE"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Query: {test['query']}")
        print(f"  Expected: {test['expected']}")

        try:
            result = solver.query(test['query'])
            print(f"  Result: {result.answer} (confidence: {result.confidence:.3f})")
            print(f"  Explanation: {result.explanation}")
        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)


def test_formula_parsing():
    """Test formula parsing with various operators."""

    print("=" * 80)
    print("FORMULA PARSING TEST")
    print("=" * 80)
    print()

    # Simple structure for testing parsing
    simple_structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "Prop 1"},
            {"id": "P_2", "translation": "Prop 2"},
            {"id": "P_3", "translation": "Prop 3"}
        ],
        "hard_constraints": [
            {"formula": "P_1 => P_2", "translation": "If P1 then P2"}
        ],
        "soft_constraints": []
    }

    solver = LogicSolver(simple_structure)

    test_formulas = [
        "P_1",
        "~P_1",
        "P_1 & P_2",
        "P_1 | P_2",
        "P_1 => P_2",
        "P_1 <=> P_2",
        "(P_1 & P_2) => P_3",
        "P_1 => (P_2 | P_3)",
        "~(P_1 & P_2)",
    ]

    for formula in test_formulas:
        print(f"Testing: {formula}")
        try:
            result = solver.query(formula)
            print(f"  ✓ Parsed successfully: {result.answer} (conf: {result.confidence:.3f})")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

    print("=" * 80)
    print("Parsing tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    print()

    # Run parsing tests first
    test_formula_parsing()
    print("\n\n")

    # Run main tests
    test_basic_queries()
