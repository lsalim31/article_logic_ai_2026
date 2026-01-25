"""
Evaluation metrics module for LOGIC-LM++ baseline.

This module provides evaluation metrics for both accuracy and efficiency,
enabling comparison with RAG baseline and main logification system.

Core responsibilities:
1. Standard classification metrics (accuracy, precision, recall, F1)
2. LOGIC-LM++ specific metrics (formalization success, solver execution rate)
3. Efficiency metrics (time, LLM calls, cost)
4. Result aggregation and reporting

Key functions:
- evaluate_predictions(predictions, ground_truth) -> dict
  Compute standard classification metrics

- compute_logiclm_metrics(results) -> dict
  Compute LOGIC-LM++ specific metrics (formalization success, etc.)

- compute_efficiency_metrics(results) -> dict
  Analyze time, LLM calls, cost per query

- generate_report(all_results) -> dict
  Comprehensive evaluation report with all metrics

Standard metrics:
- Overall accuracy
- Per-class precision, recall, F1
- Confusion matrix
- Macro/micro averaging

LOGIC-LM++ specific metrics:
- Formalization success rate: % examples successfully formalized
- Solver execution rate: % formulations successfully solved (no errors)
- Average refinement iterations: Mean number of refinement steps
- Refinement improvement rate: % examples where refinement helped

Efficiency metrics:
- Total time per query (mean, median, std)
- Formalization time vs. solving time breakdown
- Total LLM calls per query (1 initial + ~6 refinement)
- Token usage and estimated cost
- Comparison: time/cost vs. RAG and main system

Output format from generate_report():
{
    'accuracy_metrics': {
        'overall_accuracy': float,
        'per_class': Dict[str, dict],  # {class: {precision, recall, f1}}
        'confusion_matrix': List[List[int]]
    },
    'logiclm_metrics': {
        'formalization_success_rate': float,
        'solver_execution_rate': float,
        'avg_refinement_iterations': float,
        'refinement_improvement_rate': float
    },
    'efficiency_metrics': {
        'avg_time_per_query': float,
        'avg_llm_calls_per_query': float,
        'time_breakdown': {'formalization': float, 'refinement': float, 'solving': float},
        'total_cost_estimate': float
    },
    'comparison_to_baselines': {
        'accuracy_vs_rag': float,      # Percentage point difference
        'time_vs_rag': float,          # Relative speedup/slowdown
        'accuracy_vs_main': float,
        'time_vs_main': float
    }
}

Design decisions:
- Shared metrics compatible with RAG evaluator
- Track failures explicitly (formalization, solver errors)
- Efficiency metrics critical for "logify once vs. per-query" argument
- Per-dataset breakdown (FOLIO, ProofWriter, ContractNLI)
"""
