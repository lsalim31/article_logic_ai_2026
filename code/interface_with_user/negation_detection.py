#!/usr/bin/env python3
"""
Utilities for detecting negation and polarity mismatches in translated queries.

Purpose:
- Identifies negative wording in hypotheses and propositions.
- Checks whether a generated logical formula matches the query's polarity.
- Optionally suggests or applies a negation correction.

Inputs:
- Hypothesis text.
- Proposition translations.
- Generated logical formula.
- Retrieved proposition metadata.

Outputs:
- Boolean negation signals.
- Polarity validation results.
- Optional corrected logical formula and explanation.
"""

import re
from typing import List, Dict, Tuple, Optional


def detect_negation_in_hypothesis(hypothesis: str) -> bool:
    """
    Detect if hypothesis expresses prohibition or negation.

    Returns True for: "shall not", "only include", "no party may", etc.
    """
    negation_patterns = [
        r'\bshall not\b', r'\bmust not\b', r'\bcannot\b', r'\bcan not\b',
        r'\bwill not\b', r'\bmay not\b', r'\bshould not\b',
        r'\bprohibit(ed|s)?\b', r'\bforbid(den|s)?\b', r'\bban(ned|s)?\b',
        r'\bno\s+\w+\s+(shall|must|will|may|can)\b',
        r'\bneither\b.*\bnor\b',
        r'\bonly\s+include\b', r'\bexclusively\b', r'\bsolely\b',
        r'\bnot\s+\w+\s+(to|be|have)\b',
    ]

    for pattern in negation_patterns:
        if re.search(pattern, hypothesis, re.IGNORECASE):
            return True
    return False


def detect_negation_in_proposition(translation: str) -> bool:
    """
    Detect if proposition is phrased negatively.

    Returns True for: "does not", "without", "lacks", etc.
    """
    negation_indicators = [
        r'\bnot\b', r'\bno\b', r'\bnever\b', r'\bcannot\b', r'\bwithout\b',
        r'\bexclude(s|d)?\b', r'\bprohibit(s|ed)?\b', r'\bforbid(s|den)?\b',
        r'\black(s|ing)?\b', r'\babsent\b', r'\bmissing\b',
    ]

    for pattern in negation_indicators:
        if re.search(pattern, translation, re.IGNORECASE):
            return True
    return False


def check_polarity_match(
    hypothesis: str,
    formula: str,
    retrieved_props: List[Dict]
) -> Tuple[bool, str, Optional[str]]:
    """
    Check if hypothesis polarity matches formula.

    Returns:
        (is_valid, explanation, corrected_formula)
    """
    hypothesis_is_negative = detect_negation_in_hypothesis(hypothesis)
    formula_has_negation = bool(re.search(r'[¬~]', formula))

    props_are_negative = any(
        detect_negation_in_proposition(prop['translation'])
        for prop in retrieved_props
    )

    # Negative hypothesis without negation operator = mismatch
    if hypothesis_is_negative and not formula_has_negation and not props_are_negative:
        # Add negation to formula
        corrected = f"¬({formula})" if any(op in formula for op in ['∧', '∨', '⟹']) else f"¬{formula}"

        explanation = (
            f"POLARITY MISMATCH: Hypothesis '{hypothesis[:60]}...' is NEGATIVE "
            f"but formula '{formula}' has no negation. Suggested: '{corrected}'"
        )
        return False, explanation, corrected

    # Valid polarity
    return True, "Polarity consistent", None


def apply_polarity_correction(
    formula: str,
    hypothesis: str,
    retrieved_props: List[Dict],
    auto_correct: bool = False
) -> Tuple[str, bool, str]:
    """
    Validate and optionally auto-correct polarity.

    Returns:
        (final_formula, was_corrected, explanation)
    """
    is_valid, explanation, corrected_formula = check_polarity_match(
        hypothesis, formula, retrieved_props
    )

    if is_valid:
        return formula, False, explanation

    if auto_correct and corrected_formula:
        explanation += f"\n→ Auto-corrected: {formula} → {corrected_formula}"
        return corrected_formula, True, explanation
    else:
        explanation += f"\n→ Auto-correction disabled, using original: {formula}"
        return formula, False, explanation
