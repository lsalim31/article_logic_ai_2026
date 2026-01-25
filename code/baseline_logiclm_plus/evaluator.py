"""
Evaluation metrics module for LOGIC-LM++ baseline.

This module provides evaluation metrics matching the Logic-LM++ paper (Table 1-2, Figure 3-4),
enabling comparison with Logic-LM, RAG baseline, and main logification system.

Core responsibilities:
1. Standard classification metrics (accuracy, precision, recall, F1)
2. LOGIC-LM++ specific metrics (execution rate, execution accuracy, backtracking stats)
3. Efficiency metrics (time, LLM calls, cost)
4. Result aggregation and reporting

Key functions:
- evaluate_predictions(predictions, ground_truth) -> dict
  Compute standard classification metrics (Table 1 format)

- compute_logiclm_metrics(results) -> dict
  Compute LOGIC-LM++ specific metrics (Table 2 format: Er and Ea)

- compute_backtracking_stats(results) -> dict
  Analyze backtracking behavior (Figure 4 statistics)

- compute_efficiency_metrics(results) -> dict
  Analyze time, LLM calls, cost per query

- generate_report(all_results) -> dict
  Comprehensive evaluation report with all metrics

Standard metrics (Table 1 in paper):
- Overall accuracy per dataset (FOLIO, ProofWriter, AR-LSAT)
- Comparison: Standard prompting, CoT, Logic-LM, Logic-LM++
- Per-class performance for multi-class problems

LOGIC-LM++ specific metrics (Table 2 in paper):
- **Execution Rate (Er)**: % of formulations that execute without syntax/runtime errors
  (Note: Syntactically correct but semantically wrong formulations still count as executed)
- **Execution Accuracy (Ea)**: % of correctly answered queries among executed formulations
  (Ea = correct_answers / executed_formulations, NOT correct_answers / total_queries)
- Average refinement iterations: Mean number of refinement steps taken
- Backtracking rate: % of iterations where backtracking occurred (REVERT decision)
- Early stopping rate: % of examples that stopped before max iterations

Backtracking statistics (Figure 4 in paper):
- Number of formulations corrected per iteration
- Comparison: with backtracking vs. without backtracking
- Tracking "winning" vs "losing" cases (semantic improvement vs. degradation)

Efficiency metrics:
- Total time per query (mean, median, std)
- Time breakdown: formalization, refinement (per iteration), solving
- Total LLM calls per query (1 initial formalization + 2*num_iterations for refinement +
  num_iterations for pairwise comparison + num_iterations for backtracking decision)
- Token usage and estimated cost
- Per-query cost (important for comparing "logify once" vs. "per-query formalization")

Output format from generate_report():
{
    'accuracy_metrics': {
        'overall_accuracy': float,              # Table 1 format
        'per_dataset': Dict[str, float],        # FOLIO, ProofWriter, AR-LSAT
        'per_class': Dict[str, dict],           # {class: {precision, recall, f1}}
        'confusion_matrix': List[List[int]]
    },
    'logiclm_metrics': {                        # Table 2 format
        'execution_rate_Er': float,             # % formulations that execute (no syntax errors)
        'execution_accuracy_Ea': float,         # % correct among executed (NOT among all)
        'formalization_success_rate': float,    # % initial formalizations that parse correctly
        'avg_refinement_iterations': float,     # Mean iterations per example
        'backtracking_rate': float,             # % iterations with REVERT decision
        'early_stopping_rate': float            # % examples stopped before max iterations
    },
    'backtracking_stats': {                     # Figure 4 analysis
        'num_formulations_corrected_per_iteration': List[int],  # [iter1, iter2, iter3, ...]
        'with_backtracking': int,               # Total corrected with backtracking
        'without_backtracking': int,            # Total corrected without backtracking (for comparison)
        'winning_cases': int,                   # Examples where refinement improved answer
        'losing_cases': int                     # Examples where refinement degraded answer
    },
    'efficiency_metrics': {
        'avg_time_per_query': float,
        'avg_llm_calls_per_query': float,
        'time_breakdown': {
            'formalization': float,
            'refinement': float,
            'backtracking': float,
            'solving': float
        },
        'total_cost_estimate': float
    },
    'comparison_to_baselines': {
        'accuracy_vs_logic_lm': float,          # Percentage point difference (paper reports ~5%)
        'accuracy_vs_cot': float,               # Percentage point difference (paper reports ~12%)
        'accuracy_vs_standard': float,          # Percentage point difference (paper reports ~18%)
        'time_vs_rag': float,                   # For cross-system comparison
        'cost_per_query_vs_main_system': float  # Amortized cost comparison
    }
}

Design decisions (from Logic-LM++ paper):
- Separate execution rate (Er) from execution accuracy (Ea) - key distinction in Table 2
- Track backtracking decisions explicitly (paper's central contribution)
- Report metrics per dataset (FOLIO, ProofWriter, AR-LSAT have different characteristics)
- Compare against Logic-LM, not just RAG (paper's main baseline)
- Efficiency metrics support "logify once vs. per-query" cost analysis
"""
