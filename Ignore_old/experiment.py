#!/usr/bin/env python3
"""
experiment.py

Debug-focused experiment runner for ContractNLI-style JSON files.

Usage:
    python experiment.py --dataset-path contractnli_test.json
    python experiment.py --dataset-path contractnli_test.json --doc-id 1 --hypothesis-key test-3
    
    
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from from_text_to_logic.logify import LogifyConverter
from from_text_to_logic.weights import assign_weights
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver
from config.retrieval_config import (
    HARDNESS_CONSTANT,
    MAX_TOKENS,
    REASONING_EFFORT,
    REASONING_MODEL,
    SBERT_TOP_K,
    TEMPERATURE_LOGIC_CONVERTER,
    TRANSLATE_MODEL,
)

CACHE_DIR = _script_dir / "cache"


@dataclass
class QueryDebugResult:
    hypothesis_key: str
    hypothesis_text: str
    ground_truth: str
    prediction: Optional[str]
    confidence: Optional[float]
    formula: Optional[str]
    query_mode: Optional[str]
    explanation: Optional[str]
    error: Optional[str]
    query_latency_sec: float


def load_dataset(dataset_path: str) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_ground_truth_label(choice: str) -> str:
    mapping = {
        "Entailment": "TRUE",
        "Contradiction": "FALSE",
        "NotMentioned": "UNCERTAIN",
    }
    return mapping.get(choice, "UNCERTAIN")


def get_cached_logified_path(doc_id: int) -> Path:
    return CACHE_DIR / f"doc_{doc_id}_weighted.json"


def logify_document(
    text: str,
    doc_id: int,
    api_key: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    k_weights: int,
    verbose: bool = True,
) -> Dict[str, Any]:
    cache_path = get_cached_logified_path(doc_id)
    if cache_path.exists():
        if verbose:
            print(f"[CACHE HIT] {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            logified_structure = json.load(f)
        return {
            "logified_structure": logified_structure,
            "logify_latency_sec": 0.0,
            "logify_cached": True,
        }

    if verbose:
        print("[LOGIFY] Converting document to logic...")
    start_time = time.time()

    converter = LogifyConverter(
        api_key=api_key,
        model=REASONING_MODEL,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens,
    )

    try:
        logic_structure = converter.convert_text_to_logic(text)
    finally:
        converter.close()

    intermediate_path = CACHE_DIR / f"doc_{doc_id}.json"
    with open(intermediate_path, "w", encoding="utf-8") as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    if verbose:
        print("[WEIGHTS] Assigning weights...")
    temp_text_path = CACHE_DIR / f"doc_{doc_id}_text.txt"
    with open(temp_text_path, "w", encoding="utf-8") as f:
        f.write(text)

    assign_weights(
        pathfile=str(temp_text_path),
        json_path=str(intermediate_path),
        hardness_criterion=HARDNESS_CONSTANT,
        k=k_weights,
        verbose=verbose,
    )

    with open(cache_path, "r", encoding="utf-8") as f:
        logified_structure = json.load(f)

    temp_text_path.unlink(missing_ok=True)

    logify_latency = time.time() - start_time
    if verbose:
        print(f"[LOGIFY] Completed in {logify_latency:.2f}s")

    return {
        "logified_structure": logified_structure,
        "logify_latency_sec": logify_latency,
        "logify_cached": False,
    }


def query_hypothesis(
    hypothesis_key: str,
    hypothesis_text: str,
    logified_structure: Dict[str, Any],
    json_path: str,
    api_key: str,
    model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    k_query: int,
    ground_truth: str,
    verbose: bool,
) -> QueryDebugResult:
    start_time = time.time()
    try:
        translation_result = translate_query(
            query=hypothesis_text,
            json_path=json_path,
            api_key=api_key,
            model=model,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            k=k_query,
            verbose=verbose,
        )
        query_mode = translation_result.get("query_mode", "entailment")
        
        formula = translation_result.get("formula")
        
        if formula == "NONE":
            return QueryDebugResult(
                hypothesis_key=hypothesis_key,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                prediction="UNCERTAIN",
                confidence=0.5,
                formula=formula,
                query_mode=query_mode,
                explanation="No matching proposition for hypothesis",
                error=None,
                query_latency_sec=time.time() - start_time,
            )
    
        if formula == "ERROR":
            return QueryDebugResult(
                hypothesis_key=hypothesis_key,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                prediction=None,
                confidence=None,
                formula=formula,
                query_mode=query_mode,
                explanation=None,
                error="LLM failed to generate a valid formula",
                query_latency_sec=time.time() - start_time,
            )



        solver = LogicSolver(logified_structure)
        if query_mode == "consistency":
            solver_result = solver.check_consistency(formula)
        else:
            solver_result = solver.query(formula)

        return QueryDebugResult(
            hypothesis_key=hypothesis_key,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=solver_result.answer,
            confidence=solver_result.confidence,
            formula=formula,
            query_mode=query_mode,
            explanation=solver_result.explanation,
            error=None,
            query_latency_sec=time.time() - start_time,
        )
    except Exception as exc:
        return QueryDebugResult(
            hypothesis_key=hypothesis_key,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=None,
            confidence=None,
            formula=None,
            query_mode=None,
            explanation=None,
            error=str(exc),
            query_latency_sec=time.time() - start_time,
        )




def run_debug_experiment(
    dataset_path: str,
    api_key: str,
    doc_id: Optional[int],
    hypothesis_key: Optional[str],
    query_model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    k_weights: int,
    k_query: int,
    verbose: bool = True,
) -> List[QueryDebugResult]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(dataset_path)
    documents = dataset.get("documents", [])
    labels = dataset.get("labels", {})

    if doc_id is not None:
        documents = [doc for doc in documents if doc.get("id") == doc_id]

    if not documents:
        raise ValueError("No matching document found for the provided doc_id.")

    results: List[QueryDebugResult] = []

    for doc in documents:
        current_doc_id = doc.get("id")
        text = doc.get("text", "")
        annotations = doc.get("annotation_sets", [{}])[0].get("annotations", {})

        if verbose:
            print(f"\n[DOC {current_doc_id}] Text length: {len(text)} chars")

        logify_result = logify_document(
            text=text,
            doc_id=current_doc_id,
            api_key=api_key,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            k_weights=k_weights,
            verbose=verbose,
        )

        logified_structure = logify_result["logified_structure"]
        json_path = str(get_cached_logified_path(current_doc_id))

        for key, label_info in labels.items():
            if hypothesis_key and key != hypothesis_key:
                continue

            hypothesis_text = label_info.get("hypothesis", "")
            annotation = annotations.get(key, {})
            choice = annotation.get("choice", "NotMentioned")
            ground_truth = get_ground_truth_label(choice)

            result = query_hypothesis(
                hypothesis_key=key,
                hypothesis_text=hypothesis_text,
                logified_structure=logified_structure,
                json_path=json_path,
                api_key=api_key,
                model=query_model,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
                max_tokens=max_tokens,
                k_query=k_query,
                ground_truth=ground_truth,
                verbose=verbose,
            )
            results.append(result)

            if verbose:
                status = "✓" if result.prediction == ground_truth else "✗"
                print(f"[{status}] {key}: {result.prediction} (gt={ground_truth})")
                if result.formula:
                    print(f"    formula: {result.formula}")
                if result.query_mode:
                    print(f"    mode: {result.query_mode}")
                if result.explanation:
                    print(f"    explanation: {result.explanation}")
                if result.error:
                    print(f"    query error: {result.error}")
                print(f"    latency: {result.query_latency_sec:.2f}s")

    return results

def write_experiment_debug_report(
    results: List[QueryDebugResult],
    output_name: str = "debug_report.md",
    include_raw: bool = True,
) -> Path:
    """
    Write a markdown/text debug report to _script_dir with all outcomes and details.

    Contents:
    - Summary counts (total, correct, incorrect, errors)
    - Per-query details (hypothesis, formula, mode, prediction, confidence, explanation, error, latency)
    - Optional raw fields for deeper debugging
    """
    output_path = _script_dir / output_name

    total = len(results)
    correct = sum(1 for r in results if r.prediction == r.ground_truth)
    errors = sum(1 for r in results if r.error)
    incorrect = total - correct - errors

    lines = []
    lines.append("# Experiment Debug Report\n")
    lines.append("## Summary\n")
    lines.append(f"- Total: {total}\n")
    lines.append(f"- Correct: {correct}\n")
    lines.append(f"- Incorrect: {incorrect}\n")
    lines.append(f"- Errors: {errors}\n")

    lines.append("\n## Detailed Results\n")
    for r in results:
        lines.append(f"### {r.hypothesis_key}\n")
        lines.append(f"- Hypothesis: {r.hypothesis_text}\n")
        lines.append(f"- Ground Truth: {r.ground_truth}\n")
        lines.append(f"- Prediction: {r.prediction}\n")
        lines.append(f"- Confidence: {r.confidence}\n")
        lines.append(f"- Formula: {r.formula}\n")
        lines.append(f"- Query Mode: {r.query_mode}\n")
        lines.append(f"- Explanation: {r.explanation}\n")
        lines.append(f"- Error: {r.error}\n")
        lines.append(f"- Latency (sec): {r.query_latency_sec:.3f}\n")

        if include_raw:
            lines.append("\n**Raw Fields**\n")
            lines.append(f"- hypothesis_key: {r.hypothesis_key}\n")
            lines.append(f"- formula: {r.formula}\n")
            lines.append(f"- query_mode: {r.query_mode}\n")
            lines.append(f"- error: {r.error}\n")

        lines.append("\n---\n")

    output_path.write_text("".join(lines), encoding="utf-8")
    print(f"[DEBUG REPORT] Saved to: {output_path}")
    return output_path
    


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug ContractNLI-style experiments")
    parser.add_argument("--dataset-path", required=True, help="Path to ContractNLI-style JSON")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key for LLM calls (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument("--doc-id", type=int, default=None, help="Document ID to evaluate")
    parser.add_argument("--hypothesis-key", default=None, help="Hypothesis key to evaluate")
    parser.add_argument(
        "--query-model",
        default=TRANSLATE_MODEL,
        help="Model for query translation",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=TEMPERATURE_LOGIC_CONVERTER,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=REASONING_EFFORT,
        choices=["none", "low", "medium", "high", "xhigh"],
        help="Reasoning effort",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=MAX_TOKENS,
        help="Max tokens for logification/translation",
    )
    parser.add_argument(
        "--k-weights",
        type=int,
        default=10,
        help="Top-k chunks for weight assignment",
    )
    parser.add_argument(
        "--k-query",
        type=int,
        default=SBERT_TOP_K,
        help="Top-k propositions for query",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debugging output",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return 1

    if not Path(args.dataset_path).exists():
        print(f"Error: Dataset not found: {args.dataset_path}")
        return 1

    try:
        results = run_debug_experiment(
            dataset_path=args.dataset_path,
            api_key=args.api_key,
            doc_id=args.doc_id,
            hypothesis_key=args.hypothesis_key,
            query_model=args.query_model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            k_weights=args.k_weights,
            k_query=args.k_query,
            verbose=args.verbose,
        )
        
        write_experiment_debug_report(results)
        
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
