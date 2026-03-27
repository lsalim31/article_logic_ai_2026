#!/usr/bin/env python3
"""
experiment_rag_baseline.py

Experiment: RAG baseline on gold_balanced_sudhu_edit dataset.

This script runs a simple RAG + LLM baseline (no logic solver) for comparison
with the Logify neuro-symbolic pipeline.

Pipeline:
    For each premise:
        1. Chunk premise into overlapping segments
        2. Encode chunks using SBERT
        3. For each hypothesis:
            a. Retrieve top-k relevant chunks
            b. Perform Chain-of-Thought reasoning with LLM
            c. Parse response to extract prediction and confidence
        4. Save intermediate results

Usage:
    python experiment_rag_baseline.py --api-key $OPENROUTER_API_KEY
    python experiment_rag_baseline.py --api-key $OPENROUTER_API_KEY --limit 5
    python experiment_rag_baseline.py --api-key $OPENROUTER_API_KEY --premise-id 0
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add directories to Python path
_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parent.parent
_code_dir = _repo_root / "code"
_experiments_dir = _repo_root / "experiments"

for p in (_repo_root, _code_dir, _experiments_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Import baseline_rag modules (from experiments/baseline_rag/)
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    retrieve
)
from baseline_rag import config as rag_config

# Directory configuration
RESULTS_DIR = _script_dir / "results_rag"
DATASET_DIR = _script_dir / "dataset"
DEFAULT_DATASET_PATH = DATASET_DIR / "gold_balanced_sudhu_edit.json"


# =============================================================================
# Chain-of-Thought Prompt Template (4-way classification)
# =============================================================================

COT_PROMPT = """You are a document analyst specializing in natural language inference. Given excerpts from a document (premise) and a hypothesis, determine the logical relationship.

**Document Excerpts:**
{context}

**Hypothesis:** {hypothesis}

**Instructions:**
Determine if the hypothesis is:
- TRUE (entailment): The document clearly and explicitly supports this statement as true
- FALSE (contradiction): The document clearly and explicitly contradicts this statement
- UNCERTAIN: The document is consistent with the hypothesis being true OR false, but doesn't confirm either
- NOT_MENTIONED: The hypothesis is about something completely unrelated to the document

Provide your confidence level as a number between 0.0 and 1.0.

**Format your response exactly as follows:**
**Reasoning:** [Your step-by-step analysis]
**Answer:** [TRUE or FALSE or UNCERTAIN or NOT_MENTIONED]
**Confidence:** [A number between 0.0 and 1.0]

Begin your analysis:"""


# =============================================================================
# Data Loading
# =============================================================================

def load_dataset(data_path: Path) -> Dict[str, Any]:
    """Load the dataset from JSON file."""
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_prediction_to_binary(prediction: Optional[str]) -> Optional[str]:
    """
    Map LLM prediction to binary entailment label.

    TRUE -> entailment
    FALSE -> not_entailment
    UNCERTAIN -> not_entailment
    NOT_MENTIONED -> not_entailment
    """
    if prediction is None:
        return None
    mapping = {
        "TRUE": "entailment",
        "FALSE": "not_entailment",
        "UNCERTAIN": "not_entailment",
        "NOT_MENTIONED": "not_entailment"
    }
    return mapping.get(prediction, "not_entailment")


# =============================================================================
# Response Parsing
# =============================================================================

def parse_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract answer and confidence.

    Returns:
        Dictionary with 'answer', 'confidence', and 'reasoning' keys
    """
    answer = None
    confidence = 0.5
    reasoning = response

    # Extract answer from **Answer:** section
    answer_match = re.search(
        r'\*\*Answer:\*\*\s*(TRUE|FALSE|UNCERTAIN|NOT_MENTIONED)',
        response,
        re.IGNORECASE
    )
    if answer_match:
        answer = answer_match.group(1).upper()
    else:
        # Fallback: search for keywords
        response_upper = response.upper()
        if 'NOT_MENTIONED' in response_upper or 'NOT MENTIONED' in response_upper:
            answer = 'NOT_MENTIONED'
        elif 'UNCERTAIN' in response_upper:
            answer = 'UNCERTAIN'
        elif 'FALSE' in response_upper:
            answer = 'FALSE'
        elif 'TRUE' in response_upper:
            answer = 'TRUE'
        else:
            answer = 'UNCERTAIN'

    # Extract confidence from **Confidence:** section
    confidence_match = re.search(r'\*\*Confidence:\*\*\s*([\d.]+)', response)
    if confidence_match:
        try:
            confidence = float(confidence_match.group(1))
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            confidence = 0.5
    else:
        fallback_match = re.search(r'confidence[:\s]+(\d*\.?\d+)', response, re.IGNORECASE)
        if fallback_match:
            try:
                confidence = float(fallback_match.group(1))
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.5

    # Extract reasoning
    reasoning_match = re.search(
        r'\*\*Reasoning:\*\*\s*(.*?)(?=\*\*Answer:|\Z)',
        response,
        re.DOTALL
    )
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()

    return {
        'answer': answer,
        'confidence': confidence,
        'reasoning': reasoning
    }


# =============================================================================
# LLM Interaction
# =============================================================================

def call_llm(
    prompt: str,
    model_name: str,
    api_key: str,
    temperature: float = 0
) -> str:
    """Call the LLM API with the constructed prompt."""
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )

    return response.choices[0].message.content


def construct_prompt(hypothesis: str, retrieved_chunks: List[Dict]) -> str:
    """Construct the full prompt from template, hypothesis, and retrieved chunks."""
    formatted_chunks = []
    for i, chunk in enumerate(retrieved_chunks):
        formatted_chunks.append(f"[Excerpt {i+1}]\n{chunk['text']}")

    context = "\n\n".join(formatted_chunks)

    return COT_PROMPT.format(
        context=context,
        hypothesis=hypothesis
    )


# =============================================================================
# Processing Functions
# =============================================================================

def process_premise(premise_text: str, sbert_model) -> Tuple[List[Dict], Any]:
    """Chunk and encode a premise for retrieval."""
    chunks = chunk_document(
        premise_text,
        chunk_size=rag_config.CHUNK_SIZE,
        overlap=rag_config.OVERLAP
    )
    chunk_embeddings = encode_chunks(chunks, sbert_model)
    return chunks, chunk_embeddings


def process_hypothesis(
    hypothesis_text: str,
    chunk_embeddings,
    chunks: List[Dict],
    sbert_model,
    model_name: str,
    api_key: str,
    temperature: float
) -> Dict[str, Any]:
    """Process a single hypothesis against pre-computed premise chunks."""
    start_time = time.time()

    try:
        # Encode hypothesis as query
        query_embedding = encode_query(hypothesis_text, sbert_model)

        # Retrieve top-k relevant chunks
        retrieved_chunks = retrieve(
            query_embedding,
            chunk_embeddings,
            chunks,
            k=rag_config.TOP_K
        )

        # Construct prompt with retrieved context
        prompt = construct_prompt(hypothesis_text, retrieved_chunks)

        # Call LLM for reasoning
        raw_response = call_llm(prompt, model_name, api_key, temperature)

        # Parse response
        parsed = parse_response(raw_response)

        return {
            "prediction": parsed['answer'],
            "confidence": parsed['confidence'],
            "reasoning": parsed['reasoning'],
            "query_latency_sec": time.time() - start_time,
            "error": None
        }

    except Exception as e:
        return {
            "prediction": None,
            "confidence": None,
            "reasoning": None,
            "query_latency_sec": time.time() - start_time,
            "error": str(e)
        }


# =============================================================================
# Main Experiment
# =============================================================================

def run_experiment(
    api_key: str,
    data_path: Path = DEFAULT_DATASET_PATH,
    model_name: str = None,
    temperature: float = 0,
    premise_id: Optional[int] = None,
    limit: Optional[int] = None,
    verbose: bool = True
) -> Tuple[Dict[str, Any], Path]:
    """Run the RAG baseline experiment."""

    if model_name is None:
        model_name = rag_config.DEFAULT_MODEL

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading data from {data_path}...")
    data = load_dataset(data_path)
    premises = data.get("premises", [])
    metadata = data.get("metadata", {})

    # Filter by premise_id if specified
    if premise_id is not None:
        premises = [p for p in premises if p.get("premise_id") == premise_id]
        if not premises:
            raise ValueError(f"No premise found with premise_id={premise_id}")

    # Apply limit
    if limit is not None:
        premises = premises[:limit]

    # Count total hypotheses
    total_hypotheses = sum(len(p.get("hypotheses", [])) for p in premises)
    print(f"  Loaded {len(premises)} premises with {total_hypotheses} total hypotheses")

    # Load SBERT model
    print(f"Loading SBERT model: {rag_config.SBERT_MODEL}")
    sbert_model = load_sbert_model(rag_config.SBERT_MODEL)

    # Initialize results
    timestamp = datetime.now().isoformat()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    results_payload = {
        "metadata": {
            "timestamp": timestamp,
            "experiment_type": "rag_baseline",
            "model": model_name,
            "temperature": temperature,
            "chunk_size": rag_config.CHUNK_SIZE,
            "overlap": rag_config.OVERLAP,
            "top_k": rag_config.TOP_K,
            "sbert_model": rag_config.SBERT_MODEL,
            "data_path": str(data_path),
            "num_premises": len(premises),
            "num_hypotheses": total_hypotheses,
            "premise_filter": premise_id,
            "limit": limit,
            "data_metadata": metadata,
        },
        "premise_metrics": [],
        "results": [],
    }

    total_correct = 0
    total_evaluated = 0
    total_errors = 0

    # Track per-label accuracy
    label_correct = {"entailment": 0, "not_entailment": 0}
    label_total = {"entailment": 0, "not_entailment": 0}

    # Process each premise
    for premise_idx, premise_data in enumerate(premises):
        current_premise_id = premise_data.get("premise_id")
        premise_text = premise_data.get("premise", "")
        premise_word_count = premise_data.get("premise_word_count", len(premise_text.split()))
        hypotheses = premise_data.get("hypotheses", [])

        print(f"\n[{premise_idx + 1}/{len(premises)}] Premise {current_premise_id}: {premise_word_count} words, {len(hypotheses)} hypotheses")

        if not premise_text or not premise_text.strip():
            print(f"  [SKIP] Empty premise text")
            continue

        # Process premise (chunk and encode)
        premise_start_time = time.time()
        try:
            chunks, chunk_embeddings = process_premise(premise_text, sbert_model)
            premise_process_latency = time.time() - premise_start_time
            premise_process_error = None
            print(f"  Created {len(chunks)} chunks in {premise_process_latency:.2f}s")
        except Exception as e:
            print(f"  [ERROR] Premise processing failed: {e}")
            chunks = None
            chunk_embeddings = None
            premise_process_latency = time.time() - premise_start_time
            premise_process_error = str(e)

        premise_correct = 0
        premise_total = 0
        query_latency_total = 0.0

        # Query each hypothesis
        for hyp_idx, hyp in enumerate(hypotheses):
            original_idx = hyp.get("original_idx", hyp_idx)
            hypothesis_text = hyp.get("hypothesis", "")
            ground_truth = hyp.get("label", "not_entailment")

            if chunks is not None and chunk_embeddings is not None:
                result = process_hypothesis(
                    hypothesis_text=hypothesis_text,
                    chunk_embeddings=chunk_embeddings,
                    chunks=chunks,
                    sbert_model=sbert_model,
                    model_name=model_name,
                    api_key=api_key,
                    temperature=temperature
                )
                prediction = result.get("prediction")
                confidence = result.get("confidence")
                reasoning = result.get("reasoning")
                query_latency = result.get("query_latency_sec", 0.0)
                error = result.get("error")
            else:
                prediction = None
                confidence = None
                reasoning = None
                query_latency = 0.0
                error = premise_process_error

            query_latency_total += query_latency

            # Map prediction to binary
            prediction_binary = map_prediction_to_binary(prediction)

            # Check correctness
            is_correct = (prediction_binary == ground_truth) if prediction_binary else False

            if prediction_binary is not None:
                premise_total += 1
                total_evaluated += 1
                label_total[ground_truth] = label_total.get(ground_truth, 0) + 1

                if is_correct:
                    premise_correct += 1
                    total_correct += 1
                    label_correct[ground_truth] = label_correct.get(ground_truth, 0) + 1

            if error:
                total_errors += 1

            # Store result
            result_entry = {
                "premise_id": current_premise_id,
                "original_idx": original_idx,
                "hypothesis_text": hypothesis_text,
                "ground_truth": ground_truth,
                "prediction": prediction,
                "prediction_binary": prediction_binary,
                "confidence": confidence,
                "is_correct": is_correct,
                "query_latency_sec": query_latency,
                "error": error,
            }
            results_payload["results"].append(result_entry)

            # Print progress
            status = "+" if is_correct else ("?" if prediction is None else "x")
            print(f"  [{status}] hyp {hyp_idx + 1}: pred={prediction} ({prediction_binary}) gt={ground_truth}")
            if verbose and reasoning:
                print(f"      reasoning: {reasoning[:100]}...")

        # Store premise metrics
        premise_accuracy = premise_correct / premise_total if premise_total > 0 else 0.0
        premise_metrics = {
            "premise_id": current_premise_id,
            "premise_length": len(premise_text),
            "premise_word_count": premise_word_count,
            "num_hypotheses": len(hypotheses),
            "num_chunks": len(chunks) if chunks else 0,
            "premise_process_latency_sec": premise_process_latency,
            "premise_process_error": premise_process_error,
            "query_latency_total_sec": query_latency_total,
            "premise_correct": premise_correct,
            "premise_total": premise_total,
            "premise_accuracy": premise_accuracy,
        }
        results_payload["premise_metrics"].append(premise_metrics)

        print(f"  Premise accuracy: {premise_correct}/{premise_total} = {premise_accuracy:.2%}")

        # Save intermediate results
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results_payload, f, indent=2, ensure_ascii=False)

    # Calculate per-label accuracy
    entailment_acc = label_correct["entailment"] / label_total["entailment"] if label_total["entailment"] > 0 else 0.0
    not_entailment_acc = label_correct["not_entailment"] / label_total["not_entailment"] if label_total["not_entailment"] > 0 else 0.0

    # Final summary
    overall_accuracy = total_correct / total_evaluated if total_evaluated > 0 else 0.0
    results_payload["metadata"]["total_correct"] = total_correct
    results_payload["metadata"]["total_evaluated"] = total_evaluated
    results_payload["metadata"]["overall_accuracy"] = overall_accuracy
    results_payload["metadata"]["total_errors"] = total_errors
    results_payload["metadata"]["per_label_accuracy"] = {
        "entailment": {
            "correct": label_correct["entailment"],
            "total": label_total["entailment"],
            "accuracy": entailment_acc,
        },
        "not_entailment": {
            "correct": label_correct["not_entailment"],
            "total": label_total["not_entailment"],
            "accuracy": not_entailment_acc,
        },
    }

    # Save final results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE (RAG BASELINE)")
    print("=" * 60)
    print(f"Premises processed: {len(premises)}")
    print(f"Hypotheses evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"  - Entailment accuracy: {label_correct['entailment']}/{label_total['entailment']} = {entailment_acc:.2%}")
    print(f"  - Not-entailment accuracy: {label_correct['not_entailment']}/{label_total['not_entailment']} = {not_entailment_acc:.2%}")
    print(f"Total errors: {total_errors}")
    print(f"Results saved to: {output_path}")

    return results_payload, output_path


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RAG baseline experiment on gold_balanced_sudhu_edit dataset"
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
        "--model",
        default=None,
        help="LLM model name (default: from rag_config)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="Sampling temperature (default: 0)",
    )
    parser.add_argument(
        "--premise-id",
        type=int,
        default=None,
        help="Single premise ID to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of premises to process",
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
        return 1

    try:
        run_experiment(
            api_key=args.api_key,
            data_path=args.data_path,
            model_name=args.model,
            temperature=args.temperature,
            premise_id=args.premise_id,
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
