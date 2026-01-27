# How to Test the Logic Solver

## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
cd /workspace/repo/code/logic_solver
pip install python-sat
```

### 2. Run Tests
```bash
# All tests should pass!
python comprehensive_test.py
```

Expected output:
```
Total: 9/9 tests passed
🎉 ALL TESTS PASSED! 🎉
```

### 3. Run Demo
```bash
python demo_complete_system.py
```

You'll see the solver answer 5 queries about Alice studying!

### 4. Try It Yourself (Interactive)
```bash
python try_it_yourself.py
```

Then type queries like:
- `P_3 => P_4` (Does studying hard imply passing?)
- `P_3 & ~P_4` (Can Alice study hard but not pass?)
- `P_3` (Does Alice study hard?)

---

## What You Can Test

### ✅ Formula Parsing
Try these formulas in `try_it_yourself.py`:
```
P_1                 # Single proposition
~P_1                # Negation
P_1 & P_2           # Conjunction (AND)
P_1 | P_2           # Disjunction (OR)
P_1 => P_2          # Implication
P_1 <=> P_2         # Biconditional (IFF)
(P_1 & P_2) => P_3  # Nested formulas
~(P_1 | P_2)        # De Morgan's laws
```

### ✅ Reasoning Types

**Entailment** (Query must be true):
```python
result = solver.query("P_3 => P_4")
# → TRUE (confidence 1.0) - It's a hard constraint!
```

**Contradiction** (Query cannot be true):
```python
result = solver.query("P_3 & ~P_4")
# → FALSE (confidence 1.0) - Violates hard constraint
```

**Uncertainty** (Query is possible but not certain):
```python
result = solver.query("P_3")
# → UNCERTAIN (confidence ~0.66) - Soft constraint suggests it
```

---

## Testing with Your Own Data

### Option 1: Use Existing Logified Structure
```python
import json
from logic_solver import LogicSolver

# Load any logified JSON
with open('your_logified.json', 'r') as f:
    logified = json.load(f)

# Create solver
solver = LogicSolver(logified)

# Query (you need to write formulas manually)
result = solver.query("P_1 => P_2")
print(f"{result.answer} (confidence: {result.confidence:.2f})")
```

### Option 2: Create Your Own Structure
```python
from logic_solver import LogicSolver

# Define your own knowledge base
my_knowledge = {
    "primitive_props": [
        {"id": "P_1", "translation": "It is raining"},
        {"id": "P_2", "translation": "The ground is wet"},
        {"id": "P_3", "translation": "I carry an umbrella"}
    ],
    "hard_constraints": [
        {
            "formula": "P_1 => P_2",
            "translation": "If it rains, the ground gets wet"
        }
    ],
    "soft_constraints": [
        {
            "formula": "P_1 => P_3",
            "weight": 0.8,
            "translation": "Usually carry umbrella when raining"
        }
    ]
}

# Test it!
solver = LogicSolver(my_knowledge)

print(solver.query("P_1 => P_2"))  # TRUE (hard constraint)
print(solver.query("P_1 & ~P_2"))  # FALSE (contradiction)
print(solver.query("P_1 => P_3"))  # UNCERTAIN (soft constraint)
```

---

## Understanding the Output

Every query returns a `SolverResult` with:

```python
result = solver.query("P_1 => P_2")

result.answer       # "TRUE", "FALSE", or "UNCERTAIN"
result.confidence   # 0.0 to 1.0
result.explanation  # Human-readable explanation
```

### Answer Types:

**TRUE** - Query is entailed by the knowledge base
- Confidence is always 1.0
- The query MUST be true given the facts

**FALSE** - Query contradicts the knowledge base
- Confidence is always 1.0
- The query CANNOT be true given the facts

**UNCERTAIN** - Query is consistent but not entailed
- Confidence varies based on soft constraints (0.0 to 1.0)
- The query MIGHT be true, but we're not certain

---

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'pysat'
```
**Fix:** `pip install python-sat`

### Unknown Proposition Error
```
Error during solving: Unknown proposition: P_99
```
**Fix:** Make sure you only use propositions defined in your structure (P_1, P_2, etc.)

### Syntax Error
```
Error during solving: Invalid proposition ID: &
```
**Fix:** Check your formula syntax. Use: `&`, `|`, `~`, `=>`, `<=>`

---

## What to Test Next?

1. **Edge Cases**
   - Empty structures
   - Tautologies: `P_1 | ~P_1`
   - Contradictions: `P_1 & ~P_1`
   - Complex nested formulas

2. **Performance**
   - Time how long queries take
   - Try structures with 50+ propositions

3. **Confidence Scores**
   - Test with different soft constraint weights
   - Compare confidence for high vs low weights

4. **Error Handling**
   - Invalid formulas
   - Unknown propositions
   - Malformed JSON structures

---

## Files to Try

### Test Files
- `comprehensive_test.py` - Full test suite (9 tests)
- `test_logic_solver.py` - Original test suite (6 tests)
- `demo_complete_system.py` - Full demo with Alice example

### Interactive
- `try_it_yourself.py` - Interactive query testing

### Debug Scripts
- `debug_solver.py` - Check encoding details
- `debug_consistency.py` - Test consistency checking

### Example Data
- `/workspace/repo/artifacts/code/logify2_full_demo.json` - Alice example

---

## Getting Help

### Documentation
- `README.md` - Full API documentation
- `LOGIC_SOLVER_IMPLEMENTATION.md` - Implementation details
- `TEST_RESULTS.md` - Test results and coverage
- `INTEGRATION_STATUS.md` - What's done and what's left

### Quick Reference
- `QUICK_START.md` - Quick reference guide

---

## Next Steps

Once you're comfortable with the logic solver:

1. **Test on your own data** - Create your own logified structures
2. **Implement NL interface** - See `INTEGRATION_STATUS.md` for details
3. **Integrate with full system** - Connect text → logic → solver → answer

The logic solver is ready! You just need the NL interface to complete the system.
