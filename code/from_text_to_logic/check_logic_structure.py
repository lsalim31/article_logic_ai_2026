#!/usr/bin/env python3
"""
check_logic_structure.py - Deterministic enrichment of logified JSON

This module reads the LLM-generated logified.json and enriches it by:
1. Verifying and completing modal pairs (P_modal, P_base, constraints)
2. Detecting modal opposites and adding exclusion constraints
3. Detecting explicit negations in source text
4. Verifying auxiliary negative constraints

Pipeline position:
    logify.py → logified.json → [THIS FILE] → logified_enriched.json → weights.py

Usage:
    python check_logic_structure.py logified.json source_document.txt
    
Usage (Python):
    from from_text_to_logic.check_logic_structure import enrich_logic_structure
    enriched = enrich_logic_structure(logified_path="logified.json", source_path="doc.txt")

    update: Feb 21:
    Main function: Enrich logified.json with deterministic constraint verification.

    Runs all five enrichment steps:
    1. verify_modal_pairs - Handle modal words (typically, sometimes, etc.)
    2. detect_modal_opposites - Add exclusion constraints for modal antonyms
    3. detect_explicit_negations - Find negations in source text
    4. generate_finite_domain_auxiliaries - Create auxiliaries for academic majors, roles, etc.
    5. verify_auxiliary_negatives - Ensure all auxiliaries have proper constraints

    Args:
    ...
    

"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import spacy
import nltk
from nltk.corpus import wordnet

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch


# Ensure wordnet is downloaded
try:
    wordnet.synsets('test')
except LookupError:
    nltk.download('wordnet')

# Import SBERT utilities from existing codebase
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    raise ImportError("Please install sentence-transformers: pip install sentence-transformers")


# =============================================================================
# CONSTANTS
# =============================================================================

MODAL_WORDS: Dict[str, float] = {
    # word: default_weight for base event
    
    # =========================================================================
    # ABSOLUTE CERTAINTY (weight = 1.0)
    # =========================================================================
    "always": 1.0,
    "never": 1.0,
    "must": 1.0,
    "cannot": 1.0,
    "invariably": 1.0,
    "absolutely": 1.0,
    "certainly": 1.0,
    "definitely": 1.0,
    "undoubtedly": 1.0,
    "necessarily": 1.0,
    "inevitably": 1.0,
    "unconditionally": 1.0,
    "perpetually": 1.0,
    "constantly": 1.0,
    "continuously": 1.0,
    "permanently": 1.0,
    "eternally": 1.0,
    "unfailingly": 1.0,
    
    # Prohibition / Impossibility
    "forbidden": 1.0,
    "prohibited": 1.0,
    "banned": 1.0,
    "barred": 1.0,
    "impossible": 1.0,
    "inconceivable": 1.0,
    
    # Requirement / Obligation
    "required": 0.95,
    "mandatory": 0.95,
    "obligatory": 0.95,
    "compulsory": 0.95,
    "essential": 0.95,
    "imperative": 0.95,
    "necessary": 0.95,
    "needed": 0.90,
    
    # =========================================================================
    # STRONG PROBABILITY / EXPECTATION (weight = 0.85)
    # =========================================================================
    "should": 0.85,
    "ought": 0.85,
    "expected": 0.85,
    "supposed": 0.85,
    "likely": 0.85,
    "probably": 0.85,
    "presumably": 0.85,
    "predominantly": 0.85,
    "primarily": 0.85,
    "mainly": 0.85,
    "mostly": 0.85,
    "largely": 0.85,
    "chiefly": 0.85,
    "principally": 0.85,
    
    # Recommendations
    "recommended": 0.85,
    "advised": 0.85,
    "suggested": 0.80,
    "preferred": 0.80,
    "desirable": 0.80,
    "advisable": 0.80,
    
    # =========================================================================
    # HIGH FREQUENCY / TENDENCY (weight = 0.65-0.75)
    # =========================================================================
    "typically": 0.70,
    "usually": 0.70,
    "generally": 0.70,
    "normally": 0.70,
    "ordinarily": 0.70,
    "customarily": 0.70,
    "habitually": 0.70,
    "routinely": 0.70,
    "regularly": 0.70,
    "commonly": 0.70,
    "standardly": 0.70,
    "conventionally": 0.70,
    "traditionally": 0.70,
    
    "often": 0.65,
    "frequently": 0.65,
    "repeatedly": 0.65,
    "recurrently": 0.65,
    
    # =========================================================================
    # MODERATE FREQUENCY / POSSIBILITY (weight = 0.40-0.55)
    # =========================================================================
    "sometimes": 0.45,
    "occasionally": 0.45,
    "periodically": 0.45,
    "intermittently": 0.45,
    "sporadically": 0.40,
    
    # Possibility
    "may": 0.50,
    "might": 0.45,
    "could": 0.45,
    "can": 0.50,
    "possibly": 0.45,
    "perhaps": 0.45,
    "maybe": 0.45,
    "conceivably": 0.40,
    "potentially": 0.50,
    "feasibly": 0.50,
    "plausibly": 0.50,
    
    # Weak suggestion / permission
    "encouraged": 0.45,
    "permitted": 0.50,
    "allowed": 0.50,
    "acceptable": 0.50,
    "optional": 0.40,
    "discretionary": 0.40,
    
    # =========================================================================
    # LOW FREQUENCY / WEAK (weight = 0.20-0.35)
    # =========================================================================
    "rarely": 0.25,
    "seldom": 0.25,
    "infrequently": 0.25,
    "uncommonly": 0.25,
    "barely": 0.20,
    "scarcely": 0.20,
    "little": 0.30,
    "few": 0.30,
    
    # Weak / unlikely
    "unlikely": 0.25,
    "improbable": 0.20,
    "doubtful": 0.25,
    "questionable": 0.30,
    "uncertain": 0.35,
    "unsure": 0.35,
    
    # Discouraged
    "discouraged": 0.30,
    "inadvisable": 0.25,
    "undesirable": 0.25,
    
    # =========================================================================
    # CONDITIONAL / CONTEXTUAL (weight varies)
    # =========================================================================
    "ideally": 0.60,
    "preferably": 0.65,
    "optimally": 0.60,
    "hopefully": 0.50,
    "theoretically": 0.50,
    "hypothetically": 0.40,
    "supposedly": 0.55,
    "allegedly": 0.45,
    "reportedly": 0.55,
    "apparently": 0.60,
    "seemingly": 0.55,
    "ostensibly": 0.50,
    "purportedly": 0.50,
    
    # =========================================================================
    # TEMPORAL MODIFIERS (weight based on implication)
    # =========================================================================
    "eventually": 0.70,
    "ultimately": 0.75,
    "finally": 0.80,
    "temporarily": 0.50,
    "briefly": 0.40,
    "momentarily": 0.35,
    "soon": 0.65,
    "shortly": 0.65,
    "immediately": 0.90,
    "instantly": 0.90,
    "promptly": 0.85,
    "currently": 0.80,
    "presently": 0.75,
    "formerly": 0.70,
    "previously": 0.70,
}


MODAL_OPPOSITES_FALLBACK: Dict[str, List[str]] = {
    # =========================================================================
    # FREQUENCY OPPOSITES
    # =========================================================================
    "always": ["never"],
    "never": ["always"],
    "invariably": ["never"],
    "perpetually": ["never"],
    "constantly": ["never", "rarely"],
    "continuously": ["never", "intermittently"],
    
    "often": ["rarely", "seldom", "infrequently"],
    "frequently": ["rarely", "seldom", "infrequently"],
    "regularly": ["rarely", "irregularly", "sporadically"],
    "repeatedly": ["rarely", "seldom"],
    "commonly": ["rarely", "uncommonly"],
    "usually": ["rarely", "seldom"],
    "typically": ["rarely", "seldom", "never"],
    "normally": ["rarely", "seldom"],
    "generally": ["rarely", "seldom"],
    "ordinarily": ["rarely"],
    "customarily": ["rarely"],
    "habitually": ["rarely", "occasionally"],
    "routinely": ["rarely", "sporadically"],
    
    "rarely": ["often", "frequently", "commonly", "usually"],
    "seldom": ["often", "frequently", "commonly"],
    "infrequently": ["often", "frequently", "regularly"],
    "uncommonly": ["often", "commonly", "frequently"],
    "sporadically": ["regularly", "constantly", "continuously"],
    "intermittently": ["continuously", "constantly"],
    
    "sometimes": ["always", "never"],
    "occasionally": ["always", "frequently", "constantly"],
    "periodically": ["constantly", "continuously"],
    "never": ["always", "sometimes", "often", "frequently", "usually", "typically"],
 

    
    # =========================================================================
    # PROBABILITY OPPOSITES
    # =========================================================================
    "likely": ["unlikely", "improbable"],
    "unlikely": ["likely", "probably"],
    "probably": ["unlikely"],
    "possibly": ["certainly"],
    "certainly": ["possibly", "uncertainly"],
    "definitely": ["possibly", "maybe"],
    "perhaps": ["certainly", "definitely"],
    "maybe": ["certainly", "definitely"],
    
    # =========================================================================
    # OBLIGATION / PERMISSION OPPOSITES
    # =========================================================================
    "required": ["forbidden", "prohibited", "optional"],
    "mandatory": ["optional", "forbidden"],
    "obligatory": ["optional", "forbidden"],
    "compulsory": ["optional"],
    "necessary": ["unnecessary", "optional"],
    "essential": ["optional", "unnecessary"],
    "needed": ["unneeded", "unnecessary"],
    
    "forbidden": ["required", "mandatory", "permitted", "allowed"],
    "prohibited": ["required", "permitted", "allowed", "mandatory"],
    "banned": ["permitted", "allowed", "required"],
    
    "permitted": ["forbidden", "prohibited", "banned"],
    "allowed": ["forbidden", "prohibited", "banned"],
    "acceptable": ["unacceptable", "forbidden"],
    
    "optional": ["required", "mandatory", "compulsory"],
    
    # =========================================================================
    # RECOMMENDATION OPPOSITES
    # =========================================================================
    "recommended": ["discouraged", "inadvisable"],
    "advised": ["discouraged", "inadvisable"],
    "suggested": ["discouraged", "inadvisable"],
    "encouraged": ["discouraged", "forbidden"],
    "preferred": ["discouraged", "undesirable"],
    "desirable": ["undesirable", "inadvisable"],
    "advisable": ["inadvisable"],
    
    "discouraged": ["encouraged", "recommended", "advised"],
    "inadvisable": ["advisable", "recommended"],
    "undesirable": ["desirable", "preferred"],
    
    # =========================================================================
    # POSSIBILITY / CAPABILITY OPPOSITES
    # =========================================================================
    "possible": ["impossible"],
    "impossible": ["possible", "feasible"],
    "feasible": ["impossible"],
    "conceivable": ["inconceivable"],
    "inconceivable": ["conceivable", "possible"],
    "can": ["cannot"],
    "cannot": ["can", "may"],
    
    # =========================================================================
    # CERTAINTY / DOUBT OPPOSITES
    # =========================================================================
    "certain": ["uncertain", "doubtful"],
    "uncertain": ["certain"],
    "sure": ["unsure", "uncertain"],
    "unsure": ["sure", "certain"],
    "doubtful": ["certain"],
    "undoubtedly": ["doubtfully"],
    "questionable": ["certain"],
    
    # =========================================================================
    # TEMPORAL OPPOSITES
    # =========================================================================
    "permanently": ["temporarily"],
    "temporarily": ["permanently"],
    "briefly": ["permanently", "continuously", "always"],
    "momentarily": ["permanently", "continuously"],
    
    "immediately": ["eventually", "never"],
    "eventually": ["never", "immediately"],
    "soon": ["never"],
    
    "currently": ["formerly", "never"],
    "formerly": ["currently"],
    "previously": ["currently", "never"],
    
    # =========================================================================
    # DEGREE OPPOSITES
    # =========================================================================
    "mostly": ["rarely", "barely"],
    "largely": ["barely", "slightly"],
    "mainly": ["rarely", "barely"],
    "predominantly": ["rarely"],
    "primarily": ["rarely"],
    
    "barely": ["mostly", "largely"],
    "scarcely": ["mostly", "largely"],
}


# Semantic contradiction pairs - words that contradict each other in context
SEMANTIC_CONTRADICTION_PAIRS = {
    # Pass/fail semantics
    "fails": ["passes", "pass", "succeeds", "succeed"],
    "fail": ["passes", "pass", "succeeds", "succeed"],
    "passes": ["fails", "fail"],
    "pass": ["fails", "fail"],

    # Complete/miss semantics
    "misses": ["completes", "complete", "finishes", "finish", "submits", "submit"],
    "miss": ["completes", "complete", "finishes", "finish", "submits", "submit"],
    "completes": ["misses", "miss", "skips", "skip"],
    "complete": ["misses", "miss", "skips", "skip"],

    # Early/on-time/late semantics
    "early": ["on time", "late"],
    "late": ["on time", "early"],
    "on time": ["early", "late"],

    # Success/failure semantics
    "succeeds": ["fails", "fail"],
    "succeed": ["fails", "fail"],
    "wins": ["loses", "lose"],
    "loses": ["wins", "win"],
    "lose": ["wins", "win"],
}


# =============================================================================
# TEXT EXTRACTION
# =============================================================================

def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from PDF, DOCX, or TXT file.
    
    Args:
        file_path: Path to source document
        
    Returns:
        Full text content of the document
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.txt':
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            raise ImportError("Please install PyMuPDF: pip install pymupdf")
    
    elif suffix in ['.docx', '.doc']:
        try:
            import docx
            doc = docx.Document(path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ImportError("Please install python-docx: pip install python-docx")
    
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


# =============================================================================
# SPACY UTILITIES
# =============================================================================

def load_spacy_model(model_name: str = "en_core_web_sm") -> spacy.Language:
    """
    Load SpaCy language model.
    
    Args:
        model_name: Name of SpaCy model to load
        
    Returns:
        Loaded SpaCy language model
    """
    try:
        return spacy.load(model_name)
    except OSError:
        print(f"Downloading SpaCy model: {model_name}")
        spacy.cli.download(model_name)
        return spacy.load(model_name)


def detect_modal_word(text: str, nlp: spacy.Language) -> Optional[Tuple[str, int]]:
    """
    Detect modal word in proposition text using SpaCy tokenization.
    
    Args:
        text: Proposition translation text
        nlp: Loaded SpaCy model
        
    Returns:
        Tuple of (modal_word, token_index) if found, None otherwise
    """
    text_lower = text.lower()
    doc = nlp(text_lower)
    
    # Check single-word modals via tokenization
    for i, token in enumerate(doc):
        if token.text in MODAL_WORDS:
            return (token.text, i)
    
    return None


def remove_modal_word(text: str, modal_word: str, nlp: spacy.Language) -> str:
    """
    Remove modal word from text and reconstruct sentence.
    
    Args:
        text: Original proposition text with modal word
        modal_word: The modal word to remove
        nlp: Loaded SpaCy model
        
    Returns:
        Reconstructed text without the modal word
    """
    doc = nlp(text)
    
    tokens = []
    for token in doc:
        if token.text.lower() != modal_word.lower():
            tokens.append(token.text)
    
    # Reconstruct with proper spacing
    result = ""
    for i, token in enumerate(tokens):
        if i == 0:
            result = token
        elif token in ".,;:!?":
            result += token
        else:
            result += " " + token
    
    # Clean up double spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


def detect_negation_in_sentence(sentence: str, nlp: spacy.Language) -> Optional[Tuple[str, str]]:
    """
    Detect negation in a sentence using SpaCy dependency parsing with fallback.
    
    Args:
        sentence: Source document sentence
        nlp: Loaded SpaCy model
        
    Returns:
        Tuple of (negated_verb, affirmative_clause) if found, None otherwise
    """
    doc = nlp(sentence)
    
    # Method 1: SpaCy dependency parsing
    for token in doc:
        if token.dep_ == "neg":
            # Found negation, get the head (negated verb)
            negated_verb = token.head
            
            # Build the negated clause
            # Get the subtree of the negated verb
            subtree_tokens = list(negated_verb.subtree)
            
            # Sort by position and build clause
            subtree_tokens.sort(key=lambda t: t.i)
            
            # Build the affirmative version (without negation)
            affirmative_tokens = [t.text for t in subtree_tokens if t.dep_ != "neg"]
            affirmative_clause = " ".join(affirmative_tokens)
            
            return (negated_verb.text, affirmative_clause)
    
    # Method 2: Fallback keyword detection for cases SpaCy misses
    negation_patterns = [
        (r"\bdoes\s+not\b", "does not"),
        (r"\bdo\s+not\b", "do not"),
        (r"\bis\s+not\b", "is not"),
        (r"\bare\s+not\b", "are not"),
        (r"\bwas\s+not\b", "was not"),
        (r"\bwere\s+not\b", "were not"),
        (r"\bhas\s+not\b", "has not"),
        (r"\bhave\s+not\b", "have not"),
        (r"\bhad\s+not\b", "had not"),
        (r"\bwill\s+not\b", "will not"),
        (r"\bwould\s+not\b", "would not"),
        (r"\bcannot\b", "cannot"),
        (r"\bcan't\b", "can't"),
        (r"\bwon't\b", "won't"),
        (r"\bdoesn't\b", "doesn't"),
        (r"\bdon't\b", "don't"),
        (r"\bisn't\b", "isn't"),
        (r"\baren't\b", "aren't"),
        (r"\bwasn't\b", "wasn't"),
        (r"\bweren't\b", "weren't"),
        (r"\bhasn't\b", "hasn't"),
        (r"\bhaven't\b", "haven't"),
        (r"\bhadn't\b", "hadn't"),
        (r"\bwouldn't\b", "wouldn't"),
        (r"\bcouldn't\b", "couldn't"),
        (r"\bshouldn't\b", "shouldn't"),
        (r"\bnever\b", "never"),
    ]
    
    sentence_lower = sentence.lower()
    for pattern, neg_word in negation_patterns:
        match = re.search(pattern, sentence_lower)
        if match:
            # Remove negation to get affirmative
            affirmative = re.sub(pattern, "", sentence_lower, count=1)
            # Clean up auxiliary verbs left behind
            affirmative = re.sub(r'\bdoes\b\s*', '', affirmative)
            affirmative = re.sub(r'\bdo\b\s*', '', affirmative)
            affirmative = re.sub(r'\s+', ' ', affirmative).strip()
            
            return (neg_word, affirmative)
    
    return None


# ==========================================
# 4b. IMPLICATION CONTRADICTION DETECTION
# ==========================================

def detect_implication_contradiction(
    query: str,
    logified_structure: Dict[str, Any],
    sbert_model,
    verbose: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Detect if the hypothesis contradicts an implication in the KB.

    For example:
    - Hypothesis: "Alice fails her exams even when she studies hard"
    - KB has: "If Alice studies hard, then she passes her exams" (P_6 ⟹ P_7)
    - The hypothesis asserts: antecedent (studies hard) AND negation of consequent (fails = ¬passes)
    - This contradicts the implication, so return ¬(P_6 ⟹ P_7)
    """
    query_lower = query.lower()

    if verbose:
        print("  [Implication Contradiction] Checking for implication contradictions...")

    # Get all hard constraints that are implications
    hard_constraints = logified_structure.get('hard_constraints', [])
    primitive_props = logified_structure.get('primitive_props', [])

    # Build prop_id -> translation map
    prop_map = {p['id']: p['translation'] for p in primitive_props}

    # Find implication constraints (formula contains ⟹ or =>)
    implications = []
    for c in hard_constraints:
        formula = c.get('formula', '')
        if '⟹' in formula or '=>' in formula:
            if '⟹' in formula:
                parts = formula.split('⟹')
            else:
                parts = formula.split('=>')

            if len(parts) == 2:
                antecedent = parts[0].strip()
                consequent = parts[1].strip()

                # Skip negated consequents (exclusion constraints)
                if consequent.startswith('¬') or consequent.startswith('~'):
                    continue

                implications.append({
                    'constraint_id': c.get('id'),
                    'formula': formula,
                    'antecedent': antecedent,
                    'consequent': consequent,
                    'translation': c.get('translation', '')
                })

    if verbose:
        print(f"  [Implication Contradiction] Found {len(implications)} non-negated implications")

    # For each implication, check if the hypothesis contradicts it
    for impl in implications:
        antecedent_id = impl['antecedent']
        consequent_id = impl['consequent']

        antecedent_text = prop_map.get(antecedent_id, '').lower()
        consequent_text = prop_map.get(consequent_id, '').lower()

        if not antecedent_text or not consequent_text:
            continue

        if verbose:
            print(f"  [Implication Contradiction] Checking: {impl['formula']}")
            print(f"    Antecedent: {antecedent_text}")
            print(f"    Consequent: {consequent_text}")

        # Check 1: Does the hypothesis mention the antecedent condition?
        antecedent_keywords = set(antecedent_text.replace('.', '').split())
        antecedent_keywords -= {'alice', 'she', 'her', 'is', 'a', 'an', 'the'}

        query_words = set(query_lower.replace('.', '').split())
        antecedent_overlap = len(antecedent_keywords & query_words) / max(len(antecedent_keywords), 1)

        if antecedent_overlap < 0.3:
            continue

        if verbose:
            print(f"    Antecedent overlap: {antecedent_overlap:.2f}")

        # Check 2: Does the hypothesis contain a semantic contradiction to the consequent?
        consequent_keywords = consequent_text.replace('.', '').split()

        for cons_word in consequent_keywords:
            if cons_word in ['alice', 'she', 'her', 'is', 'a', 'an', 'the']:
                continue

            contradictions = SEMANTIC_CONTRADICTION_PAIRS.get(cons_word, [])

            for contra_word in contradictions:
                if contra_word in query_lower:
                    if verbose:
                        print(f"    ✓ Found semantic contradiction: '{contra_word}' contradicts '{cons_word}'")

                    negated_formula = f"¬({impl['formula']})"

                    return {
                        "formula": negated_formula,
                        "translation": f"it is not the case that {impl['translation']}",
                        "explanation": f"Implication contradiction: hypothesis '{contra_word}' contradicts consequent '{cons_word}' of rule {impl['formula']}",
                        "confidence": 1.0,
                        "implication_contradiction_detected": True
                    }

        # Check 3: Qualifier strengthening (e.g., "always early" vs "on time")
        if "always" in query_lower or "every" in query_lower or "never" in query_lower:
            cons_emb = sbert_model.encode(consequent_text)
            query_emb = sbert_model.encode(query_lower)

            similarity = float(np.dot(cons_emb, query_emb) / (np.linalg.norm(cons_emb) * np.linalg.norm(query_emb)))

            if similarity > 0.6:
                for word in query_lower.split():
                    contradictions = SEMANTIC_CONTRADICTION_PAIRS.get(word, [])
                    for contra in contradictions:
                        if contra in consequent_text:
                            if verbose:
                                print(f"    ✓ Found qualifier strengthening: '{word}' vs '{contra}'")

                            negated_formula = f"¬({impl['formula']})"
                            return {
                                "formula": negated_formula,
                                "translation": f"it is not the case that {impl['translation']}",
                                "explanation": f"Qualifier strengthening contradiction: '{word}' contradicts '{contra}' in rule {impl['formula']}",
                                "confidence": 1.0,
                                "implication_contradiction_detected": True
                            }

    return None


def split_into_sentences(text: str, nlp: spacy.Language) -> List[str]:
    """
    Split text into sentences using SpaCy.
    
    Args:
        text: Full text
        nlp: Loaded SpaCy model
        
    Returns:
        List of sentence strings
    """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]

def detect_and_resolve_conflicts(logic_structure: dict, nli_model, tokenizer, original_text: str, device='cpu') -> dict:
    """
    Detect P_i and ¬P_i conflicts and resolve using NLI entailment.
    
    Args:
        logic_structure: The logified structure with primitive_props and constraints
        nli_model: Loaded NLI model (e.g., roberta-large-mnli)
        tokenizer: Tokenizer for the NLI model
        original_text: The source document text
        device: 'cpu' or 'cuda'
    
    Returns:
        Updated logic_structure with conflicts resolved
    """
    import torch
    import re
    import copy
    
    structure = copy.deepcopy(logic_structure)
    
    # Get all constraints (handle both formats)
    if 'constraints' in structure:
        constraints = structure['constraints']
        constraint_key = 'constraints'
    else:
        constraints = structure.get('hard_constraints', []) + structure.get('soft_constraints', [])
        constraint_key = 'split'
    
    # Build lookup: prop_id -> translation
    prop_translations = {p['id']: p['translation'] for p in structure['primitive_props']}
    
    # Find simple assertions: P_i or ¬P_i (no implications, conjunctions, etc.)
    simple_assertion_pattern = re.compile(r'^(¬)?P_(\d+)$')
    
    asserted_positive = {}  # prop_id -> constraint
    asserted_negative = {}  # prop_id -> constraint
    
    for c in constraints:
        formula = c.get('formula', '').strip()
        match = simple_assertion_pattern.match(formula)
        if match:
            is_negated = match.group(1) is not None
            prop_id = f"P_{match.group(2)}"
            if is_negated:
                asserted_negative[prop_id] = c
            else:
                asserted_positive[prop_id] = c
    
    # Find conflicts
    conflicts = set(asserted_positive.keys()) & set(asserted_negative.keys())
    
    if not conflicts:
        structure['_conflict_resolution_log'] = []
        return structure, []
    
    resolution_log = []
    constraints_to_remove = set()
    
    for prop_id in conflicts:
        pos_constraint = asserted_positive[prop_id]
        neg_constraint = asserted_negative[prop_id]
        
        translation = prop_translations.get(prop_id, prop_id)
        
        # Get evidence (prefer the one with actual text reference)
        evidence = pos_constraint.get('evidence', '') or neg_constraint.get('evidence', '')
        
        # Extract premise from original text using evidence
        premise = extract_premise_from_evidence(original_text, evidence)
        if not premise:
            premise = original_text[:1000]  # Fallback: use first 1000 chars
        
        # Hypotheses
        hypothesis_pos = translation
        hypothesis_neg = f"It is not the case that {translation[0].lower()}{translation[1:]}"
        
        # Run NLI
        score_pos = get_nli_entailment_score(premise, hypothesis_pos, nli_model, tokenizer, device)
        score_neg = get_nli_entailment_score(premise, hypothesis_neg, nli_model, tokenizer, device)
        
        # Decide which to keep
        if score_pos >= score_neg:
            keep = 'positive'
            remove_id = neg_constraint['id']
            constraints_to_remove.add(remove_id)
        else:
            keep = 'negative'
            remove_id = pos_constraint['id']
            constraints_to_remove.add(remove_id)
        
        resolution_log.append({
            'prop_id': prop_id,
            'translation': translation,
            'positive_constraint': pos_constraint['id'],
            'negative_constraint': neg_constraint['id'],
            'nli_score_positive': score_pos,
            'nli_score_negative': score_neg,
            'decision': f"keep {keep}",
            'removed': remove_id
        })
    
    # Remove conflicting constraints
    if constraint_key == 'constraints':
        structure['constraints'] = [c for c in structure['constraints'] 
                                    if c['id'] not in constraints_to_remove]
    else:
        structure['hard_constraints'] = [c for c in structure.get('hard_constraints', []) 
                                         if c['id'] not in constraints_to_remove]
        structure['soft_constraints'] = [c for c in structure.get('soft_constraints', []) 
                                         if c['id'] not in constraints_to_remove]
    
    structure['_conflict_resolution_log'] = resolution_log
    
    return structure, resolution_log


def extract_premise_from_evidence(original_text: str, evidence: str) -> str:
    """
    Extract the relevant sentence(s) from original text based on evidence field.
    
    Args:
        original_text: Full document text
        evidence: Evidence string like "Sentence 23" or "Sentence 23-24"
    
    Returns:
        Extracted sentence(s) or empty string if not found
    """
    import re
    
    # Split text into sentences (simple split)
    sentences = re.split(r'(?<=[.!?])\s+', original_text)
    
    # Parse evidence for sentence indices
    match = re.search(r'Sentence\s+(\d+)(?:\s*[-–]\s*(\d+))?', evidence, re.IGNORECASE)
    if not match:
        return ""
    
    start_idx = int(match.group(1))
    end_idx = int(match.group(2)) if match.group(2) else start_idx
    
    # Extract sentences (0-based indexing)
    extracted = []
    for idx in range(start_idx, min(end_idx + 1, len(sentences))):
        if 0 <= idx < len(sentences):
            extracted.append(sentences[idx])
    
    return " ".join(extracted)


def get_nli_entailment_score(premise: str, hypothesis: str, model, tokenizer, device='cpu') -> float:
    """
    Get NLI entailment score for premise -> hypothesis.
    
    Args:
        premise: The premise text
        hypothesis: The hypothesis text
        model: NLI model
        tokenizer: NLI tokenizer
        device: 'cpu' or 'cuda'
    
    Returns:
        Entailment probability (0.0 to 1.0)
    """
    import torch
    
    inputs = tokenizer(
        premise, 
        hypothesis, 
        return_tensors='pt', 
        truncation=True, 
        max_length=512
    ).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
    
    # For roberta-large-mnli: [contradiction, neutral, entailment]
    entailment_score = probs[0, 2].item()
    
    return entailment_score


# =============================================================================
# WORDNET UTILITIES
# =============================================================================

def get_modal_antonyms(modal_word: str) -> List[str]:
    """
    Get antonyms of a modal word using WordNet with fallback table.
    
    Args:
        modal_word: Modal word to find antonyms for
        
    Returns:
        List of antonym words
    """
    antonyms = set()
    
    # Try WordNet first
    for syn in wordnet.synsets(modal_word):
        for lemma in syn.lemmas():
            for ant in lemma.antonyms():
                ant_name = ant.name().lower()
                if ant_name in MODAL_WORDS:
                    antonyms.add(ant_name)
    
    # Use fallback if WordNet didn't find anything
    if not antonyms and modal_word in MODAL_OPPOSITES_FALLBACK:
        antonyms.update(MODAL_OPPOSITES_FALLBACK[modal_word])
    
    return list(antonyms)


# =============================================================================
# SBERT MATCHING
# =============================================================================

def load_sbert_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load SBERT model.
    
    Args:
        model_name: Name of sentence transformer model
        
    Returns:
        Loaded SentenceTransformer model
    """
    return SentenceTransformer(model_name)


def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity (float between -1 and 1)
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def precompute_embeddings(
    propositions: List[Dict[str, Any]],
    sbert_model: SentenceTransformer
) -> Dict[str, np.ndarray]:
    """
    Pre-compute SBERT embeddings for all propositions.
    
    Args:
        propositions: List of primitive propositions
        sbert_model: Loaded SBERT model
        
    Returns:
        Dictionary mapping proposition ID to embedding
    """
    embeddings = {}
    for prop in propositions:
        prop_id = prop.get("id", "")
        translation = prop.get("translation", "")
        if prop_id and translation:
            embeddings[prop_id] = sbert_model.encode(translation)
    return embeddings


def find_matching_proposition(
    candidate_text: str,
    propositions: List[Dict[str, Any]],
    sbert_model: SentenceTransformer,
    prop_embeddings: Optional[Dict[str, np.ndarray]] = None,
    threshold: float = 0.85
) -> Optional[Dict[str, Any]]:
    """
    Find proposition whose translation matches candidate text using SBERT.
    
    Args:
        candidate_text: Text to match against propositions
        propositions: List of primitive propositions from logified.json
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed embeddings (optional, for efficiency)
        threshold: Minimum cosine similarity for match
        
    Returns:
        Matching proposition dict if found above threshold, None otherwise
    """
    if not propositions:
        return None
    
    candidate_embedding = sbert_model.encode(candidate_text)
    
    best_match = None
    best_score = threshold
    
    for prop in propositions:
        prop_id = prop.get("id", "")
        translation = prop.get("translation", "")
        
        # Use pre-computed embedding if available
        if prop_embeddings and prop_id in prop_embeddings:
            prop_embedding = prop_embeddings[prop_id]
        else:
            prop_embedding = sbert_model.encode(translation)
        
        score = compute_cosine_similarity(candidate_embedding, prop_embedding)
        
        if score > best_score:
            best_score = score
            best_match = prop
    
    return best_match


def proposition_exists(
    candidate_text: str,
    propositions: List[Dict[str, Any]],
    sbert_model: SentenceTransformer,
    prop_embeddings: Optional[Dict[str, np.ndarray]] = None,
    threshold: float = 0.85
) -> bool:
    """
    Check if a proposition with similar text already exists.
    
    Args:
        candidate_text: Text to check
        propositions: List of primitive propositions
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed embeddings (optional)
        threshold: Minimum cosine similarity for match
        
    Returns:
        True if similar proposition exists, False otherwise
    """
    return find_matching_proposition(
        candidate_text, propositions, sbert_model, prop_embeddings, threshold
    ) is not None


# =============================================================================
# CONSTRAINT UTILITIES
# =============================================================================

def normalize_formula(formula: str) -> str:
    """
    Normalize a formula for comparison (handle spacing, unicode).
    
    Args:
        formula: Propositional formula
        
    Returns:
        Normalized formula string
    """
    # Normalize unicode operators
    formula = formula.replace("=>", "⟹")
    formula = formula.replace("<=>", "⟺")
    formula = formula.replace("~", "¬")
    formula = formula.replace("!", "¬")
    formula = formula.replace("&", "∧")
    formula = formula.replace("|", "∨")
    
    # Remove extra spaces
    formula = re.sub(r'\s+', ' ', formula).strip()
    
    return formula


def constraint_exists(
    formula: str,
    constraints: List[Dict[str, Any]]
) -> bool:
    """
    Check if a constraint with given formula already exists.
    
    Args:
        formula: Propositional formula to check (e.g., "¬P_3", "P_1 ⟹ ¬P_2")
        constraints: List of constraints from logified.json
        
    Returns:
        True if constraint exists, False otherwise
    """
    normalized = normalize_formula(formula)
    
    for constraint in constraints:
        existing = normalize_formula(constraint.get("formula", ""))
        if existing == normalized:
            return True
    
    return False


def create_constraint(
    constraint_id: str,
    formula: str,
    translation: str,
    llm_weight: float,
    evidence: str,
    reasoning: str
) -> Dict[str, Any]:
    """
    Create a new constraint dict.
    
    Args:
        constraint_id: Unique ID (e.g., "C_42")
        formula: Propositional formula
        translation: Natural language translation
        llm_weight: Weight (typically 1.0 for generated constraints)
        evidence: Source evidence
        reasoning: Explanation for this constraint
        
    Returns:
        Constraint dict matching logified.json schema
    """
    return {
        "id": constraint_id,
        "formula": formula,
        "translation": translation,
        "llm_weight": llm_weight,
        "evidence": evidence,
        "reasoning": reasoning
    }


def create_proposition(
    prop_id: str,
    translation: str,
    evidence: str,
    explanation: str
) -> Dict[str, Any]:
    """
    Create a new proposition dict.
    
    Args:
        prop_id: Unique ID (e.g., "P_29")
        translation: Natural language proposition text
        evidence: Source evidence
        explanation: Why this proposition was added
        
    Returns:
        Proposition dict matching logified.json schema
    """
    return {
        "id": prop_id,
        "translation": translation,
        "evidence": evidence,
        "explanation": explanation
    }


def get_next_prop_id(propositions: List[Dict[str, Any]]) -> str:
    """
    Get next available proposition ID.
    
    Args:
        propositions: Current list of propositions
        
    Returns:
        Next ID string (e.g., "P_29")
    """
    max_id = 0
    for prop in propositions:
        prop_id = prop.get("id", "P_0")
        match = re.match(r'P_(\d+)', prop_id)
        if match:
            max_id = max(max_id, int(match.group(1)))
    
    return f"P_{max_id + 1}"


def get_next_constraint_id(constraints: List[Dict[str, Any]]) -> str:
    """
    Get next available constraint ID.
    
    Args:
        constraints: Current list of constraints
        
    Returns:
        Next ID string (e.g., "C_42")
    """
    max_id = 0
    for constraint in constraints:
        const_id = constraint.get("id", "C_0")
        match = re.match(r'C_(\d+)', const_id)
        if match:
            max_id = max(max_id, int(match.group(1)))
    
    return f"C_{max_id + 1}"


def find_proposition_by_id(prop_id: str, propositions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find proposition by its ID.
    
    Args:
        prop_id: Proposition ID (e.g., "P_3")
        propositions: List of propositions
        
    Returns:
        Proposition dict if found, None otherwise
    """
    for prop in propositions:
        if prop.get("id") == prop_id:
            return prop
    return None


# =============================================================================
# ENRICHMENT STEPS
# =============================================================================

def verify_modal_pairs(
    propositions: List[Dict[str, Any]],
    constraints: List[Dict[str, Any]],
    nlp: spacy.Language,
    sbert_model: SentenceTransformer,
    prop_embeddings: Dict[str, np.ndarray],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, np.ndarray], List[str]]:
    """
    Step 1: Verify and complete modal pairs.
    
    For each proposition with a modal word:
    - Check if P_base exists; if not, create it
    - Check if P_modal standalone constraint @1.0 exists
    - Check if P_base standalone constraint @modal_weight exists
    - Check if P_base ⟹ P_modal @1.0 exists
    
    Args:
        propositions: List of primitive propositions
        constraints: List of constraints
        nlp: Loaded SpaCy model
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed proposition embeddings
        verbose: Print debug information
        
    Returns:
        Tuple of (updated_propositions, updated_constraints, updated_embeddings, log_messages)
    """
    log_messages = []
    updated_props = list(propositions)
    updated_constraints = list(constraints)
    updated_embeddings = dict(prop_embeddings)
    
    # Track modal propositions and their bases
    modal_pairs = []  # [(P_modal_id, modal_word, P_base_id)]
    
    for prop in propositions:
        translation = prop.get("translation", "")
        prop_id = prop.get("id", "")
        
        modal_info = detect_modal_word(translation, nlp)
        
        if modal_info:
            modal_word, _ = modal_info
            
            # Generate base text (modal word removed)
            base_text = remove_modal_word(translation, modal_word, nlp)
            
            if verbose:
                log_messages.append(f"[Modal] {prop_id}: '{translation}' has modal '{modal_word}'")
                log_messages.append(f"        Base text: '{base_text}'")
            
            # Check if P_base exists
            matching_base = find_matching_proposition(
                base_text, updated_props, sbert_model, updated_embeddings, threshold=0.85
            )
            
            if matching_base:
                base_id = matching_base.get("id")
                if verbose:
                    log_messages.append(f"        Found existing base: {base_id}")
            else:
                # Create P_base
                base_id = get_next_prop_id(updated_props)
                new_prop = create_proposition(
                    prop_id=base_id,
                    translation=base_text,
                    evidence=prop.get("evidence", "") + " (derived by removing modal)",
                    explanation=f"Derived proposition from {prop_id} by removing '{modal_word}'. Represents base event."
                )
                updated_props.append(new_prop)
                # Add embedding for new proposition
                updated_embeddings[base_id] = sbert_model.encode(base_text)
                if verbose:
                    log_messages.append(f"        Created new base: {base_id} = '{base_text}'")
            
            modal_pairs.append((prop_id, modal_word, base_id))
    
    # Now verify constraints for each modal pair
    for modal_id, modal_word, base_id in modal_pairs:
        modal_weight = MODAL_WORDS.get(modal_word, 0.5)
        
        # Check 1: P_modal standalone @1.0
        if not constraint_exists(modal_id, updated_constraints):
            modal_prop = find_proposition_by_id(modal_id, updated_props)
            modal_translation = modal_prop.get("translation", "") if modal_prop else ""
            new_constraint = create_constraint(
                constraint_id=get_next_constraint_id(updated_constraints),
                formula=modal_id,
                translation=modal_translation,
                llm_weight=1.0,
                evidence="Auto-generated",
                reasoning="Original modal statement is asserted with certainty"
            )
            updated_constraints.append(new_constraint)
            if verbose:
                log_messages.append(f"        Added constraint: {modal_id} @1.0")
        
        # Check 2: P_base standalone @modal_weight
        if not constraint_exists(base_id, updated_constraints):
            base_prop = find_proposition_by_id(base_id, updated_props)
            base_translation = base_prop.get("translation", "") if base_prop else ""
            new_constraint = create_constraint(
                constraint_id=get_next_constraint_id(updated_constraints),
                formula=base_id,
                translation=base_translation,
                llm_weight=modal_weight,
                evidence="Auto-generated",
                reasoning=f"Derived base event from '{modal_word}' has weight {modal_weight}"
            )
            updated_constraints.append(new_constraint)
            if verbose:
                log_messages.append(f"        Added constraint: {base_id} @{modal_weight}")
        
        # Check 3: P_base ⟹ P_modal @1.0
        implication_formula = f"{base_id} ⟹ {modal_id}"
        if not constraint_exists(implication_formula, updated_constraints):
            new_constraint = create_constraint(
                constraint_id=get_next_constraint_id(updated_constraints),
                formula=implication_formula,
                translation="If base event occurs, the modal pattern is satisfied",
                llm_weight=1.0,
                evidence="Auto-generated",
                reasoning="If base event occurs, it is logically consistent with the modal pattern claim"
            )
            updated_constraints.append(new_constraint)
            if verbose:
                log_messages.append(f"        Added constraint: {implication_formula} @1.0")
    
            
        # Check 4: P_modal ⟹ P_base @1.0 (if "typically X" then "X" must happen)
        reverse_implication = f"{modal_id} ⟹ {base_id}"
        if not constraint_exists(reverse_implication, updated_constraints):
            new_constraint = create_constraint(
                constraint_id=get_next_constraint_id(updated_constraints),
                formula=reverse_implication,
                translation="If modal pattern holds, the base event occurs",
                llm_weight=1.0,
                evidence="Auto-generated",
                reasoning=f"Modal '{modal_word}' implies the base event occurs (at least sometimes)"
            )
            updated_constraints.append(new_constraint)
            if verbose:
                log_messages.append(f"        Added constraint: {reverse_implication} @1.0")



    
    return updated_props, updated_constraints, updated_embeddings, log_messages


def detect_modal_opposites(
    propositions: List[Dict[str, Any]],
    constraints: List[Dict[str, Any]],
    nlp: spacy.Language,
    sbert_model: SentenceTransformer,
    prop_embeddings: Dict[str, np.ndarray],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Step 2: Detect modal opposites and add exclusion constraints.
    
    For each proposition with modal word M:
    - Find antonyms of M using WordNet
    - Check if any proposition has the antonym modal
    - If found, add P_modal ⟹ ¬P_opposite @1.0
    
    Args:
        propositions: List of primitive propositions
        constraints: List of constraints
        nlp: Loaded SpaCy model
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed proposition embeddings
        verbose: Print debug information
        
    Returns:
        Tuple of (updated_constraints, log_messages)
    """
    log_messages = []
    updated_constraints = list(constraints)
    
    # Build map of propositions with modal words
    modal_props = []  # [(prop_id, modal_word, base_text)]
    
    for prop in propositions:
        translation = prop.get("translation", "")
        prop_id = prop.get("id", "")
        
        modal_info = detect_modal_word(translation, nlp)
        if modal_info:
            modal_word, _ = modal_info
            base_text = remove_modal_word(translation, modal_word, nlp)
            modal_props.append((prop_id, modal_word, base_text))
    
    # Pre-compute base text embeddings
    base_embeddings = {}
    for prop_id, modal_word, base_text in modal_props:
        base_embeddings[prop_id] = sbert_model.encode(base_text)
    
    # For each modal proposition, look for opposites
    for prop_id, modal_word, base_text in modal_props:
        antonyms = get_modal_antonyms(modal_word)
        
        if verbose and antonyms:
            log_messages.append(f"[Opposite] {prop_id}: '{modal_word}' has antonyms {antonyms}")
        
        for antonym in antonyms:
            # Try to find a proposition that matches the opposite pattern
            for other_id, other_modal, other_base in modal_props:
                if other_id == prop_id:
                    continue
                
                # Check if same base text but opposite modal
                if other_modal == antonym:
                    # Check if base texts are similar
                    base_similarity = compute_cosine_similarity(
                        base_embeddings[prop_id],
                        base_embeddings[other_id]
                    )
                    
                    if base_similarity > 0.85:
                        # Found opposite modal pair
                        exclusion_formula = f"{prop_id} ⟹ ¬{other_id}"
                        
                        if not constraint_exists(exclusion_formula, updated_constraints):
                            new_constraint = create_constraint(
                                constraint_id=get_next_constraint_id(updated_constraints),
                                formula=exclusion_formula,
                                translation=f"If '{modal_word}' holds, then '{antonym}' cannot hold",
                                llm_weight=1.0,
                                evidence="Auto-generated",
                                reasoning=f"Modal opposites: {modal_word} and {antonym} are mutually exclusive"
                            )
                            updated_constraints.append(new_constraint)
                            if verbose:
                                log_messages.append(f"        Added opposite constraint: {exclusion_formula} @1.0")
    
    return updated_constraints, log_messages


def detect_explicit_negations(
    source_text: str,
    propositions: List[Dict[str, Any]],
    constraints: List[Dict[str, Any]],
    nlp: spacy.Language,
    sbert_model: SentenceTransformer,
    prop_embeddings: Dict[str, np.ndarray],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Step 3: Detect explicit negations in source text.
    
    For each sentence in source document:
    - Detect negation using SpaCy dependency parsing
    - Match negated clause to existing proposition via SBERT
    - If match found, add ¬P_i @1.0 constraint
    
    Args:
        source_text: Full text of source document
        propositions: List of primitive propositions
        constraints: List of constraints
        nlp: Loaded SpaCy model
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed proposition embeddings
        verbose: Print debug information
        
    Returns:
        Tuple of (updated_constraints, log_messages)
    """
    log_messages = []
    updated_constraints = list(constraints)
    
    sentences = split_into_sentences(source_text, nlp)
    
    for i, sentence in enumerate(sentences):
        negation_info = detect_negation_in_sentence(sentence, nlp)
        
        if negation_info:
            negated_verb, affirmative_clause = negation_info
            
            if verbose:
                log_messages.append(f"[Negation] Sentence {i}: Found negation of '{negated_verb}'")
                log_messages.append(f"           Affirmative clause: '{affirmative_clause}'")
            
            # Find matching proposition
            matching_prop = find_matching_proposition(
                affirmative_clause, propositions, sbert_model, prop_embeddings, threshold=0.75
            )
            
            if matching_prop:
                prop_id = matching_prop.get("id")
                negation_formula = f"¬{prop_id}"
                
                if verbose:
                    log_messages.append(f"           Matched to: {prop_id}")
                
                if not constraint_exists(negation_formula, updated_constraints):
                    new_constraint = create_constraint(
                        constraint_id=get_next_constraint_id(updated_constraints),
                        formula=negation_formula,
                        translation=f"It is not the case that {matching_prop.get('translation', '')}",
                        llm_weight=1.0,
                        evidence=f"Sentence {i}: explicit negation in source text",
                        reasoning="Explicit negation detected in source text - hard constraint"
                    )
                    updated_constraints.append(new_constraint)
                    if verbose:
                        log_messages.append(f"           Added constraint: {negation_formula} @1.0")
            else:
                if verbose:
                    log_messages.append(f"           No matching proposition found")
    
    return updated_constraints, log_messages


def verify_auxiliary_negatives(
    propositions: List[Dict[str, Any]],
    constraints: List[Dict[str, Any]],
    sbert_model: SentenceTransformer,
    prop_embeddings: Dict[str, np.ndarray],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Step 4: Verify auxiliary negative constraints.
    
    For each proposition marked as auxiliary (in explanation field):
    - Check if ¬P_aux @1.0 exists
    - Find the original asserted proposition
    - Check if P_original ⟹ ¬P_aux @1.0 exists
    
    Args:
        propositions: List of primitive propositions
        constraints: List of constraints
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed proposition embeddings
        verbose: Print debug information
        
    Returns:
        Tuple of (updated_constraints, log_messages)
    """
    log_messages = []
    updated_constraints = list(constraints)
    
    # Find auxiliary propositions by checking explanation field
    auxiliary_keywords = ["auxiliary", "mutual exclusion", "alternative", "finite domain", "mutually exclusive"]
    
    auxiliary_props = []
    original_props = []
    
    for prop in propositions:
        explanation = prop.get("explanation", "").lower()
        
        is_auxiliary = any(kw in explanation for kw in auxiliary_keywords)
        
        if is_auxiliary:
            auxiliary_props.append(prop)
        else:
            original_props.append(prop)
    
    if verbose:
        log_messages.append(f"[Auxiliary] Found {len(auxiliary_props)} auxiliary propositions")
    
    for aux_prop in auxiliary_props:
        aux_id = aux_prop.get("id")
        aux_translation = aux_prop.get("translation", "")
        
        if verbose:
            log_messages.append(f"[Auxiliary] {aux_id}: '{aux_translation}'")
        
        # Check 1: ¬P_aux @1.0 exists
        negation_formula = f"¬{aux_id}"
        
        if not constraint_exists(negation_formula, updated_constraints):
            new_constraint = create_constraint(
                constraint_id=get_next_constraint_id(updated_constraints),
                formula=negation_formula,
                translation=f"It is not the case that {aux_translation}",
                llm_weight=1.0,
                evidence="Auto-generated",
                reasoning="Negation of auxiliary proposition - definitional consequence"
            )
            updated_constraints.append(new_constraint)
            if verbose:
                log_messages.append(f"            Added constraint: {negation_formula} @1.0")
        
        # Check 2: Find original and add P_original ⟹ ¬P_aux @1.0
        # Use pre-computed embedding if available
        if aux_id in prop_embeddings:
            aux_embedding = prop_embeddings[aux_id]
        else:
            aux_embedding = sbert_model.encode(aux_translation)
        
        best_match = None
        best_score = 0.5  # Minimum threshold
        
        for orig_prop in original_props:
            orig_id = orig_prop.get("id", "")
            orig_translation = orig_prop.get("translation", "")
            
            # Use pre-computed embedding if available
            if orig_id in prop_embeddings:
                orig_embedding = prop_embeddings[orig_id]
            else:
                orig_embedding = sbert_model.encode(orig_translation)
            
            score = compute_cosine_similarity(aux_embedding, orig_embedding)
            
            if score > best_score:
                best_score = score
                best_match = orig_prop
        
        if best_match:
            orig_id = best_match.get("id")
            implication_formula = f"{orig_id} ⟹ ¬{aux_id}"
            
            if not constraint_exists(implication_formula, updated_constraints):
                new_constraint = create_constraint(
                    constraint_id=get_next_constraint_id(updated_constraints),
                    formula=implication_formula,
                    translation=f"If {best_match.get('translation', '')} then not {aux_translation}",
                    llm_weight=1.0,
                    evidence="Auto-generated",
                    reasoning="Mutual exclusion constraint between original and auxiliary"
                )
                updated_constraints.append(new_constraint)
                if verbose:
                    log_messages.append(f"            Added constraint: {implication_formula} @1.0")
    
    return updated_constraints, log_messages


# =============================================================================
# FINITE DOMAIN AUXILIARY GENERATION
# =============================================================================

# Finite domain patterns and their alternatives
FINITE_DOMAIN_PATTERNS: Dict[str, Dict[str, Any]] = {
    "academic_major": {
        "patterns": [
            r"^(?P<subject>[A-Z][a-z]+)\s+studies\s+(?P<value>(?:computer science|[\w]+))\s*[.]?$",
            r"(?P<subject>\w+)'s\s+major\s+is\s+(?P<value>[\w\s]+)",
            r"(?P<subject>\w+)\s+majors?\s+in\s+(?P<value>[\w\s]+)",
        ],
        "alternatives": [
            "biology", "mathematics", "physics", "chemistry",
            "literature", "history", "psychology", "economics",
            "computer science", "engineering", "philosophy"
        ],
        "template": "{subject} studies {value}.",
        "exclusion_template": "If {subject} studies {original}, then {subject} does not study {alternative}.",
    },
    "job_role": {
        "patterns": [
            r"(?P<subject>\w+)\s+is\s+(?:a|an)\s+(?P<value>manager|engineer|analyst|developer|designer|scientist|teacher|professor|doctor|nurse|lawyer)",
            r"(?P<subject>\w+)\s+works\s+as\s+(?:a|an)\s+(?P<value>[\w\s]+)",
        ],
        "alternatives": [
            "manager", "engineer", "analyst", "developer",
            "designer", "scientist", "teacher", "professor"
        ],
        "template": "{subject} is a {value}.",
        "exclusion_template": "If {subject} is a {original}, then {subject} is not a {alternative}.",
    },
    "department": {
        "patterns": [
            r"(?P<subject>\w+)\s+works\s+in\s+(?:the\s+)?(?P<value>[\w\s]+)\s+department",
        ],
        "alternatives": [
            "Engineering", "Marketing", "Sales", "Human Resources",
            "Finance", "Research", "Operations", "Customer Service"
        ],
        "template": "{subject} works in the {value} department.",
        "exclusion_template": "If {subject} works in {original}, then {subject} does not work in {alternative}.",
    },
    "day_of_week": {
    "patterns": [
        r"(?P<subject>[\w\s']+?)\s+(?:are\s+)?due\s+(?:every\s+)?(?P<value>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
    ],
    "alternatives": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "template": "{subject} are due {value}.",
    "exclusion_template": "If {subject} are due {original}, then {subject} are not due {alternative}.",
    },
    "education_level": {
    "patterns": [
        r"(?P<subject>\w+)\s+is\s+a\s+(?P<value>university|college|high school|middle school|graduate)\s+student",
    ],
    "alternatives": ["university", "college", "high school", "middle school", "graduate"],
    "template": "{subject} is a {value} student.",
    "exclusion_template": "If {subject} is a {original} student, then {subject} is not a {alternative} student.",
    },
    "employment_type": {
    "patterns": [
        r"(?P<subject>\w+)\s+works\s+(?P<value>full-time|part-time)",
    ],
    "alternatives": ["full-time", "part-time"],
    "template": "{subject} works {value}.",
    "exclusion_template": "If {subject} works {original}, then {subject} does not work {alternative}.",
    }
}


def generate_finite_domain_auxiliaries(
    propositions: List[Dict[str, Any]],
    constraints: List[Dict[str, Any]],
    nlp: spacy.Language,
    sbert_model: SentenceTransformer,
    prop_embeddings: Dict[str, np.ndarray],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, np.ndarray], List[str]]:
    """
    Step 4: Generate auxiliary propositions for finite domains.

    Detects patterns like "X studies computer science" and generates
    auxiliary propositions for alternative values (biology, mathematics, etc.)
    with appropriate mutual exclusion constraints.

    Args:
        propositions: List of primitive propositions
        constraints: List of constraints
        nlp: Loaded SpaCy model
        sbert_model: Loaded SBERT model
        prop_embeddings: Pre-computed proposition embeddings
        verbose: Print debug information

    Returns:
        Tuple of (updated_propositions, updated_constraints, updated_embeddings, log_messages)
    """
    log_messages = []
    updated_props = list(propositions)
    updated_constraints = list(constraints)
    updated_embeddings = dict(prop_embeddings)

    # Track what domains we've already processed
    processed_domains = set()

    for prop in propositions:
        prop_id = prop.get("id", "")
        translation = prop.get("translation", "")
        explanation = prop.get("explanation", "").lower()

        # Skip if this is already an auxiliary proposition
        if "auxiliary" in explanation:
            continue

        # Try each domain pattern
        for domain_name, domain_config in FINITE_DOMAIN_PATTERNS.items():
            for pattern in domain_config["patterns"]:
                match = re.search(pattern, translation, re.IGNORECASE)
                if match:
                    subject = match.group("subject")
                    value = match.group("value").strip().lower()

                    # Skip if subject is a modal word
                    subject_lower = subject.lower()
                    if subject_lower in MODAL_WORDS:
                        if verbose:
                            log_messages.append(f"[FiniteDomain] Skipping {prop_id}: Subject '{subject}' is a modal word")
                        continue

                    # Validate subject is a proper noun
                    if not subject[0].isupper():
                        continue


                    # Create a unique key for this domain instance
                    domain_key = f"{domain_name}:{subject}:{value}"
                    if domain_key in processed_domains:
                        continue
                    processed_domains.add(domain_key)

                    if verbose:
                        log_messages.append(f"[FiniteDomain] {prop_id}: Detected {domain_name} pattern")
                        log_messages.append(f"              Subject: {subject}, Value: {value}")

                    # Get alternatives (excluding the current value)
                    alternatives = [
                        alt for alt in domain_config["alternatives"]
                        if alt.lower() != value
                    ]

                    # Limit to 3-4 most common alternatives to avoid explosion
                    alternatives = alternatives[:4]

                    for alt in alternatives:
                        # Generate auxiliary proposition text
                        aux_text = domain_config["template"].format(
                            subject=subject,
                            value=alt
                        )

                        # Check if this auxiliary already exists
                        if proposition_exists(aux_text, updated_props, sbert_model, updated_embeddings, threshold=0.90):
                            if verbose:
                                log_messages.append(f"              Auxiliary '{alt}' already exists, skipping")
                            continue

                        # Create new auxiliary proposition
                        aux_id = get_next_prop_id(updated_props)
                        aux_prop = create_proposition(
                            prop_id=aux_id,
                            translation=aux_text,
                            evidence=f"{prop.get('evidence', '')} (auxiliary proposition for {domain_name} domain)",
                            explanation=f"Auxiliary proposition for mutual exclusion with {prop_id}. Part of finite set: {domain_name}. Mutually exclusive alternative."
                        )
                        updated_props.append(aux_prop)
                        updated_embeddings[aux_id] = sbert_model.encode(aux_text)

                        if verbose:
                            log_messages.append(f"              Added auxiliary: {aux_id} = '{aux_text}'")

                        # Add negation constraint: ¬P_aux @1.0
                        negation_formula = f"¬{aux_id}"
                        if not constraint_exists(negation_formula, updated_constraints):
                            neg_constraint = create_constraint(
                                constraint_id=get_next_constraint_id(updated_constraints),
                                formula=negation_formula,
                                translation=f"It is not the case that {aux_text}",
                                llm_weight=1.0,
                                evidence="Auto-generated",
                                reasoning="Negation of auxiliary proposition - definitional consequence"
                            )
                            updated_constraints.append(neg_constraint)
                            if verbose:
                                log_messages.append(f"              Added constraint: {negation_formula} @1.0")

                        # Add mutual exclusion constraint: P_original ⟹ ¬P_aux @1.0
                        exclusion_formula = f"{prop_id} ⟹ ¬{aux_id}"
                        if not constraint_exists(exclusion_formula, updated_constraints):
                            excl_constraint = create_constraint(
                                constraint_id=get_next_constraint_id(updated_constraints),
                                formula=exclusion_formula,
                                translation=domain_config["exclusion_template"].format(
                                    subject=subject,
                                    original=value,
                                    alternative=alt
                                ),
                                llm_weight=1.0,
                                evidence="Auto-generated",
                                reasoning=f"Mutual exclusion over {domain_name} domain with weight 1.0"
                            )
                            updated_constraints.append(excl_constraint)
                            if verbose:
                                log_messages.append(f"              Added constraint: {exclusion_formula} @1.0")

                    break  # Don't try other patterns once we found a match

    return updated_props, updated_constraints, updated_embeddings, log_messages



# =============================================================================
# MAIN ENRICHMENT FUNCTION
# =============================================================================

def enrich_logic_structure(
    logified_path: str,
    source_path: str,
    output_path: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Main function: Enrich logified.json with deterministic constraint verification.
    
    Runs all four enrichment steps:
    1. verify_modal_pairs
    2. detect_modal_opposites
    3. detect_explicit_negations
    4. verify_auxiliary_negatives
    
    Args:
        logified_path: Path to logified.json from LLM
        source_path: Path to source document (PDF, DOCX, TXT)
        output_path: Path for output (default: logified_enriched.json)
        verbose: Print debug information
        
    Returns:
        Enriched logified structure dict
    """
    # Load inputs
    with open(logified_path, 'r', encoding='utf-8') as f:
        logified = json.load(f)
    
    source_text = extract_text_from_document(source_path)
    
    # Load models
    if verbose:
        print("Loading SpaCy model...")
    nlp = load_spacy_model()
    
    if verbose:
        print("Loading SBERT model...")
    sbert_model = load_sbert_model()
    
    
    # Load NLI model for conflict resolution
    if verbose:
        print("Loading NLI model for conflict resolution...")
    nli_model_name = "roberta-large-mnli"
    nli_tokenizer = AutoTokenizer.from_pretrained(nli_model_name)
    nli_model = AutoModelForSequenceClassification.from_pretrained(nli_model_name)
    nli_model.eval()

    
    # Extract initial data
    propositions = logified.get("primitive_props", [])
    constraints = logified.get("constraints", [])
    
    # Pre-compute embeddings for efficiency
    if verbose:
        print("Pre-computing proposition embeddings...")
    prop_embeddings = precompute_embeddings(propositions, sbert_model)
    
    all_logs = []
    
    # Step 1: Verify modal pairs
    if verbose:
        print("\n" + "="*60)
        print("STEP 1: Verifying modal pairs")
        print("="*60)
    
    propositions, constraints, prop_embeddings, logs = verify_modal_pairs(
        propositions, constraints, nlp, sbert_model, prop_embeddings, verbose
    )
    all_logs.extend(logs)
    if verbose:
        for log in logs:
            print(log)
    
    # Step 2: Detect modal opposites
    if verbose:
        print("\n" + "="*60)
        print("STEP 2: Detecting modal opposites")
        print("="*60)
    
    constraints, logs = detect_modal_opposites(
        propositions, constraints, nlp, sbert_model, prop_embeddings, verbose
    )
    all_logs.extend(logs)
    if verbose:
        for log in logs:
            print(log)
    
    # Step 3: Detect explicit negations
    if verbose:
        print("\n" + "="*60)
        print("STEP 3: Detecting explicit negations in source text")
        print("="*60)
    
    constraints, logs = detect_explicit_negations(
        source_text, propositions, constraints, nlp, sbert_model, prop_embeddings, verbose
    )
    all_logs.extend(logs)
    if verbose:
        for log in logs:
            print(log)
    
    # Step 4.a: Generate finite domain auxiliaries
    if verbose:
        print("\n" + "="*60)
        print("STEP 4: Generating finite domain auxiliaries")
        print("="*60)

    propositions, constraints, prop_embeddings, logs = generate_finite_domain_auxiliaries(
        propositions, constraints, nlp, sbert_model, prop_embeddings, verbose
    )
    all_logs.extend(logs)
    if verbose:
        for log in logs:
            print(log)

    
    
    # Step 4.b: Verify auxiliary negatives
    if verbose:
        print("\n" + "="*60)
        print("STEP 4: Verifying auxiliary negatives")
        print("="*60)
    
    constraints, logs = verify_auxiliary_negatives(
        propositions, constraints, sbert_model, prop_embeddings, verbose
    )
    all_logs.extend(logs)
    if verbose:
        for log in logs:
            print(log)
    
    # Build enriched structure
    enriched = {
        "primitive_props": propositions,
        "constraints": constraints,
        "_enrichment_log": all_logs
    }
    
    
    # =========================================================================
    # Step 5: Detect and resolve P_i / ¬P_i conflicts using NLI
    # =========================================================================
    if verbose:
        print("\n" + "="*60)
        print("STEP 5: Resolving P_i / ¬P_i conflicts via NLI")
        print("="*60)
    
    temp_structure = {
        "primitive_props": propositions,
        "constraints": constraints
    }
    
    resolved_structure, logs = detect_and_resolve_conflicts(
        logic_structure=temp_structure,
        original_text=source_text,
        nli_model=nli_model,
        tokenizer=nli_tokenizer
    )
    
    propositions = resolved_structure["primitive_props"]
    constraints = resolved_structure["constraints"]
    all_logs.extend(logs)
    
    if verbose:
        for log in logs:
            print(log)
    
    # Build enriched structure AFTER conflict resolution
    enriched = {
        "primitive_props": propositions,
        "constraints": constraints,
        "_enrichment_log": all_logs
    }    

    # =========================================================================

    
    # Save output
    if output_path is None:
        # Correctly handle the suffix replacement
        base_path = str(Path(logified_path))
        if base_path.endswith('.json'):
            output_path = base_path[:-5] + '_enriched.json'
        else:
            output_path = base_path + '_enriched.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print("\n" + "="*60)
        print(f"DONE: Enriched JSON saved to {output_path}")
        print(f"      Propositions: {len(propositions)}")
        print(f"      Constraints: {len(constraints)}")
        print("="*60)
    
    return enriched


# =============================================================================
# CLI
# =============================================================================

def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Enrich logified.json with deterministic constraint verification"
    )
    parser.add_argument(
        "logified_path",
        type=str,
        help="Path to logified.json from LLM"
    )
    parser.add_argument(
        "source_path",
        type=str,
        help="Path to source document (PDF, DOCX, TXT)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output path (default: logified_enriched.json)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    enrich_logic_structure(
        logified_path=args.logified_path,
        source_path=args.source_path,
        output_path=args.output,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
