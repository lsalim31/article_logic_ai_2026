"""
Logic-LM++ experiment runner with FORCED REFINEMENT for LogicBench-v1.0.

This is a modified version of run_logicbench_experiment.py that forces at least
one refinement iteration, bypassing the early-stop on solver success.

The original Logic-LM++ only refines on solver ERRORS, not on solver success.
This means wrong answers (e.g., 'Unknown' when should be 'Proved') don't trigger
refinement. This script tests whether forcing refinement improves accuracy.

Usage:
    python run_logicbench_with_refinement.py --logic_type propositional_logic --task_type BQA --output results_with_refinement.json --max_samples 20
"""

import json
import os
import sys
import argparse
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import MODEL_NAME
from formalizer import formalize
from refiner import generate_refinements, select_best_formulation, backtracking_decision
from solver_interface import solve_fol

# Import the shared loader
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fol_vs_boolean'))
from load_logicbench import load_logicbench as load_from_github


def load_logicbench_from_github(logic_type, task_type='BQA', max_examples=None):
    """Load LogicBench dataset directly from GitHub raw files."""
    import urllib.request
    import urllib.error

    print(f"Loading LogicBench from GitHub: {logic_type}/{task_type}")

    pattern_lists = {
        'propositional_logic': [
            'modus_tollens', 'disjunctive_syllogism', 'hypothetical_syllogism',
            'constructive_dilemma', 'destructive_dilemma', 'bidirectional_dilemma',
            'commutation', 'material_implication'
        ],
        'first_order_logic': [
            'universal_instantiation', 'existential_generalization',
            'modus_ponens', 'modus_tollens', 'disjunctive_syllogism',
            'hypothetical_syllogism', 'constructive_dilemma', 'destructive_dilemma',
            'bidirectional_dilemma'
        ],
        'nm_logic': [
            'default_reasoning_default', 'default_reasoning_irr',
            'default_reasoning_open', 'default_reasoning_several',
            'reasoning_about_exceptions_1', 'reasoning_about_exceptions_2',
            'reasoning_about_exceptions_3', 'reasoning_about_priority'
        ]
    }

    patterns = pattern_lists.get(logic_type, [])
    base_url = f"https://raw.githubusercontent.com/Mihir3009/LogicBench/main/data/LogicBench(Eval)/{task_type}/{logic_type}"

    examples = []
    for pattern in patterns:
        url = f"{base_url}/{pattern}/data_instances.json"
        print(f"  Loading pattern: {pattern}")

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())

            rule_type = data.get('type', '')
            axiom = data.get('axiom', '')

            for sample in data.get('samples', []):
                context = sample.get('context', '')
                sample_id = sample.get('id', 0)

                for qa_pair in sample.get('qa_pairs', []):
                    question = qa_pair.get('question', '')
                    answer = qa_pair.get('answer', '')

                    examples.append({
                        'context': context,
                        'question': question,
                        'answer': answer,
                        'id': f"{pattern}_{sample_id}",
                        'rule_type': rule_type,
                        'axiom': axiom
                    })

                    if max_examples and len(examples) >= max_examples:
                        print(f"  Reached max_examples limit: {max_examples}")
                        return examples

            print(f"    Loaded {len([e for e in examples if e['axiom'] == axiom])} examples")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"    Pattern not found (skipping): {pattern}")
            else:
                print(f"    Error loading {pattern}: {e}")
        except Exception as e:
            print(f"    Error processing {pattern}: {e}")

    print(f"Total loaded: {len(examples)} examples")
    return examples


def normalize_answer(answer):
    """Normalize answers from LogicBench to standard format."""
    answer_lower = answer.lower().strip()
    if answer_lower in ['yes', 'true']:
        return 'yes'
    elif answer_lower in ['no', 'false']:
        return 'no'
    elif answer_lower in ['unknown', 'uncertain']:
        return 'unknown'
    if answer.upper() in ['A', 'B', 'C', 'D', 'E']:
        return answer.upper()
    return answer


def convert_logiclm_answer_to_logicbench(logiclm_answer):
    """Convert Logic-LM++ answer format to LogicBench format."""
    if logiclm_answer == 'Proved':
        return 'yes'
    elif logiclm_answer == 'Disproved':
        return 'no'
    elif logiclm_answer == 'Unknown':
        return 'unknown'
    else:
        return 'error'


def run_with_forced_refinement(text, query, logic_type='propositional',
                                model_name=MODEL_NAME, min_refinements=1,
                                max_iterations=4, solver='z3', solver_timeout=30):
    """
    Run Logic-LM++ pipeline with FORCED refinement iterations.

    Unlike the standard pipeline which stops on solver success, this version
    forces at least `min_refinements` iterations before accepting a result.
    """
    import time

    start_time = time.time()
    total_llm_calls = 0

    # Step 1: Initial formalization
    formalization_start = time.time()
    current_formulation = formalize(text, query, logic_type, model_name)
    formalization_time = time.time() - formalization_start
    total_llm_calls += 1

    if current_formulation.get('formalization_error'):
        return {
            'answer': 'Error',
            'correct': None,
            'final_formulation': current_formulation,
            'initial_formulation': current_formulation,
            'num_refinement_iterations': 0,
            'backtracking_history': [],
            'num_backtracks': 0,
            'early_stop_reason': 'formalization_failed',
            'total_llm_calls': total_llm_calls,
            'total_time': time.time() - start_time,
            'time_breakdown': {'formalization': formalization_time, 'refinement': 0, 'solving': 0},
            'formalization_success': False,
            'execution_success': False,
            'formulation_history': [current_formulation],
            'error': current_formulation.get('formalization_error')
        }

    initial_formulation = current_formulation
    refinement_history = [initial_formulation]
    backtracking_history = []
    refinement_iterations = 0

    # Step 2: FORCED refinement loop
    refinement_start = time.time()

    for iteration in range(max_iterations):
        # Check solver result
        solver_result = solve_fol(
            premises=current_formulation.get('premises', []),
            conclusion=current_formulation.get('conclusion', ''),
            solver=solver,
            timeout=solver_timeout
        )

        # KEY CHANGE: Only stop early AFTER min_refinements
        if iteration >= min_refinements and solver_result['answer'] != 'Error':
            break

        # If we haven't done min_refinements yet, force a refinement
        # even if solver succeeded
        if solver_result['answer'] == 'Error':
            error_feedback = solver_result.get('error', 'Solver error')
        else:
            # Provide feedback that we're refining for potential semantic issues
            error_feedback = f"Solver returned '{solver_result['answer']}'. Checking if formulation is semantically optimal. Please verify the conclusion matches the query intent."

        # Generate refinement candidates
        candidates = generate_refinements(
            current_formulation=current_formulation,
            error_feedback=error_feedback,
            original_text=text,
            original_query=query,
            num_candidates=2,
            model_name=model_name
        )
        total_llm_calls += 1

        if len(candidates) == 0:
            backtracking_history.append('REVERT')
            continue

        # Select best candidate
        selected = select_best_formulation(
            candidates=candidates,
            original_text=text,
            original_query=query,
            model_name=model_name
        )
        total_llm_calls += 1

        if selected is None:
            backtracking_history.append('REVERT')
            continue

        # Backtracking decision
        decision = backtracking_decision(
            previous_formulation=current_formulation,
            refined_formulation=selected,
            original_text=text,
            original_query=query,
            model_name=model_name
        )
        total_llm_calls += 1
        backtracking_history.append(decision)

        if decision == 'IMPROVED':
            current_formulation = selected
            refinement_history.append(selected)

        refinement_iterations += 1

    refinement_time = time.time() - refinement_start

    # Step 3: Final solve
    solving_start = time.time()
    final_result = solve_fol(
        premises=current_formulation.get('premises', []),
        conclusion=current_formulation.get('conclusion', ''),
        solver=solver,
        timeout=solver_timeout
    )
    solving_time = time.time() - solving_start

    answer = final_result['answer']
    execution_success = (answer != 'Error')

    return {
        'answer': answer,
        'correct': None,  # Will be set by caller
        'final_formulation': current_formulation,
        'initial_formulation': initial_formulation,
        'num_refinement_iterations': refinement_iterations,
        'backtracking_history': backtracking_history,
        'num_backtracks': backtracking_history.count('REVERT'),
        'early_stop_reason': None,
        'total_llm_calls': total_llm_calls,
        'total_time': time.time() - start_time,
        'time_breakdown': {
            'formalization': formalization_time,
            'refinement': refinement_time,
            'backtracking': 0,
            'solving': solving_time
        },
        'formalization_success': True,
        'execution_success': execution_success,
        'formulation_history': refinement_history,
        'error': final_result.get('error')
    }


def run_experiment(logic_type, task_type, output_path, max_samples=None,
                   min_refinements=1, max_iterations=4, solver='z3', model_name=MODEL_NAME):
    """Run experiment with forced refinement."""

    print("="*80)
    print(f"Logic-LM++ Experiment WITH FORCED REFINEMENT")
    print(f"Logic Type: {logic_type}")
    print(f"Task Type: {task_type}")
    print(f"Model: {model_name}")
    print(f"Min Refinements: {min_refinements}")
    print(f"Max Iterations: {max_iterations}")
    print(f"Solver: {solver}")
    print("="*80)

    # Load dataset
    print("\nLoading dataset...")
    examples = load_logicbench_from_github(logic_type, task_type, max_examples=max_samples)

    if max_samples is not None:
        examples = examples[:max_samples]

    print(f"Loaded {len(examples)} examples")

    # Determine formalization type
    formalization_logic_type = 'propositional' if logic_type == 'propositional_logic' else 'fol'

    # Run on each example
    results = []
    correct_count = 0
    execution_success_count = 0

    for i, example in enumerate(examples):
        print(f"\nProcessing example {i+1}/{len(examples)}: {example['id']}")
        print(f"  Rule: {example['rule_type']}")

        context = example['context']
        question = example['question']
        ground_truth = normalize_answer(example['answer'])

        try:
            result = run_with_forced_refinement(
                text=context,
                query=question,
                logic_type=formalization_logic_type,
                model_name=model_name,
                min_refinements=min_refinements,
                max_iterations=max_iterations,
                solver=solver
            )

            # Convert answer
            logiclm_answer = result['answer']
            converted_answer = convert_logiclm_answer_to_logicbench(logiclm_answer)
            is_correct = (converted_answer == ground_truth)

            if result['execution_success']:
                execution_success_count += 1
            if is_correct:
                correct_count += 1

            # Add metadata
            result['example_id'] = example['id']
            result['rule_type'] = example['rule_type']
            result['axiom'] = example.get('axiom', '')
            result['context'] = context
            result['question'] = question
            result['ground_truth'] = ground_truth
            result['converted_answer'] = converted_answer
            result['is_correct'] = is_correct

            results.append(result)

            print(f"  Answer: {logiclm_answer} -> {converted_answer}")
            print(f"  Ground truth: {ground_truth}")
            print(f"  Correct: {is_correct}")
            print(f"  Iterations: {result['num_refinement_iterations']}")
            print(f"  Backtracks: {result['num_backtracks']}")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'example_id': example['id'],
                'rule_type': example['rule_type'],
                'context': context,
                'question': question,
                'ground_truth': ground_truth,
                'answer': 'Error',
                'error': str(e),
                'is_correct': False,
                'execution_success': False
            })

    # Compute metrics
    total = len(results)
    overall_accuracy = correct_count / total if total > 0 else 0
    execution_rate = execution_success_count / total if total > 0 else 0

    executed_results = [r for r in results if r.get('execution_success', False)]
    correct_among_executed = sum(1 for r in executed_results if r.get('is_correct', False))
    execution_accuracy = correct_among_executed / len(executed_results) if executed_results else 0

    # Per-rule accuracy
    rule_types = set(r['rule_type'] for r in results if 'rule_type' in r)
    per_rule_accuracy = {}
    for rule_type in rule_types:
        rule_results = [r for r in results if r.get('rule_type') == rule_type]
        rule_correct = sum(1 for r in rule_results if r.get('is_correct', False))
        per_rule_accuracy[rule_type] = {
            'accuracy': rule_correct / len(rule_results) if rule_results else 0,
            'count': len(rule_results),
            'correct': rule_correct
        }

    # Aggregate stats
    total_time = sum(r.get('total_time', 0) for r in results)
    total_llm_calls = sum(r.get('total_llm_calls', 0) for r in results)
    total_iterations = sum(r.get('num_refinement_iterations', 0) for r in results)
    total_backtracks = sum(r.get('num_backtracks', 0) for r in results)

    output = {
        'metadata': {
            'dataset': 'LogicBench-v1.0',
            'logic_type': logic_type,
            'task_type': task_type,
            'model': model_name,
            'min_refinements': min_refinements,
            'max_iterations': max_iterations,
            'solver': solver,
            'timestamp': datetime.now().isoformat(),
            'total_examples': total,
            'experiment_type': 'forced_refinement'
        },
        'metrics': {
            'overall_accuracy': overall_accuracy,
            'execution_rate_Er': execution_rate,
            'execution_accuracy_Ea': execution_accuracy,
            'correct_count': correct_count,
            'execution_success_count': execution_success_count,
            'avg_refinement_iterations': total_iterations / total if total > 0 else 0,
            'backtracking_rate': total_backtracks / total_iterations if total_iterations > 0 else 0,
            'avg_time_per_query': total_time / total if total > 0 else 0,
            'avg_llm_calls_per_query': total_llm_calls / total if total > 0 else 0,
            'per_rule_accuracy': per_rule_accuracy
        },
        'results': results
    }

    # Save results
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print("\n" + "="*80)
    print("EXPERIMENT SUMMARY (WITH FORCED REFINEMENT)")
    print("="*80)
    print(f"Total examples: {total}")
    print(f"Overall accuracy: {overall_accuracy:.3f} ({correct_count}/{total})")
    print(f"Execution rate (Er): {execution_rate:.3f}")
    print(f"Execution accuracy (Ea): {execution_accuracy:.3f}")
    print(f"Avg refinement iterations: {total_iterations / total if total > 0 else 0:.2f}")
    print(f"Backtracking rate: {total_backtracks / total_iterations if total_iterations > 0 else 0:.3f}")
    print(f"Avg time per query: {total_time / total if total > 0 else 0:.2f}s")
    print(f"Avg LLM calls per query: {total_llm_calls / total if total > 0 else 0:.1f}")
    print(f"\nPer-rule-type accuracy:")
    for rule_type, metrics in sorted(per_rule_accuracy.items()):
        print(f"  {rule_type}: {metrics['accuracy']:.3f} ({metrics['correct']}/{metrics['count']})")
    print(f"\nResults saved to: {output_path}")
    print("="*80)

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Run Logic-LM++ with FORCED REFINEMENT on LogicBench-v1.0'
    )
    parser.add_argument('--logic_type', type=str, required=True,
                       choices=['propositional_logic', 'first_order_logic', 'nm_logic'])
    parser.add_argument('--task_type', type=str, default='BQA',
                       choices=['BQA', 'MCQA'])
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--max_samples', type=int, default=None)
    parser.add_argument('--min_refinements', type=int, default=1,
                       help='Minimum refinement iterations to force (default: 1)')
    parser.add_argument('--iterations', type=int, default=4)
    parser.add_argument('--solver', type=str, default='z3', choices=['z3', 'prover9'])
    parser.add_argument('--model', type=str, default=MODEL_NAME)

    args = parser.parse_args()

    run_experiment(
        logic_type=args.logic_type,
        task_type=args.task_type,
        output_path=args.output,
        max_samples=args.max_samples,
        min_refinements=args.min_refinements,
        max_iterations=args.iterations,
        solver=args.solver,
        model_name=args.model
    )


if __name__ == '__main__':
    main()
