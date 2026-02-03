# B Report Feb 3 — logic_solver

Scope: `code/logic_solver/*.py`. Docstrings ignored. Focus on concrete errors and mismatches.

## Issues

1) **Reverse implication symbols are normalized but not supported by the parser**
Severity: Medium
File: `code/logic_solver/encoding.py`
Function: `FormulaParser.parse`
Lines: 53-57
Problem: `⟸`/`⇐` are normalized to `<=`, but the tokenizer and parser never handle `<=`. This can silently drop tokens and produce wrong parses.
Proposed solution: Reject unsupported `<=` early to avoid wrong encodings.
Minimal replacement:
```python
def parse(self, formula: str) -> List[List[int]]:
    formula = formula.strip()
    formula = formula.replace('⇒', '=>').replace('⟹', '=>').replace('→', '=>')
    formula = formula.replace('⟺', '<=>').replace('⇔', '<=>').replace('↔', '<=>')
    formula = formula.replace('∧', '&').replace('∨', '|').replace('¬', '~')

    if '<=' in formula:
        raise ValueError("Reverse implication (<=) is not supported")

    return self._parse_and_convert_to_cnf(formula)
```

2) **`_compute_confidence_uncertain` treats cost=0 as infinity**
Severity: High
File: `code/logic_solver/maxsat.py`
Function: `_compute_confidence_uncertain`
Lines: 345-365
Problem: `cost_not_q = self._solve_maxsat(...) or float('inf')` converts a valid cost of `0` into `inf`, flipping confidence logic.
Proposed solution: distinguish `None` from `0` explicitly.
Minimal replacement:
```python
def _compute_confidence_uncertain(self, query_formula: str) -> float:
    wcnf_with_q = self._copy_wcnf(self.base_wcnf)
    for clause in self.encoder.encode_query(query_formula, negate=False):
        wcnf_with_q.append(clause)
    cost_q = self._solve_maxsat(wcnf_with_q)
    if cost_q is None:
        cost_q = float('inf')

    wcnf_with_not_q = self._copy_wcnf(self.base_wcnf)
    for clause in self.encoder.encode_query(query_formula, negate=True):
        wcnf_with_not_q.append(clause)
    cost_not_q = self._solve_maxsat(wcnf_with_not_q)
    if cost_not_q is None:
        cost_not_q = float('inf')

    if cost_q == float('inf') and cost_not_q == float('inf'):
        return 0.5
    if cost_q + cost_not_q == 0:
        return 0.5
    return cost_not_q / (cost_q + cost_not_q)
```

3) **Hard-coded confidence values ignore computed confidence**
Severity: Low
File: `code/logic_solver/maxsat.py`
Functions: `check_entailment`, `check_consistency`
Lines: 92-140, 185-193
Problem: `confidence` is computed in some branches but the returned value is hard-coded to `1` in entailment and consistency SAT branches. This is a mismatch between computed values and returned output.
Proposed solution: return the computed confidence when available.
Minimal replacement:
```python
# In check_entailment(), replace confidence=1 with confidence=confidence
return SolverResult(
    answer="UNCERTAIN",
    confidence=confidence,
    model=model,
    explanation="Query is neither entailed nor contradicted by the knowledge base"
)

# In check_consistency(), replace confidence=1 with confidence=confidence
return SolverResult(
    answer="TRUE",
    confidence=confidence,
    model=model,
    explanation="Query is consistent with the knowledge base"
)
```

4) **`encode` ignores `constraints` when only unweighted constraints exist**
Severity: Medium
File: `code/logic_solver/encoding.py`
Function: `LogicEncoder.encode`
Lines: 357-386
Problem: The encoder only reads `hard_constraints` and `soft_constraints`. If the logified JSON only has `constraints` (pre-weighting), all constraints are ignored.
Proposed solution: fall back to `constraints` as hard constraints when `hard_constraints` is missing.
Minimal replacement:
```python
def encode(self) -> WCNF:
    hard_constraints = self.structure.get('hard_constraints')
    if hard_constraints is None:
        hard_constraints = self.structure.get('constraints', [])

    for constraint in hard_constraints:
        formula = constraint['formula']
        clauses = self.parser.parse(formula)
        for clause in clauses:
            self.wcnf.append(clause)

    next_var = len(self.prop_to_var) + 1
    for constraint in self.structure.get('soft_constraints', []):
        formula = constraint['formula']
        weight = self._extract_weight(constraint, default=0.5)
        int_weight = self._weight_to_int(weight)
        clauses = self.parser.parse(formula)
        selector = next_var
        next_var += 1
        for clause in clauses:
            self.wcnf.append([-selector] + clause)
        self.wcnf.append([selector], weight=int_weight)

    return self.wcnf
```

---

No tests included per instructions.
