#!/usr/bin/env python3
"""
Complete End-to-End Demo of the Logic Solver

This demonstrates the full pipeline:
1. Load a logified text structure (from logify.py output)
2. Ask queries in propositional logic form
3. Get TRUE/FALSE/UNCERTAIN answers with confidence scores
"""

import json
from logic_solver import LogicSolver


def main():
    print("="*80)
    print("LOGIC-AWARE TEXT REASONING SYSTEM - COMPLETE DEMO")
    print("="*80)
    print()

    # Step 1: Load the logified structure (output from from_text_to_logic)
    print("STEP 1: Loading logified text structure...")
    print()

    logified_file = '/workspace/repo/artifacts/code/logify2_full_demo.json'

    with open(logified_file, 'r') as f:
        logified_structure = json.load(f)

    print(f"✓ Loaded structure from: {logified_file}")
    print(f"  - Propositions: {len(logified_structure['primitive_props'])}")
    print(f"  - Hard constraints: {len(logified_structure['hard_constraints'])}")
    print(f"  - Soft constraints: {len(logified_structure['soft_constraints'])}")
    print()

    # Display some of the content
    print("Sample propositions:")
    for prop in logified_structure['primitive_props'][:3]:
        print(f"  {prop['id']}: {prop['translation']}")
    print()

    print("Hard constraints (must hold):")
    for constraint in logified_structure['hard_constraints']:
        print(f"  {constraint['id']}: {constraint['formula']}")
        print(f"    → {constraint['translation']}")
    print()

    print("Soft constraints (defeasible, with confidence weights):")
    for constraint in logified_structure['soft_constraints']:
        weight = constraint.get('weight', 'N/A')
        print(f"  {constraint['id']}: {constraint['formula']} (weight: {weight})")
        print(f"    → {constraint['translation']}")
    print()

    # Step 2: Initialize the logic solver
    print("="*80)
    print("STEP 2: Initializing logic solver with PySAT RC2...")
    print()

    solver = LogicSolver(logified_structure)
    print("✓ Solver initialized successfully!")
    print()

    # Step 3: Run queries
    print("="*80)
    print("STEP 3: Asking queries about the text...")
    print()

    queries = [
        {
            "question": "Does the text entail that IF Alice studies hard, THEN she passes?",
            "formula": "P_3 => P_4",
            "note": "This should be TRUE (hard constraint H_1)"
        },
        {
            "question": "Does Alice study hard?",
            "formula": "P_3",
            "note": "This should be UNCERTAIN (soft constraint says 'usually', weight 0.8)"
        },
        {
            "question": "Can Alice study hard but NOT pass the exam?",
            "formula": "P_3 & ~P_4",
            "note": "This should be FALSE (contradicts hard constraint H_1)"
        },
        {
            "question": "If Alice is focused, does she complete her homework?",
            "formula": "P_6 => P_7",
            "note": "This should be TRUE (hard constraint H_2)"
        },
        {
            "question": "Does Alice prefer studying in the library?",
            "formula": "P_9",
            "note": "This should be UNCERTAIN (soft constraint, weight 0.75)"
        },
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query['question']}")
        print(f"  Formula: {query['formula']}")
        print(f"  Note: {query['note']}")
        print()

        result = solver.query(query['formula'])

        print(f"  ⟹ ANSWER: {result.answer}")
        print(f"  ⟹ CONFIDENCE: {result.confidence:.3f}")
        print(f"  ⟹ EXPLANATION: {result.explanation}")
        print()

    # Step 4: Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("The logic solver successfully:")
    print("  ✓ Parsed propositional logic formulas")
    print("  ✓ Converted them to CNF for SAT solving")
    print("  ✓ Used PySAT RC2 to check entailment and consistency")
    print("  ✓ Computed confidence scores based on soft constraints")
    print("  ✓ Returned TRUE/FALSE/UNCERTAIN with explanations")
    print()
    print("This demonstrates the 'logify once, query many' paradigm:")
    print("  1. Text is logified ONCE (already done)")
    print("  2. Multiple queries are answered via SYMBOLIC REASONING")
    print("  3. No need to re-process the original text")
    print("  4. Provably correct answers (given correct logification)")
    print()
    print("="*80)


if __name__ == "__main__":
    main()
