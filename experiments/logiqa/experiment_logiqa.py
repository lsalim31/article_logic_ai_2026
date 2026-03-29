#!/usr/bin/env python3
"""
experiment_logiqa.py

Experiment: Evaluate Logify on the LogiQA dataset (binary yes/no format).

This script runs the neuro-symbolic reasoning pipeline on LogiQA's
context + qa_pairs format (converted from multiple choice to binary yes/no).

Usage:
    python experiment_logiqa.py --api-key $OPENROUTER_API_KEY
    python experiment_logiqa.py --api-key $OPENROUTER_API_KEY --doc-id 1
    python experiment_logiqa.py --api-key $OPENROUTER_API_KEY --limit 5
    python experiment_logiqa.py --api-key $OPENROUTER_API_KEY --verbose
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
_repo_root = _script_dir.parent.parent
_code_dir = _repo_root / "code"

for p in (_repo_root, _code_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from from_text_to_logic.logify import LogifyConverter
from from_text_to_logic.weights import assign_weights
from interface_with_user.translate import translate_query
from from_text_to_logic.check_logic_structure import enrich_logic_structure
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


# Directory configuration
CACHE_DIR = _script_dir / "cache"
RESULTS_DIR = _script_dir / "results"
DATASET_DIR = _script_dir / "dataset"
DEFAULT_DATASET_PATH = DATASET_DIR / "logiqa_binary.json"


@dataclass
class QueryDebugResult:
    """Result of querying a single question against a logified context."""
    doc_id: str
    sample_id: int
    question_idx: int
    question_text: str
    ground_truth: str  # "yes" or "no"
    prediction: Optional[str]  # Solver output: TRUE, FALSE, UNCERTAIN, NOT MENTIONED
    prediction_binary: Optional[str]  # Mapped to "yes" or "no"
    confidence: Optional[float]
    formula: Optional[str]
    query_mode: Optional[str]
    explanation: Optional[str]
    error: Optional[str]
    error_type: Optional[str]
    is_correct: bool
    query_latency_sec: float
    # Additional metadata
    option_index: Optional[int] = None
    is_correct_answer: Optional[bool] = None
    # Translation/NLI confidence and voting fields
    nli_confidence: Optional[float] = None
    sbert_confidence: Optional[float] = None
    voting_triggered: bool = False
    voting_confidence: Optional[float] = None
    vote_counts: Optional[Dict[str, int]] = None


def load_dataset(data_path: Path) -> Dict[str, Any]:
    """Load the LogiQA dataset from JSON file."""
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_solver_to_binary(prediction: Optional[str]) -> Optional[str]:
    """
    Map solver prediction to binary yes/no label.

    TRUE -> yes
    FALSE -> no
    UNCERTAIN -> no
    NOT MENTIONED -> no
    """
    if prediction is None:
        return None
    mapping = {
        "TRUE": "yes",
        "FALSE": "no",
        "UNCERTAIN": "no",
        "NOT MENTIONED": "no",
    }
    return mapping.get(prediction, "no")


def get_cached_logified_path(doc_id: str) -> Path:
    """Get path to cached weighted logified structure."""
    safe_id = str(doc_id).replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"doc_{safe_id}_weighted.json"


def get_intermediate_logified_path(doc_id: str) -> Path:
    """Get path to intermediate (pre-weighted) logified structure."""
    safe_id = str(doc_id).replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"doc_{safe_id}.json"


def logify_context(
    text: str,
    doc_id: str,
    api_key: str,
    temperature: float,
    reasoning_effort: str,
    max_tokens: int,
    k_weights: int,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Convert a context text to logic representation and cache the result.

    Steps:
    1. Check cache for existing logified structure
    2. Convert text to logic using LogifyConverter
    3. Enrich the logic structure
    4. Assign weights to propositions
    5. Cache and return the result
    """
    cache_path = get_cached_logified_path(doc_id)

    # Check cache first
    if cache_path.exists():
        if verbose:
            print(f"    [CACHE HIT] {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            logified_structure = json.load(f)
        return {
            "logified_structure": logified_structure,
            "logify_latency_sec": 0.0,
            "logify_cached": True,
            "logify_error": None,
        }

    if verbose:
        print(f"    [LOGIFY] Converting context {doc_id} to logic...")
    start_time = time.time()

    # Initialize converter
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

    # Save intermediate (non-weighted) JSON
    intermediate_path = get_intermediate_logified_path(doc_id)
    with open(intermediate_path, "w", encoding="utf-8") as f:
        json.dump(logic_structure, f, indent=2, ensure_ascii=False)

    # Create temp text file for weights and enrichment
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

    # Assign weights
    if verbose:
        print(f"    [WEIGHTS] Assigning weights...")

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
            print(f"    [LOGIFY] Completed in {logify_latency:.2f}s")

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


def query_question(
    doc_id: str,
    sample_id: int,
    question_idx: int,
    question_text: str,
    ground_truth: str,
    option_index: int,
    is_correct_answer: bool,
    logified_structure: Dict[str, Any],
    json_path: str,
    api_key: str,
    model: str,
    temperature: float,
    reasoning_effort: str,
    query_max_tokens: int,
    k_query: int,
    verbose: bool = True,
) -> QueryDebugResult:
    """
    Query a question against a logified context structure.

    Steps:
    1. Translate the question to a logical formula
    2. Query the logic solver
    3. Map solver result to binary yes/no label
    4. Return structured result with metrics
    """
    start_time = time.time()

    try:
        # Translate question to logical formula
        translation_result = translate_query(
            query=question_text,
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

        # Extract NLI/voting metadata
        nli_confidence = translation_result.get("confidence")
        sbert_confidence = translation_result.get("sbert_confidence")
        voting_triggered = translation_result.get("voting_triggered", False)
        voting_confidence = translation_result.get("voting_confidence")
        vote_counts = translation_result.get("vote_counts")

        # Handle NONE formula (question not found in context)
        if formula == "NONE":
            prediction = "NOT MENTIONED"
            prediction_binary = map_solver_to_binary(prediction)
            is_correct = prediction_binary == ground_truth
            return QueryDebugResult(
                doc_id=doc_id,
                sample_id=sample_id,
                question_idx=question_idx,
                question_text=question_text,
                ground_truth=ground_truth,
                prediction=prediction,
                prediction_binary=prediction_binary,
                confidence=1.0,
                formula=formula,
                query_mode=query_mode,
                explanation="No matching proposition for question",
                error=None,
                error_type=None,
                is_correct=is_correct,
                query_latency_sec=time.time() - start_time,
                option_index=option_index,
                is_correct_answer=is_correct_answer,
                nli_confidence=nli_confidence,
                sbert_confidence=sbert_confidence,
                voting_triggered=voting_triggered,
                voting_confidence=voting_confidence,
                vote_counts=vote_counts,
            )

        # Handle ERROR or missing formula
        if not formula or formula == "ERROR":
            return QueryDebugResult(
                doc_id=doc_id,
                sample_id=sample_id,
                question_idx=question_idx,
                question_text=question_text,
                ground_truth=ground_truth,
                prediction=None,
                prediction_binary=None,
                confidence=None,
                formula=formula,
                query_mode=query_mode,
                explanation=None,
                error="ERROR: LLM failed to generate a valid formula",
                error_type="translate_error",
                is_correct=False,
                query_latency_sec=time.time() - start_time,
                option_index=option_index,
                is_correct_answer=is_correct_answer,
                nli_confidence=nli_confidence,
                sbert_confidence=sbert_confidence,
                voting_triggered=voting_triggered,
                voting_confidence=voting_confidence,
                vote_counts=vote_counts,
            )

        # Query the logic solver
        solver = LogicSolver(logified_structure)
        if query_mode == "consistency":
            solver_result = solver.check_consistency(formula)
        else:
            solver_result = solver.query(formula)

        prediction = solver_result.answer
        prediction_binary = map_solver_to_binary(prediction)
        is_correct = prediction_binary == ground_truth if prediction_binary else False

        error = None
        error_type = None
        if solver_result.explanation and "Error" in solver_result.explanation:
            error = solver_result.explanation
            error_type = "solver_error"

        return QueryDebugResult(
            doc_id=doc_id,
            sample_id=sample_id,
            question_idx=question_idx,
            question_text=question_text,
            ground_truth=ground_truth,
            prediction=prediction,
            prediction_binary=prediction_binary,
            confidence=solver_result.confidence,
            formula=formula,
            query_mode=query_mode,
            explanation=solver_result.explanation,
            error=error,
            error_type=error_type,
            is_correct=is_correct,
            query_latency_sec=time.time() - start_time,
            option_index=option_index,
            is_correct_answer=is_correct_answer,
            nli_confidence=nli_confidence,
            sbert_confidence=sbert_confidence,
            voting_triggered=voting_triggered,
            voting_confidence=voting_confidence,
            vote_counts=vote_counts,
        )

    except Exception as exc:
        return QueryDebugResult(
            doc_id=doc_id,
            sample_id=sample_id,
            question_idx=question_idx,
            question_text=question_text,
            ground_truth=ground_truth,
            prediction=None,
            prediction_binary=None,
            confidence=None,
            formula=None,
            query_mode=None,
            explanation=None,
            error=str(exc),
            error_type="runtime_error",
            is_correct=False,
            query_latency_sec=time.time() - start_time,
            option_index=option_index,
            is_correct_answer=is_correct_answer,
        )


def run_experiment(
    api_key: str,
    data_path: Path = DEFAULT_DATASET_PATH,
    query_model: str = TRANSLATE_MODEL,
    temperature: float = TEMPERATURE_LOGIC_CONVERTER,
    reasoning_effort: str = REASONING_EFFORT,
    max_tokens: int = MAX_TOKENS,
    query_max_tokens: int = MAX_TOKENS,
    k_weights: int = 10,
    k_query: int = SBERT_TOP_K,
    doc_id: Optional[int] = None,
    limit: Optional[int] = None,
    verbose: bool = True,
) -> Tuple[List[QueryDebugResult], Dict[str, Any], Path]:
    """
    Run the experiment on the LogiQA dataset.

    Args:
        api_key: API key for LLM calls
        data_path: Path to dataset JSON file
        query_model: Model for query translation
        temperature: Sampling temperature
        reasoning_effort: Reasoning effort level
        max_tokens: Max tokens for logification
        query_max_tokens: Max tokens for query translation
        k_weights: Top-k chunks for weight assignment
        k_query: Top-k propositions for query translation
        doc_id: Optional single sample ID to evaluate
        limit: Optional limit on number of samples to process
        verbose: Enable detailed output

    Returns:
        Tuple of (results list, results payload dict, output path)
    """

    # Ensure directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading data from {data_path}...")
    data = load_dataset(data_path)
    samples = data.get("samples", [])
    metadata = data.get("metadata", {})

    # Filter by doc_id if specified
    if doc_id is not None:
        samples = [s for s in samples if s.get("sample_id") == doc_id]
        if not samples:
            raise ValueError(f"No sample found with sample_id={doc_id}")

    # Apply limit
    if limit is not None:
        samples = samples[:limit]

    # Count total questions
    total_questions = sum(len(s.get("qa_pairs", [])) for s in samples)
    print(f"  Loaded {len(samples)} samples with {total_questions} total questions")

    # Print label distribution from metadata if available
    if "label_distribution" in metadata:
        print(f"  Label distribution: {metadata['label_distribution']}")

    # Initialize results
    timestamp = datetime.now().isoformat()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    results_payload = {
        "metadata": {
            "timestamp": timestamp,
            "data_path": str(data_path),
            "logify_model": REASONING_MODEL,
            "query_model": query_model,
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "query_max_tokens": query_max_tokens,
            "k_weights": k_weights,
            "k_query": k_query,
            "num_samples": len(samples),
            "num_questions": total_questions,
            "doc_filter": doc_id,
            "limit": limit,
            "data_metadata": metadata,
        },
        "retrieval_config": get_full_retrieval_config(),
        "sample_metrics": [],
        "results": [],
    }

    results: List[QueryDebugResult] = []
    total_correct = 0
    total_evaluated = 0
    total_errors = 0

    # Track per-label accuracy
    label_correct = {"yes": 0, "no": 0}
    label_total = {"yes": 0, "no": 0}

    # Process each sample
    for sample_idx, sample_data in enumerate(samples):
        sample_id = sample_data.get("sample_id")
        original_id = sample_data.get("original_id", sample_id)
        context_text = sample_data.get("context", "")
        qa_pairs = sample_data.get("qa_pairs", [])
        reasoning_types = sample_data.get("reasoning_types", [])

        # Create unique doc_id
        current_doc_id = f"logiqa_{sample_id}"
        context_word_count = sample_data.get("context_word_count", len(context_text.split()))

        print(f"\n[{sample_idx + 1}/{len(samples)}] Sample {sample_id} (orig:{original_id}): {context_word_count} words, {len(qa_pairs)} questions")
        if reasoning_types:
            print(f"  Reasoning types: {reasoning_types}")

        if not context_text or not context_text.strip():
            print(f"  [SKIP] Empty context text")
            results_payload["sample_metrics"].append({
                "doc_id": current_doc_id,
                "sample_id": sample_id,
                "original_id": original_id,
                "context_length": len(context_text),
                "context_word_count": context_word_count,
                "num_questions": len(qa_pairs),
                "reasoning_types": reasoning_types,
                "logify_latency_sec": 0.0,
                "logify_cached": False,
                "logify_error": "Empty context text",
                "query_latency_total_sec": 0.0,
                "sample_correct": 0,
                "sample_total": 0,
                "sample_accuracy": 0.0,
            })
            continue

        # Logify context
        logify_result = logify_context(
            text=context_text,
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

        sample_correct = 0
        sample_total = 0
        query_latency_total = 0.0

        # Query each question
        for q_idx, qa in enumerate(qa_pairs):
            question_text = qa.get("question", "")
            ground_truth = qa.get("answer", "no").lower()  # "yes" or "no"
            option_index = qa.get("option_index", q_idx)
            is_correct_answer = qa.get("is_correct_answer", False)

            if logified_structure is None:
                result = QueryDebugResult(
                    doc_id=current_doc_id,
                    sample_id=sample_id,
                    question_idx=q_idx,
                    question_text=question_text,
                    ground_truth=ground_truth,
                    prediction=None,
                    prediction_binary=None,
                    confidence=None,
                    formula=None,
                    query_mode=None,
                    explanation=None,
                    error=logify_error or "Logification failed",
                    error_type="logify_error",
                    is_correct=False,
                    query_latency_sec=0.0,
                    option_index=option_index,
                    is_correct_answer=is_correct_answer,
                )
            else:
                result = query_question(
                    doc_id=current_doc_id,
                    sample_id=sample_id,
                    question_idx=q_idx,
                    question_text=question_text,
                    ground_truth=ground_truth,
                    option_index=option_index,
                    is_correct_answer=is_correct_answer,
                    logified_structure=logified_structure,
                    json_path=json_path,
                    api_key=api_key,
                    model=query_model,
                    temperature=temperature,
                    reasoning_effort=reasoning_effort,
                    query_max_tokens=query_max_tokens,
                    k_query=k_query,
                    verbose=verbose,
                )

            results.append(result)
            results_payload["results"].append(asdict(result))
            query_latency_total += result.query_latency_sec

            if result.prediction_binary is not None:
                sample_total += 1
                total_evaluated += 1
                label_total[ground_truth] = label_total.get(ground_truth, 0) + 1

                if result.is_correct:
                    sample_correct += 1
                    total_correct += 1
                    label_correct[ground_truth] = label_correct.get(ground_truth, 0) + 1

            if result.error:
                total_errors += 1

            # Print progress
            status = "+" if result.is_correct else ("?" if result.prediction is None else "x")
            opt_marker = "*" if is_correct_answer else " "
            print(f"  [{status}]{opt_marker} q{q_idx} (opt{option_index}): pred={result.prediction} ({result.prediction_binary}) gt={ground_truth}")
            if verbose:
                if result.formula:
                    print(f"      formula: {result.formula}")
                if result.nli_confidence is not None:
                    print(f"      nli_confidence: {result.nli_confidence:.2f}")
                if result.sbert_confidence is not None:
                    print(f"      sbert_confidence: {result.sbert_confidence:.2f}")
                if result.voting_triggered:
                    print(f"      voting: TRIGGERED (conf={result.voting_confidence:.2f}, counts={result.vote_counts})")
                if result.error:
                    print(f"      error ({result.error_type}): {result.error}")

        # Store sample metrics
        sample_accuracy = sample_correct / sample_total if sample_total > 0 else 0.0
        sample_metrics = {
            "doc_id": current_doc_id,
            "sample_id": sample_id,
            "original_id": original_id,
            "context_length": len(context_text),
            "context_word_count": context_word_count,
            "num_questions": len(qa_pairs),
            "reasoning_types": reasoning_types,
            "logify_latency_sec": logify_result["logify_latency_sec"],
            "logify_cached": logify_result["logify_cached"],
            "logify_error": logify_error,
            "query_latency_total_sec": query_latency_total,
            "sample_correct": sample_correct,
            "sample_total": sample_total,
            "sample_accuracy": sample_accuracy,
        }
        results_payload["sample_metrics"].append(sample_metrics)

        print(f"  Sample accuracy: {sample_correct}/{sample_total} = {sample_accuracy:.2%}")
        print(f"  Logify: {logify_result['logify_latency_sec']:.2f}s (cached: {logify_result['logify_cached']})")

        # Save intermediate results
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results_payload, f, indent=2, ensure_ascii=False)

    # Calculate per-label accuracy
    yes_acc = label_correct["yes"] / label_total["yes"] if label_total["yes"] > 0 else 0.0
    no_acc = label_correct["no"] / label_total["no"] if label_total["no"] > 0 else 0.0

    # Final summary
    overall_accuracy = total_correct / total_evaluated if total_evaluated > 0 else 0.0
    results_payload["metadata"]["total_correct"] = total_correct
    results_payload["metadata"]["total_evaluated"] = total_evaluated
    results_payload["metadata"]["overall_accuracy"] = overall_accuracy
    results_payload["metadata"]["total_errors"] = total_errors
    results_payload["metadata"]["per_label_accuracy"] = {
        "yes": {
            "correct": label_correct["yes"],
            "total": label_total["yes"],
            "accuracy": yes_acc,
        },
        "no": {
            "correct": label_correct["no"],
            "total": label_total["no"],
            "accuracy": no_acc,
        },
    }

    # Save final results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Samples processed: {len(samples)}")
    print(f"Questions evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"  - Yes accuracy: {label_correct['yes']}/{label_total['yes']} = {yes_acc:.2%}")
    print(f"  - No accuracy: {label_correct['no']}/{label_total['no']} = {no_acc:.2%}")
    print(f"Total errors: {total_errors}")
    print(f"Results saved to: {output_path}")

    return results, results_payload, output_path


def main() -> int:
    """Main entry point for the experiment."""
    parser = argparse.ArgumentParser(
        description="Logify Experiment on LogiQA dataset"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help=f"Path to dataset JSON (default: {DEFAULT_DATASET_PATH})",
    )
    parser.add_argument(
        "--doc-id",
        type=int,
        default=None,
        help="Single sample ID to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples to process",
    )
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
        default=SBERT_TOP_K,
        help="Top-k chunks for weight assignment",
    )
    parser.add_argument(
        "--k-query",
        type=int,
        default=SBERT_TOP_K,
        help="Top-k propositions for query translation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Enable detailed output",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key. Set OPENROUTER_API_KEY or use --api-key")
        return 1

    if not args.data_path.exists():
        print(f"Error: Data not found: {args.data_path}")
        print(f"\nPlease run the data constructor first:")
        print(f"  cd {DATASET_DIR}")
        print(f"  python data_constructor_logiqa.py")
        return 1

    try:
        run_experiment(
            api_key=args.api_key,
            data_path=args.data_path,
            query_model=args.query_model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            query_max_tokens=args.query_max_tokens,
            k_weights=args.k_weights,
            k_query=args.k_query,
            doc_id=args.doc_id,
            limit=args.limit,
            verbose=args.verbose,
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
