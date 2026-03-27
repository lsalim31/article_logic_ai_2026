#!/usr/bin/env python3
"""
experiment_rag_contract_NLI.py

Experiment: Evaluate RAG baseline on ContractNLI dataset.

This script runs the Reasoning LLM + RAG baseline on ContractNLI,
using the same data source, evaluation structure, and output format
as the Logify experiment for fair comparison.

Pipeline:
    For each document in ContractNLI:
        1. Chunk document into overlapping segments
        2. Encode chunks using SBERT
        3. For each of 17 hypotheses:
            a. Retrieve top-k relevant chunks
            b. Perform Chain-of-Thought reasoning with LLM
            c. Parse response to extract prediction and confidence
            d. Store result
        4. Save intermediate results

Output format matches experiment_logify_contract_NLI.py exactly.

Usage:
    python experiment_rag_contract_NLI.py --dataset-path contract-nli/dev.json
    python experiment_rag_contract_NLI.py --dataset-path contract-nli/dev.json --num-docs 5
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

# Results directory
RESULTS_DIR = _script_dir / "results_rag_contract_NLI"


# =============================================================================
# ContractNLI-specific Chain-of-Thought Prompt Template
# =============================================================================

CONTRACTNLI_COT_PROMPT = """You are a legal contract analyst. Given excerpts from a contract and a hypothesis, determine whether the hypothesis is supported by the contract.

**Contract Excerpts:**
{context}

**Hypothesis:** {hypothesis}

**Instructions:**
1. Carefully read the contract excerpts provided above
2. Determine if the hypothesis is:
   - TRUE: The contract clearly states or logically entails this hypothesis
   - FALSE: The contract clearly contradicts this hypothesis
   - UNCERTAIN: The contract does not mention or address this hypothesis
3. Provide your confidence level as a number between 0.0 and 1.0:
   - 1.0 = Absolutely certain (explicit statement in contract)
   - 0.7-0.9 = High confidence (strong implication)
   - 0.4-0.6 = Moderate confidence (some evidence but not conclusive)
   - 0.1-0.3 = Low confidence (weak or indirect evidence)
   - 0.0 = No support for this conclusion

**Format your response exactly as follows:**
**Reasoning:** [Your step-by-step analysis of the contract excerpts]
**Answer:** [TRUE or FALSE or UNCERTAIN]
**Confidence:** [A number between 0.0 and 1.0]

Begin your analysis:"""


# =============================================================================
# Data Loading (same as Logify experiment)
# =============================================================================

def load_contractnli_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Load ContractNLI dataset from local JSON file.

    Args:
        dataset_path: Path to ContractNLI JSON file (e.g., dev.json)

    Returns:
        Dictionary containing 'documents' and 'labels' keys
    """
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_ground_truth_label(choice: str) -> str:
    """
    Map ContractNLI label to experiment output format.

    Mapping:
        Entailment -> TRUE
        Contradiction -> FALSE
        NotMentioned -> UNCERTAIN

    Args:
        choice: ContractNLI label string

    Returns:
        Mapped label (TRUE, FALSE, or UNCERTAIN)
    """
    mapping = {
        "Entailment": "TRUE",
        "Contradiction": "FALSE",
        "NotMentioned": "UNCERTAIN"
    }
    return mapping.get(choice, "UNCERTAIN")


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
    prompt = CONTRACTNLI_COT_PROMPT.format(
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
    Process a single hypothesis against pre-computed document chunks.

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
# Document Processing
# =============================================================================

def process_document(
    doc_text: str,
    sbert_model
) -> tuple:
    """
    Chunk and encode a document for retrieval.

    Args:
        doc_text: Full document text
        sbert_model: Loaded SBERT model

    Returns:
        Tuple of (chunks, chunk_embeddings)
    """
    # Chunk the document using config settings
    chunks = chunk_document(
        doc_text,
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
    dataset_path: str,
    model_name: str = None,
    temperature: float = 0,
    num_docs: int = 20
) -> Dict[str, Any]:
    """
    Run the ContractNLI RAG baseline experiment.

    Args:
        dataset_path: Path to ContractNLI JSON file
        model_name: LLM model name (default: from rag_config)
        temperature: Sampling temperature (default: 0)
        num_docs: Number of documents to process (default: 20)

    Returns:
        Experiment results dictionary matching Logify output format
    """
    # Use default model if not specified
    if model_name is None:
        model_name = rag_config.DEFAULT_MODEL

    # Ensure results directory exists
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

        # Process document (chunk and encode)
        doc_start_time = time.time()
        try:
            chunks, chunk_embeddings = process_document(doc_text, sbert_model)
            doc_process_latency = time.time() - doc_start_time
            doc_process_error = None
            print(f"  Created {len(chunks)} chunks in {doc_process_latency:.2f}s")
        except Exception as e:
            print(f"  [ERROR] Document processing failed: {e}")
            chunks = None
            chunk_embeddings = None
            doc_process_latency = time.time() - doc_start_time
            doc_process_error = str(e)

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
                query_error = doc_process_error

            query_latency_total += query_latency

            # Check correctness
            is_correct = (prediction == ground_truth) if prediction else False
            if prediction:
                doc_total += 1
                total_pairs += 1
                if is_correct:
                    doc_correct += 1
                    total_correct += 1

            # Store result (matching Logify format)
            result_entry = {
                "doc_id": doc_id,
                "hypothesis_key": hyp_key,
                "hypothesis_text": hypothesis_text,
                "prediction": prediction,
                "confidence": confidence,
                "ground_truth": ground_truth,
                "amount_evidence": amount_evidence,
                "error": query_error
            }
            results["results"].append(result_entry)

            # Print progress
            status = "✓" if is_correct else ("✗" if prediction else "?")
            print(f"    [{status}] {hyp_key}: pred={prediction}, gt={ground_truth}, conf={confidence}")

        # Document summary
        doc_accuracy = doc_correct / doc_total if doc_total > 0 else 0.0
        print(f"  Document accuracy: {doc_correct}/{doc_total} = {doc_accuracy:.2%}")
        print(f"  Document process latency: {doc_process_latency:.2f}s")
        print(f"  Query latency total: {query_latency_total:.2f}s")

        # Store document-level metrics (matching Logify format)
        doc_metrics = {
            "doc_id": doc_id,
            "text_length": len(doc_text),
            "num_chunks": len(chunks) if chunks else 0,
            "doc_process_latency_sec": doc_process_latency,
            "doc_process_error": doc_process_error,
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


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """
    Command-line entry point.

    Parses arguments and runs the experiment.
    """
    parser = argparse.ArgumentParser(
        description="Run RAG baseline evaluation on ContractNLI dataset",
        epilog="Output format matches experiment_logify_contract_NLI.py for comparison."
    )
    parser.add_argument(
        "--dataset-path",
        required=True,
        help="Path to ContractNLI JSON file (e.g., contract-nli/dev.json)"
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
        "--num-docs",
        type=int,
        default=20,
        help="Number of documents to process (default: 20)"
    )

    args = parser.parse_args()

    # Validate API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return 1

    # Validate dataset path
    if not Path(args.dataset_path).exists():
        print(f"Error: Dataset not found: {args.dataset_path}")
        return 1

    try:
        run_experiment(
            dataset_path=args.dataset_path,
            model_name=args.model,
            temperature=args.temperature,
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
