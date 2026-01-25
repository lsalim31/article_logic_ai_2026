# Logic-LM++ Documentation Updates

## Summary

All module documentation has been corrected to accurately reflect the Logic-LM++ paper (ACL 2024) methodology. The implementation structure comments now correctly describe:

1. **First-order logic (FOL)** formalization, not SAT
2. **Variable iterations** with early stopping, not fixed 3 iterations
3. **Backtracking agent** as the key innovation
4. **Prover9/Z3** theorem provers, not SAT solvers
5. Correct evaluation metrics: **Execution Rate (Er)** vs **Execution Accuracy (Ea)**

---

## Changes by File

### 1. `config.py`

**Key Changes:**
- Symbolic target: `SAT` → `FOL` (First-order logic)
- Max iterations: Fixed 3 → Variable (0-4, tested in paper)
- Added: `MAX_CONSECUTIVE_BACKTRACKS = 2` for early stopping
- Added: `BACKTRACKING_PROMPT` (the paper's key innovation)

**Prompt Updates:**
- **Formalization prompt**: Now targets FOL with predicates, quantifiers, premises/conclusion
- **Refinement prompt**: Added context (problem statement), self-reflection instructions, semantic error guidance
- **Pairwise comparison**: Emphasizes semantic correctness over syntax
- **Backtracking prompt**: NEW - compares refined vs. previous formulation

**Rationale:**
- Paper uses Prover9 (FOL theorem prover) and Z3, not SAT solvers
- Figure 3 shows experiments with 0-4 iterations, not fixed 3
- Section 3.2-3.3 describe context-rich prompts without few-shots
- Backtracking is the central contribution (Section 3.3, Figures 2 & 4)

---

### 2. `formalizer.py`

**Key Changes:**
- Function name: `formalize_to_sat()` → `formalize_to_fol()`
- Output format: `clauses/query_literal` → `predicates/premises/conclusion`
- Added: FOL syntax validation requirements

**Rationale:**
- FOLIO, ProofWriter, AR-LSAT datasets require first-order logic
- Paper explicitly mentions Prover9 (FOL theorem prover)
- CNF/DIMACS format is propositional-only, incompatible with quantifiers

---

### 3. `refiner.py`

**Key Changes:**
- Added: `backtracking_decision()` function (paper's key innovation)
- Loop logic: Fixed iterations → Variable with early stopping
- Added: Tracking `backtracking_history`, `num_backtracks`
- Added: Early stop reason (consecutive backtracks or solver success)

**Output format additions:**
```python
'backtracking_history': List[str],      # ['IMPROVED', 'REVERT', ...]
'num_backtracks': int,
'early_stop_reason': str | None
```

**Refinement loop (corrected):**
1. Validate with solver (early terminate if success)
2. Generate N=2 candidates
3. Pairwise comparison → select best
4. **BACKTRACKING**: compare selected vs. previous
   - `IMPROVED`: accept, reset counter
   - `REVERT`: keep previous, increment counter
5. Early stop if consecutive REVERTs >= threshold

**Rationale:**
- Paper Section 3.3: "Backtracking Agent" prevents semantic degradation
- Figure 2: Shows REVERT decision when refinement is semantically worse
- Figure 4: Tracks formulations corrected per iteration with/without backtracking
- Figure 3: Shows variable iteration counts, convergence differs with/without backtracking

---

### 4. `solver_interface.py`

**Key Changes:**
- Solver: `python-sat` → `Prover9` (primary) and `Z3` (fallback)
- Function: `solve_sat()` → `solve_fol()`
- Input format: CNF clauses → FOL premises/conclusion
- Output: `'Entailed'/'Contradicted'` → `'Proved'/'Disproved'`
- Added: Error message parsing for refinement feedback

**Entailment logic:**
- SAT: UNSAT testing on clauses ∧ ¬query
- FOL: Theorem proving (premises ⊢ conclusion)

**Rationale:**
- Paper page 3, line 309: "Prover9 and Z3 theorem prover"
- FOLIO/AR-LSAT use FOL with quantifiers (∀, ∃)
- ProofWriter uses open-world assumption (OWA), not propositional logic

---

### 5. `evaluator.py`

**Key Changes:**
- Added distinction: **Execution Rate (Er)** vs **Execution Accuracy (Ea)**
- Added: `compute_backtracking_stats()` (Figure 4 metrics)
- Comparison baseline: RAG → **Logic-LM** (paper's actual baseline)
- Added: Per-iteration correction tracking

**Metric definitions (from Table 2):**
- **Er (Execution Rate)**: % formulations that execute without syntax/runtime errors
  - Includes syntactically correct but semantically wrong formulations
- **Ea (Execution Accuracy)**: % correct answers among executed formulations
  - `Ea = correct_answers / executed_formulations` (NOT / total_queries)

**Backtracking stats (Figure 4):**
- Formulations corrected per iteration
- With vs. without backtracking comparison
- Winning/losing cases

**Rationale:**
- Paper Table 2 explicitly separates Er and Ea
- Table 1 compares against Logic-LM, not RAG
- Figure 4 shows per-iteration correction tracking

---

### 6. `main.py`

**Key Changes:**
- Pipeline: `SAT formulation` → `FOL formulation`
- Iterations: "Always 3" → "Variable (may be < max if early stop)"
- Added: Backtracking tracking in output
- Added: Early stop reason
- Answer format: `'Entailed'/'Contradicted'` → `'Proved'/'Disproved'`

**Output additions:**
```python
'initial_formulation': dict,
'backtracking_history': List[str],
'num_backtracks': int,
'early_stop_reason': str | None,
'execution_success': bool,           # Er
'execution_accuracy': bool | None     # Ea
```

**Dataset specifics:**
- FOLIO: 204 test examples, labels True/False/Uncertain
- ProofWriter: 600 OWA 5-hop examples, labels Proved/Disproved/Unknown
- AR-LSAT: 231 MCQ, labels A/B/C/D/E

**Rationale:**
- Pipeline must track backtracking decisions (paper's central contribution)
- Er/Ea distinction required for Table 2 metrics
- Early stopping via backtracking is key innovation

---

### 7. `test_logiclm.py`

**Key Changes:**
- Test suite: SAT → FOL theorem proving
- Added: Backtracking tests
- Added: Early stopping tests
- Added: Er vs Ea metric tests
- Added: Semantic vs. syntactic comparison tests

**New test categories:**
- `test_backtracking_decision()`: IMPROVED/REVERT logic
- `test_early_stopping_consecutive_backtracks()`: Threshold behavior
- `test_backtracking_prevents_degradation()`: Semantic improvement
- `test_execution_rate_Er()` and `test_execution_accuracy_Ea()`: Metric distinction

**Rationale:**
- Must test backtracking mechanism (paper's key contribution)
- Must verify Er/Ea separation (Table 2 requirement)
- Must test early stopping (Figure 3 shows variable iteration counts)

---

## Critical Corrections Summary

### ❌ Previous (Incorrect)
1. SAT formalization (propositional logic only)
2. Fixed 3 iterations, no early stopping
3. No backtracking mechanism
4. Pairwise comparison only (no semantic reversion)
5. Single metric: "formalization success rate"
6. Comparison to RAG baseline

### ✅ Corrected (Paper-Accurate)
1. FOL formalization (first-order logic with quantifiers)
2. Variable iterations (0-4), early stopping via backtracking
3. **Backtracking agent** (key innovation from paper Section 3.3)
4. Pairwise comparison + backtracking decision (IMPROVED/REVERT)
5. Er (execution rate) vs Ea (execution accuracy) distinction
6. Comparison to Logic-LM baseline (paper's main comparison)

---

## References from Paper

1. **Section 3.2 (Self-Refinement Agent)**: Context-rich prompts, no few-shots
2. **Section 3.3 (Backtracking Agent)**: Semantic comparison to prevent degradation
3. **Figure 2**: Example showing REVERT decision prevents semantic error
4. **Figure 3**: Variable iteration counts (0-4), convergence behavior
5. **Figure 4**: Formulations corrected per iteration, with/without backtracking
6. **Table 1**: Accuracy comparison (Standard/CoT/Logic-LM/Logic-LM++)
7. **Table 2**: Er (Execution Rate) vs Ea (Execution Accuracy) with/without backtracking
8. **Page 3, line 309**: "Prover9 and Z3 theorem prover"

---

## Implementation Status

✅ **Documentation**: All corrected to match paper
⚠️ **Code**: NOT implemented (per user request: "do not code")

Next steps (when implementing):
1. Replace SAT solver with Prover9/Z3 interface
2. Implement `backtracking_decision()` function
3. Add early stopping logic (consecutive backtracks)
4. Update refinement loop with backtracking
5. Implement Er/Ea metric computation
6. Add backtracking statistics tracking (Figure 4)

---

## Key Insight

**The backtracking agent is Logic-LM++'s central contribution**, not just pairwise comparison. The paper shows (Figure 3-4) that without backtracking, refinement can degrade performance by accepting syntactically correct but semantically wrong formulations. The REVERT decision prevents this degradation, enabling consistent improvement across iterations.
