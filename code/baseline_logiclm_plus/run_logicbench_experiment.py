"""
Single-file Logic-LM++ experiment runner for LogicBench-v1.0 dataset.

This script loads the LogicBench dataset from HuggingFace and runs Logic-LM++
experiments on all three logic types (propositional, first-order, non-monotonic).

Usage:
    python run_logicbench_experiment.py --logic_type propositional_logic --task_type BQA --output results_prop_bqa.json
    python run_logicbench_experiment.py --logic_type first_order_logic --task_type MCQA --output results_fol_mcqa.json
    python run_logicbench_experiment.py --logic_type nm_logic --task_type BQA --output results_nm_bqa.json

Arguments:
    --logic_type: propositional_logic, first_order_logic, or nm_logic
    --task_type: BQA (Boolean QA) or MCQA (Multiple Choice QA)
    --output: Output JSON file path
    --max_samples: Maximum number of samples to process (default: all)
    --iterations: Max refinement iterations (default: 4)
    --solver: z3 or prover9 (default: z3)
"""

import json
import os
import argparse
from datetime import datetime
from main import run_logiclm_plus
from config import MODEL_NAME


def load_logicbench_from_huggingface(logic_type, task_type='BQA'):
    """
    Load LogicBench dataset from HuggingFace.

    Args:
        logic_type: 'propositional_logic', 'first_order_logic', or 'nm_logic'
        task_type: 'BQA' or 'MCQA'

    Returns:
        List[dict] with keys: context, question, answer, id, rule_type
    """
    try:
        from datasets import load_dataset

        print(f"Loading LogicBench from HuggingFace: {logic_type}/{task_type}")

        # Try to load the dataset
        dataset = load_dataset("cogint/LogicBench-v1.0")

        # Extract examples based on logic type and task type
        examples = []

        # Note: The actual structure may differ, this is based on documentation
        # We may need to iterate through the dataset structure
        for item in dataset:
            examples.append({
                'context': item.get('context', ''),
                'question': item.get('question', ''),
                'answer': item.get('answer', ''),
                'id': item.get('id', 0),
                'rule_type': item.get('type', '')
            })

        return examples

    except Exception as e:
        print(f"Error loading from HuggingFace: {e}")
        print("Falling back to local file loading...")
        return load_logicbench_from_local(logic_type, task_type)


def load_logicbench_from_local(logic_type, task_type='BQA'):
    """
    Load LogicBench dataset from local JSON files.

    Args:
        logic_type: 'propositional_logic', 'first_order_logic', or 'nm_logic'
        task_type: 'BQA' or 'MCQA'

    Returns:
        List[dict] with keys: context, question, answer, id, rule_type
    """
    # Construct path to local data
    data_dir = os.path.join('data', 'LogicBench(Eval)', task_type, logic_type)

    if not os.path.exists(data_dir):
        raise FileNotFoundError(
            f"LogicBench data not found at: {data_dir}\n"
            f"Please download from: https://huggingface.co/datasets/cogint/LogicBench-v1.0"
        )

    examples = []

    # Iterate through all JSON files in the directory
    for filename in os.listdir(data_dir):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(data_dir, filename)

        with open(filepath, 'r') as f:
            data = json.load(f)

        rule_type = data.get('type', '')
        axiom = data.get('axiom', '')

        # Extract samples
        for sample in data.get('samples', []):
            context = sample.get('context', '')
            sample_id = sample.get('id', 0)

            # Extract QA pairs
            for qa_pair in sample.get('qa_pairs', []):
                question = qa_pair.get('question', '')
                answer = qa_pair.get('answer', '')

                examples.append({
                    'context': context,
                    'question': question,
                    'answer': answer,
                    'id': f"{filename}_{sample_id}",
                    'rule_type': rule_type,
                    'axiom': axiom
                })

    return examples


def normalize_answer(answer):
    """
    Normalize answers from LogicBench to standard format.

    LogicBench uses: 'yes', 'no', or option letters (A, B, C, D, E)
    Logic-LM++ uses: 'Proved', 'Disproved', 'Unknown'

    Args:
        answer: str, raw answer from dataset

    Returns:
        str, normalized answer
    """
    answer_lower = answer.lower().strip()

    # Boolean answers
    if answer_lower in ['yes', 'true']:
        return 'yes'
    elif answer_lower in ['no', 'false']:
        return 'no'
    elif answer_lower in ['unknown', 'uncertain']:
        return 'unknown'

    # Multiple choice (keep as is)
    if answer.upper() in ['A', 'B', 'C', 'D', 'E']:
        return answer.upper()

    return answer


def convert_logiclm_answer_to_logicbench(logiclm_answer):
    """
    Convert Logic-LM++ answer format to LogicBench format.

    Args:
        logiclm_answer: 'Proved', 'Disproved', 'Unknown', or 'Error'

    Returns:
        str, LogicBench format answer
    """
    if logiclm_answer == 'Proved':
        return 'yes'
    elif logiclm_answer == 'Disproved':
        return 'no'
    elif logiclm_answer == 'Unknown':
        return 'unknown'
    else:
        return 'error'


def run_experiment(logic_type, task_type, output_path, max_samples=None,
                   max_iterations=4, solver='z3', model_name=MODEL_NAME):
    """
    Run Logic-LM++ experiment on LogicBench dataset.

    Args:
        logic_type: 'propositional_logic', 'first_order_logic', or 'nm_logic'
        task_type: 'BQA' or 'MCQA'
        output_path: Path to save results
        max_samples: Maximum samples to process (None = all)
        max_iterations: Max refinement iterations
        solver: 'z3' or 'prover9'
        model_name: LLM model name

    Returns:
        dict with results and metrics
    """
    print("="*80)
    print(f"Logic-LM++ Experiment on LogicBench-v1.0")
    print(f"Logic Type: {logic_type}")
    print(f"Task Type: {task_type}")
    print(f"Model: {model_name}")
    print(f"Max Iterations: {max_iterations}")
    print(f"Solver: {solver}")
    print("="*80)

    # Load dataset
    print("\nLoading dataset...")
    examples = load_logicbench_from_local(logic_type, task_type)

    if max_samples is not None:
        examples = examples[:max_samples]

    print(f"Loaded {len(examples)} examples")

    # Run Logic-LM++ on each example
    results = []
    correct_count = 0
    execution_success_count = 0

    for i, example in enumerate(examples):
        print(f"\nProcessing example {i+1}/{len(examples)}: {example['id']}")
        print(f"  Rule: {example['rule_type']}")

        context = example['context']
        question = example['question']
        ground_truth_raw = example['answer']
        ground_truth = normalize_answer(ground_truth_raw)

        # Run Logic-LM++
        config = {
            'max_iterations': max_iterations,
            'solver': solver,
            'num_candidates': 2,
            'max_consecutive_backtracks': 2
        }

        try:
            result = run_logiclm_plus(
                text=context,
                query=question,
                model_name=model_name,
                ground_truth=ground_truth,
                config=config
            )

            # Convert answer to LogicBench format
            logiclm_answer = result['answer']
            converted_answer = convert_logiclm_answer_to_logicbench(logiclm_answer)

            # Check correctness
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

    # Compute aggregate metrics
    total = len(results)
    overall_accuracy = correct_count / total if total > 0 else 0
    execution_rate = execution_success_count / total if total > 0 else 0

    # Compute execution accuracy (correct among executed)
    executed_results = [r for r in results if r.get('execution_success', False)]
    correct_among_executed = sum(1 for r in executed_results if r.get('is_correct', False))
    execution_accuracy = correct_among_executed / len(executed_results) if len(executed_results) > 0 else 0

    # Compute per-rule-type accuracy
    rule_types = set(r['rule_type'] for r in results if 'rule_type' in r)
    per_rule_accuracy = {}

    for rule_type in rule_types:
        rule_results = [r for r in results if r.get('rule_type') == rule_type]
        rule_correct = sum(1 for r in rule_results if r.get('is_correct', False))
        rule_accuracy = rule_correct / len(rule_results) if len(rule_results) > 0 else 0
        per_rule_accuracy[rule_type] = {
            'accuracy': rule_accuracy,
            'count': len(rule_results),
            'correct': rule_correct
        }

    # Aggregate timing and LLM calls
    total_time = sum(r.get('total_time', 0) for r in results)
    total_llm_calls = sum(r.get('total_llm_calls', 0) for r in results)
    avg_time = total_time / total if total > 0 else 0
    avg_llm_calls = total_llm_calls / total if total > 0 else 0

    # Refinement statistics
    total_iterations = sum(r.get('num_refinement_iterations', 0) for r in results)
    total_backtracks = sum(r.get('num_backtracks', 0) for r in results)
    avg_iterations = total_iterations / total if total > 0 else 0
    backtracking_rate = total_backtracks / total_iterations if total_iterations > 0 else 0

    # Build final output
    output = {
        'metadata': {
            'dataset': 'LogicBench-v1.0',
            'logic_type': logic_type,
            'task_type': task_type,
            'model': model_name,
            'max_iterations': max_iterations,
            'solver': solver,
            'timestamp': datetime.now().isoformat(),
            'total_examples': total
        },
        'metrics': {
            'overall_accuracy': overall_accuracy,
            'execution_rate_Er': execution_rate,
            'execution_accuracy_Ea': execution_accuracy,
            'correct_count': correct_count,
            'execution_success_count': execution_success_count,
            'avg_refinement_iterations': avg_iterations,
            'backtracking_rate': backtracking_rate,
            'avg_time_per_query': avg_time,
            'avg_llm_calls_per_query': avg_llm_calls,
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
    print("EXPERIMENT SUMMARY")
    print("="*80)
    print(f"Total examples: {total}")
    print(f"Overall accuracy: {overall_accuracy:.3f} ({correct_count}/{total})")
    print(f"Execution rate (Er): {execution_rate:.3f}")
    print(f"Execution accuracy (Ea): {execution_accuracy:.3f}")
    print(f"Avg refinement iterations: {avg_iterations:.2f}")
    print(f"Backtracking rate: {backtracking_rate:.3f}")
    print(f"Avg time per query: {avg_time:.2f}s")
    print(f"Avg LLM calls per query: {avg_llm_calls:.1f}")
    print(f"\nPer-rule-type accuracy:")
    for rule_type, metrics in sorted(per_rule_accuracy.items()):
        print(f"  {rule_type}: {metrics['accuracy']:.3f} ({metrics['correct']}/{metrics['count']})")
    print(f"\nResults saved to: {output_path}")
    print("="*80)

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Run Logic-LM++ experiment on LogicBench-v1.0 dataset'
    )
    parser.add_argument('--logic_type', type=str, required=True,
                       choices=['propositional_logic', 'first_order_logic', 'nm_logic'],
                       help='Type of logic to test')
    parser.add_argument('--task_type', type=str, default='BQA',
                       choices=['BQA', 'MCQA'],
                       help='Task type: BQA (Boolean QA) or MCQA (Multiple Choice QA)')
    parser.add_argument('--output', type=str, required=True,
                       help='Output JSON file path')
    parser.add_argument('--max_samples', type=int, default=None,
                       help='Maximum number of samples to process (default: all)')
    parser.add_argument('--iterations', type=int, default=4,
                       help='Maximum refinement iterations (default: 4)')
    parser.add_argument('--solver', type=str, default='z3',
                       choices=['z3', 'prover9'],
                       help='Solver to use (default: z3)')
    parser.add_argument('--model', type=str, default=MODEL_NAME,
                       help=f'LLM model name (default: {MODEL_NAME})')

    args = parser.parse_args()

    # Run experiment
    run_experiment(
        logic_type=args.logic_type,
        task_type=args.task_type,
        output_path=args.output,
        max_samples=args.max_samples,
        max_iterations=args.iterations,
        solver=args.solver,
        model_name=args.model
    )


if __name__ == '__main__':
    main()
