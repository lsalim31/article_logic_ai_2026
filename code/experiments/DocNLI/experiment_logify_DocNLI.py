#!/usr/bin/env python3
"""
experiment_logify_DocNLI.py

Experiment: Evaluate Logify on DocNLI dataset (100 filtered examples).

See DESCRIPTION_EXPERIMENT_DOCNLI_LOGIFY.md for details.

Usage:
    python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY
    python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY --temperature 0.0

Environment:
    OPENROUTER_API_KEY: API key (used if --api-key not provided)

Models:
    - Logification: openai/gpt-5.2 (fixed)
    - Query translation: openai/gpt-5-nano (configurable)
    - Weight assignment: gpt-4o (configurable)
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
RESULTS_DIR = _script_dir / "results_logify_DocNLI"
SAMPLE_DATA_PATH = _script_dir / "doc-nli" / "sample_100.json"

# Fixed model for logification
LOGIFY_MODEL = "openai/gpt-5.2"


def load_sample_data(data_path: Path = SAMPLE_DATA_PATH) -> Dict[str, Any]:
    """Load sample DocNLI data from JSON file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def map_prediction_to_binary(prediction: Optional[str]) -> Optional[str]:
    """
    Map Logify prediction to DocNLI binary label.

    TRUE -> entailment
    FALSE -> not_entailment
    UNCERTAIN -> not_entailment
    """
    if prediction is None:
        return None
    mapping = {
        "TRUE": "entailment",
        "FALSE": "not_entailment",
        "UNCERTAIN": "not_entailment"
    }
    return mapping.get(prediction, "not_entailment")


def get_cached_logified_path(example_id: int) -> Path:
    """Get path to cached logified JSON for an example."""
    return CACHE_DIR / f"example_{example_id}_weighted.json"


def logify_premise(
    text: str,
    example_id: int,
    api_key: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    weights_model: str,
    k_weights: int
) -> Dict[str, Any]:
    """
    Logify a premise and cache the result.

    Returns:
        Dict with logified_structure and metrics (latency, cached).
    """
    cache_path = get_cached_logified_path(example_id)

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
    print(f"    [LOGIFY] Converting example {example_id} to logic...")
    start_time = time.time()

    converter = LogifyConverter(
        api_key=api_key,
        model=LOGIFY_MODEL,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens
    )

    try:
        logic_structure = converter.convert_text_to_logic(text)
    finally:
        converter.close()

    # Save intermediate (non-weighted) JSON
    intermediate_path = CACHE_DIR / f"example_{example_id}.json"
    with open(intermediate_path, 'w', encoding='utf-8') as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    # Assign weights
    print(f"    [WEIGHTS] Assigning weights...")

    # Create a temporary text file for weights.py (it expects a file path)
    temp_text_path = CACHE_DIR / f"example_{example_id}_text.txt"
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
        Dict with prediction, confidence, formula, latency, and any error.
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
    api_key: str,
    data_path: Path = SAMPLE_DATA_PATH,
    query_model: str = "openai/gpt-5-nano",
    weights_model: str = "gpt-4o",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 128000,
    query_max_tokens: int = 64000,
    k_weights: int = 10,
    k_query: int = 20
) -> Dict[str, Any]:
    """
    Run the DocNLI experiment.

    Args:
        api_key: API key for LLM calls
        data_path: Path to sample_100.json
        query_model: Model for query translation
        weights_model: Model for weight assignment (must support logprobs)
        temperature: Sampling temperature
        reasoning_effort: Reasoning effort for reasoning models
        max_tokens: Max tokens for logification
        query_max_tokens: Max tokens for query translation
        k_weights: Top-k chunks for weight assignment
        k_query: Top-k propositions for query translation

    Returns:
        Experiment results dict
    """
    # Ensure directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load sample data
    print(f"Loading sample data from {data_path}...")
    data = load_sample_data(data_path)
    examples = data.get("examples", [])
    metadata = data.get("metadata", {})

    print(f"  Loaded {len(examples)} examples")
    print(f"  Filter criteria: {metadata.get('filter_criteria', {})}")

    # Initialize results
    timestamp = datetime.now().isoformat()
    results = {
        "metadata": {
            "timestamp": timestamp,
            "logify_model": LOGIFY_MODEL,
            "query_model": query_model,
            "weights_model": weights_model,
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "query_max_tokens": query_max_tokens,
            "k_weights": k_weights,
            "k_query": k_query,
            "num_examples": len(examples),
            "data_source": str(data_path),
            "data_metadata": metadata
        },
        "document_metrics": [],
        "results": []
    }

    # Output file (with timestamp)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    # Process examples
    total_evaluated = 0
    total_correct = 0

    for ex in examples:
        example_id = ex.get("example_id")
        original_idx = ex.get("original_idx")
        premise_text = ex.get("premise", "")
        hypothesis_text = ex.get("hypothesis", "")
        ground_truth = ex.get("label")  # "entailment" or "not_entailment"
        premise_word_count = ex.get("premise_word_count", len(premise_text.split()))

        print(f"\n[{example_id + 1}/{len(examples)}] Processing example {example_id} (original_idx: {original_idx})")
        print(f"  Premise: {premise_word_count} words")
        print(f"  Ground truth: {ground_truth}")

        # Skip empty premises
        if not premise_text or not premise_text.strip():
            print(f"  [SKIP] Empty premise text")
            continue

        # Logify premise
        try:
            logify_result = logify_premise(
                text=premise_text,
                example_id=example_id,
                api_key=api_key,
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

        # Query hypothesis
        if logified_structure is not None:
            json_path = str(get_cached_logified_path(example_id))
            query_result = query_hypothesis(
                hypothesis_text=hypothesis_text,
                logified_structure=logified_structure,
                json_path=json_path,
                api_key=api_key,
                model=query_model,
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

        # Map prediction to binary
        prediction_binary = map_prediction_to_binary(prediction)

        # Check correctness
        is_correct = (prediction_binary == ground_truth) if prediction_binary else False
        if prediction_binary:
            total_evaluated += 1
            if is_correct:
                total_correct += 1

        # Store document metrics
        doc_metrics = {
            "example_id": example_id,
            "original_idx": original_idx,
            "premise_length": len(premise_text),
            "premise_word_count": premise_word_count,
            "logify_latency_sec": logify_latency,
            "logify_cached": logify_cached,
            "logify_error": logify_error,
            "query_latency_sec": query_latency
        }
        results["document_metrics"].append(doc_metrics)

        # Store result
        result_entry = {
            "example_id": example_id,
            "original_idx": original_idx,
            "hypothesis_text": hypothesis_text,
            "prediction": prediction,
            "prediction_binary": prediction_binary,
            "confidence": confidence,
            "ground_truth": ground_truth,
            "formula": formula,
            "error": query_error
        }
        results["results"].append(result_entry)

        # Print progress
        status = "✓" if is_correct else ("✗" if prediction_binary else "?")
        print(f"  [{status}] pred={prediction} ({prediction_binary}), gt={ground_truth}, conf={confidence}")
        print(f"  Logify: {logify_latency:.2f}s (cached: {logify_cached}), Query: {query_latency:.2f}s")

        # Save intermediate results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # Final summary
    overall_accuracy = total_correct / total_evaluated if total_evaluated > 0 else 0.0
    results["metadata"]["total_correct"] = total_correct
    results["metadata"]["total_evaluated"] = total_evaluated
    results["metadata"]["overall_accuracy"] = overall_accuracy

    print(f"\n{'='*60}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Examples processed: {len(examples)}")
    print(f"Examples evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Results saved to: {output_path}")

    # Final save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run Logify evaluation on DocNLI dataset",
        epilog="See DESCRIPTION_EXPERIMENT_DOCNLI_LOGIFY.md for details."
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key for LLM calls (default: OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=SAMPLE_DATA_PATH,
        help=f"Path to sample data JSON (default: {SAMPLE_DATA_PATH})"
    )
    parser.add_argument(
        "--query-model",
        default="openai/gpt-5-nano",
        help="Model for query translation (default: openai/gpt-5-nano). Logification uses fixed model: openai/gpt-5.2"
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
        "--limit",
        type=int,
        default=None,
        help="Limit number of examples to process (default: all)"
    )

    args = parser.parse_args()

    # Validate API key
    if not args.api_key:
        print("Error: No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return 1

    # Validate data path
    if not args.data_path.exists():
        print(f"Error: Sample data not found: {args.data_path}")
        print("Run download_sample.py first to download the data.")
        return 1

    try:
        run_experiment(
            api_key=args.api_key,
            data_path=args.data_path,
            query_model=args.query_model,
            weights_model=args.weights_model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            query_max_tokens=args.query_max_tokens,
            k_weights=args.k_weights,
            k_query=args.k_query,
            limit=args.limit
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
