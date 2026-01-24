#!/usr/bin/env python3
"""
Interactive demo - Try the logic solver yourself!

This lets you test queries against the Alice example.
"""

import json
from logic_solver import LogicSolver


def main():
    print("="*80)
    print("INTERACTIVE LOGIC SOLVER DEMO")
    print("="*80)
    print()

    # Load the Alice example
    with open('/workspace/repo/artifacts/code/logify2_full_demo.json', 'r') as f:
        logified = json.load(f)

    # Show available propositions
    print("Available propositions:")
    for prop in logified['primitive_props']:
        print(f"  {prop['id']}: {prop['translation']}")
    print()

    print("Hard constraints:")
    for constraint in logified['hard_constraints']:
        print(f"  {constraint['id']}: {constraint['translation']}")
        print(f"    Formula: {constraint['formula']}")
    print()

    print("Soft constraints:")
    for constraint in logified['soft_constraints']:
        weight = constraint.get('weight', 'N/A')
        print(f"  {constraint['id']}: {constraint['translation']} (weight: {weight})")
        print(f"    Formula: {constraint['formula']}")
    print()

    # Initialize solver
    solver = LogicSolver(logified)
    print("Solver initialized!")
    print()

    # Example queries
    print("="*80)
    print("TRY THESE EXAMPLE QUERIES:")
    print("="*80)
    print()
    print("Examples:")
    print("  P_3 => P_4        (Does studying hard imply passing?)")
    print("  P_3 & ~P_4        (Can Alice study hard but not pass?)")
    print("  P_3               (Does Alice study hard?)")
    print("  P_1 & P_2         (Is Alice a student who loves math?)")
    print("  P_6 => P_7        (Does focus imply homework completion?)")
    print("  ~P_5              (Is Alice NOT distracted?)")
    print()
    print("Operators: & (AND), | (OR), ~ (NOT), => (IMPLIES), <=> (IFF)")
    print()

    # Interactive loop
    print("="*80)
    print("Enter your queries (or 'quit' to exit):")
    print("="*80)
    print()

    while True:
        try:
            query = input("Query> ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not query:
                continue

            # Solve the query
            result = solver.query(query)

            print()
            print(f"  Answer: {result.answer}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Explanation: {result.explanation}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"  Error: {e}")
            print()


if __name__ == "__main__":
    main()
