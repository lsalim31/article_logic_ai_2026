#!/usr/bin/env python3
"""
experiment_logify_logicBench.py

Evaluates the Logify neuro-symbolic pipeline on LogicBench (BQA).
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
    PROMPT_TRANSLATION
)
from config import retrieval_config


def get_full_retrieval_config() -> Dict[str, Any]:
    """
    Export ALL configuration values from retrieval_config.py for reproducibility.
    This ensures experiment results contain the complete configuration state.
    """
    return {
        # Models
        "SBERT_MODEL": retrieval_config.SBERT_MODEL,
        "NLI_MODEL": retrieval_config.NLI_MODEL,
        "REASONING_MODEL": retrieval_config.REASONING_MODEL,
        "TRANSLATE_MODEL": retrieval_config.TRANSLATE_MODEL,
        # Token limits
        "MAX_COMPLETION_TOKENS": retrieval_config.MAX_COMPLETION_TOKENS,
        "MAX_TOKENS": retrieval_config.MAX_TOKENS,
        # Reasoning settings
        "REASONING_EFFORT": retrieval_config.REASONING_EFFORT,
        "TEMPERATURE_LOGIC_CONVERTER": retrieval_config.TEMPERATURE_LOGIC_CONVERTER,
        "REASONING_EFFORT_TRANSLATE": retrieval_config.REASONING_EFFORT_TRANSLATE,
        "TEMPERATURE_TRANSLATE": retrieval_config.TEMPERATURE_TRANSLATE,
        # Prompts
        "PROMPT_TRANSLATION": retrieval_config.PROMPT_TRANSLATION,
        "PROMPT_PASS_1": retrieval_config.PROMPT_PASS_1,
        "PROMPT_PASS_2": retrieval_config.PROMPT_PASS_2,
        "PROMPT_EXTRACTION": retrieval_config.PROMPT_EXTRACTION,
        # SBERT settings
        "SBERT_TOP_K": retrieval_config.SBERT_TOP_K,
        "SBERT_MIN_SIMILARITY": retrieval_config.SBERT_MIN_SIMILARITY,
        # NLI settings
        "NLI_ENTAILMENT_THRESHOLD": retrieval_config.NLI_ENTAILMENT_THRESHOLD,
        "NLI_CONTRADICTION_THRESHOLD": retrieval_config.NLI_CONTRADICTION_THRESHOLD,
        "NLI_BATCH_SIZE": retrieval_config.NLI_BATCH_SIZE,
        # Feature flags
        "ENABLE_NLI_FILTERING": retrieval_config.ENABLE_NLI_FILTERING,
        "ENABLE_HYBRID_EMBEDDING": retrieval_config.ENABLE_HYBRID_EMBEDDING,
        "ENABLE_AUTO_NEGATION_CORRECTION": retrieval_config.ENABLE_AUTO_NEGATION_CORRECTION,
        "ENABLE_NEGATION_WARNINGS": retrieval_config.ENABLE_NEGATION_WARNINGS,
        # Confidence thresholds
        "CONFIDENCE_THRESHOLD_TRUE": retrieval_config.CONFIDENCE_THRESHOLD_TRUE,
        "MIN_PROPOSITION_WEIGHT": retrieval_config.MIN_PROPOSIT3ION_WEIGHT,
        # Query expansion
        "ON_EXPAND_QUERY_SYN": retrieval_config.ON_EXPAND_QUERY_SYN,
        "MAX_SYNONYMS": retrieval_config.MAX_SYNONYMS,
        # Adaptive voting
        "TRIGGER_QUERY": retrieval_config.TRIGGER_QUERY,
        "ADDITIONAL_LLM_QUERY": retrieval_config.ADDITIONAL_LLM_QUERY,
        # Subset/clustering settings
        "SUBSET_TOP_K_RETRIEVAL": retrieval_config.SUBSET_TOP_K_RETRIEVAL,
        "SUBSET_NUM_CLUSTERS": retrieval_config.SUBSET_NUM_CLUSTERS,
        "SUBSET_TOP_PER_CLUSTER": retrieval_config.SUBSET_TOP_PER_CLUSTER,
        "SUBSET_ENTAILMENT_THRESHOLD": retrieval_config.SUBSET_ENTAILMENT_THRESHOLD,
        "MAX_VARIANTS": retrieval_config.MAX_VARIANTS,
        # Logify settings
        "USE_OPENIE": retrieval_config.USE_OPENIE,
        "HARDNESS_CONSTANT": retrieval_config.HARDNESS_CONSTANT,
        "USE_ENRICHMENT": retrieval_config.USE_ENRICHMENT,
        "USE_SUBSET": retrieval_config.USE_SUBSET,
        "DIRECT_RETRIEVAL_MULTIPLIER": retrieval_config.DIRECT_RETRIEVAL_MULTIPLIER,
        "DEFAULT_MIN_WORDS": retrieval_config.DEFAULT_MIN_WORDS,
        "DEFAULT_MAX_WORDS": retrieval_config.DEFAULT_MAX_WORDS,
    }


# LogicBench data is at baseline_logiclm_plus/data/
LOGICBENCH_DATA_DIR = _code_dir / "baseline_logiclm_plus" / "data" / "LogicBench(Eval)" / "BQA"
CACHE_DIR = _script_dir / "cache"
RESULTS_DIR = _script_dir / "results_logify_LOGICBENCH"
DEFAULT_DATASET_PATH = LOGICBENCH_DATA_DIR / "propositional_logic" / "modus_tollens" / "data_instances.json"
DEFAULT_DOC_IDS = [1]

@dataclass
class QueryDebugResult:
    doc_id: str  # Changed to str for LogicBench IDs like "propositional_logic_modus_tollens_1"
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
    # Translation/NLI confidence and voting fields
    nli_confidence: Optional[float] = None
    sbert_confidence: Optional[float] = None
    voting_triggered: bool = False
    voting_confidence: Optional[float] = None
    vote_counts: Optional[Dict[str, int]] = None


def load_dataset(dataset_path: str) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_ground_truth_label(choice: str) -> str:
    """Map LogicBench yes/no to solver output format."""
    mapping = {
        "yes": "TRUE",
        "no": "FALSE",
    }
    return mapping.get(choice, "UNCERTAIN")


def get_cached_logified_path(doc_id: str) -> Path:
    """Return cache path for a sample's logified structure."""
    safe_id = str(doc_id).replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"doc_{safe_id}_weighted.json"


def get_intermediate_logified_path(doc_id: str) -> Path:
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
    doc_id: str,
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

    from from_text_to_logic.check_logic_structure import enrich_logic_structure

    intermediate_path = get_intermediate_logified_path(doc_id)
    with open(intermediate_path, "w", encoding="utf-8") as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    # Create temp text file
    temp_text_path = CACHE_DIR / f"doc_{doc_id}_text.txt"
    with open(temp_text_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Enrich logic structure
    enrich_logic_structure(
        logified_path=str(intermediate_path),
        source_path=str(temp_text_path),
        output_path=str(intermediate_path),
        verbose=verbose,
    )

    if verbose:
        print("[WEIGHTS] Assigning weights...")

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
    doc_id: str,
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
    verbose = True,
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

        # Extract NLI/voting metadata from translation result
        nli_confidence = translation_result.get("confidence")
        sbert_confidence = translation_result.get("sbert_confidence")
        voting_triggered = translation_result.get("voting_triggered", False)
        voting_confidence = translation_result.get("voting_confidence")
        vote_counts = translation_result.get("vote_counts")

        if formula == "NONE":
            prediction = "NOT MENTIONED"
            is_correct = prediction == ground_truth
            return QueryDebugResult(
                doc_id=doc_id,
                hypothesis_key=hypothesis_key,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                prediction=prediction,
                confidence=1,
                formula=formula,
                query_mode=query_mode,
                explanation="No matching proposition for hypothesis",
                error=None,
                error_type=None,
                amount_evidence=amount_evidence,
                is_correct=is_correct,
                query_latency_sec=time.time() - start_time,
                nli_confidence=nli_confidence,
                sbert_confidence=sbert_confidence,
                voting_triggered=voting_triggered,
                voting_confidence=voting_confidence,
                vote_counts=vote_counts,
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
                error="ERROR: LLM failed to generate a valid formula.",
                error_type="translate_error",
                amount_evidence=amount_evidence,
                is_correct=False,
                query_latency_sec=time.time() - start_time,
                nli_confidence=nli_confidence,
                sbert_confidence=sbert_confidence,
                voting_triggered=voting_triggered,
                voting_confidence=voting_confidence,
                vote_counts=vote_counts,
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
            nli_confidence=nli_confidence,
            sbert_confidence=sbert_confidence,
            voting_triggered=voting_triggered,
            voting_confidence=voting_confidence,
            vote_counts=vote_counts,
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
            "num_pairs": num_hypotheses,
        },
        "retrieval_config": get_full_retrieval_config(),
        "document_metrics": [],
        "results": [],
    }


def save_json_results(results_payload: Dict[str, Any], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)


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
    samples = dataset.get("samples", [])
    logic_type = dataset.get("type", "unknown")
    axiom = dataset.get("axiom", "unknown")

    # Filter by doc_ids if specified (matches sample["id"])
    if doc_ids is not None:
        doc_id_set = set(doc_ids)
        samples = [s for s in samples if s.get("id") in doc_id_set]

    print(f"Processing {len(samples)} samples from {logic_type}/{axiom}")

    if not samples:
        raise ValueError(
            f"No matching samples found. Requested doc_ids={doc_ids}"
        )

    # Count total qa_pairs
    total_qa_pairs = sum(len(s.get("qa_pairs", [])) for s in samples)

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
        doc_ids=doc_ids if doc_ids else [s.get("id") for s in samples],
        num_documents=len(samples),
        num_hypotheses=total_qa_pairs,
    )

    results: List[QueryDebugResult] = []

    total_correct = 0
    total_evaluated = 0
    total_errors = 0

    for doc_idx, sample in enumerate(samples):
        sample_id = sample.get("id", doc_idx)
        # Create unique doc_id combining logic_type, axiom, and sample id
        current_doc_id = f"{logic_type}_{axiom}_{sample_id}"
        text = sample.get("context", "")
        qa_pairs = sample.get("qa_pairs", [])

        if verbose:
            print(f"\n[{doc_idx + 1}/{len(samples)}] [DOC {current_doc_id}] Text length: {len(text)} chars")

        if not text or not text.strip():
            if verbose:
                print(f"[SKIP] Empty context for doc_id={current_doc_id}")
            results_payload["document_metrics"].append(
                {
                    "doc_id": current_doc_id,
                    "text_length": len(text),
                    "logify_latency_sec": 0.0,
                    "logify_cached": False,
                    "logify_error": "Empty context",
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

        for qa_idx, qa in enumerate(qa_pairs):
            key = f"q{qa_idx}"
            if hypothesis_key and key != hypothesis_key:
                continue

            hypothesis_text = qa.get("question", "")
            choice = qa.get("answer", "")
            ground_truth = get_ground_truth_label(choice)
            amount_evidence = 0  # LogicBench has no evidence spans

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
                if result.nli_confidence is not None:
                    print(f"    nli_confidence: {result.nli_confidence:.2f}")
                if result.sbert_confidence is not None:
                    print(f"    sbert_confidence: {result.sbert_confidence:.2f}")
                if result.voting_triggered:
                    print(f"    voting: TRIGGERED (confidence: {result.voting_confidence:.2f}, counts: {result.vote_counts})")
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
    print(f"Documents processed: {len(samples)}")
    print(f"Pairs evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Total errors: {total_errors}")
    print(f"JSON results saved to: {output_path}")

    return results, results_payload, output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Logify on LogicBench (BQA)")
    parser.add_argument(
        "--dataset-path",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to LogicBench data_instances.json file",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key for LLM calls (default: OPENROUTER_API_KEY env var)",
    )

    # Filtering
    parser.add_argument("--doc-id", type=int, default=None, help="Single sample ID to evaluate")
    parser.add_argument(
        "--doc-ids",
        type=str,
        default=None,
        help="Comma-separated list of sample IDs to process",
    )
    parser.add_argument("--hypothesis-key", default=None, help="Single question key to evaluate (e.g., q0, q1)")

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

        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
