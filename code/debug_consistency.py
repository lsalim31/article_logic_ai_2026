#!/usr/bin/env python3
"""Debug consistency check."""

import json
from logic_solver import LogicSolver
from pysat.solvers import Solver

# Load structure
with open('/workspace/repo/artifacts/code/logify2_full_demo.json', 'r') as f:
    logified = json.load(f)

# Create solver
logic_solver = LogicSolver(logified)

# Test query: P_3 & ~P_4 (should be inconsistent with H_1: P_3 => P_4)
query = "P_3 & ~P_4"

print(f"Testing query: {query}")
print("This should be INCONSISTENT because:")
print("  - Hard constraint H_1: P_3 => P_4 (i.e., ~P_3 | P_4)")
print("  - Query adds: P_3 & ~P_4")
print("  - Together: ~P_3 | P_4, P_3, ~P_4")
print("  - This is UNSAT!")
print()

# Manually check
base_clauses = [[-3, 4], [-6, 7], [-9, 10]]  # Hard constraints
query_clauses = [[3], [-4]]  # P_3 & ~P_4

all_clauses = base_clauses + query_clauses

print(f"All clauses: {all_clauses}")
print()

# Check SAT
solver = Solver(name='g3', bootstrap_with=all_clauses)
is_sat = solver.solve()

print(f"Manual SAT check: {'SAT' if is_sat else 'UNSAT'}")

if is_sat:
    model = solver.get_model()
    print(f"Model: {model}")
else:
    print("No model (UNSAT as expected!)")

solver.delete()

print()
print("="*80)
print("Now testing with LogicSolver:")

result = logic_solver.check_consistency(query)
print(f"Result: {result}")
print(f"  Answer: {result.answer}")
print(f"  Confidence: {result.confidence}")
print(f"  Explanation: {result.explanation}")
