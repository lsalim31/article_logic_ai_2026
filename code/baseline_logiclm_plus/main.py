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

import json
import time
import os
from config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_REFINEMENT_ITERATIONS,
    NUM_REFINEMENT_CANDIDATES,
    SOLVER_TIMEOUT,
    MAX_CONSECUTIVE_BACKTRACKS
)
from formalizer import formalize_to_fol
from refiner import refine_loop
from solver_interface import solve_fol


def run_logiclm_plus(text, query, model_name=MODEL_NAME, ground_truth=None,
                     config=None, **kwargs):
    """
    End-to-end Logic-LM++ pipeline for single example.

    Args:
        text: str, natural language text (premises)
        query: str, natural language query (conclusion to test)
        model_name: str, LLM model name
        ground_truth: str, ground truth answer (for evaluation)
        config: dict, optional configuration dict with keys:
                - max_iterations: int, maximum refinement iterations
                - solver: str, 'prover9' or 'z3'
                - solver_timeout: int, solver timeout in seconds
                - temperature: float, sampling temperature
                - num_candidates: int, number of refinement candidates per iteration
                - max_consecutive_backtracks: int, early stop threshold
        **kwargs: individual parameters (override config if both provided)

    Returns:
        dict with comprehensive results (see module docstring for format)
    """
    # Merge config dict with defaults
    if config is None:
        config = {}

    max_iterations = kwargs.get('max_iterations',
                                config.get('max_iterations', MAX_REFINEMENT_ITERATIONS))
    solver = kwargs.get('solver', config.get('solver', 'z3'))
    solver_timeout = kwargs.get('solver_timeout',
                               config.get('solver_timeout', SOLVER_TIMEOUT))
    temperature = kwargs.get('temperature',
                           config.get('temperature', TEMPERATURE))
    num_candidates = kwargs.get('num_candidates',
                               config.get('num_candidates', NUM_REFINEMENT_CANDIDATES))
    max_consecutive_backtracks = kwargs.get('max_consecutive_backtracks',
                                           config.get('max_consecutive_backtracks',
                                                     MAX_CONSECUTIVE_BACKTRACKS))

    start_time = time.time()
    time_breakdown = {
        'formalization': 0,
        'refinement': 0,
        'backtracking': 0,
        'solving': 0
    }

    # Step 1: Initial formalization
    formalization_start = time.time()
    initial_formulation = formalize_to_fol(text, query, model_name, temperature)
    time_breakdown['formalization'] = time.time() - formalization_start

    # Check formalization success
    formalization_success = (initial_formulation.get('formalization_error') is None)

    if not formalization_success:
        # Formalization failed - count as execution failure
        return {
            'answer': 'Error',
            'correct': None,
            'final_formulation': initial_formulation,
            'initial_formulation': initial_formulation,
            'num_refinement_iterations': 0,
            'backtracking_history': [],
            'num_backtracks': 0,
            'early_stop_reason': 'formalization_failed',
            'total_llm_calls': 1,
            'total_time': time.time() - start_time,
            'time_breakdown': time_breakdown,
            'formalization_success': False,
            'execution_success': False,
            'execution_accuracy': None,
            'formulation_history': [initial_formulation],
            'error': initial_formulation.get('formalization_error')
        }

    # Step 2: Refinement loop with backtracking
    refinement_start = time.time()
    refinement_result = refine_loop(
        initial_formulation=initial_formulation,
        original_text=text,
        original_query=query,
        max_iterations=max_iterations,
        solver=solver,
        solver_timeout=solver_timeout,
        model_name=model_name,
        temperature=temperature,
        num_candidates=num_candidates,
        max_consecutive_backtracks=max_consecutive_backtracks
    )
    time_breakdown['refinement'] = time.time() - refinement_start
    # Note: backtracking time is included in refinement time

    final_formulation = refinement_result['final_formulation']
    llm_calls_refinement = refinement_result['total_llm_calls']

    # Step 3: Final solver execution
    solving_start = time.time()
    solver_result = solve_fol(
        premises=final_formulation.get('premises', []),
        conclusion=final_formulation.get('conclusion', ''),
        solver=solver,
        timeout=solver_timeout
    )
    time_breakdown['solving'] = time.time() - solving_start

    # Get final answer
    answer = solver_result['answer']

    # Check execution success (Er)
    execution_success = (answer != 'Error')

    # Check execution accuracy (Ea) if ground truth provided
    execution_accuracy = None
    correct = None
    if ground_truth is not None and execution_success:
        # Normalize answers for comparison
        answer_normalized = answer.lower()
        ground_truth_normalized = ground_truth.lower()
        correct = (answer_normalized == ground_truth_normalized)
        execution_accuracy = correct

    # Aggregate results
    total_llm_calls = 1 + llm_calls_refinement  # 1 for formalization + refinement calls
    total_time = time.time() - start_time

    return {
        'answer': answer,
        'correct': correct,
        'final_formulation': final_formulation,
        'initial_formulation': initial_formulation,
        'num_refinement_iterations': refinement_result['num_iterations'],
        'backtracking_history': refinement_result['backtracking_history'],
        'num_backtracks': refinement_result['num_backtracks'],
        'early_stop_reason': refinement_result['early_stop_reason'],
        'total_llm_calls': total_llm_calls,
        'total_time': total_time,
        'time_breakdown': time_breakdown,
        'formalization_success': formalization_success,
        'execution_success': execution_success,
        'execution_accuracy': execution_accuracy,
        'formulation_history': refinement_result['refinement_history'],
        'error': solver_result.get('error', None)
    }


def run_batch(examples, model_name=MODEL_NAME, config=None,
              output_dir=None, save_interval=10, **kwargs):
    """
    Process multiple examples, save intermediate results.

    Args:
        examples: List[dict], each with 'text', 'query', 'ground_truth'
        model_name: str, LLM model name
        config: dict, optional configuration dict (see run_logiclm_plus for keys)
        output_dir: str, directory to save results (optional)
        save_interval: int, save intermediate results every N examples
        **kwargs: individual parameters (override config if both provided)

    Returns:
        dict with aggregated results and metrics
    """
    results = []

    for i, example in enumerate(examples):
        print(f"Processing example {i+1}/{len(examples)}...")

        # Extract example fields
        text = example.get('text', '')
        query = example.get('query', '')
        ground_truth = example.get('ground_truth', None)

        # Run Logic-LM++ pipeline
        result = run_logiclm_plus(
            text=text,
            query=query,
            model_name=model_name,
            ground_truth=ground_truth,
            config=config,
            **kwargs
        )

        # Add example metadata
        result['example_id'] = i
        result['text'] = text
        result['query'] = query
        result['ground_truth'] = ground_truth

        results.append(result)

        # Save intermediate results
        if output_dir is not None and (i + 1) % save_interval == 0:
            intermediate_path = os.path.join(output_dir, f'intermediate_{i+1}.json')
            save_results(results, intermediate_path)
            print(f"Saved intermediate results to {intermediate_path}")

    # Compute aggregate metrics
    aggregated = compute_aggregate_metrics(results)

    # Save final results
    if output_dir is not None:
        final_path = os.path.join(output_dir, 'final_results.json')
        save_results(results, final_path)

        metrics_path = os.path.join(output_dir, 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(aggregated, f, indent=2)

        print(f"Saved final results to {final_path}")
        print(f"Saved metrics to {metrics_path}")

    return {
        'results': results,
        'metrics': aggregated
    }


def load_dataset(dataset_name, data_dir='data', use_huggingface=True):
    """
    Load dataset from HuggingFace or local files (FOLIO, ProofWriter, or AR-LSAT).

    Args:
        dataset_name: str, 'folio', 'proofwriter', or 'ar-lsat'
        data_dir: str, directory containing local dataset files (fallback)
        use_huggingface: bool, if True load from HuggingFace Hub

    Returns:
        List[dict], each with 'text', 'query', 'ground_truth'
    """
    dataset_name = dataset_name.lower()

    if use_huggingface:
        try:
            from datasets import load_dataset as hf_load_dataset

            # Map to HuggingFace dataset names
            hf_names = {
                'folio': 'yale-nlp/FOLIO',
                'proofwriter': 'allenai/proofwriter',
                'ar-lsat': 'allenai/ar-lsat'
            }

            if dataset_name not in hf_names:
                raise ValueError(f"Unknown dataset: {dataset_name}")

            print(f"Loading dataset from HuggingFace: {hf_names[dataset_name]}")

            # Load from HuggingFace
            dataset = hf_load_dataset(hf_names[dataset_name], split='test')

            # Normalize format
            examples = []
            for item in dataset:
                # Different datasets have different field names
                if dataset_name == 'folio':
                    example = {
                        'text': item.get('premises', item.get('context', '')),
                        'query': item.get('conclusion', item.get('question', '')),
                        'ground_truth': item.get('label', item.get('answer'))
                    }
                elif dataset_name == 'proofwriter':
                    example = {
                        'text': item.get('theory', item.get('context', '')),
                        'query': item.get('question', ''),
                        'ground_truth': item.get('answer', item.get('label'))
                    }
                elif dataset_name == 'ar-lsat':
                    example = {
                        'text': item.get('context', item.get('passage', '')),
                        'query': item.get('question', ''),
                        'ground_truth': item.get('answer', item.get('label'))
                    }
                else:
                    # Generic fallback
                    example = {
                        'text': item.get('premises', item.get('context', item.get('text', ''))),
                        'query': item.get('conclusion', item.get('question', item.get('query', ''))),
                        'ground_truth': item.get('label', item.get('answer'))
                    }
                examples.append(example)

            print(f"Loaded {len(examples)} examples from HuggingFace")
            return examples

        except ImportError:
            print("HuggingFace datasets library not installed. Falling back to local files.")
            print("Install with: pip install datasets")
        except Exception as e:
            print(f"Error loading from HuggingFace: {e}")
            print("Falling back to local files.")

    # Fallback to local files
    if dataset_name == 'folio':
        file_path = os.path.join(data_dir, 'folio_test.json')
    elif dataset_name == 'proofwriter':
        file_path = os.path.join(data_dir, 'proofwriter_owa_5hop.json')
    elif dataset_name == 'ar-lsat':
        file_path = os.path.join(data_dir, 'ar_lsat.json')
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}\n"
            f"Either install HuggingFace datasets (pip install datasets) "
            f"or place dataset files in {data_dir}/"
        )

    print(f"Loading dataset from local file: {file_path}")

    # Load dataset
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Normalize format
    examples = []
    for item in data:
        example = {
            'text': item.get('text', item.get('premises', '')),
            'query': item.get('query', item.get('conclusion', '')),
            'ground_truth': item.get('label', item.get('answer', None))
        }
        examples.append(example)

    print(f"Loaded {len(examples)} examples from local file")
    return examples


def save_results(results, output_path):
    """
    Serialize results as JSON for later analysis.

    Args:
        results: List[dict] or dict, results to save
        output_path: str, path to output file
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save as JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def compute_aggregate_metrics(results):
    """
    Compute aggregate metrics from batch results.

    Args:
        results: List[dict], results from run_batch

    Returns:
        dict with metrics (accuracy, Er, Ea, backtracking stats, timing)
    """
    total = len(results)

    # Count successes
    formalization_success_count = sum(1 for r in results if r['formalization_success'])
    execution_success_count = sum(1 for r in results if r['execution_success'])

    # Count correct answers (only among executed)
    executed_results = [r for r in results if r['execution_success']]
    correct_count = sum(1 for r in executed_results if r.get('correct') == True)

    # Compute rates
    formalization_success_rate = formalization_success_count / total if total > 0 else 0
    execution_rate_Er = execution_success_count / total if total > 0 else 0
    execution_accuracy_Ea = correct_count / len(executed_results) if len(executed_results) > 0 else 0
    overall_accuracy = correct_count / total if total > 0 else 0

    # Backtracking statistics
    total_backtracks = sum(r['num_backtracks'] for r in results)
    total_iterations = sum(r['num_refinement_iterations'] for r in results)
    backtracking_rate = total_backtracks / total_iterations if total_iterations > 0 else 0

    early_stop_count = sum(1 for r in results if r['early_stop_reason'] is not None)
    early_stopping_rate = early_stop_count / total if total > 0 else 0

    # Refinement statistics
    avg_refinement_iterations = sum(r['num_refinement_iterations'] for r in results) / total if total > 0 else 0

    # Timing statistics
    avg_time_per_query = sum(r['total_time'] for r in results) / total if total > 0 else 0
    avg_llm_calls_per_query = sum(r['total_llm_calls'] for r in results) / total if total > 0 else 0

    # Time breakdown
    avg_formalization_time = sum(r['time_breakdown']['formalization'] for r in results) / total if total > 0 else 0
    avg_refinement_time = sum(r['time_breakdown']['refinement'] for r in results) / total if total > 0 else 0
    avg_solving_time = sum(r['time_breakdown']['solving'] for r in results) / total if total > 0 else 0

    return {
        'total_examples': total,
        'accuracy_metrics': {
            'overall_accuracy': overall_accuracy,
            'correct_count': correct_count
        },
        'logiclm_metrics': {
            'execution_rate_Er': execution_rate_Er,
            'execution_accuracy_Ea': execution_accuracy_Ea,
            'formalization_success_rate': formalization_success_rate,
            'avg_refinement_iterations': avg_refinement_iterations,
            'backtracking_rate': backtracking_rate,
            'early_stopping_rate': early_stopping_rate
        },
        'backtracking_stats': {
            'total_backtracks': total_backtracks,
            'total_iterations': total_iterations,
            'backtracking_rate': backtracking_rate
        },
        'efficiency_metrics': {
            'avg_time_per_query': avg_time_per_query,
            'avg_llm_calls_per_query': avg_llm_calls_per_query,
            'time_breakdown': {
                'formalization': avg_formalization_time,
                'refinement': avg_refinement_time,
                'solving': avg_solving_time
            }
        }
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run Logic-LM++ baseline')
    parser.add_argument('--dataset', type=str, choices=['folio', 'proofwriter', 'ar-lsat'],
                       help='Dataset to run on')
    parser.add_argument('--text', type=str, help='Single example text (premises)')
    parser.add_argument('--query', type=str, help='Single example query (conclusion)')
    parser.add_argument('--model', type=str, default=MODEL_NAME, help='LLM model name')
    parser.add_argument('--iterations', type=int, default=MAX_REFINEMENT_ITERATIONS,
                       help='Maximum refinement iterations')
    parser.add_argument('--solver', type=str, default='z3', choices=['z3', 'prover9'],
                       help='Solver to use')
    parser.add_argument('--output', type=str, help='Output file path for results')
    parser.add_argument('--output-dir', type=str, help='Output directory for results (deprecated, use --output)')
    parser.add_argument('--data-dir', type=str, default='data', help='Data directory')

    args = parser.parse_args()

    if args.dataset:
        # Batch mode
        print(f"Loading dataset: {args.dataset}")
        examples = load_dataset(args.dataset, args.data_dir)
        print(f"Loaded {len(examples)} examples")

        # Determine output directory (--output takes precedence)
        output_dir = args.output if args.output else args.output_dir
        if not output_dir:
            output_dir = f'results_{args.dataset}'

        print(f"Running Logic-LM++ on {args.dataset}...")
        result = run_batch(
            examples=examples,
            model_name=args.model,
            config={'max_iterations': args.iterations, 'solver': args.solver},
            output_dir=output_dir
        )

        print("\n=== Results ===")
        print(f"Overall accuracy: {result['metrics']['accuracy_metrics']['overall_accuracy']:.3f}")
        print(f"Execution rate (Er): {result['metrics']['logiclm_metrics']['execution_rate_Er']:.3f}")
        print(f"Execution accuracy (Ea): {result['metrics']['logiclm_metrics']['execution_accuracy_Ea']:.3f}")
        print(f"Avg refinement iterations: {result['metrics']['logiclm_metrics']['avg_refinement_iterations']:.2f}")
        print(f"Backtracking rate: {result['metrics']['logiclm_metrics']['backtracking_rate']:.3f}")

    elif args.text and args.query:
        # Single example mode
        print("Running Logic-LM++ on single example...")
        result = run_logiclm_plus(
            text=args.text,
            query=args.query,
            model_name=args.model,
            max_iterations=args.iterations,
            solver=args.solver
        )

        print("\n=== Result ===")
        print(f"Answer: {result['answer']}")
        print(f"Refinement iterations: {result['num_refinement_iterations']}")
        print(f"Backtracks: {result['num_backtracks']}")
        print(f"Total time: {result['total_time']:.2f}s")
        print(f"LLM calls: {result['total_llm_calls']}")

        if args.output_dir:
            output_path = os.path.join(args.output_dir, 'single_result.json')
            save_results(result, output_path)
            print(f"\nSaved result to {output_path}")

    else:
        parser.print_help()
