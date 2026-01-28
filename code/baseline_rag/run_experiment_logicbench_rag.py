#!/usr/bin/env python3
"""
RAG baseline experiment on LogicBench dataset.

This script runs the Reasoning LLM + RAG baseline on LogicBench,
evaluating performance on propositional and first-order logic reasoning tasks.

Usage:
    python run_experiment_logicbench_rag.py --logic_type propositional_logic
    python run_experiment_logicbench_rag.py --logic_type first_order_logic --max_examples 10
"""

import sys
import json
import argparse

sys.path.insert(0, '../fol_vs_boolean')
from load_logicbench import load_logicbench

import config
from chunker import chunk_document
from retriever import load_sbert_model, encode_chunks, encode_query, retrieve
from reasoner import reason_with_cot
from evaluator import evaluate, format_results, normalize_label


LOGICBENCH_PROMPT_TEMPLATE = """You are a precise logical reasoning assistant. Given a set of premises and a question, determine whether the statement in the question is true or false based solely on the given premises.

Premises:
{retrieved_chunks}

Question: {query}

Instructions:
1. Carefully read all the premises provided
2. Identify the logical relationships and implications
3. Reason step-by-step to determine if the statement follows from the premises
4. Answer True if the statement logically follows, False if it contradicts the premises, or Unknown if it cannot be determined

Format your response as:
**Reasoning:** [Your step-by-step logical analysis]
**Answer:** [True/False/Unknown]

Begin your analysis:
"""


def preprocess_text(text):
    """
    Preprocess text before chunking.

    Args:
        text: Raw text string

    Returns:
        Cleaned text with normalized whitespace
    """
    import re
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def convert_ground_truth(ground_truth):
    """
    Convert LogicBench ground truth to standard label format.

    Args:
        ground_truth: Raw ground truth value (bool, str, or other)

    Returns:
        Normalized label string ('True', 'False', or 'Unknown')
    """
    if isinstance(ground_truth, bool):
        return 'True' if ground_truth else 'False'
    if isinstance(ground_truth, str):
        gt_lower = ground_truth.strip().lower()
        if gt_lower in ['true', 'yes']:
            return 'True'
        if gt_lower in ['false', 'no']:
            return 'False'
    return 'Unknown'


def run_logicbench_experiment(logic_type, reasoning_patterns=None, max_examples_per_pattern=None, model_name=None):
    """
    Run RAG baseline experiment on LogicBench.

    Args:
        logic_type: 'propositional_logic' or 'first_order_logic'
        reasoning_patterns: List of patterns to evaluate (None for all)
        max_examples_per_pattern: Limit examples per pattern
        model_name: LLM model name (defaults to config.DEFAULT_MODEL)

    Returns:
        Dictionary with metrics, predictions, and per-pattern breakdown
    """
    if model_name is None:
        model_name = config.DEFAULT_MODEL

    print(f"Running LogicBench RAG experiment")
    print(f"  Logic type: {logic_type}")
    print(f"  Model: {model_name}")

    examples = load_logicbench(
        logic_type=logic_type,
        reasoning_patterns=reasoning_patterns,
        max_examples_per_pattern=max_examples_per_pattern
    )

    if not examples:
        print("No examples loaded. Exiting.")
        return None

    print(f"\nLoading SBERT model: {config.SBERT_MODEL}")
    sbert_model = load_sbert_model(config.SBERT_MODEL)

    predictions = []
    ground_truths = []
    results_by_pattern = {}

    for i, example in enumerate(examples):
        print(f"Processing {i+1}/{len(examples)}: {example['id']}")

        text = preprocess_text(example['text'])
        query = example['query']
        gt = convert_ground_truth(example['ground_truth'])
        pattern = example['pattern']

        chunks = chunk_document(text, config.CHUNK_SIZE, config.OVERLAP)
        chunk_embeddings = encode_chunks(chunks, sbert_model)
        query_embedding = encode_query(query, sbert_model)

        retrieved_chunks = retrieve(query_embedding, chunk_embeddings, chunks, k=config.TOP_K)

        result = reason_with_cot(query, retrieved_chunks, model_name, LOGICBENCH_PROMPT_TEMPLATE, config.TEMPERATURE)
        pred = normalize_label(result['answer'])

        predictions.append(pred)
        ground_truths.append(gt)

        if pattern not in results_by_pattern:
            results_by_pattern[pattern] = {'predictions': [], 'ground_truths': []}
        results_by_pattern[pattern]['predictions'].append(pred)
        results_by_pattern[pattern]['ground_truths'].append(gt)

    print("\nComputing overall metrics...")
    overall_metrics = evaluate(predictions, ground_truths)

    print("\nComputing per-pattern metrics...")
    pattern_metrics = {}
    for pattern, data in results_by_pattern.items():
        pattern_metrics[pattern] = evaluate(data['predictions'], data['ground_truths'])

    return {
        'overall_metrics': overall_metrics,
        'pattern_metrics': pattern_metrics,
        'predictions': predictions,
        'ground_truths': ground_truths,
        'logic_type': logic_type,
        'num_examples': len(examples)
    }


def save_results(results, output_path):
    """
    Save experiment results to JSON file.

    Args:
        results: Results dictionary from run_logicbench_experiment
        output_path: Path to output file
    """
    serializable = {
        'logic_type': results['logic_type'],
        'num_examples': results['num_examples'],
        'overall_metrics': {
            'accuracy': results['overall_metrics']['accuracy'],
            'precision': results['overall_metrics']['precision'],
            'recall': results['overall_metrics']['recall'],
            'f1': results['overall_metrics']['f1']
        },
        'pattern_metrics': {
            pattern: {
                'accuracy': m['accuracy'],
                'precision': m['precision'],
                'recall': m['recall'],
                'f1': m['f1']
            }
            for pattern, m in results['pattern_metrics'].items()
        },
        'predictions': results['predictions'],
        'ground_truths': results['ground_truths']
    }

    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)

    print(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Run RAG baseline on LogicBench')
    parser.add_argument('--logic_type', type=str, default='propositional_logic',
                        choices=['propositional_logic', 'first_order_logic'],
                        help='Type of logic to evaluate')
    parser.add_argument('--patterns', type=str, nargs='*', default=None,
                        help='Specific reasoning patterns to evaluate')
    parser.add_argument('--max_examples', type=int, default=None,
                        help='Max examples per pattern')
    parser.add_argument('--model', type=str, default=config.DEFAULT_MODEL,
                        help='LLM model name')
    parser.add_argument('--output', type=str, default='logicbench_rag_results.json',
                        help='Output file path')

    args = parser.parse_args()

    results = run_logicbench_experiment(
        logic_type=args.logic_type,
        reasoning_patterns=args.patterns,
        max_examples_per_pattern=args.max_examples,
        model_name=args.model
    )

    if results:
        print("\n" + "="*60)
        print(format_results(results['overall_metrics'], f"LogicBench ({args.logic_type})"))

        print("\nPer-Pattern Breakdown:")
        for pattern, metrics in results['pattern_metrics'].items():
            print(f"  {pattern}: Accuracy={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")

        save_results(results, args.output)


if __name__ == "__main__":
    main()
