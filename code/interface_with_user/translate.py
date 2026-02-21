#!/usr/bin/env python3
"""
translate.py - Neuro-Symbolic Logic Translator

A drop-in replacement for the previous translation logic.
Input: User Query + JSON Logified Data
Output: Propositional Formula (verified via NLI)

Architecture:
1. Retrieval: SBERT/Hybrid search (Preserved from original)
2. Modal Opposite Detection: Check if hypothesis contradicts KB via modal antonyms
3. Antonym Contradiction Detection: Check if hypothesis contradicts KB via lexical antonyms
4. Generation: LLM generates candidate formula(s)
5. Verbalization: Python recursively converts Logic -> "Structured English"
6. Verification: NLI model scores candidates to find the best semantic match
7. Adaptive Voting: If NLI confidence < threshold, sample more and vote
"""

import sys
import os
import re
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Union, Tuple, Optional
from collections import Counter

from config.retrieval_config import TEMPERATURE_LOGIC_CONVERTER, MAX_TOKENS, REASONING_EFFORT, SBERT_TOP_K, SBERT_MIN_SIMILARITY, ENABLE_HYBRID_EMBEDDING
from config.retrieval_config import REASONING_MODEL, TRANSLATE_MODEL, TEMPERATURE_TRANSLATE, REASONING_EFFORT_TRANSLATE, PROMPT_TRANSLATION
from config.retrieval_config import TRIGGER_QUERY, ADDITIONAL_LLM_QUERY, SBERT_MODEL, NLI_MODEL

# Add code directory to Python path
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import negation detection
from interface_with_user import negation_detection

# Import modal detection functions from check_logic_structure
from from_text_to_logic.check_logic_structure import (
    detect_modal_word,
    remove_modal_word,
    get_modal_antonyms,
    load_spacy_model,
    MODAL_WORDS
)

# External Dependencies
try:
    from openai import OpenAI
    from sentence_transformers import CrossEncoder, SentenceTransformer


    # Reuse your existing RAG infrastructure
    from baseline_rag.retriever import (
        load_sbert_model,
        encode_chunks,
        encode_query,
        compute_cosine_similarity
    )

except ImportError as e:
    print(f"CRITICAL: Missing dependencies.\nError: {e}")
    sys.exit(1)

# Global cache for NLI model and SpaCy model
_cached_nli_model = None
_cached_spacy_model = None

# ==========================================
# 1. INFIX FORMULA PARSER (matches translate_old.py style)
# ==========================================

Formula = Union[str, Tuple[str, ...]]

def tokenize_formula(formula: str) -> List[str]:
    """Tokenize an infix formula into operators, parentheses, and proposition IDs."""
    # Normalize Unicode operators to ASCII
    formula = formula.replace('⟹', '=>').replace('⇒', '=>').replace('→', '=>')
    formula = formula.replace('⟺', '<=>').replace('⇔', '<=>').replace('↔', '<=>')
    formula = formula.replace('∧', '&').replace('∨', '|')
    formula = formula.replace('¬', '~').replace('!', '~')

    # Pattern: proposition IDs (P_\d+), operators, parentheses
    pattern = r'(P_\d+|<=>|=>|<=|[&|~()])'
    tokens = re.findall(pattern, formula)
    return [t.strip() for t in tokens if t.strip()]


def parse_infix_formula(formula_str: str) -> Formula:
    """
    Parse infix formula string into nested tuple structure.

    Supports: ¬/~ (NOT), ∧/& (AND), ∨/| (OR), ⟹/=> (IMPLIES), ⟺/<=> (IFF)

    Grammar (precedence low to high):
      formula := iff_expr
      iff_expr := implies_expr ('<=>' implies_expr)*
      implies_expr := or_expr ('=>' or_expr)*
      or_expr := and_expr ('|' and_expr)*
      and_expr := not_expr ('&' not_expr)*
      not_expr := '~' not_expr | atom
      atom := '(' formula ')' | prop_id
    """
    tokens = tokenize_formula(formula_str)
    if not tokens:
        raise ValueError(f"Empty formula: {formula_str}")

    expr, remaining = _parse_iff(tokens)

    if remaining:
        raise ValueError(f"Unexpected tokens after parsing: {remaining}")

    return expr

def _parse_implies(tokens: List[str]) -> Tuple[Any, List[str]]:
    left, tokens = _parse_or(tokens)

    while tokens and tokens[0] in ('=>', '<='):
        op = tokens[0]
        tokens = tokens[1:]
        right, tokens = _parse_or(tokens)
        if op == '=>':
            left = ('IMPLIES', left, right)
        else:
            # A <= B  ==  B => A
            left = ('IMPLIES', right, left)

    return left, tokens


def _parse_iff(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse IFF (biconditional) expressions."""
    left, tokens = _parse_implies(tokens)

    while tokens and tokens[0] == '<=>':
        tokens = tokens[1:]  # consume '<=>'
        right, tokens = _parse_implies(tokens)
        left = ('IFF', left, right)

    return left, tokens


def _parse_or(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse OR expressions."""
    left, tokens = _parse_and(tokens)

    while tokens and tokens[0] == '|':
        tokens = tokens[1:]  # consume '|'
        right, tokens = _parse_and(tokens)
        left = ('OR', left, right)

    return left, tokens


def _parse_and(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse AND expressions."""
    left, tokens = _parse_not(tokens)

    while tokens and tokens[0] == '&':
        tokens = tokens[1:]  # consume '&'
        right, tokens = _parse_not(tokens)
        left = ('AND', left, right)

    return left, tokens


def _parse_not(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse NOT expressions."""
    if not tokens:
        raise ValueError("Unexpected end of formula")

    if tokens[0] == '~':
        tokens = tokens[1:]  # consume '~'
        expr, tokens = _parse_not(tokens)
        return ('NOT', expr), tokens
    else:
        return _parse_atom(tokens)


def _parse_atom(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse atomic propositions or parenthesized expressions."""
    if not tokens:
        raise ValueError("Unexpected end of formula")

    if tokens[0] == '(':
        tokens = tokens[1:]  # consume '('
        expr, tokens = _parse_iff(tokens)
        if not tokens or tokens[0] != ')':
            raise ValueError("Missing closing parenthesis")
        tokens = tokens[1:]  # consume ')'
        return expr, tokens

    # Must be a proposition ID
    prop_id = tokens[0]
    if not prop_id.startswith('P_'):
        raise ValueError(f"Invalid proposition ID: {prop_id}")

    return prop_id, tokens[1:]


def verbalize(formula: Formula, prop_map: Dict[str, str]) -> str:
    """Recursively converts logic to NLI-ready English."""
    if isinstance(formula, str):
        if formula not in prop_map:
            raise ValueError(f"Unknown proposition ID: {formula}")
        return prop_map[formula]

    op = formula[0]
    if op == "NOT":
        return f"it is not the case that {verbalize(formula[1], prop_map)}"
    elif op == "AND":
        return f"{verbalize(formula[1], prop_map)}, and {verbalize(formula[2], prop_map)}"
    elif op == "OR":
        return f"{verbalize(formula[1], prop_map)}, or {verbalize(formula[2], prop_map)}"
    elif op == "IMPLIES":
        return f"if {verbalize(formula[1], prop_map)}, then {verbalize(formula[2], prop_map)}"
    elif op == "IFF":
        return f"{verbalize(formula[1], prop_map)} if and only if {verbalize(formula[2], prop_map)}"
    else:
        raise ValueError(f"Unknown operator in formula: {op}")


def verbalize_from_string(formula_str: str, prop_map: Dict[str, str]) -> str:
    """Parse infix formula and verbalize it."""
    return verbalize(parse_infix_formula(formula_str), prop_map)


# ==========================================
# 2. RETRIEVAL & HELPERS
# ==========================================

def extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = ENABLE_HYBRID_EMBEDDING) -> List[Dict]:
    """Preserved: Extract primitive propositions from logified JSON."""
    primitive_props = logified_structure.get('primitive_props', [])
    chunks = []
    for prop in primitive_props:
        translation = prop['translation']
        evidence = prop.get('evidence', '')
        text_to_embed = f"{translation} | Evidence: {evidence[:200]}" if hybrid_embedding and evidence else translation

        chunks.append({
            'text': text_to_embed,
            'id': prop['id'],
            'translation': prop['translation'],
            'evidence': evidence,
            'explanation': prop.get('explanation', '')
        })
    return chunks


def retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: int = SBERT_TOP_K, minimal_similarity = SBERT_MIN_SIMILARITY) -> List[Dict]:
    """Preserved (simplified): Retrieve relevant chunks using SBERT."""
    chunk_embeddings = encode_chunks(chunks, sbert_model)
    query_embedding = encode_query(query, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)
    top_k_indices = np.argsort(similarities)[::-1][:k]

    retrieved = []
    for idx in top_k_indices:
        if similarities[idx] < minimal_similarity:
            break
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
        retrieved.append(chunk)
    return retrieved


def is_yes_no_question(query: str) -> bool:
    """Preserved: Detect yes/no questions."""
    starters = ['is ', 'are ', 'was ', 'were ', 'will ', 'would ', 'should ', 'could ', 'can ', 'may ', 'must ', 'does ', 'do ', 'did ']
    return any(query.lower().strip().startswith(s) for s in starters)


def get_configured_client(api_key: str, model: str) -> Tuple[OpenAI, str]:
    """Helper to configure OpenAI client for OpenRouter if needed."""
    if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
        client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
        if not model.startswith('openai/'):
            model = f'openai/{model}'
    else:
        client = OpenAI(api_key=api_key)
    return client, model


def convert_yes_no_to_statement(
    query: str,
    api_key: str,
    model: str = REASONING_MODEL,
    temperature: float = TEMPERATURE_LOGIC_CONVERTER,
    reasoning_effort: str = REASONING_EFFORT,
    max_tokens: int = MAX_TOKENS
) -> str:
    """
    Convert a Yes/No question to a declarative statement using an LLM.
    """
    prompt = f"""Convert the following Yes/No question into a declarative statement that expresses what the question is asking about.

    EXAMPLES:
    Question: "Can the receiving party share information with third parties?"
    Statement: "The receiving party can share information with third parties"

    Question: "Is Alice a student?"
    Statement: "Alice is a student"

    Question: "Does the policy allow data retention?"
    Statement: "The policy allows data retention"

    Question: "Will the contract expire in 2025?"
    Statement: "The contract will expire in 2025"

    Question: "Should employees wear safety equipment?"
    Statement: "Employees should wear safety equipment"

    Now convert this question:
    Question: "{query}"

    OUTPUT FORMAT (JSON only, no other text):
    {{
        "statement": "<declarative statement>",
        "reasoning": "<1 sentence explanation>"
    }}"""

    if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
        client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
        if not model.startswith('openai/'):
            model = f'openai/{model}'
    else:
        client = OpenAI(api_key=api_key)

    base_model = model.replace("openai/", "")
    is_reasoning_model = base_model.startswith("gpt-5") or base_model.startswith("o1") or base_model.startswith("o3")

    if is_reasoning_model:
        if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
            api_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "extra_body": {"reasoning": {"effort": reasoning_effort, "enabled": True}}
            }
        else:
            api_params = {
                "model": model,
                "messages": [
                    {"role": "developer", "content": "You are a precise question-to-statement converter."},
                    {"role": "user", "content": prompt}
                ],
                "reasoning_effort": reasoning_effort,
                "max_completion_tokens": max_tokens
            }
    else:
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a precise question-to-statement converter."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    response = client.chat.completions.create(**api_params)

    response_text = response.choices[0].message.content
    if response_text is None:
        raise ValueError("LLM returned empty response")

    response_text = response_text.strip()

    try:
        result = json.loads(response_text)
        return result['statement']
    except (json.JSONDecodeError, KeyError) as e:
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
            try:
                result = json.loads(json_text)
                return result['statement']
            except (json.JSONDecodeError, KeyError):
                pass
        raise ValueError(f"Failed to parse LLM response: {e}\nResponse: {response_text}")


# ==========================================
# 3. MODAL OPPOSITE DETECTION
# ==========================================

def get_spacy_model_singleton():
    """Load SpaCy model once and cache it."""
    global _cached_spacy_model
    if _cached_spacy_model is None:
        _cached_spacy_model = load_spacy_model()
    return _cached_spacy_model


def detect_modal_opposite(
    query: str,
    retrieved_chunks: List[Dict],
    sbert_model,
    verbose: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Detect if the hypothesis has a modal word that is the opposite of a KB proposition.

    For example:
    - Hypothesis: "Alice often studies late at night" (modal: "often")
    - KB has: "Alice rarely studies late at night" (modal: "rarely")
    - "often" and "rarely" are antonyms with same base text
    - Returns negation of the KB proposition: ¬P_27

    Args:
        query: The hypothesis text
        retrieved_chunks: List of retrieved propositions from KB
        sbert_model: Loaded SBERT model for embedding comparison
        verbose: Print debug information

    Returns:
        Dict with formula result if modal opposite found, None otherwise
    """
    nlp = get_spacy_model_singleton()

    # Check if hypothesis has a modal word
    hypothesis_modal_info = detect_modal_word(query, nlp)

    if not hypothesis_modal_info:
        return None

    hyp_modal_word, _ = hypothesis_modal_info
    hyp_base_text = remove_modal_word(query, hyp_modal_word, nlp)
    hyp_base_embedding = sbert_model.encode(hyp_base_text)
    antonyms = get_modal_antonyms(hyp_modal_word)

    if verbose:
        print(f"  [Modal Detection] Hypothesis modal: '{hyp_modal_word}'")
        print(f"  [Modal Detection] Base text: '{hyp_base_text}'")
        print(f"  [Modal Detection] Antonyms: {antonyms}")

    if not antonyms:
        return None

    # Check each retrieved proposition for modal opposite
    for chunk in retrieved_chunks:
        prop_translation = chunk['translation']
        prop_modal_info = detect_modal_word(prop_translation, nlp)

        if not prop_modal_info:
            continue

        prop_modal_word, _ = prop_modal_info

        # Is this an antonym modal?
        if prop_modal_word in antonyms:
            prop_base_text = remove_modal_word(prop_translation, prop_modal_word, nlp)
            prop_base_embedding = sbert_model.encode(prop_base_text)

            # Check base text similarity using cosine similarity
            norm_hyp = np.linalg.norm(hyp_base_embedding)
            norm_prop = np.linalg.norm(prop_base_embedding)

            if norm_hyp > 0 and norm_prop > 0:
                similarity = float(np.dot(hyp_base_embedding, prop_base_embedding) / (norm_hyp * norm_prop))
            else:
                similarity = 0.0

            if verbose:
                print(f"  [Modal Detection] Found KB prop with antonym modal '{prop_modal_word}'")
                print(f"  [Modal Detection] KB base text: '{prop_base_text}'")
                print(f"  [Modal Detection] Base similarity: {similarity:.3f}")

            if similarity > 0.85:
                # MODAL OPPOSITE FOUND!
                prop_id = chunk['id']

                if verbose:
                    print(f"  [Modal Detection] ✓ MATCH! Returning ¬{prop_id}")

                return {
                    "formula": f"¬{prop_id}",
                    "translation": f"it is not the case that {prop_translation}",
                    "explanation": f"Modal opposite detected: hypothesis '{hyp_modal_word}' contradicts KB '{prop_modal_word}' (base similarity: {similarity:.2f})",
                    "confidence": 1.0,
                    "modal_opposite_detected": True
                }

    return None


# ==========================================
# 4. ANTONYM CONTRADICTION DETECTION
# ==========================================

# Fallback antonym pairs for cases WordNet misses
ANTONYM_PAIRS_FALLBACK = {
    "part-time": ["full-time"],
    "full-time": ["part-time"],
    "parttime": ["fulltime", "full-time"],
    "fulltime": ["parttime", "part-time"],
    "morning": ["evening", "night", "afternoon"],
    "evening": ["morning"],
    "night": ["day", "morning"],
    "day": ["night"],
    "hot": ["cold"],
    "cold": ["hot"],
    "big": ["small"],
    "small": ["big"],
    "open": ["closed", "close"],
    "closed": ["open"],
    "close": ["open"],
    "start": ["end", "finish"],
    "end": ["start", "begin"],
    "begin": ["end", "finish"],
    "finish": ["start", "begin"],
    "before": ["after"],
    "after": ["before"],
    "indoor": ["outdoor"],
    "outdoor": ["indoor"],
    "indoors": ["outdoors"],
    "outdoors": ["indoors"],
    "online": ["offline"],
    "offline": ["online"],
    "public": ["private"],
    "private": ["public"],
    "temporary": ["permanent"],
    "permanent": ["temporary"],
    "active": ["inactive"],
    "inactive": ["active"],
    "visible": ["invisible", "hidden"],
    "invisible": ["visible"],
    "hidden": ["visible"],
    "senior": ["junior"],
    "junior": ["senior"],
    "male": ["female"],
    "female": ["male"],
    "married": ["single", "unmarried"],
    "single": ["married"],
    "unmarried": ["married"],
    "employed": ["unemployed"],
    "unemployed": ["employed"],
}


def get_word_antonyms(word: str) -> List[str]:
    """Get antonyms of a word using WordNet with fallback table."""
    from nltk.corpus import wordnet as wn
    
    antonyms = set()
    word_lower = word.lower()
    
    # Try different formats for WordNet lookup
    word_underscore = word_lower.replace("-", "_")
    word_hyphen = word_lower.replace("_", "-")
    word_nohyphen = word_lower.replace("-", "")
    
    # WordNet lookup
    for word_variant in [word_underscore, word_hyphen, word_lower, word_nohyphen]:
        for syn in wn.synsets(word_variant):
            for lemma in syn.lemmas():
                for antonym in lemma.antonyms():
                    ant_name = antonym.name().replace("_", "-")
                    antonyms.add(ant_name.lower())
    
    # Fallback table lookup
    for variant in [word_lower, word_nohyphen, word_hyphen]:
        if variant in ANTONYM_PAIRS_FALLBACK:
            antonyms.update(ANTONYM_PAIRS_FALLBACK[variant])
    
    return list(antonyms)


def detect_antonym_contradiction(
    query: str,
    retrieved_chunks: List[Dict],
    sbert_model,
    verbose: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Detect if the hypothesis contains a word that is an antonym of a word 
    in a KB proposition, in the same context.
    
    For example:
    - Hypothesis: "Alice works full-time"
    - KB has: "Alice works part-time" (P_5)
    - "full-time" and "part-time" are antonyms
    - Replacing "full-time" with "part-time" gives high similarity to KB prop
    - Returns negation of the KB proposition: ¬P_5
    
    Args:
        query: The hypothesis text
        retrieved_chunks: List of retrieved propositions from KB
        sbert_model: Loaded SBERT model for embedding comparison
        verbose: Print debug information
        
    Returns:
        Dict with formula result if antonym contradiction found, None otherwise
    """
    nlp = get_spacy_model_singleton()
    query_lower = query.lower()
    
    if verbose:
        print("  [Antonym Detection] Checking for antonym contradictions...")
    
    # Step 1: Extract words to check from the query
    # Use regex to find hyphenated compounds (SpaCy may tokenize them incorrectly)
    hyphenated_pattern = re.compile(r'\b[\w]+-[\w]+\b')
    hyphenated_words = hyphenated_pattern.findall(query_lower)
    words_to_check = list(hyphenated_words)
    
    # Also add content words from SpaCy tokenization
    query_doc = nlp(query_lower)
    for token in query_doc:
        if token.pos_ in ('NOUN', 'VERB', 'ADJ', 'ADV') and len(token.text) >= 3:
            if token.text not in words_to_check:
                words_to_check.append(token.text)
    
    if verbose:
        print(f"  [Antonym Detection] Words to check: {words_to_check}")
    
    # Step 2: For each word, check if it has antonyms that appear in KB propositions
    for word in words_to_check:
        antonyms = get_word_antonyms(word)
        if not antonyms:
            continue
            
        if verbose:
            print(f"  [Antonym Detection] Word '{word}' has antonyms: {antonyms}")
        
        # Step 3: Check each retrieved proposition for antonym matches
        for chunk in retrieved_chunks:
            prop_text = chunk['translation'].lower()
            
            for antonym in antonyms:
                # Check if the antonym appears in the proposition
                # Handle both hyphenated and non-hyphenated forms
                antonym_variants = [antonym, antonym.replace("-", ""), antonym.replace("-", " ")]
                
                antonym_found = any(variant in prop_text for variant in antonym_variants)
                
                if antonym_found:
                    # Step 4: Verify same context using embedding similarity
                    # Replace the word in the query with the antonym
                    modified_query = query_lower.replace(word, antonym)
                    
                    # Also try replacing non-hyphenated form if needed
                    if word.replace("-", "") in query_lower:
                        modified_query = query_lower.replace(word.replace("-", ""), antonym)
                    
                    # Compute embedding similarity
                    mod_emb = sbert_model.encode(modified_query)
                    prop_emb = sbert_model.encode(prop_text)
                    
                    norm_mod = np.linalg.norm(mod_emb)
                    norm_prop = np.linalg.norm(prop_emb)
                    
                    if norm_mod > 0 and norm_prop > 0:
                        similarity = float(np.dot(mod_emb, prop_emb) / (norm_mod * norm_prop))
                    else:
                        similarity = 0.0
                    
                    if verbose:
                        print(f"  [Antonym Detection] Found antonym pair: '{word}' vs '{antonym}'")
                        print(f"  [Antonym Detection] Modified query: '{modified_query}'")
                        print(f"  [Antonym Detection] KB proposition: '{prop_text}'")
                        print(f"  [Antonym Detection] Context similarity: {similarity:.3f}")
                    
                    # High similarity means same context → contradiction
                    if similarity > 0.90:
                        prop_id = chunk['id']
                        
                        if verbose:
                            print(f"  [Antonym Detection] ✓ MATCH! Returning ¬{prop_id}")
                        
                        return {
                            "formula": f"¬{prop_id}",
                            "translation": f"it is not the case that {chunk['translation']}",
                            "explanation": f"Antonym contradiction: '{word}' contradicts '{antonym}' in KB (similarity: {similarity:.2f})",
                            "confidence": 1.0,
                            "antonym_contradiction_detected": True
                        }
    
    return None


# ==========================================
# 5. NEURO-SYMBOLIC CORE
# ==========================================

sbert_model = SentenceTransformer(SBERT_MODEL)


def load_nli_model_singleton():
    global _cached_nli_model
    if _cached_nli_model is None:
        print("  Loading NLI Model (cross-encoder/nli-deberta-v3-large)...")
        _cached_nli_model = CrossEncoder(NLI_MODEL)
    return _cached_nli_model



def generate_candidates_llm(
    prompt: str, api_key: str, model: str, temperature: float = TEMPERATURE_TRANSLATE
    ) -> List[Dict]:
    """Call LLM to get JSON result - handles both single object and candidates list."""
    client, model = get_configured_client(api_key, model)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)

        if 'candidates' in result:
            return result['candidates']
        elif 'formula' in result:
            return [result]
        else:
            print(f"  Warning: LLM response missing 'formula' or 'candidates' key")
            return []

    except Exception as e:
        print(f"  Warning: LLM generation failed or returned invalid JSON: {e}")
        print(f"  [LLM ERROR] Generation failed: {type(e).__name__}: {e}")
        return []

def load_prompt_template(prompt_name: str) -> str:
    prompt_path = code_dir / "prompts" / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")



def build_prompt(query: str, props_text: str, available_ids: str, query_is_negative: bool) -> str:
    """
    Build the LLM prompt for translating query to propositional formula.
    """

    polarity_str = "NEGATIVE (prohibition/restriction)" if query_is_negative else "AFFIRMATIVE"

    template = load_prompt_template(PROMPT_TRANSLATION)
    prompt = (
    template
    .replace("{props_text}", props_text)
    .replace("{query}", query)
    .replace("{available_ids}", available_ids)
    .replace("{polarity_str}", polarity_str)
    )

    return prompt


def normalize_formula(formula: str) -> str:
    """
    Normalize a formula for comparison purposes.
    Removes whitespace and normalizes operator symbols.
    """
    if formula is None:
        return "NONE"
    # Normalize to ASCII operators
    normalized = formula.replace('⟹', '=>').replace('⇒', '=>').replace('→', '=>')
    normalized = normalized.replace('⟺', '<=>').replace('⇔', '<=>').replace('↔', '<=>')
    normalized = normalized.replace('∧', '&').replace('∨', '|')
    normalized = normalized.replace('¬', '~').replace('!', '~')
    # Remove whitespace
    normalized = re.sub(r'\s+', '', normalized)
    return normalized


def compute_nli_confidence(original_text: str, back_translated_text: str) -> float:
    """Compute SBERT-based confidence score between original and back-translated text.
    
    Uses cosine similarity of sentence embeddings instead of NLI.
    This works better for identical/paraphrased sentences where NLI incorrectly
    returns NEUTRAL with very low confidence.
    """
    embeddings = sbert_model.encode([original_text, back_translated_text])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


def select_best_candidate(
    candidates: List[Dict],
    query: str,
    prop_map: Dict[str, str],
    nli_model,
    verbose: bool = True
) -> Tuple[Optional[Dict], str, float]:
    """
    Select the best candidate using NLI verification.
    
    Returns:
        Tuple of (winner_candidate, verbalized_text, nli_confidence)
    """
    valid_candidates = []
    verbalized_texts = []

    for c in candidates:
        if c.get('formula') == "NONE":
            valid_candidates.append(c)
            verbalized_texts.append("Not matching proposition")
            continue
        try:
            v_text = verbalize_from_string(c['formula'], prop_map)
            valid_candidates.append(c)
            verbalized_texts.append(v_text)
        except Exception as e:
            if verbose:
                print(f"  Skipped invalid formula {c.get('formula')}: {e}")
            continue

    if not valid_candidates:
        return None, "", -999.0

    pairs = [(query, v_text) for v_text in verbalized_texts]
    logits = nli_model.predict(pairs)
    exp_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    best_net_score = -999.0
    best_idx = 0

    for i, (prob, c) in enumerate(zip(probs, valid_candidates)):
        entailment = float(prob[2])
        contradiction = float(prob[0])
        net_score = entailment - contradiction

        if verbose:
            print(f"  Cand {i}: {c['formula']}")
            print(f"    -> Verbal: {verbalized_texts[i][:60]}...")
            print(f"    -> Score: {net_score:.2f} (Ent: {entailment:.2f}, Con: {contradiction:.2f})")

        if net_score > best_net_score:
            best_net_score = net_score
            best_idx = i

    return valid_candidates[best_idx], verbalized_texts[best_idx], best_net_score


def translate_query(
    query: str,
    json_path: str,
    api_key: str,
    model: str = TRANSLATE_MODEL,
    temperature: float = TEMPERATURE_TRANSLATE,
    reasoning_effort: str = REASONING_EFFORT_TRANSLATE,
    max_tokens: int = MAX_TOKENS,
    k: int = SBERT_TOP_K,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True
    ) -> Dict[str, Any]:
    """
    Main Interface Function.
    Replaces the old logic with the Generate -> Verbalize -> Verify loop.
    Now includes Modal Opposite Detection and Antonym Contradiction Detection before LLM generation.
    Also includes adaptive voting when NLI confidence is below threshold.
    """

    # 1. Pre-process (Yes/No Handling)
    original_query = query
    if is_yes_no_question(query):
        if verbose:
            print(f"Detected Yes/No question. Converting...")
        try:
            query = convert_yes_no_to_statement(query, api_key, model)
            if verbose:
                print(f"  → Statement: {query}")
        except:
            if verbose:
                print("  → Conversion failed, proceeding with original.")

    # 2. Retrieval
    if verbose:
        print(f"Loading propositions from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        logified_structure = json.load(f)

    chunks = extract_proposition_chunks(logified_structure)
    sbert_model = load_sbert_model(sbert_model_name)
    retrieved = retrieve_top_k_propositions(query, chunks, sbert_model, k=k)

    if not retrieved:
        return {
            "formula": "NONE",
            "translation": "No relevant props",
            "query": query,
            "original_query": original_query,
            "explanation": "No documents found.",
            "confidence": 0.5
        }

    # 3. MODAL OPPOSITE DETECTION
    # Check if hypothesis has a modal word that contradicts a KB proposition
    if verbose:
        print("\nChecking for modal opposites...")

    modal_opposite_result = detect_modal_opposite(query, retrieved, sbert_model, verbose=verbose)

    if modal_opposite_result:
        # Modal opposite found - return immediately without LLM
        modal_opposite_result["query"] = query
        modal_opposite_result["original_query"] = original_query
        if verbose:
            print(f"  → Modal opposite detected! Returning: {modal_opposite_result['formula']}")
        return modal_opposite_result

    # 4. ANTONYM CONTRADICTION DETECTION (NEW STEP)
    # Check if hypothesis has a lexical antonym that contradicts a KB proposition
    if verbose:
        print("\nChecking for antonym contradictions...")

    antonym_result = detect_antonym_contradiction(query, retrieved, sbert_model, verbose=verbose)

    if antonym_result:
        # Antonym contradiction found - return immediately without LLM
        antonym_result["query"] = query
        antonym_result["original_query"] = original_query
        if verbose:
            print(f"  → Antonym contradiction detected! Returning: {antonym_result['formula']}")
        return antonym_result

    # 5. Build Prompt Variables (matching translate_old.py style)
    props_text = ""
    prop_ids = []
    for chunk in retrieved:
        prop_id = chunk['id']
        prop_ids.append(prop_id)

        # Add polarity annotation
        is_negative = negation_detection.detect_negation_in_proposition(chunk['translation'])
        polarity = "NEGATIVE" if is_negative else "AFFIRMATIVE"

        props_text += f"""
    {prop_id}: {chunk['translation']} [Polarity: {polarity}]
    Evidence: {chunk.get('evidence', 'N/A')}
    Explanation: {chunk.get('explanation', 'N/A')}
    """

    # Create available IDs string (no ellipsis text in ID list)
    available_ids = ", ".join(prop_ids[:10])

    # Build prop_map for verbalization
    prop_map = {p['id']: p['translation'].strip(".") for p in retrieved}

    # Detect query polarity
    query_is_negative = negation_detection.detect_negation_in_hypothesis(query)

    # Build the prompt
    prompt = build_prompt(query, props_text, available_ids, query_is_negative)

    # 6. Generate Candidates (Step A)
    if verbose:
        print("\nStep A: Generating logical candidates...")

    candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature)

    if not candidates:
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "LLM failed to generate valid candidates."
        }

    # If model abstained, return UNCERTAIN
    if len(candidates) == 1 and candidates[0].get("formula") == "NONE":
        return {
            "formula": "NONE",
            "translation": candidates[0].get("translation", "Not matching proposition"),
            "query": query,
            "original_query": original_query,
            "explanation": "LLM abstained (no matching proposition).",
"confidence": 0.5
        }

    # 7. Verbalize & Verify (Step B & C)
    if verbose:
        print("Step B & C: Verbalizing and Verifying with NLI...")
    nli_model = load_nli_model_singleton()

    winner, winning_text, best_net_score = select_best_candidate(
        candidates, query, prop_map, nli_model, verbose=verbose
    )

    if winner is None:
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "All candidates failed syntax parsing."
        }

    # Compute SBERT confidence for voting trigger decision
    sbert_confidence = compute_nli_confidence(query, winning_text)
    if verbose:
        print(f"  SBERT confidence: {sbert_confidence:.4f} (NLI score: {best_net_score:.4f})")

    # 8. ADAPTIVE VOTING (NEW STEP)
    # If SBERT confidence is below threshold, sample more candidates and vote
    if sbert_confidence < TRIGGER_QUERY and ADDITIONAL_LLM_QUERY > 0:
    #if best_net_score < TRIGGER_QUERY and ADDITIONAL_LLM_QUERY > 0:
        if verbose:
            print(f"\n[Adaptive Voting] Confidence {best_net_score:.2f} < {TRIGGER_QUERY}, triggering voting...")
            print(f"[Adaptive Voting] Making {ADDITIONAL_LLM_QUERY} additional LLM calls...")

        # Collect all formulas (first one + additional samples)
        all_formulas = [normalize_formula(winner['formula'])]
        all_results = [(winner, winning_text, best_net_score)]

        for i in range(ADDITIONAL_LLM_QUERY):
            if verbose:
                print(f"  [Voting] Additional call {i+1}/{ADDITIONAL_LLM_QUERY}...")
            
            additional_candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature)
            
            if additional_candidates and not (len(additional_candidates) == 1 and additional_candidates[0].get("formula") == "NONE"):
                add_winner, add_text, add_score = select_best_candidate(
                    additional_candidates, query, prop_map, nli_model, verbose=False
                )
                if add_winner is not None:
                    all_formulas.append(normalize_formula(add_winner['formula']))
                    all_results.append((add_winner, add_text, add_score))
                    if verbose:
                        print(f"    → Got formula: {add_winner['formula']} (score: {add_score:.2f})")
            else:
                # LLM abstained
                all_formulas.append("NONE")
                if verbose:
                    print(f"    → LLM abstained (NONE)")

        # Majority vote
        formula_counts = Counter(all_formulas)
        winning_formula, vote_count = formula_counts.most_common(1)[0]
        
        if verbose:
            print(f"\n[Adaptive Voting] Vote results: {dict(formula_counts)}")
            print(f"[Adaptive Voting] Winner: {winning_formula} ({vote_count}/{len(all_formulas)} votes)")

        # Find the result with the winning formula (prefer highest NLI score if tie)
        matching_results = [(w, t, s) for (w, t, s) in all_results 
                           if normalize_formula(w['formula']) == winning_formula]
        
        if matching_results:
            # Pick the one with highest NLI score
            matching_results.sort(key=lambda x: x[2], reverse=True)
            winner, winning_text, best_net_score = matching_results[0]
        
        # Update explanation with voting info
        voting_confidence = vote_count / len(all_formulas)
        explanation = f"Selected via voting ({vote_count}/{len(all_formulas)} votes, NLI: {best_net_score:.2f}). LLM Reasoning: {winner.get('reasoning', '')}"
        
        return {
            "formula": winner['formula'],
            "translation": winning_text,
            "query": query,
            "original_query": original_query,
            "explanation": explanation,
            "confidence": best_net_score,
            "voting_triggered": True,
            "voting_confidence": voting_confidence,
            "vote_counts": dict(formula_counts)
        }

    # No voting needed - return original result
    return {
        "formula": winner['formula'],
        "translation": winning_text,
        "query": query,
        "original_query": original_query,
        "explanation": f"Selected via NLI (Confidence: {best_net_score:.2f}). LLM Reasoning: {winner.get('reasoning', '')}",
        "confidence": best_net_score
    }


# ==========================================
# 6. MAIN ENTRY POINT
# ==========================================

def main():
    """Command-line interface for query translation."""
    parser = argparse.ArgumentParser(
        description="Neuro-Symbolic Logic Translator (Drop-in Replacement)",
        epilog="Example: python translate.py \"Can info be shared?\" logified.json --api-key sk-xxx"
    )
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("json_path", help="Path to logified JSON")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--model", default=TRANSLATE_MODEL, help="LLM model (default: gpt-4o)")
    parser.add_argument("--temperature", type=float, default=TEMPERATURE_TRANSLATE, help="Sampling temp")
    parser.add_argument("--reasoning-effort", default=REASONING_EFFORT, help="Reasoning effort (for reasoning models)")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS, help="Max tokens")
    parser.add_argument("--k", type=int, default=SBERT_TOP_K, help="Retrieval K")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    parser.add_argument("--sbert-model-name", default="all-MiniLM-L6-v2", help="SBERT model")

    args = parser.parse_args()

    if not os.path.exists(args.json_path):
        print(f"Error: JSON file not found: {args.json_path}")
        return 1

    try:
        result = translate_query(
            query=args.query,
            json_path=args.json_path,
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            k=args.k,
            sbert_model_name=args.sbert_model_name,
            verbose=not args.quiet
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nOutput saved to: {args.output}")
        else:
            if not args.quiet:
                print("\n" + "=" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
