"""
Main orchestration module for LOGIC-LM++ baseline.

This module provides the end-to-end pipeline for LOGIC-LM++ baseline evaluation,
coordinating formalization, refinement, solving, and evaluation.

Core responsibilities:
1. Single-example pipeline: formalize → refine → solve
2. Batch processing: run on full datasets
3. Result aggregation and serialization
4. Integration with evaluator for metrics

Key functions:
- run_logiclm_plus(text, query, model_name, config) -> dict
  End-to-end pipeline for single example

- run_batch(examples, model_name, config, output_dir=None) -> dict
  Process multiple examples, save intermediate results

- load_dataset(dataset_name) -> List[dict]
  Load FOLIO, ProofWriter, or ContractNLI dataset

- save_results(results, output_path) -> None
  Serialize results as JSON for later analysis

Pipeline flow (run_logiclm_plus):
1. Initial formalization (formalizer.py)
   - NL → SAT via LLM
   - Returns: variables, clauses, query_literal

2. Refinement loop (refiner.py)
   - Fixed 3 iterations (no early stopping)
   - Generate 2 candidates per iteration
   - Pairwise comparison selection
   - Returns: refined formulation + history

3. Solver execution (solver_interface.py)
   - Test entailment via UNSAT
   - Returns: answer + diagnostics

4. Result aggregation
   - Collect all intermediate outputs
   - Track timing, LLM calls, errors

Output format from run_logiclm_plus():
{
    'answer': str,                          # 'Entailed' | 'Contradicted' | 'Unknown'
    'final_formulation': dict,              # Refined SAT formulation
    'num_refinement_iterations': int,       # Always 3 (fixed)
    'total_llm_calls': int,                 # ~10 per query
    'total_time': float,                    # End-to-end latency
    'time_breakdown': {
        'formalization': float,
        'refinement': float,
        'solving': float
    },
    'solver_time': float,                   # Time in SAT solver
    'formalization_success': bool,          # Did initial formalization succeed?
    'solver_success': bool,                 # Did solver execute without error?
    'formalization_history': List[dict],    # All formulations tried
    'error': str | None                     # Error message if pipeline failed
}

Batch processing (run_batch):
- Iterate through dataset
- Call run_logiclm_plus() per example
- Save intermediate results every N examples (crash recovery)
- Aggregate results and compute metrics
- Generate evaluation report via evaluator.py

Error handling:
- Formalization failure: count as error, record in results
- Solver failure: count as error, keep in results for analysis
- Malformed outputs: no retry, count as failure (per Q2)
- Timeouts: record as timeout, continue to next example

Design decisions:
- As-published LOGIC-LM++: per-query formalization (no caching)
- Fixed 3 refinement iterations (faithful to paper)
- Comprehensive result tracking (enables post-hoc analysis)
- JSON serialization (reproducibility, debugging)
"""
