# How to Use: Logic Solver

## Quick Start

```python
import json
from logic_solver import LogicSolver

# Load logified structure
with open('logified_weighted.json') as f:
    logified = json.load(f)

# Initialize solver
solver = LogicSolver(logified)

# Query
result = solver.query("P_1 ⟹ P_2")

print(f"Answer: {result.answer}")        # TRUE/FALSE/UNCERTAIN
print(f"Confidence: {result.confidence}") # 0.0 to 1.0
```

## Query Syntax

| Operator | Symbol | ASCII | Example |
|----------|--------|-------|---------|
| NOT | ¬ | ~ | ¬P_1 or ~P_1 |
| AND | ∧ | & | P_1 ∧ P_2 |
| OR | ∨ | \| | P_1 ∨ P_2 |
| IMPLIES | ⟹ | => | P_1 ⟹ P_2 |
| IFF | ⟺ | <=> | P_1 ⟺ P_2 |

## Examples

```python
# Simple queries
solver.query("P_1")              # Is P_1 true?
solver.query("P_1 ∧ P_2")        # Are both true?
solver.query("P_1 ⟹ P_2")       # Does P_1 imply P_2?
solver.query("¬(P_1 ∧ ¬P_2)")   # Complex formula

# Check results
if result.answer == "TRUE":
    print("Formula is entailed")
elif result.answer == "FALSE":
    print("Formula contradicts KB")
else:
    print(f"Uncertain (confidence: {result.confidence:.2f})")
```

## Testing

```bash
python code/logic_solver/test_logic_solver.py
```
