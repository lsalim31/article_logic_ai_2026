#!/usr/bin/env python3
"""
experiment_logify_contract_NLI.py

Experiment: Evaluate Logify on ContractNLI dataset.

See DESCRIPTION_EXPERIMENT_CONTRACTNLI_LOGIFY.md for details.

Usage:
    python experiment_logify_contract_NLI.py --api-key sk-... --dataset-path /path/to/contractnli.json
    python experiment_logify_contract_NLI.py --api-key sk-... --dataset-path /path/to/contractnli.json --num-docs 5
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from from_text_to_logic.logify import LogifyConverter
from from_text_to_logic.weights import assign_weights
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver


# Paths
CACHE_DIR = _script_dir / "cache"
RESULTS_DIR = _script_dir / "results_logify_contract_NLI"


def load_contractnli_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load ContractNLI dataset from JSON file."""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_ground_truth_label(choice: str) -> str:
    """Map ContractNLI label to Logify expected output."""
    mapping = {
        "Entailment": "TRUE",
        "Contradiction": "FALSE",
        "NotMentioned": "UNCERTAIN"
    }
    return mapping.get(choice, "UNCERTAIN")


def get_cached_logified_path(doc_id: int) -> Path:
    """Get path to cached logified JSON for a document."""
    return CACHE_DIR / f"doc_{doc_id}_weighted.json"


def logify_document(
    text: str,
    doc_id: int,
    api_key: str,
    model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    weights_model: str,
    k_weights: int
) -> Dict[str, Any]:
    """
    Logify a document and cache the result.

    Returns:
        Dict with logified_structure and metrics (tokens, latency).
    """
    cache_path = get_cached_logified_path(doc_id)

    # Check cache
    if cache_path.exists():
        print(f"    [CACHE HIT] Loading from {cache_path}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            logified_structure = json.load(f)
        return {
            "logified_structure": logified_structure,
            "logify_latency_sec": 0.0,
            "logify_cached": True
        }

    # Logify
    print(f"    [LOGIFY] Converting document {doc_id} to logic...")
    start_time = time.time()

    converter = LogifyConverter(
        api_key=api_key,
        model=model,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens
    )

    try:
        logic_structure = converter.convert_text_to_logic(text)
    finally:
        converter.close()

    # Save intermediate (non-weighted) JSON
    intermediate_path = CACHE_DIR / f"doc_{doc_id}.json"
    with open(intermediate_path, 'w', encoding='utf-8') as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    # Assign weights
    print(f"    [WEIGHTS] Assigning weights...")

    # Create a temporary text file for weights.py (it expects a file path)
    temp_text_path = CACHE_DIR / f"doc_{doc_id}_text.txt"
    with open(temp_text_path, 'w', encoding='utf-8') as f:
        f.write(text)

    assign_weights(
        pathfile=str(temp_text_path),
        json_path=str(intermediate_path),
        api_key=api_key,
        model=weights_model,
        temperature=0.0,
        max_tokens=5,
        k=k_weights,
        verbose=False
    )

    # Load weighted structure
    with open(cache_path, 'r', encoding='utf-8') as f:
        logified_structure = json.load(f)

    # Clean up temp file
    temp_text_path.unlink(missing_ok=True)

    logify_latency = time.time() - start_time
    print(f"    [LOGIFY] Completed in {logify_latency:.2f}s")

    return {
        "logified_structure": logified_structure,
        "logify_latency_sec": logify_latency,
        "logify_cached": False
    }


def query_hypothesis(
    hypothesis_text: str,
    logified_structure: Dict[str, Any],
    json_path: str,
    api_key: str,
    model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    k_query: int
) -> Dict[str, Any]:
    """
    Query a hypothesis against a logified structure.

    Returns:
        Dict with prediction, confidence, latency, and any error.
    """
    start_time = time.time()

    try:
        # Translate hypothesis to formula
        translation_result = translate_query(
            query=hypothesis_text,
            json_path=json_path,
            api_key=api_key,
            model=model,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            k=k_query,
            verbose=False
        )

        formula = translation_result.get('formula')
        if not formula:
            return {
                "prediction": None,
                "confidence": None,
                "query_latency_sec": time.time() - start_time,
                "error": "Failed to translate hypothesis to formula"
            }

        # Solve
        solver = LogicSolver(logified_structure)
        solver_result = solver.query(formula)

        return {
            "prediction": solver_result.answer,
            "confidence": solver_result.confidence,
            "formula": formula,
            "query_latency_sec": time.time() - start_time,
            "error": None
        }

    except Exception as e:
        return {
            "prediction": None,
            "confidence": None,
            "query_latency_sec": time.time() - start_time,
            "error": str(e)
        }


def run_experiment(
    dataset_path: str,
    api_key: str,
    model: str = "gpt-5-nano",
    weights_model: str = "gpt-4o",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 128000,
    query_max_tokens: int = 64000,
    k_weights: int = 10,
    k_query: int = 20,
    num_docs: int = 20
) -> Dict[str, Any]:
    """
    Run the ContractNLI experiment.

    Args:
        dataset_path: Path to ContractNLI JSON file
        api_key: API key for LLM calls
        model: Model for logification and query translation
        weights_model: Model for weight assignment (must support logprobs)
        temperature: Sampling temperature
        reasoning_effort: Reasoning effort for reasoning models
        max_tokens: Max tokens for logification
        query_max_tokens: Max tokens for query translation
        k_weights: Top-k chunks for weight assignment
        k_query: Top-k propositions for query translation
        num_docs: Number of documents to process

    Returns:
        Experiment results dict
    """
    # Ensure directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load dataset
    print(f"Loading dataset from {dataset_path}...")
    dataset = load_contractnli_dataset(dataset_path)

    documents = dataset.get("documents", [])
    labels = dataset.get("labels", {})

    print(f"  Found {len(documents)} documents")
    print(f"  Found {len(labels)} hypotheses")

    # Limit documents
    documents = documents[:num_docs]
    print(f"  Processing {len(documents)} documents")

    # Initialize results
    timestamp = datetime.now().isoformat()
    results = {
        "metadata": {
            "timestamp": timestamp,
            "model": model,
            "weights_model": weights_model,
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "query_max_tokens": query_max_tokens,
            "k_weights": k_weights,
            "k_query": k_query,
            "num_documents": len(documents),
            "num_hypotheses": len(labels),
            "num_pairs": len(documents) * len(labels)
        },
        "document_metrics": [],
        "results": []
    }

    # Output file (with timestamp)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    # Process documents
    total_pairs = 0
    total_correct = 0

    for doc_idx, doc in enumerate(documents):
        doc_id = doc.get("id", doc_idx)
        doc_text = doc.get("text", "")
        annotations = doc.get("annotation_sets", [{}])[0].get("annotations", {})

        print(f"\n[{doc_idx + 1}/{len(documents)}] Processing document {doc_id}")
        print(f"  Text length: {len(doc_text)} chars")

        # Skip empty documents
        if not doc_text or not doc_text.strip():
            print(f"  [SKIP] Empty document text")
            continue

        # Logify document
        try:
            logify_result = logify_document(
                text=doc_text,
                doc_id=doc_id,
                api_key=api_key,
                model=model,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
                max_tokens=max_tokens,
                weights_model=weights_model,
                k_weights=k_weights
            )
            logified_structure = logify_result["logified_structure"]
            logify_latency = logify_result["logify_latency_sec"]
            logify_cached = logify_result["logify_cached"]
            logify_error = None
        except Exception as e:
            print(f"  [ERROR] Logification failed: {e}")
            logified_structure = None
            logify_latency = 0.0
            logify_cached = False
            logify_error = str(e)

        # Process hypotheses
        query_latency_total = 0.0
        doc_correct = 0
        doc_total = 0

        for hyp_key, hyp_info in labels.items():
            hypothesis_text = hyp_info.get("hypothesis", "")

            # Get ground truth
            annotation = annotations.get(hyp_key, {})
            choice = annotation.get("choice", "NotMentioned")
            evidence_spans = annotation.get("spans", [])

            ground_truth = get_ground_truth_label(choice)
            amount_evidence = len(evidence_spans)

            # Query
            if logified_structure is not None:
                json_path = str(get_cached_logified_path(doc_id))
                query_result = query_hypothesis(
                    hypothesis_text=hypothesis_text,
                    logified_structure=logified_structure,
                    json_path=json_path,
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    reasoning_effort=reasoning_effort,
                    max_tokens=query_max_tokens,
                    k_query=k_query
                )
                prediction = query_result.get("prediction")
                confidence = query_result.get("confidence")
                query_latency = query_result.get("query_latency_sec", 0.0)
                query_error = query_result.get("error")
                formula = query_result.get("formula")
            else:
                prediction = None
                confidence = None
                query_latency = 0.0
                query_error = logify_error
                formula = None

            query_latency_total += query_latency

            # Check correctness
            is_correct = (prediction == ground_truth) if prediction else False
            if prediction:
                doc_total += 1
                total_pairs += 1
                if is_correct:
                    doc_correct += 1
                    total_correct += 1

            # Store result
            result_entry = {
                "doc_id": doc_id,
                "hypothesis_key": hyp_key,
                "hypothesis_text": hypothesis_text,
                "prediction": prediction,
                "confidence": confidence,
                "ground_truth": ground_truth,
                "amount_evidence": amount_evidence,
                "formula": formula,
                "error": query_error
            }
            results["results"].append(result_entry)

            # Print progress
            status = "✓" if is_correct else ("✗" if prediction else "?")
            print(f"    [{status}] {hyp_key}: pred={prediction}, gt={ground_truth}, conf={confidence}")

        # Document summary
        doc_accuracy = doc_correct / doc_total if doc_total > 0 else 0.0
        print(f"  Document accuracy: {doc_correct}/{doc_total} = {doc_accuracy:.2%}")
        print(f"  Logify latency: {logify_latency:.2f}s (cached: {logify_cached})")
        print(f"  Query latency total: {query_latency_total:.2f}s")

        # Store document-level metrics
        doc_metrics = {
            "doc_id": doc_id,
            "text_length": len(doc_text),
            "logify_latency_sec": logify_latency,
            "logify_cached": logify_cached,
            "logify_error": logify_error,
            "query_latency_total_sec": query_latency_total,
            "doc_correct": doc_correct,
            "doc_total": doc_total,
            "doc_accuracy": doc_accuracy
        }
        results["document_metrics"].append(doc_metrics)

        # Save intermediate results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # Final summary
    overall_accuracy = total_correct / total_pairs if total_pairs > 0 else 0.0
    results["metadata"]["total_correct"] = total_correct
    results["metadata"]["total_evaluated"] = total_pairs
    results["metadata"]["overall_accuracy"] = overall_accuracy

    print(f"\n{'='*60}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Documents processed: {len(documents)}")
    print(f"Pairs evaluated: {total_pairs}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Results saved to: {output_path}")

    # Final save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run Logify evaluation on ContractNLI dataset",
        epilog="See DESCRIPTION_EXPERIMENT_CONTRACTNLI_LOGIFY.md for details."
    )
    parser.add_argument(
        "--dataset-path",
        required=True,
        help="Path to ContractNLI JSON file"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="API key for LLM calls"
    )
    parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="Model for logification and query (default: gpt-5-nano)"
    )
    parser.add_argument(
        "--weights-model",
        default="gpt-4o",
        help="Model for weight assignment (default: gpt-4o)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (default: 0.1)"
    )
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["none", "low", "medium", "high", "xhigh"],
        help="Reasoning effort (default: medium)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=128000,
        help="Max tokens for logification (default: 128000)"
    )
    parser.add_argument(
        "--query-max-tokens",
        type=int,
        default=64000,
        help="Max tokens for query translation (default: 64000)"
    )
    parser.add_argument(
        "--k-weights",
        type=int,
        default=10,
        help="Top-k chunks for weight assignment (default: 10)"
    )
    parser.add_argument(
        "--k-query",
        type=int,
        default=20,
        help="Top-k propositions for query (default: 20)"
    )
    parser.add_argument(
        "--num-docs",
        type=int,
        default=20,
        help="Number of documents to process (default: 20)"
    )

    args = parser.parse_args()

    # Validate dataset path
    if not Path(args.dataset_path).exists():
        print(f"Error: Dataset not found: {args.dataset_path}")
        return 1

    try:
        run_experiment(
            dataset_path=args.dataset_path,
            api_key=args.api_key,
            model=args.model,
            weights_model=args.weights_model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            query_max_tokens=args.query_max_tokens,
            k_weights=args.k_weights,
            k_query=args.k_query,
            num_docs=args.num_docs
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
