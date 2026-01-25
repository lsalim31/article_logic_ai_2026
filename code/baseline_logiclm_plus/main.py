"""
Main orchestration module for LOGIC-LM++ baseline.

This module implements the complete Logic-LM++ pipeline from the ACL 2024 paper:
"LOGIC-LM++: Multi-Step Refinement for Symbolic Formulations"

Pipeline overview (Section 3 of paper):
1. Problem Formulation: NL → FOL via LLM
2. Symbolic Reasoning: Prover9/Z3 theorem proving
3. Self-Refinement Agent: Context-rich refinement with solver feedback
4. Backtracking Agent: Semantic comparison to prevent degradation
5. Result Interpretation: Map proof results to answers

Core responsibilities:
1. Single-example pipeline: formalize → refine (with backtracking) → solve
2. Batch processing: run on full datasets (FOLIO, ProofWriter, AR-LSAT)
3. Result aggregation and serialization
4. Integration with evaluator for metrics (Tables 1-2, Figures 3-4)

Key functions:
- run_logiclm_plus(text, query, model_name, config, ground_truth=None) -> dict
  End-to-end pipeline for single example

- run_batch(examples, model_name, config, output_dir=None) -> dict
  Process multiple examples, save intermediate results

- load_dataset(dataset_name) -> List[dict]
  Load FOLIO (204 test), ProofWriter (600 OWA 5-hop), or AR-LSAT (231 MCQ)

- save_results(results, output_path) -> None
  Serialize results as JSON for later analysis

Pipeline flow (run_logiclm_plus):
1. Initial formalization (formalizer.py)
   - NL → FOL via LLM
   - Returns: predicates, premises, conclusion
   - Track: formalization_success (syntax parsing)

2. Refinement loop with backtracking (refiner.py)
   - Variable iterations (0-4, tested in Figure 3)
   - Per iteration:
     a. Validate with Prover9/Z3 (if success, terminate early)
     b. Generate 2 refinement candidates (with problem statement in prompt)
     c. Pairwise comparison: select best candidate
     d. **BACKTRACKING**: compare selected vs. previous
        - If IMPROVED: accept, reset backtrack counter
        - If REVERT: keep previous, increment backtrack counter
     e. If consecutive backtracks >= threshold: early stop
   - Returns: refined formulation + history + backtracking stats

3. Solver execution (solver_interface.py)
   - Test entailment via Prover9/Z3 theorem proving
   - Returns: Proved/Disproved/Unknown + diagnostics
   - Track: execution_success (Er), correctness (Ea)

4. Result aggregation
   - Collect all intermediate outputs
   - Track timing, LLM calls, backtracking decisions, errors
   - Compute per-example metrics

Output format from run_logiclm_plus():
{
    'answer': str,                          # 'Proved' | 'Disproved' | 'Unknown' | 'Error'
    'correct': bool | None,                 # Compared to ground_truth if provided
    'final_formulation': dict,              # Refined FOL formulation
    'initial_formulation': dict,            # Initial formalization (for comparison)
    'num_refinement_iterations': int,       # Actual iterations (may be < max if early stop)
    'backtracking_history': List[str],      # ['IMPROVED', 'REVERT', 'IMPROVED', ...]
    'num_backtracks': int,                  # Total REVERT decisions
    'early_stop_reason': str | None,        # Reason if stopped before max iterations
    'total_llm_calls': int,                 # 1 formalization + 2*iter (candidates) + iter (pairwise) + iter (backtrack)
    'total_time': float,                    # End-to-end latency
    'time_breakdown': {
        'formalization': float,
        'refinement': float,
        'backtracking': float,
        'solving': float
    },
    'formalization_success': bool,          # Did initial formalization parse?
    'execution_success': bool,              # Er: Did solver execute without error?
    'execution_accuracy': bool | None,      # Ea: Was answer correct (if executed)?
    'formulation_history': List[dict],      # All formulations tried
    'error': str | None                     # Error message if pipeline failed
}

Batch processing (run_batch):
- Iterate through dataset
- Call run_logiclm_plus() per example
- Save intermediate results every N examples (crash recovery)
- Aggregate results and compute metrics (Tables 1-2 format)
- Generate evaluation report via evaluator.py
- Output: accuracy, Er, Ea, backtracking stats (Figure 4), timing

Error handling:
- Formalization failure: count as execution failure (Er = 0), continue
- Solver failure: count as execution failure (Er = 0), keep in results
- Malformed outputs: no retry, count as failure
- Timeouts: record as timeout, continue to next example

Dataset specifics:
- FOLIO: 204 test examples, FOL reasoning, labels: True/False/Uncertain
- ProofWriter: 600 OWA 5-hop examples, labels: Proved/Disproved/Unknown
- AR-LSAT: 231 multiple-choice, FOL reasoning, labels: A/B/C/D/E

Design decisions (from Logic-LM++ paper):
- Per-query formalization (no caching) - matches Logic-LM baseline
- Variable iterations with early stopping via backtracking
- Comprehensive result tracking (enables Figure 3-4 reproduction)
- JSON serialization (reproducibility, debugging)
- Execution rate (Er) vs. execution accuracy (Ea) distinction (Table 2)
"""
