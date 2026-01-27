# Comparison: RC2 (Implementation) vs. MiniMaxSAT (Article Citation)

**Question:** How does PySAT's RC2 weighted MaxSAT solver (used in implementation) compare to MiniMaxSAT (cited in the article)?

---

## What the Article Says

### Citation in Article (Line 83, 215)

The article cites:
> \cite{heras2007minimaxsat}

**Full reference (from `biblio.bib`):**
```
@inproceedings{heras2007minimaxsat,
  title     = {{MiniMaxSat}: A New Weighted Max-{SAT} Solver},
  author    = {Heras, Federico and Larrosa, Javier and Oliveras, Albert},
  booktitle = {Theory and Applications of Satisfiability Testing -- SAT 2007},
  pages     = {41--55},
  year      = {2007}
}
```

### What the Article Claims (Line 373)

> "We interface with off-the-shelf Max-SAT solvers (e.g., RC2, MaxHS, or Open-WBO)."

**Important:** The article mentions **both MiniMaxSAT (cited) and RC2 (mentioned)** as options!

---

## Algorithm Comparison

### MiniMaxSAT (2007)
**Paper:** Heras, Larrosa, Oliveras - "MiniMaxSat: A New Weighted Max-SAT Solver" (SAT 2007)

**Algorithm Type:** Branch-and-Bound

**Key Features:**
1. **Learning and backjumping** on hard clauses
2. **Resolution-based and subtraction-based lower bounding**
3. **Lazy propagation** with two-watched literals scheme
4. Handles **hard clauses** (mandatory satisfaction)
5. Handles **soft clauses** (falsification penalized by cost)
6. Supports **pseudo-Boolean objective functions** and constraints

**Approach:**
- Branch-and-bound search through solution space
- Prunes branches using lower bounds
- Uses SAT solver techniques (clause learning, conflict analysis)
- Optimizes by minimizing violated soft clause weights

**Performance (2007):**
- State-of-the-art for weighted MaxSAT at the time
- Close to or better than specialized alternatives on optimization benchmarks

**Historical Context:**
- Built on MiniSat SAT solver foundations
- Pioneered integration of SAT techniques into MaxSAT
- Branch-and-bound was dominant MaxSAT approach in 2007

---

### RC2 (2019)
**Paper:** Ignatiev, Morgado, Marques-Silva - "RC2: an Efficient MaxSAT Solver" (JSAT 2019)

**Algorithm Type:** Core-Guided (Unsatisfiable Core Based)

**Key Features:**
1. **Relaxable cardinality constraints** (RC2 stands for this)
2. **Unsatisfiable core exhaustion**
3. **Unsatisfiable core reduction**
4. **Intrinsic AtMost1 constraints** heuristic
5. Based on **OLLITI algorithm** (from MSCG solver)
6. Iteratively relaxes soft constraints

**Approach:**
- Iteratively finds unsatisfiable cores
- Relaxes soft constraints by adding cardinality constraints
- Incrementally builds solution without explicit branching
- Uses core-guided search (fundamentally different from branch-and-bound)

**Performance (2018-2019):**
- **Ranked #1 in MaxSAT Evaluations 2018 and 2019**
- **First place in both unweighted and weighted complete categories**
- State-of-the-art as of 2019+
- Still competitive in 2025+

**Implementation:**
- Native Python implementation in PySAT
- Surprisingly efficient despite being Python (not C++)
- Uses any PySAT SAT solver as backend (default: Glucose 3)

---

## Technical Differences

| Feature | MiniMaxSAT (2007) | RC2 (2019) |
|---------|-------------------|------------|
| **Algorithm Class** | Branch-and-Bound | Core-Guided |
| **Search Strategy** | Exhaustive tree search with pruning | Iterative core extraction + relaxation |
| **Lower Bounds** | Resolution-based, subtraction-based | Cardinality-based (from cores) |
| **Hard Clauses** | Must satisfy (branching respects) | Must satisfy (cores never include) |
| **Soft Clauses** | Penalized in objective | Relaxed iteratively via cores |
| **Clause Learning** | On hard clauses (SAT-style) | On SAT subproblems during core finding |
| **Optimality** | Proven via branch-and-bound tree | Proven via cardinality constraint tightening |
| **Incremental** | Limited | Strong (adds constraints incrementally) |
| **Year** | 2007 | 2019 |
| **Competition Results** | State-of-art in 2007 | #1 in MaxSAT Eval 2018-2019 |

---

## Core-Guided vs. Branch-and-Bound (Simplified)

### Branch-and-Bound (MiniMaxSAT):

```
1. Start with full formula
2. Branch on variable assignments
3. At each node, compute lower bound on violated soft clauses
4. Prune branches where lower bound ≥ current best
5. Continue until optimal solution found
```

**Analogy:** Like searching a tree, cutting off bad branches early.

### Core-Guided (RC2):

```
1. Assume all soft clauses can be satisfied
2. Try to find SAT solution
3. If UNSAT, extract unsatisfiable core (minimal conflicting soft clauses)
4. Relax one soft clause in the core (allow it to be violated)
5. Add cardinality constraint: "at most k soft clauses in this core can be violated"
6. Repeat until SAT (found optimal solution)
```

**Analogy:** Like negotiating constraints - find conflicts, relax minimum necessary.

---

## Why Core-Guided (RC2) is Better (Modern Consensus)

### Advantages of Core-Guided Approach:

1. **Better scalability** - doesn't explore exponential search tree
2. **Incremental** - builds solution iteratively, reusing learned information
3. **Tighter bounds** - cardinality constraints provide stronger reasoning
4. **Fewer backtracks** - guided by actual conflicts, not speculative branching
5. **SAT solver integration** - leverages modern SAT solver advances directly

### Why RC2 Won 2018-2019 Competitions:

- Modern SAT solvers (Glucose, CryptoMiniSat) are extremely efficient
- Core-guided methods benefit from every SAT solver improvement
- Cardinality encoding (via Totalizer, sequential counters) is well-optimized
- Branch-and-bound approaches hit scaling limits on large instances

### Academic Consensus (2020+):

**Core-guided methods dominate modern MaxSAT solving**, especially for:
- Large industrial instances
- Weighted MaxSAT (partial MaxSAT)
- Instances with many soft constraints

Branch-and-bound still competitive for:
- Small, highly structured instances
- Problems with few soft constraints
- Cases where lower bounds are very tight

---

## Article's Citation Choice

### Why Cite MiniMaxSAT (2007)?

The article cites MiniMaxSAT for **historical/theoretical reasons**:

1. **Pioneering work** - First to effectively integrate SAT techniques into weighted MaxSAT
2. **Foundational paper** - Established weighted MaxSAT as practical approach
3. **Conceptual clarity** - Branch-and-bound is easier to explain theoretically
4. **Citation conventions** - Cite seminal work, not just newest solver

**This is standard practice in academic papers** - cite foundational work even if implementation uses newer methods.

### Does This Matter?

**NO - Not for correctness or alignment.**

The article says (Line 373):
> "We interface with off-the-shelf Max-SAT solvers (e.g., RC2, MaxHS, or Open-WBO)."

**RC2 is explicitly mentioned as an option!** The implementation chose RC2, which is:
- ✅ Mentioned in the article as acceptable
- ✅ State-of-the-art (better than MiniMaxSAT)
- ✅ More recent (2019 vs 2007)
- ✅ Better performance on modern benchmarks

---

## Implementation Analysis

### What the Code Uses (`logic_solver/maxsat.py`)

```python
from pysat.examples.rc2 import RC2

def _solve_maxsat(self, wcnf: WCNF):
    with RC2(wcnf) as solver:
        model = solver.compute()
        cost = solver.cost
        return cost
```

**Solver:** RC2 (core-guided)

**Library:** PySAT

**Backend SAT solver:** Glucose 3 (default)

---

## Is This the Right Choice?

### ✅ **YES - RC2 is an excellent choice!**

**Reasons:**

1. **State-of-the-art** - Won MaxSAT Evaluations 2018-2019
2. **Mentioned in article** - Line 373 explicitly lists RC2 as option
3. **Better than MiniMaxSAT** - Superior performance on modern instances
4. **Pure Python** - Easy integration, no C++ compilation
5. **Well-maintained** - Active PySAT project, regular updates
6. **Flexible** - Can switch SAT backend if needed

### Alternative Solvers Mentioned in Article

**From Line 373:**
- ✅ **RC2** (used in implementation)
- **MaxHS** (core-guided, similar to RC2)
- **Open-WBO** (core-guided, C++ implementation, very fast)

All three are **core-guided solvers**, not branch-and-bound like MiniMaxSAT.

**Implication:** The article's implementation guidance (Line 373) is more current than its theoretical citation (2007).

---

## Performance Comparison (Approximate)

Based on MaxSAT Evaluation results:

| Solver | Year | Algorithm | Weighted MaxSAT Performance |
|--------|------|-----------|----------------------------|
| MiniMaxSAT | 2007 | Branch-and-Bound | Good for 2007 |
| RC2 | 2019 | Core-Guided | **#1 in 2018-2019** |
| MaxHS | 2018 | Core-Guided | Top 3 in 2018-2019 |
| Open-WBO | 2020+ | Core-Guided | Top 3 in recent years |

**Conclusion:** RC2 is among the best available solvers, superior to MiniMaxSAT.

---

## Could You Use MiniMaxSAT Instead?

### Technically: YES
- Both solve weighted MaxSAT
- Both handle hard and soft constraints
- Both produce optimal solutions

### Practically: NO - RC2 is better
- ✅ **Faster** on modern benchmarks
- ✅ **More scalable** to large instances
- ✅ **Better maintained** (PySAT is active)
- ✅ **Easier integration** (pure Python)
- ✅ **More flexible** (can swap SAT backend)

### MiniMaxSAT disadvantages:
- ❌ 2007 technology (18 years old)
- ❌ C++ implementation (harder integration)
- ❌ Less maintained (superseded by newer solvers)
- ❌ Branch-and-bound doesn't scale as well

---

## Summary Table

| Aspect | MiniMaxSAT (Article Citation) | RC2 (Implementation) |
|--------|-------------------------------|----------------------|
| **Year** | 2007 | 2019 |
| **Algorithm** | Branch-and-Bound | Core-Guided |
| **Performance** | State-of-art in 2007 | **#1 in 2018-2019** |
| **Implementation** | C++ | Python (PySAT) |
| **Scalability** | Moderate | Excellent |
| **Maintenance** | Superseded | Active |
| **Mentioned in Article?** | Cited (theoretical) | ✅ Yes (Line 373) |
| **Correct for use?** | ✅ Yes | ✅ **Better choice** |
| **Alignment with Article** | Historical citation | **Recommended option** |

---

## Conclusion

### Is RC2 Aligned with the Article?

✅ **YES - Perfectly aligned!**

**Evidence:**

1. Article explicitly mentions RC2 as an option (Line 373)
2. RC2 is superior to MiniMaxSAT (the cited solver)
3. RC2 is state-of-the-art for weighted MaxSAT
4. Implementation correctly uses RC2 from PySAT

### Why Does Article Cite MiniMaxSAT?

**Standard academic practice:**
- Cite **seminal/foundational work** for historical context
- Implementation uses **best available solver**

**Analogy:**
- Paper on sorting might cite **QuickSort (1960)** for theory
- Implementation uses **Timsort (2002)** for efficiency
- Both correct!

### Recommendation

**No changes needed.** The implementation's use of RC2 is:
- ✅ Better than the cited MiniMaxSAT
- ✅ Explicitly mentioned in the article
- ✅ State-of-the-art technology
- ✅ Correctly solves weighted MaxSAT

---

## Additional Notes

### Core-Guided Solvers Evolution

```
2007: MiniMaxSAT (branch-and-bound)
       ↓
2012: WPM1/WPM2 (early core-guided)
       ↓
2014: MSCG (OLLITI algorithm - core-guided)
       ↓
2019: RC2 (improved OLLITI, Python)
       ↓
2020+: Open-WBO, MaxHS (optimized core-guided)
```

**RC2 is part of the modern core-guided family**, which has largely superseded branch-and-bound for weighted MaxSAT.

### If You Want Maximum Performance

If you need absolute fastest solving (beyond RC2):

1. **Open-WBO** (C++, very fast, competitive in recent evaluations)
2. **MaxHS** (C++, core-guided, strong on industrial instances)
3. **Exact** (C++, hybrid approach, good on structured problems)

But **RC2 is excellent for a Python-based system** - the convenience and maintainability outweigh the ~2x speed difference from C++ solvers.

---

## Sources

- [RC2 MaxSAT solver - PySAT Documentation](https://pysathq.github.io/docs/html/api/examples/rc2.html)
- [RC2: an Efficient MaxSAT Solver (Paper)](https://alexeyignatiev.github.io/assets/pdf/imms-jsat19-preprint.pdf)
- [MiniMaxSat: A New Weighted Max-SAT Solver (Paper)](https://link.springer.com/chapter/10.1007/978-3-540-72788-0_8)
- [MiniMaxSAT: An Efficient Weighted Max-SAT solver (JAIR)](https://www.semanticscholar.org/paper/MiniMaxSAT:-An-Efficient-Weighted-Max-SAT-solver-Heras-Larrosa/b562be840ecf8c64b08aa37466d869e8b64b2462)
- [PySAT GitHub - RC2 Implementation](https://github.com/pysathq/pysat/blob/master/examples/rc2.py)

---

## Final Verdict

### Implementation vs. Article Citation

| Question | Answer |
|----------|--------|
| Does implementation use cited solver? | No - uses RC2, not MiniMaxSAT |
| Is RC2 mentioned in article? | ✅ Yes (Line 373) |
| Is RC2 better than MiniMaxSAT? | ✅ Yes - state-of-art in 2019 |
| Is implementation correct? | ✅ Yes - excellent choice |
| Is alignment broken? | ❌ No - RC2 explicitly recommended |

**Conclusion:** Implementation uses a **better solver than the cited one**, which is **explicitly approved in the article**. No issues!
