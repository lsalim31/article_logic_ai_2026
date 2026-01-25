"""
Main orchestration script for Reasoning LLM + RAG baseline.

This script coordinates the end-to-end baseline experiment pipeline:
1. Load dataset (FOLIO, ProofWriter, or ContractNLI)
2. Chunk documents into overlapping segments
3. Encode chunks using SBERT
4. For each query:
   - Retrieve top-k relevant chunks
   - Perform Chain-of-Thought reasoning with LLM
   - Collect predictions
5. Evaluate predictions against ground truth
6. Report and save results

The script supports configurable model selection while maintaining fixed
hyperparameters for chunking, retrieval, and prompting.
"""

import config
from chunker import chunk_document
from retriever import load_sbert_model, encode_chunks, encode_query, retrieve
from reasoner import reason_with_cot
from evaluator import evaluate, format_results


def load_dataset(dataset_name, split='validation'):
    """
    Load benchmark dataset for evaluation.

    Args:
        dataset_name: One of ['folio', 'proofwriter', 'contractnli']
        split: Dataset split to load (e.g., 'test', 'validation')

    Returns:
        List of examples, each a dictionary containing:
            - 'document': Source document text (string)
            - 'query': Question or hypothesis (string)
            - 'label': Ground truth label (string)
            - 'id': Unique example identifier (string or int)
    """
    from datasets import load_dataset as hf_load_dataset

    if dataset_name == 'folio':
        dataset = hf_load_dataset('yale-nlp/FOLIO', split=split)
        examples = []
        for i, item in enumerate(dataset):
            examples.append({
                'document': item['premises'],
                'query': item['conclusion'],
                'label': item['label'],
                'id': i
            })
    elif dataset_name == 'proofwriter':
        dataset = hf_load_dataset('allenai/proofwriter', 'depth-5', split=split)
        examples = []
        for i, item in enumerate(dataset):
            examples.append({
                'document': item['theory'],
                'query': item['question'],
                'label': item['answer'],
                'id': i
            })
    elif dataset_name == 'contractnli':
        dataset = hf_load_dataset('koreeda/contractnli', split=split)
        examples = []
        for i, item in enumerate(dataset):
            examples.append({
                'document': item['document'],
                'query': item['hypothesis'],
                'label': item['label'],
                'id': i
            })
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    return examples


def preprocess_document(document):
    """
    Preprocess document text before chunking.

    Args:
        document: Raw document text (string)

    Returns:
        Cleaned and normalized document text (string) with:
        - Collapsed whitespace
        - Trimmed leading/trailing whitespace
        - Normalized to single spaces between words
    """
    import re

    text = document.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


def run_baseline_experiment(dataset_name, model_name=None):
    """
    Execute complete RAG baseline experiment on a dataset.

    This is the main orchestration function that coordinates all pipeline stages.

    Args:
        dataset_name: Name of the dataset to evaluate (string)
        model_name: LLM model name (string, defaults to config.DEFAULT_MODEL)

    Returns:
        Dictionary containing:
            - 'metrics': Evaluation metrics dict from evaluator.py
            - 'predictions': List of predicted labels (strings)
            - 'examples': List of example output dicts for inspection
    """
    if model_name is None:
        model_name = config.DEFAULT_MODEL

    print(f"Loading dataset: {dataset_name}")
    examples = load_dataset(dataset_name)

    print("Loading SBERT model")
    sbert_model = load_sbert_model(config.SBERT_MODEL)

    predictions = []
    ground_truth = []
    example_outputs = []

    for i, example in enumerate(examples):
        print(f"Processing example {i+1}/{len(examples)}")

        preprocessed_doc = preprocess_document(example['document'])
        chunks = chunk_document(preprocessed_doc, config.CHUNK_SIZE, config.OVERLAP)
        chunk_embeddings = encode_chunks(chunks, sbert_model)

        result = process_single_example(example, chunk_embeddings, chunks, sbert_model, model_name)

        predictions.append(result['prediction'])
        ground_truth.append(example['label'])

        if i < 5:
            example_outputs.append({
                'id': example['id'],
                'query': example['query'],
                'prediction': result['prediction'],
                'ground_truth': example['label'],
                'reasoning': result['reasoning']
            })

    print("Evaluating results")
    metrics = evaluate(predictions, ground_truth)

    return {
        'metrics': metrics,
        'predictions': predictions,
        'examples': example_outputs
    }


def process_single_example(example, chunk_embeddings, chunks, sbert_model, llm_model):
    """
    Process a single query-document pair through the RAG pipeline.

    Args:
        example: Example dictionary from dataset
        chunk_embeddings: Pre-computed embeddings for document chunks (numpy array)
        chunks: List of chunk dictionaries from chunker
        sbert_model: Loaded SBERT model object
        llm_model: Name of LLM to use (string)

    Returns:
        Dictionary containing:
            - 'prediction': Model's predicted answer (string)
            - 'reasoning': Chain-of-thought reasoning (string)
            - 'retrieved_chunks': Chunks used for reasoning (list of dicts)
    """
    query = example['query']

    query_embedding = encode_query(query, sbert_model)

    retrieved_chunks = retrieve(query_embedding, chunk_embeddings, chunks, k=config.TOP_K)

    result = reason_with_cot(query, retrieved_chunks, llm_model, config.COT_PROMPT_TEMPLATE, config.TEMPERATURE)

    return {
        'prediction': result['answer'],
        'reasoning': result['reasoning'],
        'retrieved_chunks': retrieved_chunks
    }


def save_results(results, output_path):
    """
    Save experiment results to file.

    Args:
        results: Results dictionary from run_baseline_experiment
        output_path: Path to save results (string, JSON format)

    Returns:
        None (writes JSON file to output_path)
    """
    import json

    serializable_results = {
        'metrics': {
            'accuracy': results['metrics']['accuracy'],
            'precision': results['metrics']['precision'],
            'recall': results['metrics']['recall'],
            'f1': results['metrics']['f1'],
            'confusion_matrix': {f"{k[0]}__{k[1]}": v for k, v in results['metrics']['confusion_matrix'].items()},
            'per_class_metrics': results['metrics']['per_class_metrics']
        },
        'predictions': results['predictions'],
        'examples': results['examples']
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)

    print(f"Results saved to {output_path}")


def main():
    """
    Command-line entry point for baseline experiments.

    Parses arguments for dataset selection and model configuration,
    runs the experiment, and saves results.

    Returns:
        None (prints results to console and saves to file)
    """
    import argparse

    parser = argparse.ArgumentParser(description='Run RAG baseline experiments')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['folio', 'proofwriter', 'contractnli'],
                       help='Dataset to evaluate')
    parser.add_argument('--model', type=str, default=config.DEFAULT_MODEL,
                       help='LLM model name')
    parser.add_argument('--output', type=str, default='results.json',
                       help='Output file path')

    args = parser.parse_args()

    results = run_baseline_experiment(args.dataset, args.model)

    formatted = format_results(results['metrics'], args.dataset)
    print(formatted)

    save_results(results, args.output)


if __name__ == "__main__":
    main()
