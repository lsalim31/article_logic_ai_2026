#!/usr/bin/env python3
"""
experiment_direct_llm_FeverNLI.py

Experiment: Direct LLM baseline for NLI on FEVER-NLI dataset.

This is the simplest baseline - just pass premise + hypothesis to LLM
and ask for TRUE/FALSE with chain-of-thought reasoning.

Pipeline:
    For each premise:
        For each hypothesis:
            1. Construct prompt with premise + hypothesis + CoT example
            2. Call LLM once
            3. Parse response -> TRUE/FALSE + confidence
            4. Map to binary label (TRUE -> entailment, FALSE -> not_entailment)

Output format matches experiment_logify_DocNLI.py for direct comparison.

Usage:
    python experiment_direct_llm_FeverNLI.py
    python experiment_direct_llm_FeverNLI.py --model openai/gpt-4o
    python experiment_direct_llm_FeverNLI.py --limit 5
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

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


# Paths
_script_dir = Path(__file__).resolve().parent
RESULTS_DIR = _script_dir / "results_direct_llm_FeverNLI"
SAMPLE_DATA_PATH = _script_dir / "fever-nli" / "sample_10.json"

# Default model
DEFAULT_MODEL = TRANSLATE_MODEL
DEFAULT_TEMPERATURE = 0.0


# Chain-of-Thought prompt with example
NLI_COT_PROMPT_TEMPLATE = """You are an expert at natural language inference (NLI). Your task is to determine whether a hypothesis is entailed by a premise.

## Definitions
- **TRUE (entailment)**: The premise provides sufficient evidence to conclude the hypothesis is true.
- **FALSE (not_entailment)**: The premise does NOT provide sufficient evidence. This includes:
  - The premise contradicts the hypothesis
  - The premise lacks enough information to confirm the hypothesis

## Instructions
Think step-by-step:
1. Identify the key claim in the hypothesis
2. Check if the premise explicitly or implicitly supports this claim
3. If the premise clearly supports the hypothesis, answer TRUE
4. If the premise contradicts OR simply doesn't mention/support the claim, answer FALSE

## Example

**Premise:** "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. It was constructed from 1887 to 1889 as the entrance arch for the 1889 World's Fair."

**Hypothesis:** "The Eiffel Tower was built in Paris."

**Reasoning:** 
- The hypothesis claims the Eiffel Tower was built in Paris.
- The premise states the tower is "on the Champ de Mars in Paris, France" and was "constructed from 1887 to 1889".
- "Constructed" means "built", and the location is explicitly stated as Paris.
- The premise directly supports the hypothesis.

**Answer:** TRUE
**Confidence:** 0.95

---

Now evaluate the following:

**Premise:** {premise}

**Hypothesis:** {hypothesis}

**Reasoning:**"""


@dataclass
class QueryDebugResult:
    """Result for a single hypothesis evaluation - matches Logify format."""
    premise_id: int
    original_idx: int
    hypothesis_text: str
    ground_truth: str
    prediction: Optional[str]
    prediction_binary: Optional[str]
    confidence: Optional[float]
    formula: Optional[str]  # None for direct LLM
    query_mode: Optional[str]  # "direct_llm" for this baseline
    explanation: Optional[str]  # LLM reasoning
    error: Optional[str]
    error_type: Optional[str]
    is_correct: bool
    query_latency_sec: float
    # These fields are None for direct LLM (Logify-specific)
    nli_confidence: Optional[float] = None
    sbert_confidence: Optional[float] = None
    voting_triggered: bool = False
    voting_confidence: Optional[float] = None
    vote_counts: Optional[Dict[str, int]] = None


def load_dataset(data_path: Path) -> Dict[str, Any]:
    """Load FEVER-NLI sample data."""
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_prediction_to_binary(prediction: Optional[str]) -> Optional[str]:
    """
    Map LLM prediction to binary label.
    
    TRUE -> entailment
    FALSE -> not_entailment
    UNCERTAIN -> not_entailment
    NOT MENTIONED -> not_entailment
    """
    if prediction is None:
        return None
    mapping = {
        "TRUE": "entailment",
        "FALSE": "not_entailment",
        "UNCERTAIN": "not_entailment",
        "NOT MENTIONED": "not_entailment",
    }
    return mapping.get(prediction.upper(), "not_entailment")


def parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract answer, confidence, and reasoning.
    
    Expected format:
        **Reasoning:** ...
        **Answer:** TRUE or FALSE
        **Confidence:** 0.0 to 1.0
    """
    answer = None
    confidence = 0.5
    reasoning = ""

    # Extract answer
    answer_match = re.search(r'\*\*Answer:\*\*\s*(TRUE|FALSE|UNCERTAIN)', response, re.IGNORECASE)
    if answer_match:
        answer = answer_match.group(1).upper()
    else:
        # Fallback: look for TRUE/FALSE in last 100 chars
        tail = response[-100:].upper()
        if "TRUE" in tail and "FALSE" not in tail:
            answer = "TRUE"
        elif "FALSE" in tail and "TRUE" not in tail:
            answer = "FALSE"
        else:
            # Last resort: scan full response
            if response.upper().count("TRUE") > response.upper().count("FALSE"):
                answer = "TRUE"
            else:
                answer = "FALSE"

    # Extract confidence
    confidence_match = re.search(r'\*\*Confidence:\*\*\s*([\d.]+)', response)
    if confidence_match:
        try:
            confidence = float(confidence_match.group(1))
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            confidence = 0.5
    else:
        # Fallback: look for decimal after "confidence"
        fallback_match = re.search(r'confidence[:\s]+([\d.]+)', response, re.IGNORECASE)
        if fallback_match:
            try:
                confidence = float(fallback_match.group(1))
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.5

    # Extract reasoning (everything before **Answer:**)
    reasoning_match = re.search(r'^(.*?)(?=\*\*Answer:|\Z)', response, re.DOTALL)
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()
        # Remove the **Reasoning:** prefix if present
        reasoning = re.sub(r'^\*\*Reasoning:\*\*\s*', '', reasoning)
    else:
        reasoning = response

    return {
        "answer": answer,
        "confidence": confidence,
        "reasoning": reasoning
    }


def call_llm(
    client: OpenAI,
    prompt: str,
    model: str,
    temperature: float
) -> str:
    """Call LLM API and return response."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content


def evaluate_hypothesis(
    client: OpenAI,
    premise_id: int,
    original_idx: int,
    premise_text: str,
    hypothesis_text: str,
    ground_truth: str,
    model: str,
    temperature: float
) -> QueryDebugResult:
    """Evaluate a single hypothesis against a premise using direct LLM with CoT."""
    start_time = time.time()

    try:
        # Construct prompt with CoT
        prompt = NLI_COT_PROMPT_TEMPLATE.format(
            premise=premise_text,
            hypothesis=hypothesis_text
        )

        # Call LLM
        raw_response = call_llm(client, prompt, model, temperature)

        # Parse response
        parsed = parse_llm_response(raw_response)
        prediction = parsed["answer"]
        confidence = parsed["confidence"]
        reasoning = parsed["reasoning"]

        # Map to binary
        prediction_binary = map_prediction_to_binary(prediction)
        is_correct = (prediction_binary == ground_truth)

        return QueryDebugResult(
            premise_id=premise_id,
            original_idx=original_idx,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=prediction,
            prediction_binary=prediction_binary,
            confidence=confidence,
            formula=None,  # No formula for direct LLM
            query_mode="direct_llm",
            explanation=reasoning,  # LLM's chain-of-thought
            error=None,
            error_type=None,
            is_correct=is_correct,
            query_latency_sec=time.time() - start_time,
            # Logify-specific fields (None for this baseline)
            nli_confidence=None,
            sbert_confidence=None,
            voting_triggered=False,
            voting_confidence=None,
            vote_counts=None,
        )

    except Exception as e:
        return QueryDebugResult(
            premise_id=premise_id,
            original_idx=original_idx,
            hypothesis_text=hypothesis_text,
            ground_truth=ground_truth,
            prediction=None,
            prediction_binary=None,
            confidence=None,
            formula=None,
            query_mode="direct_llm",
            explanation=None,
            error=str(e),
            error_type="runtime_error",
            is_correct=False,
            query_latency_sec=time.time() - start_time,
        )


def run_experiment(
    api_key: str,
    data_path: Path = SAMPLE_DATA_PATH,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    premise_id: Optional[int] = None,
    limit: Optional[int] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """Run the direct LLM baseline experiment."""

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize OpenAI client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

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

    # Initialize results (matching Logify format)
    timestamp = datetime.now().isoformat()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp_str}.json"

    results_payload = {
        "metadata": {
            "experiment_type": "direct_llm_baseline",
            "timestamp": timestamp,
            "data_path": str(data_path),
            "model": model,
            "query_model": model,  # For compatibility with Logify output
            "temperature": temperature,
            "num_premises": len(premises),
            "num_hypotheses": total_hypotheses,
            "premise_filter": premise_id,
            "limit": limit,
            "data_metadata": metadata,
        },
        "premise_metrics": [],
        "results": [],
    }

    results: List[QueryDebugResult] = []
    total_correct = 0
    total_evaluated = 0
    total_errors = 0

    # Process each premise
    for premise_idx, premise_data in enumerate(premises):
        current_premise_id = premise_data.get("premise_id")
        premise_text = premise_data.get("premise", "")
        premise_word_count = premise_data.get("premise_word_count", len(premise_text.split()))
        hypotheses = premise_data.get("hypotheses", [])

        print(f"\n[{premise_idx + 1}/{len(premises)}] Premise {current_premise_id}: {premise_word_count} words, {len(hypotheses)} hypotheses")

        if not premise_text or not premise_text.strip():
            print(f"  [SKIP] Empty premise text")
            results_payload["premise_metrics"].append({
                "premise_id": current_premise_id,
                "premise_length": len(premise_text),
                "premise_word_count": premise_word_count,
                "num_hypotheses": len(hypotheses),
                "logify_latency_sec": 0.0,  # N/A for direct LLM
                "logify_cached": False,
                "logify_error": None,
                "query_latency_total_sec": 0.0,
                "premise_correct": 0,
                "premise_total": 0,
                "premise_accuracy": 0.0,
            })
            continue

        premise_correct = 0
        premise_total = 0
        query_latency_total = 0.0

        # Evaluate each hypothesis
        for hyp_idx, hyp in enumerate(hypotheses):
            original_idx = hyp.get("original_idx", hyp_idx)
            hypothesis_text = hyp.get("hypothesis", "")
            ground_truth = hyp.get("label", "not_entailment")

            result = evaluate_hypothesis(
                client=client,
                premise_id=current_premise_id,
                original_idx=original_idx,
                premise_text=premise_text,
                hypothesis_text=hypothesis_text,
                ground_truth=ground_truth,
                model=model,
                temperature=temperature
            )

            results.append(result)
            results_payload["results"].append(asdict(result))
            query_latency_total += result.query_latency_sec

            if result.prediction_binary is not None:
                premise_total += 1
                total_evaluated += 1
                if result.is_correct:
                    premise_correct += 1
                    total_correct += 1

            if result.error:
                total_errors += 1

            # Print progress
            status = "✓" if result.is_correct else ("?" if result.prediction is None else "✗")
            print(f"  [{status}] hyp {hyp_idx + 1}: pred={result.prediction} ({result.prediction_binary}) gt={ground_truth}")
            if verbose and result.explanation:
                reasoning_short = result.explanation[:100] + "..." if len(result.explanation) > 100 else result.explanation
                print(f"      reasoning: {reasoning_short}")
            if result.error:
                print(f"      error ({result.error_type}): {result.error}")

        # Store premise metrics (matching Logify format)
        premise_accuracy = premise_correct / premise_total if premise_total > 0 else 0.0
        premise_metrics = {
            "premise_id": current_premise_id,
            "premise_length": len(premise_text),
            "premise_word_count": premise_word_count,
            "num_hypotheses": len(hypotheses),
            "logify_latency_sec": 0.0,  # N/A for direct LLM
            "logify_cached": False,
            "logify_error": None,
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

    # Final summary
    overall_accuracy = total_correct / total_evaluated if total_evaluated > 0 else 0.0
    results_payload["metadata"]["total_correct"] = total_correct
    results_payload["metadata"]["total_evaluated"] = total_evaluated
    results_payload["metadata"]["overall_accuracy"] = overall_accuracy
    results_payload["metadata"]["total_errors"] = total_errors

    # Save final results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Premises processed: {len(premises)}")
    print(f"Hypotheses evaluated: {total_evaluated}")
    print(f"Correct predictions: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print(f"Total errors: {total_errors}")
    print(f"Results saved to: {output_path}")

    return results_payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Direct LLM baseline (with CoT) for FEVER-NLI"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENROUTER_API_KEY"),
        help="API key (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=SAMPLE_DATA_PATH,
        help=f"Path to sample data JSON (default: {SAMPLE_DATA_PATH})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE})",
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
            model=args.model,
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
