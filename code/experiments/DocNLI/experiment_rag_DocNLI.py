#!/usr/bin/env python3
"""
experiment_rag_DocNLI.py

Experiment: Evaluate RAG baseline on DocNLI dataset.

This script runs the Reasoning LLM + RAG baseline on DocNLI,
using the same data source, evaluation structure, and output format
as the Logify experiment for fair comparison.

Pipeline:
    For each premise in DocNLI sample:
        1. Chunk premise into overlapping segments
        2. Encode chunks using SBERT
        3. For each hypothesis associated with the premise:
            a. Retrieve top-k relevant chunks
            b. Perform Chain-of-Thought reasoning with LLM
            c. Parse response to extract prediction and confidence
            d. Map 3-way prediction to binary label
        4. Save intermediate results

Output format matches experiment_logify_DocNLI.py exactly.

Usage:
    python experiment_rag_DocNLI.py
    python experiment_rag_DocNLI.py --limit 10
    python experiment_rag_DocNLI.py --model openai/gpt-4o --temperature 0.1
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

# Import baseline_rag modules
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    retrieve
)
from baseline_rag import config as rag_config

# Paths
RESULTS_DIR = _script_dir / "results_rag_DocNLI"
SAMPLE_DATA_PATH = _script_dir / "doc-nli" / "sample_100.json"


# =============================================================================
# DocNLI-specific Chain-of-Thought Prompt Template
# =============================================================================

DOCNLI_COT_PROMPT = """You are a document analyst specializing in natural language inference. Given excerpts from a document (premise) and a hypothesis, determine whether the hypothesis is entailed by the document.

**Document Excerpts:**
{context}

**Hypothesis:** {hypothesis}

**Instructions:**
1. Carefully read the document excerpts provided above
2. Determine if the hypothesis is:
   - TRUE: The document clearly states or logically entails this hypothesis (entailment)
   - FALSE: The document clearly contradicts this hypothesis (not entailment)
   - UNCERTAIN: The document does not provide sufficient information to determine if the hypothesis is true or false (not entailment)
3. Provide your confidence level as a number between 0.0 and 1.0:
   - 1.0 = Absolutely certain (explicit statement in document)
   - 0.7-0.9 = High confidence (strong implication)
   - 0.4-0.6 = Moderate confidence (some evidence but not conclusive)
   - 0.1-0.3 = Low confidence (weak or indirect evidence)
   - 0.0 = No support for this conclusion

**Format your response exactly as follows:**
**Reasoning:** [Your step-by-step analysis of the document excerpts]
**Answer:** [TRUE or FALSE or UNCERTAIN]
**Confidence:** [A number between 0.0 and 1.0]

Begin your analysis:"""


# =============================================================================
# Data Loading (matching Logify experiment)
# =============================================================================

def load_sample_data(data_path: Path = SAMPLE_DATA_PATH) -> Dict[str, Any]:
    """
    Load sample DocNLI data from JSON file.

    Args:
        data_path: Path to sample_100.json

    Returns:
        Dictionary containing 'metadata', 'premises', and 'examples' keys
    """
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def map_prediction_to_binary(prediction: Optional[str]) -> Optional[str]:
    """
    Map 3-way prediction to DocNLI binary label.

    Mapping (consistent with Logify experiment):
        TRUE -> entailment
        FALSE -> not_entailment
        UNCERTAIN -> not_entailment

    Args:
        prediction: 3-way prediction (TRUE, FALSE, or UNCERTAIN)

    Returns:
        Binary label (entailment or not_entailment)
    """
    if prediction is None:
        return None
    mapping = {
        "TRUE": "entailment",
        "FALSE": "not_entailment",
        "UNCERTAIN": "not_entailment"
    }
    return mapping.get(prediction, "not_entailment")


# =============================================================================
# Response Parsing
# =============================================================================

def parse_rag_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract answer and confidence.

    Extracts:
        - Answer: TRUE, FALSE, or UNCERTAIN
        - Confidence: float between 0 and 1 (default 0.5 if not found)

    Args:
        response: Raw LLM response string

    Returns:
        Dictionary with 'answer', 'confidence', and 'reasoning' keys
    """
    import re

    answer = None
    confidence = 0.5  # Default confidence
    reasoning = response

    # Extract answer from **Answer:** section
    answer_match = re.search(r'\*\*Answer:\*\*\s*(TRUE|FALSE|UNCERTAIN)', response, re.IGNORECASE)
    if answer_match:
        answer = answer_match.group(1).upper()
    else:
        # Fallback: search for keywords in the response
        response_upper = response.upper()
        if 'UNCERTAIN' in response_upper:
            answer = 'UNCERTAIN'
        elif 'TRUE' in response_upper:
            answer = 'TRUE'
        elif 'FALSE' in response_upper:
            answer = 'FALSE'
        else:
            answer = 'UNCERTAIN'  # Default if nothing found

    # Extract confidence from **Confidence:** section
    confidence_match = re.search(r'\*\*Confidence:\*\*\s*([\d.]+)', response)
    if confidence_match:
        try:
            confidence = float(confidence_match.group(1))
            # Clamp to [0, 1]
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            confidence = 0.5
    else:
        # Fallback: search for any decimal number after "confidence"
        fallback_match = re.search(r'confidence[:\s]+(\d*\.?\d+)', response, re.IGNORECASE)
        if fallback_match:
            try:
                confidence = float(fallback_match.group(1))
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.5

    # Extract reasoning from **Reasoning:** section
    reasoning_match = re.search(r'\*\*Reasoning:\*\*\s*(.*?)(?=\*\*Answer:|\Z)', response, re.DOTALL)
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

def call_llm(prompt: str, model_name: str, temperature: float = 0) -> str:
    """
    Call the language model API with the constructed prompt.

    Uses OpenRouter API with OPENROUTER_API_KEY environment variable.

    Args:
        prompt: Complete prompt string
        model_name: Name of the model (e.g., "openai/gpt-5-nano")
        temperature: Sampling temperature (0 for deterministic)

    Returns:
        Raw string response from the LLM
    """
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY")
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )

    return response.choices[0].message.content


def construct_prompt(hypothesis: str, retrieved_chunks: List[Dict]) -> str:
    """
    Construct the full prompt from template, hypothesis, and retrieved chunks.

    Args:
        hypothesis: The hypothesis text to evaluate
        retrieved_chunks: List of retrieved chunk dictionaries with 'text' field

    Returns:
        Formatted prompt string ready for LLM
    """
    # Format chunks with separators
    formatted_chunks = []
    for i, chunk in enumerate(retrieved_chunks):
        formatted_chunks.append(f"[Excerpt {i+1}]\n{chunk['text']}")

    context = "\n\n".join(formatted_chunks)

    # Fill in the template
    prompt = DOCNLI_COT_PROMPT.format(
        context=context,
        hypothesis=hypothesis
    )

    return prompt


# =============================================================================
# Single Query Processing
# =============================================================================

def process_single_hypothesis(
    hypothesis_text: str,
    chunk_embeddings,
    chunks: List[Dict],
    sbert_model,
    model_name: str,
    temperature: float
) -> Dict[str, Any]:
    """
    Process a single hypothesis against pre-computed premise chunks.

    Pipeline:
        1. Encode hypothesis as query
        2. Retrieve top-k relevant chunks
        3. Construct prompt with retrieved context
        4. Call LLM for reasoning
        5. Parse response for answer and confidence

    Args:
        hypothesis_text: The hypothesis to evaluate
        chunk_embeddings: Pre-computed chunk embeddings (numpy array)
        chunks: List of chunk dictionaries from chunker
        sbert_model: Loaded SBERT model
        model_name: LLM model name
        temperature: Sampling temperature

    Returns:
        Dictionary with 'prediction', 'confidence', 'latency_sec', 'error'
    """
    start_time = time.time()

    try:
        # Step 1: Encode hypothesis as query
        query_embedding = encode_query(hypothesis_text, sbert_model)

        # Step 2: Retrieve top-k relevant chunks
        retrieved_chunks = retrieve(
            query_embedding,
            chunk_embeddings,
            chunks,
            k=rag_config.TOP_K
        )

        # Step 3: Construct prompt with retrieved context
        prompt = construct_prompt(hypothesis_text, retrieved_chunks)

        # Step 4: Call LLM for reasoning
        raw_response = call_llm(prompt, model_name, temperature)

        # Step 5: Parse response for answer and confidence
        parsed = parse_rag_response(raw_response)

        return {
            "prediction": parsed['answer'],
            "confidence": parsed['confidence'],
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


# =============================================================================
# Premise Processing
# =============================================================================

def process_premise(
    premise_text: str,
    sbert_model
) -> tuple:
    """
    Chunk and encode a premise for retrieval.

    Args:
        premise_text: Full premise text
        sbert_model: Loaded SBERT model

    Returns:
        Tuple of (chunks, chunk_embeddings)
    """
    # Chunk the premise using config settings
    chunks = chunk_document(
        premise_text,
        chunk_size=rag_config.CHUNK_SIZE,
        overlap=rag_config.OVERLAP
    )

    # Encode chunks
    chunk_embeddings = encode_chunks(chunks, sbert_model)

    return chunks, chunk_embeddings


# =============================================================================
# Main Experiment
# =============================================================================

def run_experiment(
    data_path: Path = SAMPLE_DATA_PATH,
    model_name: str = None,
    temperature: float = 0,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the DocNLI RAG baseline experiment.

    Args:
        data_path: Path to sample_100.json
        model_name: LLM model name (default: from rag_config)
        temperature: Sampling temperature (default: 0)
        limit: Limit number of premises to process (default: all)

    Returns:
        Experiment results dictionary matching Logify output format
    """
    # Use default model if not specified
    if model_name is None:
        model_name = rag_config.DEFAULT_MODEL

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load sample data
    print(f"Loading sample data from {data_path}...")
    data = load_sample_data(data_path)
    premises = data.get("premises", [])
    examples = data.get("examples", [])
    metadata = data.get("metadata", {})

    num_premises = len(premises)
    num_examples = len(examples)
    print(f"  Loaded {num_premises} premises with {num_examples} total hypotheses")
    print(f"  Filter criteria: {metadata.get('filter_criteria', {})}")

    # Apply limit to premises if specified
    if limit is not None:
        premises = premises[:limit]
        # Filter examples to only those from limited premises
        limited_premise_ids = {p["premise_id"] for p in premises}
        examples = [ex for ex in examples if ex.get("premise_id") in limited_premise_ids]
        print(f"  Limited to {len(premises)} premises with {len(examples)} hypotheses")

    # Load SBERT model
    print(f"Loading SBERT model: {rag_config.SBERT_MODEL}")
    sbert_model = load_sbert_model(rag_config.SBERT_MODEL)

    # Initialize results (matching Logify format)
    timestamp = datetime.now().isoformat()
    results = {
        "metadata": {
            "timestamp": timestamp,
            "model": model_name,
            "temperature": temperature,
            "chunk_size": rag_config.CHUNK_SIZE,
            "overlap": rag_config.OVERLAP,
            "top_k": rag_config.TOP_K,
            "sbert_model": rag_config.SBERT_MODEL,
            "num_premises": len(premises),
            "num_examples": len(examples),
            "data_source": str(data_path),
            "data_metadata": metadata
        },
        "premise_metrics": [],
        "results": []
    }

    # Output file (with timestamp)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    # Process premises
    total_evaluated = 0
    total_correct = 0

    for premise_idx, premise_data in enumerate(premises):
        premise_id = premise_data.get("premise_id")
        premise_text = premise_data.get("premise", "")
        premise_word_count = premise_data.get("premise_word_count", len(premise_text.split()))
        hypotheses = premise_data.get("hypotheses", [])

        print(f"\n[Premise {premise_idx + 1}/{len(premises)}] ID={premise_id}, {premise_word_count} words, {len(hypotheses)} hypotheses")

        # Skip empty premises
        if not premise_text or not premise_text.strip():
            print(f"  [SKIP] Empty premise text")
            continue

        # Process premise (chunk and encode) - done once for all hypotheses
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

        # Track premise-level metrics
        premise_correct = 0
        premise_total = 0
        query_latency_total = 0.0

        # Query each hypothesis
        for hyp_idx, hyp in enumerate(hypotheses):
            original_idx = hyp.get("original_idx")
            hypothesis_text = hyp.get("hypothesis", "")
            ground_truth = hyp.get("label")  # "entailment" or "not_entailment"

            if chunks is not None and chunk_embeddings is not None:
                query_result = process_single_hypothesis(
                    hypothesis_text=hypothesis_text,
                    chunk_embeddings=chunk_embeddings,
                    chunks=chunks,
                    sbert_model=sbert_model,
                    model_name=model_name,
                    temperature=temperature
                )
                prediction = query_result.get("prediction")
                confidence = query_result.get("confidence")
                query_latency = query_result.get("query_latency_sec", 0.0)
                query_error = query_result.get("error")
            else:
                prediction = None
                confidence = None
                query_latency = 0.0
                query_error = premise_process_error

            query_latency_total += query_latency

            # Map prediction to binary
            prediction_binary = map_prediction_to_binary(prediction)

            # Check correctness
            is_correct = (prediction_binary == ground_truth) if prediction_binary else False
            if prediction_binary:
                premise_total += 1
                total_evaluated += 1
                if is_correct:
                    premise_correct += 1
                    total_correct += 1

            # Store result (matching Logify format)
            result_entry = {
                "premise_id": premise_id,
                "original_idx": original_idx,
                "hypothesis_text": hypothesis_text,
                "prediction": prediction,
                "prediction_binary": prediction_binary,
                "confidence": confidence,
                "ground_truth": ground_truth,
                "error": query_error
            }
            results["results"].append(result_entry)

            # Print progress
            status = "✓" if is_correct else ("✗" if prediction_binary else "?")
            print(f"    [{status}] hyp {hyp_idx + 1}: pred={prediction} ({prediction_binary}), gt={ground_truth}")

        # Store premise-level metrics (matching Logify format)
        premise_accuracy = premise_correct / premise_total if premise_total > 0 else 0.0
        premise_metrics = {
            "premise_id": premise_id,
            "premise_length": len(premise_text),
            "premise_word_count": premise_word_count,
            "num_hypotheses": len(hypotheses),
            "num_chunks": len(chunks) if chunks else 0,
            "premise_process_latency_sec": premise_process_latency,
            "premise_process_error": premise_process_error,
            "query_latency_total_sec": query_latency_total,
            "premise_correct": premise_correct,
            "premise_total": premise_total,
            "premise_accuracy": premise_accuracy
        }
        results["premise_metrics"].append(premise_metrics)

        print(f"  Premise accuracy: {premise_correct}/{premise_total} = {premise_accuracy:.2%}")
        print(f"  Premise process: {premise_process_latency:.2f}s, Query total: {query_latency_total:.2f}s")

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
    print(f"Premises processed: {len(premises)}")
    print(f"Hypotheses evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Results saved to: {output_path}")

    # Final save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """
    Command-line entry point.

    Parses arguments and runs the experiment.
    """
    parser = argparse.ArgumentParser(
        description="Run RAG baseline evaluation on DocNLI dataset",
        epilog="Output format matches experiment_logify_DocNLI.py for comparison."
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=SAMPLE_DATA_PATH,
        help=f"Path to sample data JSON (default: {SAMPLE_DATA_PATH})"
    )
    parser.add_argument(
        "--model",
        default=rag_config.DEFAULT_MODEL,
        help=f"LLM model name (default: {rag_config.DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="Sampling temperature (default: 0)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of premises to process (default: all)"
    )

    args = parser.parse_args()

    # Validate API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return 1

    # Validate data path
    if not args.data_path.exists():
        print(f"Error: Sample data not found: {args.data_path}")
        print("Run download_sample.py first to download the data.")
        return 1

    try:
        run_experiment(
            data_path=args.data_path,
            model_name=args.model,
            temperature=args.temperature,
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
