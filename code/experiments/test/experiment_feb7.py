#!/usr/bin/env python3
"""
experiment code

Debug-focused + metrics-rich experiment runner for ContractNLI-style JSON files.

Simple folder structure in this directory:
- dataset/   -> dataset files (train/dev/test)
- cache/          -> cached logified files
- results/        -> experiment output JSON and optional debug reports

Usage:
    python experiment_feb7.py --dataset-path dataset/dev.json
    python experiment_feb7.py --dataset-path dataset/data_test.json --doc-id 3 --hypothesis-key nda-1
    python experiment_feb7.py --dataset-path dataset/dev.json --doc-ids 3,7,9 --verbose

Environment:
    OPENROUTER_API_KEY: API key (used if --api-key not provided)
"""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

DATASET_DIR = _script_dir / "dataset"
CACHE_DIR = _script_dir / "cache"
RESULTS_DIR = _script_dir / "results"
DEFAULT_DATASET_PATH = DATASET_DIR / "data_test.json"
DEFAULT_DOC_IDS = 1

@dataclass
class QueryDebugResult:
    doc_id: int
    hypothesis_key: str
    hypothesis_text: str
    ground_truth: str
    prediction: Optional[str]
    confidence: Optional[float]
    formula: Optional[str]
    query_mode: Optional[str]
    explanation: Optional[str]
    error: Optional[str]
    error_type: Optional[str]
    amount_evidence: int
    is_correct: bool
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


def get_intermediate_logified_path(doc_id: int) -> Path:
    return CACHE_DIR / f"doc_{doc_id}.json"


def parse_doc_ids(doc_id: Optional[int], doc_ids_csv: Optional[str]) -> Optional[List[int]]:
    if doc_id is not None:
        return [doc_id]

    if doc_ids_csv:
        parsed = []
        for chunk in doc_ids_csv.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            parsed.append(int(chunk))
        return parsed

    return None


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
            "logify_error": None,
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

    intermediate_path = get_intermediate_logified_path(doc_id)
    with open(intermediate_path, "w", encoding="utf-8") as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    if verbose:
        print("[WEIGHTS] Assigning weights...")
    temp_text_path = CACHE_DIR / f"doc_{doc_id}_text.txt"
    with open(temp_text_path, "w", encoding="utf-8") as f:
        f.write(text)

    try:
        assign_weights(
            pathfile=str(temp_text_path),
            json_path=str(intermediate_path),
            hardness_criterion=HARDNESS_CONSTANT,
            k=k_weights,
            verbose=verbose,
        )

        with open(cache_path, "r", encoding="utf-8") as f:
            logified_structure = json.load(f)

        logify_latency = time.time() - start_time
        if verbose:
            print(f"[LOGIFY] Completed in {logify_latency:.2f}s")

        return {
            "logified_structure": logified_structure,
            "logify_latency_sec": logify_latency,
            "logify_cached": False,
            "logify_error": None,
        }
    except Exception as exc:
        return {
            "logified_structure": None,
            "logify_latency_sec": time.time() - start_time,
            "logify_cached": False,
            "logify_error": str(exc),
        }
    finally:
        temp_text_path.unlink(missing_ok=True)


def query_hypothesis(
    doc_id: int,
    hypothesis_key: str,
    hypothesis_text: str,
    logified_structure: Dict[str, Any],
    json_path: str,
    api_key: str,
    model: str,
    temperature: float,
    reasoning_effort: str,
    query_max_tokens: int,
    k_query: int,
    ground_truth: str,
    amount_evidence: int,
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
            max_tokens=query_max_tokens,
            k=k_query,
            verbose=verbose,
        )

        query_mode = translation_result.get("query_mode", "entailment")
        formula = translation_result.get("formula")

        if formula == "NONE":
            prediction = "UNCERTAIN"
            is_correct = prediction == ground_truth
            return QueryDebugResult(
                doc_id=doc_id,
                hypothesis_key=hypothesis_key,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                prediction=prediction,
                confidence=0.5,
                formula=formula,
                query_mode=query_mode,
                explanation="No matching proposition for hypothesis",
                error=None,
                error_type=None,
                amount_evidence=amount_evidence,
                is_correct=is_correct,
                query_latency_sec=time.time() - start_time,
            )

        if not formula or formula == "ERROR":
            return QueryDebugResult(
                doc_id=doc_id,
                hypothesis_key=hypothesis_key,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                prediction=None,
                confidence=None,
                formula=formula,
                query_mode=query_mode,
                explanation=None,
                error="ERROR: LLM failed to generate a valid formula",
                error_type="translate_error",
                amount_evidence=amount_evidence,
                is_correct=False,
                query_latency_sec=time.time() - start_time,
            )

        solver = LogicSolver(logified_structure)
        if query_mode == "consistency":
            solver_result = solver.check_consistency(formula)
        else:
            solver_result = solver.query(formula)

        prediction = solver_result.answer
        is_correct = prediction == ground_truth if prediction else False

        error = None
        error_type = None
        if solver_result.explanation and "Error" in solver_result.explanation:
            error = solver_result.explanation
            error_type = "solver_error"

        return QueryDebugResult(
            doc_id=doc_id,
            hypothesis_key=hypothesis_key,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=prediction,
            confidence=solver_result.confidence,
            formula=formula,
            query_mode=query_mode,
            explanation=solver_result.explanation,
            error=error,
            error_type=error_type,
            amount_evidence=amount_evidence,
            is_correct=is_correct,
            query_latency_sec=time.time() - start_time,
        )

    except Exception as exc:
        return QueryDebugResult(
            doc_id=doc_id,
            hypothesis_key=hypothesis_key,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=None,
            confidence=None,
            formula=None,
            query_mode=None,
            explanation=None,
            error=str(exc),
            error_type="runtime_error",
            amount_evidence=amount_evidence,
            is_correct=False,
            query_latency_sec=time.time() - start_time,
        )


def initialize_results_payload(
    dataset_path: str,
    query_model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    query_max_tokens: int,
    k_weights: int,
    k_query: int,
    doc_ids: List[int],
    num_documents: int,
    num_hypotheses: int,
) -> Dict[str, Any]:
    timestamp = datetime.now().isoformat()
    return {
        "metadata": {
            "timestamp": timestamp,
            "dataset_path": str(dataset_path),
            "logify_model": REASONING_MODEL,
            "query_model": query_model,
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "query_max_tokens": query_max_tokens,
            "k_weights": k_weights,
            "k_query": k_query,
            "doc_ids": doc_ids,
            "num_documents": num_documents,
            "num_hypotheses": num_hypotheses,
            "num_pairs": num_documents * num_hypotheses,
        },
        "document_metrics": [],
        "results": [],
    }


def save_json_results(results_payload: Dict[str, Any], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)


def write_experiment_debug_report(
    results: List[QueryDebugResult],
    output_name: str = "debug_report.md",
    include_raw: bool = True,
) -> Path:
    output_path = RESULTS_DIR / output_name

    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    errors = sum(1 for r in results if r.error)
    incorrect = total - correct - errors
    avg_latency = sum(r.query_latency_sec for r in results) / total if total else 0.0

    lines: List[str] = []
    lines.append("# Experiment Debug Report\n\n")
    lines.append("## Summary\n")
    lines.append(f"- Total: {total}\n")
    lines.append(f"- Correct: {correct}\n")
    lines.append(f"- Incorrect: {incorrect}\n")
    lines.append(f"- Errors: {errors}\n")
    lines.append(f"- Avg latency (sec): {avg_latency:.3f}\n")

    lines.append("\n## Detailed Results\n")
    for r in results:
        lines.append(f"\n### Doc {r.doc_id} / {r.hypothesis_key}\n")
        lines.append(f"- Hypothesis: {r.hypothesis_text}\n")
        lines.append(f"- Ground Truth: {r.ground_truth}\n")
        lines.append(f"- Prediction: {r.prediction}\n")
        lines.append(f"- Correct: {r.is_correct}\n")
        lines.append(f"- Confidence: {r.confidence}\n")
        lines.append(f"- Formula: {r.formula}\n")
        lines.append(f"- Query Mode: {r.query_mode}\n")
        lines.append(f"- Evidence Spans Count: {r.amount_evidence}\n")
        lines.append(f"- Explanation: {r.explanation}\n")
        lines.append(f"- Error: {r.error}\n")
        lines.append(f"- Error Type: {r.error_type}\n")
        lines.append(f"- Latency (sec): {r.query_latency_sec:.3f}\n")

        if include_raw:
            lines.append("\n**Raw Fields**\n")
            raw = asdict(r)
            for k, v in raw.items():
                lines.append(f"- {k}: {v}\n")

        lines.append("\n---\n")

    output_path.write_text("".join(lines), encoding="utf-8")
    print(f"[DEBUG REPORT] Saved to: {output_path}")
    return output_path


def run_debug_experiment(
    dataset_path: str,
    api_key: str,
    hypothesis_key: Optional[str],
    query_model: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    query_max_tokens: int,
    k_weights: int,
    k_query: int,
    verbose: bool = True,
    doc_ids: Optional[List[int]] = None,
) -> Tuple[List[QueryDebugResult], Dict[str, Any], Path]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(dataset_path)
    documents = dataset.get("documents", [])
    labels = dataset.get("labels", {})

    if doc_ids is None:
        doc_ids = DEFAULT_DOC_IDS
    doc_id_set = set(doc_ids)
    documents = [doc for doc in documents if doc.get("id") in doc_id_set]

    print(f"Processing {len(documents)} documents with IDs: {doc_ids}")

    if not documents:
        raise ValueError(
            f"No matching documents found for doc filter. Requested doc_ids={doc_ids}"
        )

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    results_payload = initialize_results_payload(
        dataset_path=dataset_path,
        query_model=query_model,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens,
        query_max_tokens=query_max_tokens,
        k_weights=k_weights,
        k_query=k_query,
        doc_ids=doc_ids,
        num_documents=len(documents),
        num_hypotheses=len(labels),
    )

    results: List[QueryDebugResult] = []

    total_correct = 0
    total_evaluated = 0
    total_errors = 0

    for doc_idx, doc in enumerate(documents):
        current_doc_id = doc.get("id", doc_idx)
        text = doc.get("text", "")
        annotations = doc.get("annotation_sets", [{}])[0].get("annotations", {})

        if verbose:
            print(f"\n[{doc_idx + 1}/{len(documents)}] [DOC {current_doc_id}] Text length: {len(text)} chars")

        if not text or not text.strip():
            if verbose:
                print(f"[SKIP] Empty document text for doc_id={current_doc_id}")
            results_payload["document_metrics"].append(
                {
                    "doc_id": current_doc_id,
                    "text_length": len(text),
                    "logify_latency_sec": 0.0,
                    "logify_cached": False,
                    "logify_error": "Empty document text",
                    "query_latency_total_sec": 0.0,
                    "doc_correct": 0,
                    "doc_total": 0,
                    "doc_accuracy": 0.0,
                }
            )
            save_json_results(results_payload, output_path)
            continue

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
        logify_error = logify_result.get("logify_error")

        doc_correct = 0
        doc_total = 0
        query_latency_total = 0.0

        for key, label_info in labels.items():
            if hypothesis_key and key != hypothesis_key:
                continue

            hypothesis_text = label_info.get("hypothesis", "")
            annotation = annotations.get(key, {})
            choice = annotation.get("choice", "NotMentioned")
            evidence_spans = annotation.get("spans", [])

            ground_truth = get_ground_truth_label(choice)
            amount_evidence = len(evidence_spans)

            if logified_structure is None:
                result = QueryDebugResult(
                    doc_id=current_doc_id,
                    hypothesis_key=key,
                    hypothesis_text=hypothesis_text,
                    ground_truth=ground_truth,
                    prediction=None,
                    confidence=None,
                    formula=None,
                    query_mode=None,
                    explanation=None,
                    error=logify_error or "Logification failed",
                    error_type="logify_error",
                    amount_evidence=amount_evidence,
                    is_correct=False,
                    query_latency_sec=0.0,
                )
            else:
                result = query_hypothesis(
                    doc_id=current_doc_id,
                    hypothesis_key=key,
                    hypothesis_text=hypothesis_text,
                    logified_structure=logified_structure,
                    json_path=json_path,
                    api_key=api_key,
                    model=query_model,
                    temperature=temperature,
                    reasoning_effort=reasoning_effort,
                    query_max_tokens=query_max_tokens,
                    k_query=k_query,
                    ground_truth=ground_truth,
                    amount_evidence=amount_evidence,
                    verbose=verbose,
                )

            results.append(result)
            results_payload["results"].append(asdict(result))
            query_latency_total += result.query_latency_sec

            if result.prediction is not None:
                doc_total += 1
                total_evaluated += 1
                if result.is_correct:
                    doc_correct += 1
                    total_correct += 1

            if result.error:
                total_errors += 1

            if verbose:
                status = "✓" if result.is_correct else ("?" if result.prediction is None else "✗")
                print(f"[{status}] {key}: pred={result.prediction} gt={ground_truth} conf={result.confidence}")
                if result.formula:
                    print(f"    formula: {result.formula}")
                if result.query_mode:
                    print(f"    mode: {result.query_mode}")
                if result.explanation:
                    print(f"    explanation: {result.explanation}")
                if result.error:
                    print(f"    error ({result.error_type}): {result.error}")
                print(f"    latency: {result.query_latency_sec:.2f}s")

        doc_accuracy = doc_correct / doc_total if doc_total > 0 else 0.0
        doc_metrics = {
            "doc_id": current_doc_id,
            "text_length": len(text),
            "logify_latency_sec": logify_result["logify_latency_sec"],
            "logify_cached": logify_result["logify_cached"],
            "logify_error": logify_error,
            "query_latency_total_sec": query_latency_total,
            "doc_correct": doc_correct,
            "doc_total": doc_total,
            "doc_accuracy": doc_accuracy,
        }
        results_payload["document_metrics"].append(doc_metrics)

        if verbose:
            print(f"  Document accuracy: {doc_correct}/{doc_total} = {doc_accuracy:.2%}")
            print(f"  Logify latency: {logify_result['logify_latency_sec']:.2f}s (cached: {logify_result['logify_cached']})")
            print(f"  Query latency total: {query_latency_total:.2f}s")

        save_json_results(results_payload, output_path)

    overall_accuracy = total_correct / total_evaluated if total_evaluated > 0 else 0.0
    results_payload["metadata"]["total_correct"] = total_correct
    results_payload["metadata"]["total_evaluated"] = total_evaluated
    results_payload["metadata"]["overall_accuracy"] = overall_accuracy
    results_payload["metadata"]["total_errors"] = total_errors
    results_payload["metadata"]["hypothesis_filter"] = hypothesis_key

    save_json_results(results_payload, output_path)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Documents processed: {len(documents)}")
    print(f"Pairs evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Total errors: {total_errors}")
    print(f"JSON results saved to: {output_path}")

    return results, results_payload, output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug + metrics-rich experiment runner")
    parser.add_argument(
        "--dataset-path",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to ContractNLI-style JSON (default: contract-nli/dev.json)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key for LLM calls (default: OPENROUTER_API_KEY env var)",
    )

    # Filtering
    parser.add_argument("--doc-id", type=int, default=None, help="Single document ID to evaluate (overrides --doc-ids)")
    parser.add_argument(
        "--doc-ids",
        type=str,
        default=None,
        help="Comma-separated list of document IDs to process (default: predefined 20-doc list)",
    )
    parser.add_argument("--hypothesis-key", default=None, help="Single hypothesis key to evaluate")

    # Models + decoding
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
        help="Max tokens for logification",
    )
    parser.add_argument(
        "--query-max-tokens",
        type=int,
        default=MAX_TOKENS,
        help="Max tokens for query translation",
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
        help="Top-k propositions for query translation",
    )

    # Output controls
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debugging output",
    )
    parser.add_argument(
        "--debug-report",
        action="store_true",
        help="Write markdown debug report",
    )
    parser.add_argument(
        "--debug-report-name",
        default="debug_report.md",
        help="Filename for markdown debug report",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Include full raw fields in markdown debug report",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return 1

    if not Path(args.dataset_path).exists():
        print(f"Error: Dataset not found: {args.dataset_path}")
        return 1

    try:
        selected_doc_ids = parse_doc_ids(args.doc_id, args.doc_ids)

        results, _, _ = run_debug_experiment(
            dataset_path=args.dataset_path,
            api_key=args.api_key,
            hypothesis_key=args.hypothesis_key,
            query_model=args.query_model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            query_max_tokens=args.query_max_tokens,
            k_weights=args.k_weights,
            k_query=args.k_query,
            verbose=args.verbose,
            doc_ids=selected_doc_ids,
        )

        if args.debug_report:
            write_experiment_debug_report(
                results=results,
                output_name=args.debug_report_name,
                include_raw=args.include_raw,
            )

        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
