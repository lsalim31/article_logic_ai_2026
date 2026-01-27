# Logic Solver - Quick Start Guide

## Installation

```bash
pip install python-sat
```

## Basic Usage (3 Steps)

### Step 1: Load Your Logified Structure

```python
import json

with open('logified.json', 'r') as f:
    logified = json.load(f)
```

**Expected format:**
```json
{
  "primitive_props": [
    {"id": "P_1", "translation": "Alice is a student"},
    {"id": "P_2", "translation": "Alice passes exams"}
  ],
  "hard_constraints": [
    {"formula": "P_1 => P_2", "translation": "Students pass exams"}
  ],
  "soft_constraints": [
    {"formula": "P_1", "weight": 0.8, "translation": "Usually a student"}
  ]
}
```

### Step 2: Create Solver

```python
from logic_solver import LogicSolver

solver = LogicSolver(logified)
```

### Step 3: Ask Queries

```python
result = solver.query("P_1 => P_2")

print(f"Answer: {result.answer}")        # TRUE, FALSE, or UNCERTAIN
print(f"Confidence: {result.confidence}") # 0.0 to 1.0
print(f"Explanation: {result.explanation}")
```

## Formula Syntax

| Operator | Symbol | Alternative | Example |
|----------|--------|-------------|---------|
| AND | `&` | `∧` | `P_1 & P_2` |
| OR | `\|` | `∨` | `P_1 \| P_2` |
| NOT | `~` | `¬` | `~P_1` |
| IMPLIES | `=>` | `→`, `⇒`, `⟹` | `P_1 => P_2` |
| IFF | `<=>` | `↔`, `⇔`, `⟺` | `P_1 <=> P_2` |

**Examples:**
```python
# Simple propositions
solver.query("P_1")

# Conjunctions
solver.query("P_1 & P_2 & P_3")

# Implications
solver.query("P_1 => P_2")

# Complex formulas
solver.query("(P_1 & P_2) => (P_3 | P_4)")
solver.query("~(P_1 & ~P_2)")
```

## Understanding Results

### TRUE (Entailed)
```python
result = solver.query("P_1 => P_2")  # Hard constraint in KB
# → Answer: TRUE, Confidence: 1.0
```
**Meaning:** The query **must be true** given the knowledge base.

### FALSE (Contradicted)
```python
result = solver.query("P_1 & ~P_2")  # Violates P_1 => P_2
# → Answer: FALSE, Confidence: 1.0
```
**Meaning:** The query **cannot be true** - it contradicts the KB.

### UNCERTAIN
```python
result = solver.query("P_1")  # Soft constraint, weight 0.8
# → Answer: UNCERTAIN, Confidence: 0.8
```
**Meaning:** The query is **consistent but not necessary**. Confidence reflects soft constraints.

## Complete Example

```python
import json
from logic_solver import LogicSolver

# Example: Alice studying
logified = {
    "primitive_props": [
        {"id": "P_1", "translation": "Alice studies hard"},
        {"id": "P_2", "translation": "Alice passes exam"}
    ],
    "hard_constraints": [
        {"formula": "P_1 => P_2",
         "translation": "If Alice studies, she passes"}
    ],
    "soft_constraints": [
        {"formula": "P_1", "weight": 0.8,
         "translation": "Alice usually studies"}
    ]
}

solver = LogicSolver(logified)

# Query 1: Does studying imply passing?
r1 = solver.query("P_1 => P_2")
print(f"Q1: {r1.answer} ({r1.confidence:.2f})")
# → TRUE (1.00) - It's a hard constraint!

# Query 2: Does Alice study hard?
r2 = solver.query("P_1")
print(f"Q2: {r2.answer} ({r2.confidence:.2f})")
# → UNCERTAIN (0.80) - Soft constraint suggests yes

# Query 3: Can Alice study but not pass?
r3 = solver.query("P_1 & ~P_2")
print(f"Q3: {r3.answer} ({r3.confidence:.2f})")
# → FALSE (1.00) - Contradicts hard constraint
```

## Testing Your Implementation

Run the included test suite:

```bash
cd /workspace/repo/code
python test_logic_solver.py
```

Or run the complete demo:

```bash
python demo_complete_system.py
```

## Troubleshooting

### ImportError: No module named 'pysat'
```bash
pip install python-sat
```

### ValueError: Unknown proposition
- Make sure your query only uses propositions defined in `primitive_props`
- Proposition IDs must match exactly (e.g., `P_1`, not `p_1`)

### Unexpected UNCERTAIN result
- Check if you have relevant hard constraints
- UNCERTAIN means the query is consistent but not entailed
- Confidence reflects soft constraint weights

## Next Steps

- Read the [full documentation](logic_solver/README.md)
- Review the [implementation details](LOGIC_SOLVER_IMPLEMENTATION.md)
- Check out the [test suite](test_logic_solver.py) for more examples

## Need Help?

The logic solver is fully documented:
- **Quick Start**: This file
- **API Reference**: `logic_solver/README.md`
- **Implementation**: `LOGIC_SOLVER_IMPLEMENTATION.md`
- **Examples**: `demo_complete_system.py`
