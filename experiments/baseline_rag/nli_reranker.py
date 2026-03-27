#!/usr/bin/env python3
"""
nli_reranker.py - NLI cross-encoder filtering for semantic precision

Filters SBERT-retrieved propositions using NLI cross-encoder to distinguish
entailment/contradiction from neutral (document-silent) cases.
"""

import numpy as np
from typing import List, Dict, Tuple
import sys
from pathlib import Path

# Add config directory to path
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import retrieval_config


def load_nli_model(model_name: str = None):
    """
    Load NLI cross-encoder model.

    Args:
        model_name: Model name (default: from retrieval_config)

    Returns:
        Loaded CrossEncoder model
    """
    from sentence_transformers import CrossEncoder
    model_name = model_name or retrieval_config.NLI_MODEL
    print(f"Loading NLI model: {model_name}")
    return CrossEncoder(model_name)


def score_nli_pairs(
    model,
    premise_hypothesis_pairs: List[Tuple[str, str]],
    batch_size: int = None
) -> np.ndarray:
    """
    Score (premise, hypothesis) pairs using NLI cross-encoder.

    Returns logits [contradiction, neutral, entailment] for each pair.

    Args:
        model: Loaded CrossEncoder model
        premise_hypothesis_pairs: List of (premise, hypothesis) tuples
        batch_size: Batch size for inference (default: from config)

    Returns:
        Array of shape (n_pairs, 3) with [P(contra), P(neutral), P(entail)]
    """
    batch_size = batch_size or retrieval_config.NLI_BATCH_SIZE

    # CrossEncoder expects pairs in format [(premise, hypothesis), ...]
    scores = model.predict(
        premise_hypothesis_pairs,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    # Apply softmax to get probabilities
    exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
    probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)

    return probs


def filter_propositions_by_nli(
    propositions: List[Dict],
    query: str,
    model,
    entailment_threshold: float = None,
    contradiction_threshold: float = None
) -> List[Dict]:
    """
    Filter propositions by NLI scores, keeping entailing or contradicting ones.

    Discards neutral propositions (document silent on hypothesis).

    Args:
        propositions: List of proposition dicts with 'translation' field
        query: User query/hypothesis
        model: Loaded NLI model
        entailment_threshold: Min P(entailment) to keep (default: from config)
        contradiction_threshold: Min P(contradiction) to keep (default: from config)

    Returns:
        Filtered list of propositions with NLI scores added
    """
    if not propositions:
        return []

    entailment_threshold = entailment_threshold or retrieval_config.NLI_ENTAILMENT_THRESHOLD
    contradiction_threshold = contradiction_threshold or retrieval_config.NLI_CONTRADICTION_THRESHOLD

    # Build (premise, hypothesis) pairs
    # Premise = proposition translation, Hypothesis = user query
    pairs = [(prop['translation'], query) for prop in propositions]

    # Score all pairs
    probs = score_nli_pairs(model, pairs)

    # Filter: keep if P(entailment) > threshold OR P(contradiction) > threshold
    filtered = []
    for prop, prob in zip(propositions, probs):
        p_contradiction = prob[0]
        p_neutral = prob[1]
        p_entailment = prob[2]

        # Keep if entails or contradicts (discard neutral)
        if p_entailment >= entailment_threshold or p_contradiction >= contradiction_threshold:
            prop_copy = prop.copy()
            prop_copy['nli_scores'] = {
                'contradiction': float(p_contradiction),
                'neutral': float(p_neutral),
                'entailment': float(p_entailment)
            }
            filtered.append(prop_copy)

    return filtered
