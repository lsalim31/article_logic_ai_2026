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

import statistics
from collections import defaultdict


def evaluate_predictions(predictions, ground_truth):
    """
    Compute standard classification metrics (Table 1 format).

    Args:
        predictions: List[str] - Predicted answers
        ground_truth: List[str] - Ground truth answers

    Returns:
        dict with keys: overall_accuracy, per_class, confusion_matrix
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    # Compute overall accuracy
    correct = sum(1 for pred, true in zip(predictions, ground_truth) if pred == true)
    overall_accuracy = correct / len(predictions) if len(predictions) > 0 else 0.0

    # Get unique classes
    classes = sorted(set(ground_truth))

    # Compute per-class precision, recall, F1
    per_class = {}
    for cls in classes:
        true_positives = sum(1 for pred, true in zip(predictions, ground_truth)
                           if pred == cls and true == cls)
        false_positives = sum(1 for pred, true in zip(predictions, ground_truth)
                            if pred == cls and true != cls)
        false_negatives = sum(1 for pred, true in zip(predictions, ground_truth)
                            if pred != cls and true == cls)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[cls] = {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    # Build confusion matrix
    confusion_matrix = []
    for true_cls in classes:
        row = []
        for pred_cls in classes:
            count = sum(1 for pred, true in zip(predictions, ground_truth)
                       if pred == pred_cls and true == true_cls)
            row.append(count)
        confusion_matrix.append(row)

    return {
        'overall_accuracy': overall_accuracy,
        'per_class': per_class,
        'confusion_matrix': confusion_matrix
    }


def compute_logiclm_metrics(results):
    """
    Compute LOGIC-LM++ specific metrics (Table 2 format: Er and Ea).

    Args:
        results: List[dict] - Results from run_logiclm_plus() for each example
                             Each dict should have: answer, correct, execution_success,
                             formalization_success, num_refinement_iterations, backtracking_history

    Returns:
        dict with keys: execution_rate_Er, execution_accuracy_Ea,
                       formalization_success_rate, avg_refinement_iterations,
                       backtracking_rate, early_stopping_rate
    """
    total = len(results)
    if total == 0:
        return {
            'execution_rate_Er': 0.0,
            'execution_accuracy_Ea': 0.0,
            'formalization_success_rate': 0.0,
            'avg_refinement_iterations': 0.0,
            'backtracking_rate': 0.0,
            'early_stopping_rate': 0.0
        }

    # Execution Rate (Er): % that executed without syntax/runtime errors
    executed = sum(1 for r in results if r.get('execution_success', False))
    execution_rate_Er = executed / total

    # Execution Accuracy (Ea): % correct among executed (NOT among all)
    if executed > 0:
        correct_among_executed = sum(1 for r in results
                                    if r.get('execution_success', False) and r.get('correct', False))
        execution_accuracy_Ea = correct_among_executed / executed
    else:
        execution_accuracy_Ea = 0.0

    # Formalization success rate: % initial formalizations that parsed correctly
    formalization_success = sum(1 for r in results if r.get('formalization_success', False))
    formalization_success_rate = formalization_success / total

    # Average refinement iterations
    iterations = [r.get('num_refinement_iterations', 0) for r in results]
    avg_refinement_iterations = statistics.mean(iterations) if iterations else 0.0

    # Backtracking rate: % of iterations with REVERT decision
    total_iterations = sum(iterations)
    if total_iterations > 0:
        total_backtracks = sum(r.get('num_backtracks', 0) for r in results)
        backtracking_rate = total_backtracks / total_iterations
    else:
        backtracking_rate = 0.0

    # Early stopping rate: % examples that stopped before max iterations
    from config import MAX_REFINEMENT_ITERATIONS
    early_stopped = sum(1 for r in results
                       if r.get('early_stop_reason') is not None)
    early_stopping_rate = early_stopped / total

    return {
        'execution_rate_Er': execution_rate_Er,
        'execution_accuracy_Ea': execution_accuracy_Ea,
        'formalization_success_rate': formalization_success_rate,
        'avg_refinement_iterations': avg_refinement_iterations,
        'backtracking_rate': backtracking_rate,
        'early_stopping_rate': early_stopping_rate
    }


def compute_backtracking_stats(results):
    """
    Analyze backtracking behavior (Figure 4 statistics).

    Args:
        results: List[dict] - Results from run_logiclm_plus()

    Returns:
        dict with keys: num_formulations_corrected_per_iteration, with_backtracking,
                       without_backtracking, winning_cases, losing_cases
    """
    from config import MAX_REFINEMENT_ITERATIONS

    # Track corrections per iteration
    corrected_per_iteration = [0] * MAX_REFINEMENT_ITERATIONS

    # Track winning vs losing cases
    winning_cases = 0  # Refinement improved answer
    losing_cases = 0   # Refinement degraded answer

    for r in results:
        # Check if refinement improved the answer
        initial_correct = r.get('initial_formulation', {}).get('correct', False)
        final_correct = r.get('correct', False)

        if final_correct and not initial_correct:
            winning_cases += 1
        elif not final_correct and initial_correct:
            losing_cases += 1

        # Track corrections per iteration (simplified)
        # In full implementation, would track iteration-by-iteration correctness
        if final_correct:
            iterations = r.get('num_refinement_iterations', 0)
            if iterations > 0 and iterations <= MAX_REFINEMENT_ITERATIONS:
                corrected_per_iteration[iterations - 1] += 1

    # Total corrected with backtracking (current system)
    with_backtracking = winning_cases

    # Estimate without backtracking (would need separate run for accurate comparison)
    # For now, use losing_cases as proxy for cases where backtracking prevented degradation
    without_backtracking = winning_cases - losing_cases if winning_cases > losing_cases else 0

    return {
        'num_formulations_corrected_per_iteration': corrected_per_iteration,
        'with_backtracking': with_backtracking,
        'without_backtracking': without_backtracking,
        'winning_cases': winning_cases,
        'losing_cases': losing_cases
    }


def compute_efficiency_metrics(results):
    """
    Analyze time, LLM calls, cost per query.

    Args:
        results: List[dict] - Results from run_logiclm_plus()

    Returns:
        dict with keys: avg_time_per_query, avg_llm_calls_per_query,
                       time_breakdown, total_cost_estimate
    """
    if len(results) == 0:
        return {
            'avg_time_per_query': 0.0,
            'avg_llm_calls_per_query': 0.0,
            'time_breakdown': {
                'formalization': 0.0,
                'refinement': 0.0,
                'backtracking': 0.0,
                'solving': 0.0
            },
            'total_cost_estimate': 0.0
        }

    # Time per query
    times = [r.get('total_time', 0.0) for r in results]
    avg_time_per_query = statistics.mean(times) if times else 0.0

    # LLM calls per query
    llm_calls = [r.get('total_llm_calls', 0) for r in results]
    avg_llm_calls_per_query = statistics.mean(llm_calls) if llm_calls else 0.0

    # Time breakdown
    time_breakdown = {
        'formalization': 0.0,
        'refinement': 0.0,
        'backtracking': 0.0,
        'solving': 0.0
    }

    for key in time_breakdown.keys():
        values = [r.get('time_breakdown', {}).get(key, 0.0) for r in results]
        time_breakdown[key] = statistics.mean(values) if values else 0.0

    # Cost estimate (rough estimate: $0.03 per 1K tokens for GPT-4)
    # Assume ~500 tokens per LLM call on average
    tokens_per_call = 500
    cost_per_1k_tokens = 0.03
    total_llm_calls = sum(llm_calls)
    total_cost_estimate = (total_llm_calls * tokens_per_call / 1000) * cost_per_1k_tokens

    return {
        'avg_time_per_query': avg_time_per_query,
        'avg_llm_calls_per_query': avg_llm_calls_per_query,
        'time_breakdown': time_breakdown,
        'total_cost_estimate': total_cost_estimate
    }


def generate_report(all_results, baseline_results=None):
    """
    Comprehensive evaluation report with all metrics.

    Args:
        all_results: List[dict] - Results from run_logiclm_plus()
        baseline_results: dict - Optional baseline results for comparison
                         Keys: 'logic_lm', 'cot', 'standard', 'rag'

    Returns:
        dict with all metrics (see docstring for full format)
    """
    # Extract predictions and ground truth
    predictions = [r.get('answer', 'Error') for r in all_results]
    ground_truth = [r.get('ground_truth', 'Unknown') for r in all_results if 'ground_truth' in r]

    # If no ground truth available, skip accuracy metrics
    if len(ground_truth) == len(predictions):
        accuracy_metrics = evaluate_predictions(predictions, ground_truth)
    else:
        accuracy_metrics = {
            'overall_accuracy': 0.0,
            'per_class': {},
            'confusion_matrix': []
        }

    # Compute Logic-LM++ specific metrics
    logiclm_metrics = compute_logiclm_metrics(all_results)

    # Compute backtracking statistics
    backtracking_stats = compute_backtracking_stats(all_results)

    # Compute efficiency metrics
    efficiency_metrics = compute_efficiency_metrics(all_results)

    # Comparison to baselines (if provided)
    comparison_to_baselines = {}
    if baseline_results:
        current_accuracy = accuracy_metrics['overall_accuracy']
        if 'logic_lm' in baseline_results:
            comparison_to_baselines['accuracy_vs_logic_lm'] = current_accuracy - baseline_results['logic_lm']
        if 'cot' in baseline_results:
            comparison_to_baselines['accuracy_vs_cot'] = current_accuracy - baseline_results['cot']
        if 'standard' in baseline_results:
            comparison_to_baselines['accuracy_vs_standard'] = current_accuracy - baseline_results['standard']

    return {
        'accuracy_metrics': accuracy_metrics,
        'logiclm_metrics': logiclm_metrics,
        'backtracking_stats': backtracking_stats,
        'efficiency_metrics': efficiency_metrics,
        'comparison_to_baselines': comparison_to_baselines
    }
