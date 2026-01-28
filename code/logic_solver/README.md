# Logic Solver Module

## Overview

The `logic_solver` module provides SAT/MaxSAT-based reasoning over logified text structures. It implements the core reasoning component of the Logify system, using PySAT's RC2 solver to determine if propositions follow from the text.

## Architecture

```
logic_solver/
├── __init__.py        # Module exports
├── encoding.py        # Formula parsing and CNF conversion
├── maxsat.py          # RC2 solver interface
└── README.md          # This file
```

## Components

### 1. Formula Parser (`encoding.py`)

Parses propositional logic formulas and converts them to CNF (Conjunctive Normal Form) for SAT solving.

**Supported Operators:**
- `&` or `∧` : AND
- `|` or `∨` : OR
- `~` or `¬` : NOT
- `=>`, `→`, `⇒`, `⟹` : IMPLIES
- `<=>`, `↔`, `⇔`, `⟺` : IFF (biconditional)

**Example:**
```python
from logic_solver.encoding import FormulaParser, LogicEncoder

# Parse a formula
prop_to_var = {"P_1": 1, "P_2": 2, "P_3": 3}
parser = FormulaParser(prop_to_var)

# Convert "P_1 => P_2" to CNF
clauses = parser.parse("P_1 => P_2")
# Result: [[-1, 2]]  (meaning: ¬P_1 ∨ P_2)
```

**CNF Conversion:**
The parser uses a two-step process:
1. Convert to Negation Normal Form (NNF) - negations only on atoms
2. Convert NNF to CNF using distributive laws

### 2. Logic Encoder (`encoding.py`)

Encodes the complete logified structure (propositions + constraints) into WCNF (Weighted CNF) format for MaxSAT solving.

**Usage:**
```python
from logic_solver.encoding import LogicEncoder

logified = {
    "primitive_props": [
        {"id": "P_1", "translation": "Alice is a student"},
        {"id": "P_2", "translation": "Alice passes the exam"}
    ],
    "hard_constraints": [
        {"formula": "P_1 => P_2", "translation": "Students pass exams"}
    ],
    "soft_constraints": [
        {"formula": "P_1", "translation": "Usually a student", "weight": 0.8}
    ]
}

encoder = LogicEncoder(logified)
wcnf = encoder.encode()  # Returns WCNF with hard and soft clauses
```

**Soft Constraint Encoding (Selector Literals):**

Soft constraints are encoded using **selector literals** (indicator variables) to ensure each constraint contributes exactly its weight when violated, regardless of how many CNF clauses the formula expands to.

For each soft constraint with formula φ and weight w:
1. Create a fresh selector variable `r`
2. Add hard clauses: `¬r ∨ clause` for each clause in CNF(φ)
3. Add single soft clause: `[r]` with weight w

This is the standard technique used by RC2 and other MaxSAT solvers.
Reference: Ignatiev et al. "RC2: an Efficient MaxSAT Solver" (JSAT 2019)

**Weight Conversion:**
Soft constraint weights (probabilities in [0,1]) are converted to integer weights for MaxSAT:
- Log-odds transformation: `weight / (1 - weight)`
- Scaled by 1000 for integer precision
- Example: weight 0.8 → log-odds 4.0 → integer weight 4000

### 3. Logic Solver (`maxsat.py`)

Main interface for reasoning queries using PySAT's RC2 MaxSAT solver.

**Core Methods:**

#### `check_entailment(query_formula: str) -> SolverResult`
Checks if the query is **entailed** by the knowledge base.
- **Logic:** KB ⊨ Q iff KB ∧ ¬Q is UNSAT
- **Returns:** TRUE (entailed), FALSE (contradicted), or UNCERTAIN

```python
from logic_solver import LogicSolver

solver = LogicSolver(logified)
result = solver.check_entailment("P_1 => P_2")

print(result.answer)      # "TRUE", "FALSE", or "UNCERTAIN"
print(result.confidence)  # Float in [0, 1]
print(result.explanation) # Human-readable explanation
```

#### `check_consistency(query_formula: str) -> SolverResult`
Checks if the query is **consistent** with the knowledge base.
- **Logic:** KB ∧ Q is SAT
- **Returns:** TRUE (consistent) or FALSE (inconsistent)

```python
result = solver.check_consistency("P_1 & ~P_2")
```

#### `query(query_formula: str) -> SolverResult`
Combined entailment and consistency check (recommended interface).

```python
result = solver.query("P_1 => P_2")
```

## Query Types

The solver supports three types of answers:

### TRUE (Entailed)
The query **must be true** given the knowledge base.
- Hard constraints force the query to be true
- Confidence: 1.0
- Example: If KB contains "P_1 => P_2" and query is "P_1 => P_2"

### FALSE (Contradicted)
The query **cannot be true** given the knowledge base.
- The query contradicts hard constraints
- Confidence: 1.0
- Example: If KB contains "P_1 => P_2" and query is "P_1 & ~P_2"

### UNCERTAIN
The query is **neither entailed nor contradicted**.
- It's consistent but not necessary
- Confidence depends on soft constraints (in [0, 1])
- Example: If KB contains soft constraint "P_1" (weight 0.8), query "P_1" returns UNCERTAIN with confidence ≈ 0.8

## Confidence Scores

Confidence scores are computed differently for each answer type:

### For UNCERTAIN answers:
- Compare MaxSAT costs for KB ∧ Q vs KB ∧ ¬Q
- Lower cost = better fit with soft constraints
- Formula: `confidence = cost_with_not_q / (cost_with_q + cost_with_not_q)`

### For TRUE/FALSE answers:
- Always 1.0 (determined by hard constraints)

## Complete Example

```python
import json
from logic_solver import LogicSolver

# Load logified structure (from logify.py output)
with open('logified.json', 'r') as f:
    logified = json.load(f)

# Initialize solver
solver = LogicSolver(logified)

# Ask queries
queries = [
    "P_3 => P_4",      # If Alice studies hard, does she pass?
    "P_3",              # Does Alice study hard?
    "P_3 & ~P_4",       # Can Alice study hard but not pass?
]

for query in queries:
    result = solver.query(query)
    print(f"Query: {query}")
    print(f"  Answer: {result.answer}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Explanation: {result.explanation}")
    print()
```

## Technical Details

### SAT Encoding
- Hard constraints → mandatory clauses (infinite weight)
- Soft constraints → selector literal encoding (one soft clause per constraint)
- Query → additional hard clauses added temporarily

### Solvers Used
- **Glucose 3** (via PySAT): For SAT checks
- **RC2** (via PySAT): For MaxSAT optimization

### Complexity
- SAT check: NP-complete (exponential worst case)
- MaxSAT: NP-hard (exponential worst case)
- In practice: Modern solvers handle 1000s of variables efficiently

## Limitations

1. **Propositional logic only** - No quantifiers or predicates
2. **No weighted model counting** - Confidence is heuristic, not probabilistic
3. **Dependent on logification quality** - Incorrect extraction → incorrect reasoning
4. **Exponential worst case** - Large formulas may be slow

## Future Extensions

Potential improvements:
- Add support for incremental solving (add constraints dynamically)
- Integrate weighted model counting (c2d, d4) for true probabilistic confidence
- Support for First-Order Logic (with grounding)
- UNSAT core extraction for debugging
- Minimal correction sets for inconsistencies

## References

- PySAT: https://pysathq.github.io/
- RC2 MaxSAT solver: https://pysathq.github.io/docs/html/api/examples.html#module-examples.rc2
- Ignatiev, A., Morgado, A., & Marques-Silva, J. (2019). "RC2: an Efficient MaxSAT Solver". JSAT, 11(1), 53-64. DOI: 10.3233/SAT190116
- Boolean satisfiability: https://en.wikipedia.org/wiki/Boolean_satisfiability_problem
- Maximum satisfiability: https://en.wikipedia.org/wiki/Maximum_satisfiability_problem
