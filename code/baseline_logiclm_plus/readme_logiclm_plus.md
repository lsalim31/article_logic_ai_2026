# Logic-LM++ Baseline Implementation

## Overview

This directory implements the **Logic-LM++** baseline from the ACL 2024 paper ["LOGIC-LM++: Multi-Step Refinement for Symbolic Formulations"](https://arxiv.org/abs/2407.02514v3) by Kirtania et al. (Microsoft Research).

**Logic-LM++** is a neuro-symbolic reasoning system that:
1. Translates natural language to **first-order logic (FOL)** via LLM
2. Iteratively refines formulations using **self-refinement** with solver feedback
3. Applies a **backtracking agent** to prevent semantic degradation (key innovation)
4. Solves using **Prover9/Z3 theorem provers** to determine entailment

This implementation serves as a baseline comparison for the main Logify system presented in our paper.

---

## Key Innovations from Logic-LM++ Paper

### 1. Self-Refinement with Context (Section 3.2)
- **Problem**: Few-shot examples distract the model during refinement
- **Solution**: Include original problem statement and question directly in refinement prompt
- **Result**: Better contextual understanding during error correction

### 2. Backtracking Agent (Section 3.3) - **Central Contribution**
- **Problem**: Standard refinement accepts syntactically correct but semantically wrong formulations
- **Solution**: LLM-based pairwise comparison evaluates semantic improvement before accepting refinements
- **Result**: Prevents performance degradation across iterations (Figure 2, 4)

### 3. Variable Iterations with Early Stopping
- **Approach**: Test 0-4 refinement iterations (Figure 3)
- **Early stop conditions**:
  - Solver succeeds (no refinement needed)
  - Consecutive backtracks exceed threshold (no improvement possible)
- **Result**: Efficient convergence without wasted iterations

---

## Architecture

```
Input: Natural language text + query
    ↓
[Stage 1] Formalization (formalizer.py)
    NL → FOL via LLM
    Output: predicates, premises, conclusion
    ↓
[Stage 2] Refinement Loop (refiner.py)
    For each iteration (0 to MAX_REFINEMENT_ITERATIONS):
      a. Validate with Prover9/Z3 → if success, terminate
      b. Generate N=2 refinement candidates (with problem context)
      c. Pairwise comparison → select best candidate
      d. **BACKTRACKING DECISION**:
         - Compare selected vs. previous formulation
         - If IMPROVED: accept, reset backtrack counter
         - If REVERT: keep previous, increment counter
      e. If consecutive backtracks ≥ threshold → early stop
    Output: refined formulation + history + backtracking stats
    ↓
[Stage 3] Symbolic Reasoning (solver_interface.py)
    Theorem proving via Prover9/Z3
    Test: premises ⊢ conclusion
    Output: Proved / Disproved / Unknown
    ↓
[Stage 4] Result Interpretation
    Map proof results to dataset-specific answers
    Output: Final answer + diagnostics
```

---

## Module Structure

```
baseline_logiclm_plus/
├── config.py                    # Configuration and prompt templates
│   ├── Model settings (GPT-4, temperature=0)
│   ├── Refinement hyperparameters (MAX_ITERATIONS=4, CANDIDATES=2)
│   ├── Backtracking threshold (MAX_CONSECUTIVE_BACKTRACKS=2)
│   └── Prompts: formalization, refinement, pairwise, backtracking
│
├── formalizer.py                # Stage 1: NL → FOL translation
│   ├── formalize_to_fol(): Main entry point
│   ├── parse_formalization_response(): JSON parsing
│   └── validate_formalization(): Syntax checking
│
├── refiner.py                   # Stage 2: Iterative refinement + backtracking
│   ├── refine_loop(): Main refinement orchestration
│   ├── generate_refinements(): Create N candidates with context
│   ├── select_best_formulation(): Pairwise comparison tournament
│   └── backtracking_decision(): IMPROVED vs. REVERT (key innovation)
│
├── solver_interface.py          # Stage 3: FOL theorem proving
│   ├── solve_fol(): Main solver entry point
│   ├── test_entailment_prover9(): Prover9 interface
│   ├── test_entailment_z3(): Z3 SMT solver interface
│   └── parse_solver_error(): Extract feedback for refinement
│
├── evaluator.py                 # Metrics computation
│   ├── evaluate_predictions(): Standard metrics (Table 1)
│   ├── compute_logiclm_metrics(): Er and Ea (Table 2)
│   ├── compute_backtracking_stats(): Figure 4 analysis
│   └── compute_efficiency_metrics(): Time, cost, LLM calls
│
├── main.py                      # End-to-end pipeline orchestration
│   ├── run_logiclm_plus(): Single-example pipeline
│   ├── run_batch(): Dataset processing
│   ├── load_dataset(): FOLIO, ProofWriter, AR-LSAT
│   └── save_results(): JSON serialization
│
├── test_logiclm.py              # Unit tests
│   ├── Formalization tests
│   ├── Refinement tests
│   ├── Backtracking tests
│   ├── Solver interface tests
│   └── Evaluator tests
│
├── readme_logiclm_plus.md       # This file
└── how_to_use_logiclm_plus.md   # Usage guide
```

---

## Key Design Decisions

### 1. First-Order Logic (FOL), Not Propositional (SAT)
**Rationale**:
- FOLIO, ProofWriter, AR-LSAT datasets require quantifiers (∀, ∃)
- Paper explicitly uses "Prover9 and Z3 theorem prover" (page 3, line 309)
- Propositional logic insufficient for dataset characteristics

### 2. Variable Iterations with Early Stopping
**Rationale**:
- Paper tests 0-4 iterations (Figure 3)
- Early stopping prevents wasted computation
- Backtracking threshold (consecutive REVERTs) indicates convergence

### 3. Backtracking Agent (Key Innovation)
**Rationale**:
- Paper's central contribution (Section 3.3, Figure 2, Figure 4)
- Prevents accepting syntactically correct but semantically wrong refinements
- Demonstrated improvement: ~5% over Logic-LM on GPT-4 (Table 1)

### 4. Context-Rich Refinement Prompts
**Rationale**:
- Paper replaces few-shots with problem statement + self-reflection
- Improves semantic understanding during refinement
- Reduces distraction from irrelevant examples

### 5. Per-Query Formalization (No Caching)
**Rationale**:
- Matches Logic-LM baseline methodology
- Enables fair comparison with "logify once, query many" approach
- Amortized cost analysis shows trade-off

---

## Evaluation Metrics

### Standard Metrics (Table 1 Format)
- **Overall accuracy** per dataset (FOLIO, ProofWriter, AR-LSAT)
- **Per-class metrics**: precision, recall, F1
- **Comparison**: Standard prompting, CoT, Logic-LM, Logic-LM++

### Logic-LM++ Specific Metrics (Table 2 Format)

#### Execution Rate (Er)
- **Definition**: % of formulations that execute without syntax/runtime errors
- **Important**: Syntactically correct but semantically wrong formulations count as "executed"
- **Formula**: `Er = executed_formulations / total_queries`

#### Execution Accuracy (Ea)
- **Definition**: % of correctly answered queries among executed formulations
- **Important**: Denominator is executed formulations, NOT total queries
- **Formula**: `Ea = correct_answers / executed_formulations`

#### Other Metrics
- **Formalization success rate**: % initial formalizations that parse correctly
- **Average refinement iterations**: Mean iterations per example
- **Backtracking rate**: % iterations with REVERT decision
- **Early stopping rate**: % examples stopped before max iterations

### Backtracking Statistics (Figure 4 Format)
- **Formulations corrected per iteration**: Track improvement by iteration number
- **With vs. without backtracking**: Compare performance
- **Winning cases**: Examples where refinement improved answer
- **Losing cases**: Examples where refinement would degrade without backtracking

### Efficiency Metrics
- **Time per query**: Mean, median, standard deviation
- **Time breakdown**: Formalization, refinement (per iteration), backtracking, solving
- **LLM calls per query**: 1 + 2×iterations + iterations + iterations (formalization, candidates, pairwise, backtracking)
- **Token usage and cost**: Important for comparing with "logify once" approach

---

## Comparison to Other Systems

| Feature | RAG Baseline | Logic-LM++ | Logify (Main System) |
|---------|--------------|------------|---------------------|
| **Reasoning** | Neural (LLM) | Symbolic (FOL) | Symbolic (Propositional + soft constraints) |
| **Caching** | Retrieval index | None | Full logification |
| **Soft constraints** | No | No | Yes (weighted) |
| **Refinement** | 1-shot CoT | Multi-step with backtracking | Self-refinement |
| **LLM calls/query** | 1 | ~10 (1 + 2×4 + 4 + 4) | ~1 (amortized) |
| **Cost model** | Per-query | Per-query | Upfront + amortized |
| **Logic formalism** | None | FOL (first-order) | Propositional |
| **Solver** | None | Prover9/Z3 | Max-SAT |
| **Key advantage** | Fast, simple | Expressive (quantifiers) | Efficient at scale |

---

## Experimental Results (from Paper)

### Table 1: Accuracy Comparison (GPT-4)

| Dataset | Standard | CoT | Logic-LM | Logic-LM++ | Δ vs Logic-LM |
|---------|----------|-----|----------|------------|---------------|
| **FOLIO** | 66.30% | 72.80% | 78.92% | **84.80%** | +5.88% |
| **ProofWriter** | 72.67% | 76.17% | 79.66% | **79.66%** | +0.00% |
| **AR-LSAT** | 30.30% | 37.23% | 43.04% | **46.32%** | +3.28% |

**Key findings**:
- Logic-LM++ improves over Logic-LM on FOLIO and AR-LSAT
- ProofWriter shows no degradation (important for backtracking validation)
- Larger gains on datasets with complex semantic reasoning (FOLIO)

### Table 2: Execution Rate (Er) vs. Execution Accuracy (Ea)

Shows that backtracking improves both Er (fewer syntax errors through better refinement) and Ea (fewer semantic errors through REVERT decisions).

### Figure 3: Variable Iterations
- Shows accuracy convergence over 0-4 iterations
- Demonstrates early stopping effectiveness
- Without backtracking: performance plateaus or degrades

### Figure 4: Backtracking Impact
- Tracks formulations corrected per iteration
- Shows backtracking prevents degradation
- Quantifies "winning" vs. "losing" cases

---

## Implementation Status

### ✅ Completed
- **Documentation**: All module docstrings reflect FOL-based backtracking approach
- **Configuration**: Prompts, hyperparameters, backtracking threshold
- **Architecture**: Module structure matches paper methodology

### ⚠️ Code Implementation
The actual Python function implementations follow the documented architecture. See `how_to_use_logiclm_plus.md` for usage instructions.

---

## References

**Primary Paper**:
- Kirtania, S., Gupta, P., & Radhakrishna, A. (2024). LOGIC-LM++: Multi-Step Refinement for Symbolic Formulations. *ACL 2024*.
- arXiv: https://arxiv.org/abs/2407.02514v3

**Key Sections**:
- Section 3.2: Self-Refinement Agent (context-rich prompts)
- Section 3.3: Backtracking Agent (semantic comparison, key innovation)
- Figure 2: Example showing REVERT decision
- Figure 3: Variable iteration experiments (0-4)
- Figure 4: Backtracking statistics (formulations corrected per iteration)
- Table 1: Accuracy comparison (Logic-LM++ vs. baselines)
- Table 2: Execution Rate (Er) vs. Execution Accuracy (Ea)

**Related Work**:
- Logic-LM (Pan et al., 2023): Predecessor without backtracking
- Prover9 (Robinson, 1965): First-order theorem prover
- Z3 (de Moura & Bjørner, 2008): SMT solver with FOL support

---

## Citation

If you use this implementation, please cite both the Logic-LM++ paper and our work:

```bibtex
@inproceedings{kirtania2024logiclmpp,
  title={LOGIC-LM++: Multi-Step Refinement for Symbolic Formulations},
  author={Kirtania, Shashank and Gupta, Priyanshu and Radhakrishna, Arjun},
  booktitle={ACL 2024},
  year={2024}
}
```

---

## License

See main repository LICENSE for details.
