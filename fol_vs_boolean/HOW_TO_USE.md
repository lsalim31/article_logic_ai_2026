# How to Use: FOL vs Boolean Comparison

## Overview

This directory compares First-Order Logic (FOL) with Propositional Logic (Boolean) approaches.

**Key Finding**: Boolean/Propositional logic is 3-5x more reliable for text-to-logic conversion.

## Quick Comparison

```python
from fol_vs_boolean.compare import compare_approaches

text = "All students must study hard"

results = compare_approaches(text, api_key, num_trials=5)

print(f"FOL Success: {results['fol']['success_rate']:.1%}")
print(f"Boolean Success: {results['boolean']['success_rate']:.1%}")
```

## Why Boolean is Better

**FOL Issues:**
- Quantifier scope errors
- Free variables
- Wrong predicates
- Hard to ground

**Boolean Advantages:**
- No quantifiers = no quantifier errors
- Simpler formulas
- Easier validation
- Ready for SAT solving

## Example

```
Text: "All students study hard"

FOL (error-prone):
∀x (Student(x) ⟹ StudyHard(x))

Boolean (reliable):
P_1: Alice is a student
P_2: Alice studies hard
H_1: P_1 ⟹ P_2
(repeat for each student)
```

See `README.md` for detailed analysis and experimental results.
