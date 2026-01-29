#!/usr/bin/env python3
"""
semantic_bridging.py - Post-processing to add semantic bridging constraints

This module detects semantically similar propositions and adds bridging constraints
to capture implicit logical relationships that may not be explicitly stated in the text.

Key patterns detected:
1. Commitment/intention → action (e.g., "committed to X" ⟹ "does X")
2. Negation equivalences (e.g., "not prone to X" ⟺ "¬susceptible to X")
3. Subset/superset relations (e.g., "X all day" ⟹ "X half the day")
4. Synonymous propositions (e.g., "stay healthy" ⟺ "maintain good health")
"""

import re
from typing import Dict, List, Any, Tuple, Optional
import numpy as np


# Patterns for detecting commitment/intention phrases
COMMITMENT_PATTERNS = [
    r'\b(committed to|dedicated to|determined to|resolved to)\b',
    r'\b(plans to|intends to|aims to|wants to)\b',
    r'\b(should|ought to|supposed to)\b',
]

# Patterns for negation equivalences (pattern1, pattern2) where P1 ⟺ ¬P2
NEGATION_PATTERNS = [
    (r'\bnot prone to\b', r'\bsusceptible to\b'),
    (r'\bnot susceptible to\b', r'\bprone to\b'),
    (r'\bimmune to\b', r'\baffected by\b'),
    (r'\bunable to\b', r'\bable to\b'),
    (r'\bincapable of\b', r'\bcapable of\b'),
    (r'\bnot prone to\b', r'\bmore susceptible to\b'),
    (r'\bnot prone to\b', r'\bbecome.* susceptible to\b'),
]

# Antonym pairs for detecting opposite concepts that cannot both be true
# Only include truly mutually exclusive pairs
ANTONYM_PAIRS = [
    ('healthy', 'ill'),
    ('healthy', 'sick'),
    ('prone to', 'immune to'),
    ('susceptible to', 'resistant to'),
]

# Minimum similarity threshold for semantic bridging
DEFAULT_SIMILARITY_THRESHOLD = 0.75


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute simple text similarity using word overlap (Jaccard similarity).
    Falls back to this when SBERT is not available.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score in [0, 1]
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def compute_sbert_similarity(texts: List[str]) -> np.ndarray:
    """
    Compute pairwise similarity matrix using SBERT.

    Args:
        texts: List of text strings

    Returns:
        Pairwise similarity matrix (n x n)
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)

        # Compute cosine similarity matrix
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-9)
        similarity_matrix = np.dot(normalized, normalized.T)

        return similarity_matrix
    except ImportError:
        # Fallback to Jaccard similarity
        n = len(texts)
        similarity_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                similarity_matrix[i, j] = compute_text_similarity(texts[i], texts[j])
        return similarity_matrix


def extract_action_from_commitment(text: str) -> Optional[str]:
    """
    Extract the action part from a commitment phrase.

    E.g., "I am committed to watching my diet" -> "watching my diet"

    Args:
        text: Text containing a commitment phrase

    Returns:
        The action part, or None if no commitment pattern found
    """
    text_lower = text.lower()

    for pattern in COMMITMENT_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            # Extract text after the commitment phrase
            action = text_lower[match.end():].strip()
            # Clean up common patterns
            action = re.sub(r'^(that |to )', '', action)
            return action if action else None

    return None


def detect_commitment_action_pairs(propositions: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Detect pairs where one proposition is a commitment and another is the corresponding action.

    Args:
        propositions: List of proposition dicts with 'id' and 'translation' fields

    Returns:
        List of tuples (commitment_id, action_id, reasoning)
    """
    pairs = []

    for i, p1 in enumerate(propositions):
        t1 = p1.get('translation', '')
        action = extract_action_from_commitment(t1)

        if action:
            # Find propositions that match this action
            for j, p2 in enumerate(propositions):
                if i == j:
                    continue

                t2 = p2.get('translation', '').lower()

                # Check if t2 contains the action (with some flexibility)
                action_words = set(action.split())
                t2_words = set(t2.split())

                # If most action words appear in t2
                overlap = len(action_words & t2_words) / len(action_words) if action_words else 0

                if overlap >= 0.6:
                    pairs.append((
                        p1['id'],
                        p2['id'],
                        f"Commitment '{t1}' implies action '{p2.get('translation', '')}'"
                    ))

    return pairs


def detect_negation_equivalences(propositions: List[Dict]) -> List[Tuple[str, str, str, str]]:
    """
    Detect pairs where one proposition is a negation equivalent of another.

    Args:
        propositions: List of proposition dicts

    Returns:
        List of tuples (id1, id2, operator, reasoning) where operator is '⟹' or '⟺'
    """
    pairs = []

    for i, p1 in enumerate(propositions):
        t1 = p1.get('translation', '').lower()

        # Check explicit negation patterns
        for neg_pattern, pos_pattern in NEGATION_PATTERNS:
            if re.search(neg_pattern, t1):
                # Look for the positive equivalent
                for j, p2 in enumerate(propositions):
                    if i == j:
                        continue

                    t2 = p2.get('translation', '').lower()

                    if re.search(pos_pattern, t2):
                        # Check if the rest of the text is similar
                        t1_clean = re.sub(neg_pattern, '', t1).strip()
                        t2_clean = re.sub(pos_pattern, '', t2).strip()

                        if compute_text_similarity(t1_clean, t2_clean) > 0.3:
                            pairs.append((
                                p1['id'],
                                p2['id'],
                                '⟺',
                                f"'{p1.get('translation', '')}' is equivalent to ¬'{p2.get('translation', '')}'"
                            ))

    # Check antonym pairs
    for i, p1 in enumerate(propositions):
        t1 = p1.get('translation', '').lower()

        for j, p2 in enumerate(propositions):
            if i >= j:  # Avoid duplicates
                continue

            t2 = p2.get('translation', '').lower()

            for ant1, ant2 in ANTONYM_PAIRS:
                # Check if one proposition has ant1 and other has ant2
                has_ant1_in_t1 = re.search(ant1, t1) is not None
                has_ant2_in_t2 = re.search(ant2, t2) is not None
                has_ant1_in_t2 = re.search(ant1, t2) is not None
                has_ant2_in_t1 = re.search(ant2, t1) is not None

                if (has_ant1_in_t1 and has_ant2_in_t2) or (has_ant2_in_t1 and has_ant1_in_t2):
                    # These are likely antonyms - add mutual exclusion constraint
                    pairs.append((
                        p1['id'],
                        p2['id'],
                        'MUTEX',  # Special marker for mutual exclusion
                        f"'{p1.get('translation', '')}' and '{p2.get('translation', '')}' are antonyms (cannot both be true)"
                    ))

    return pairs


def detect_similar_propositions(propositions: List[Dict], threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> List[Tuple[str, str, float]]:
    """
    Detect highly similar propositions that should be logically linked.

    Args:
        propositions: List of proposition dicts
        threshold: Minimum similarity threshold

    Returns:
        List of tuples (id1, id2, similarity)
    """
    if len(propositions) < 2:
        return []

    texts = [p.get('translation', '') for p in propositions]
    similarity_matrix = compute_sbert_similarity(texts)

    pairs = []
    for i in range(len(propositions)):
        for j in range(i + 1, len(propositions)):
            sim = similarity_matrix[i, j]
            if sim >= threshold:
                pairs.append((propositions[i]['id'], propositions[j]['id'], float(sim)))

    return pairs


def add_semantic_bridges(structure: Dict[str, Any],
                         similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
                         verbose: bool = False) -> Dict[str, Any]:
    """
    Add semantic bridging constraints to a logified structure.

    This post-processing step detects:
    1. Commitment → action implications
    2. Negation equivalences
    3. Highly similar propositions that should be linked

    Args:
        structure: Logified structure with primitive_props, hard_constraints, soft_constraints
        similarity_threshold: Minimum similarity for detecting similar propositions
        verbose: Print debug information

    Returns:
        Modified structure with additional bridging constraints
    """
    props = structure.get('primitive_props', [])
    hard_constraints = structure.get('hard_constraints', [])

    if not props:
        return structure

    # Track existing constraint formulas to avoid duplicates
    existing_formulas = set()
    for c in hard_constraints:
        existing_formulas.add(c.get('formula', ''))
    for c in structure.get('soft_constraints', []):
        existing_formulas.add(c.get('formula', ''))

    new_constraints = []
    bridge_id_counter = 1

    # 1. Detect commitment → action pairs
    commitment_pairs = detect_commitment_action_pairs(props)
    for commit_id, action_id, reasoning in commitment_pairs:
        formula = f"{commit_id} ⟹ {action_id}"
        if formula not in existing_formulas:
            new_constraints.append({
                "id": f"BRIDGE_{bridge_id_counter}",
                "formula": formula,
                "translation": f"Commitment implies action",
                "evidence": "Semantic bridging: commitment/intention implies the action",
                "reasoning": reasoning
            })
            existing_formulas.add(formula)
            bridge_id_counter += 1

            if verbose:
                print(f"  Added commitment bridge: {formula}")

    # 2. Detect negation equivalences and antonym pairs
    negation_pairs = detect_negation_equivalences(props)
    for id1, id2, operator, reasoning in negation_pairs:
        if operator == 'MUTEX':
            # Mutual exclusion: ¬(P1 ∧ P2) - cannot both be true
            formula = f"¬({id1} ∧ {id2})"
            if formula not in existing_formulas:
                new_constraints.append({
                    "id": f"BRIDGE_{bridge_id_counter}",
                    "formula": formula,
                    "translation": f"Mutual exclusion (antonyms)",
                    "evidence": "Semantic bridging: antonym pair detected",
                    "reasoning": reasoning
                })
                existing_formulas.add(formula)
                bridge_id_counter += 1

                if verbose:
                    print(f"  Added mutex bridge: {formula}")
        else:
            # "not prone to X" ⟺ ¬"susceptible to X"
            formula = f"{id1} ⟺ ¬{id2}"
            if formula not in existing_formulas:
                new_constraints.append({
                    "id": f"BRIDGE_{bridge_id_counter}",
                    "formula": formula,
                    "translation": f"Negation equivalence",
                    "evidence": "Semantic bridging: negation equivalence detected",
                    "reasoning": reasoning
                })
                existing_formulas.add(formula)
                bridge_id_counter += 1

                if verbose:
                    print(f"  Added negation bridge: {formula}")

    # 3. Detect highly similar propositions
    similar_pairs = detect_similar_propositions(props, similarity_threshold)
    for id1, id2, sim in similar_pairs:
        # For very high similarity, use biconditional
        if sim >= 0.9:
            formula = f"{id1} ⟺ {id2}"
        else:
            # For moderate similarity, consider both directions as soft constraints
            # But add as hard constraint if similarity is very high
            formula = f"{id1} ⟺ {id2}"

        if formula not in existing_formulas:
            # Find the proposition texts for the reasoning
            p1_text = next((p['translation'] for p in props if p['id'] == id1), id1)
            p2_text = next((p['translation'] for p in props if p['id'] == id2), id2)

            new_constraints.append({
                "id": f"BRIDGE_{bridge_id_counter}",
                "formula": formula,
                "translation": f"Semantic equivalence",
                "evidence": f"Semantic bridging: similarity={sim:.3f}",
                "reasoning": f"'{p1_text}' is semantically equivalent to '{p2_text}'"
            })
            existing_formulas.add(formula)
            bridge_id_counter += 1

            if verbose:
                print(f"  Added similarity bridge: {formula} (sim={sim:.3f})")

    # Add new constraints to hard_constraints
    if new_constraints:
        structure['hard_constraints'] = hard_constraints + new_constraints
        if verbose:
            print(f"  Total bridges added: {len(new_constraints)}")

    return structure


def main():
    """Test semantic bridging with a sample structure."""
    sample_structure = {
        "primitive_props": [
            {"id": "P_1", "translation": "I watch my diet"},
            {"id": "P_2", "translation": "I maintain good health"},
            {"id": "P_3", "translation": "I consume excessive junk food"},
            {"id": "P_4", "translation": "I become more susceptible to illnesses"},
            {"id": "P_5", "translation": "I am committed to watching my diet"},
            {"id": "P_6", "translation": "I am not prone to illnesses"},
        ],
        "hard_constraints": [
            {"id": "H_1", "formula": "P_1 ⟹ P_2"},
            {"id": "H_2", "formula": "P_3 ⟹ P_4"},
            {"id": "H_3", "formula": "P_5 ∨ P_6"},
        ],
        "soft_constraints": []
    }

    print("Original structure:")
    print(f"  Hard constraints: {[c['formula'] for c in sample_structure['hard_constraints']]}")

    print("\nApplying semantic bridging...")
    result = add_semantic_bridges(sample_structure, verbose=True)

    print("\nUpdated structure:")
    print(f"  Hard constraints: {[c['formula'] for c in result['hard_constraints']]}")


if __name__ == "__main__":
    main()
