#!/usr/bin/env python3
"""Debug the logic solver."""

import json
from logic_solver.encoding import LogicEncoder

# Load structure
with open('/workspace/repo/artifacts/code/logify2_full_demo.json', 'r') as f:
    logified = json.load(f)

# Create encoder
encoder = LogicEncoder(logified)

print("Proposition Mapping:")
for prop_id, var in encoder.prop_to_var.items():
    print(f"  {prop_id} -> variable {var}")
print()

# Try to parse hard constraints
print("Parsing Hard Constraints:")
for constraint in logified['hard_constraints']:
    formula = constraint['formula']
    print(f"\n{constraint['id']}: {formula}")
    print(f"  Translation: {constraint['translation']}")

    try:
        clauses = encoder.parser.parse(formula)
        print(f"  CNF clauses: {clauses}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Encode full structure
print("\n" + "="*80)
print("Encoding full WCNF:")
wcnf = encoder.encode()

print(f"Hard clauses: {wcnf.hard}")
print(f"Number of hard clauses: {len(wcnf.hard)}")
print(f"Number of soft clauses: {len(wcnf.soft)}")
print(f"Soft clause weights: {[w for w in wcnf.wght if w][:10]}")  # Show first 10 weights

# Test a specific query
print("\n" + "="*80)
print("Testing query: P_3 & ~P_4 (should violate H_1: P_3 => P_4)")
query_clauses = encoder.encode_query("P_3 & ~P_4", negate=False)
print(f"Query clauses: {query_clauses}")

# Check if H_1 was encoded correctly
print("\nH_1 should produce clause: ~P_3 | P_4 = [-3, 4]")
print("Checking if this is in hard clauses...")
if [-3, 4] in wcnf.hard or [4, -3] in wcnf.hard:
    print("  ✓ Found!")
else:
    print("  ✗ NOT found")
    print(f"  Available hard clauses: {wcnf.hard}")
