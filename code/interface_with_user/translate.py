#!/usr/bin/env python3
"""
translate.py - Neuro-Symbolic Logic Translator

A drop-in replacement for the previous translation logic.
Input: User Query + JSON Logified Data
Output: Propositional Formula (verified via NLI)

Architecture:
1. Retrieval: SBERT/Hybrid search (Preserved from original)
2. Generation: LLM generates candidate formula(s)
3. Verbalization: Python recursively converts Logic -> "Structured English"
4. Verification: NLI model scores candidates to find the best semantic match
"""

import sys
import os
import re
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Union, Tuple, Optional

# Add code directory to Python path
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import negation detection
from interface_with_user import negation_detection

# External Dependencies
try:
    from openai import OpenAI
    from sentence_transformers import CrossEncoder
    
    # Reuse your existing RAG infrastructure
    from baseline_rag.retriever import (
        load_sbert_model,
        encode_chunks,
        encode_query,
        compute_cosine_similarity
    )
    
    # Reuse config
    try:
        from config import retrieval_config
    except ImportError:
        # Fallback config if not found
        class retrieval_config:
            SBERT_TOP_K = 20
            SBERT_MIN_SIMILARITY = 0.3
            ENABLE_HYBRID_EMBEDDING = True
            
except ImportError as e:
    print(f"CRITICAL: Missing dependencies.\nError: {e}")
    sys.exit(1)

# Global cache for NLI model
_cached_nli_model = None

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
    pattern = r'(P_\d+|<=>|=>|[&|~()])'
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


def _parse_iff(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse IFF (biconditional) expressions."""
    left, tokens = _parse_implies(tokens)
    
    while tokens and tokens[0] == '<=>':
        tokens = tokens[1:]  # consume '<=>'
        right, tokens = _parse_implies(tokens)
        left = ('IFF', left, right)
    
    return left, tokens


def _parse_implies(tokens: List[str]) -> Tuple[Formula, List[str]]:
    """Parse implication expressions."""
    left, tokens = _parse_or(tokens)
    
    while tokens and tokens[0] == '=>':
        tokens = tokens[1:]  # consume '=>'
        right, tokens = _parse_or(tokens)
        left = ('IMPLIES', left, right)
    
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
    return ""


def verbalize_from_string(formula_str: str, prop_map: Dict[str, str]) -> str:
    """Parse infix formula and verbalize it."""
    return verbalize(parse_infix_formula(formula_str), prop_map)


# ==========================================
# 2. RETRIEVAL & HELPERS
# ==========================================

def extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = True) -> List[Dict]:
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


def retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: int = 20) -> List[Dict]:
    """Preserved (simplified): Retrieve relevant chunks using SBERT."""
    chunk_embeddings = encode_chunks(chunks, sbert_model)
    query_embedding = encode_query(query, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)
    top_k_indices = np.argsort(similarities)[::-1][:k]
    
    retrieved = []
    for idx in top_k_indices:
        if similarities[idx] < 0.1:
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
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 1000
) -> str:
    """
    Convert a Yes/No question to a declarative statement using an LLM.

    Args:
        query: Yes/No question to convert
        api_key: OpenRouter API key
        model: LLM model (default: gpt-5.2)
        temperature: Sampling temperature (default: 0.1)
        reasoning_effort: For reasoning models (default: medium)
        max_tokens: Max response tokens (default: 1000)

    Returns:
        Converted statement string
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

    # Detect OpenRouter keys and use appropriate base URL
    if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
        client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
        # Prefix model with openai/ for OpenRouter
        if not model.startswith('openai/'):
            model = f'openai/{model}'
    else:
        client = OpenAI(api_key=api_key)

    # Determine if this is a reasoning model
    base_model = model.replace("openai/", "")
    is_reasoning_model = base_model.startswith("gpt-5") or base_model.startswith("o1") or base_model.startswith("o3")

    # Build API call parameters based on model type
    if is_reasoning_model:
        if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
            # OpenRouter format
            api_params = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "extra_body": {
                    "reasoning": {
                        "effort": reasoning_effort,
                        "enabled": True
                    }
                }
            }
        else:
            # Direct OpenAI API format
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
        # Standard models (gpt-4o, gpt-4-turbo, etc.)
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a precise question-to-statement converter."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    # Call the API
    response = client.chat.completions.create(**api_params)

    response_text = response.choices[0].message.content
    if response_text is None:
        raise ValueError("LLM returned empty response")

    response_text = response_text.strip()

    # Parse JSON response
    try:
        result = json.loads(response_text)
        return result['statement']
    except (json.JSONDecodeError, KeyError) as e:
        # Try to extract JSON from response
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
# 3. NEURO-SYMBOLIC CORE
# ==========================================

def load_nli_model_singleton():
    global _cached_nli_model
    if _cached_nli_model is None:
        print("  Loading NLI Model (cross-encoder/nli-deberta-v3-large)...")
        _cached_nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-large')
    return _cached_nli_model


def generate_candidates_llm(
    prompt: str, api_key: str, model: str, temperature: float = 0.7
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
        
        # Handle both single object and candidates list formats
        if 'candidates' in result:
            return result['candidates']
        elif 'formula' in result:
            # Single result - wrap in list
            return [result]
        else:
            print(f"  Warning: LLM response missing 'formula' or 'candidates' key")
            return []
            
    except Exception as e:
        print(f"  Warning: LLM generation failed or returned invalid JSON: {e}")
        print(f"  [LLM ERROR] Generation failed: {type(e).__name__}: {e}")
        return []


def build_prompt(query: str, props_text: str, constraints_section: str, 
                 available_ids: str, query_is_negative: bool) -> str:
    """
    Build the LLM prompt for translating query to propositional formula.
    
    Uses INFIX UNICODE syntax (∧, ∨, ⟹, ⟺, ¬) matching translate_old.py style.
    """
    
    polarity_str = "NEGATIVE (prohibition/restriction)" if query_is_negative else "AFFIRMATIVE"
    
    prompt = f"""You are a logic translator for Natural Language Inference (NLI). 
    Given a hypothesis and a set of atomic propositions from a legal document, 
    translate the hypothesis into a propositional formula.

    === AVAILABLE PROPOSITIONS ===
    {props_text}
    {constraints_section}
    === HYPOTHESIS TO CHECK ===
    "{query}"

    === TASK ===
    Translate the above hypothesis into a propositional formula using ONLY these proposition IDs: {available_ids}

    The formula will be evaluated to determine:
    - TRUE: The hypothesis is entailed (follows from the document)
    - FALSE: The hypothesis is contradicted (negation follows from the document)
    - UNCERTAIN: Neither entailment nor contradiction can be determined

    === EXAMPLES ===

    Example 1 - Simple match:
    Hypothesis: "The receiving party shall keep information confidential"
    If P_6 states "The Receiving Party shall not disclose Confidential Information..."
    Output: {{"formula": "P_6", "query_mode": "entailment", "translation": "The receiving party shall not disclose confidential information", "reasoning": "'Shall' indicates obligation - check if this is entailed"}}

    Example 2 - Negation:
    Hypothesis: "The receiving party shall not reverse engineer any information"
    If P_9 states "The Receiving Party shall not alter, modify, disassemble, reverse engineer..."
    Output: {{"formula": "P_9", "query_mode": "entailment", "translation": "The receiving party shall not reverse engineer information", "reasoning": "'Shall not' is a prohibition - check if this is entailed"}}

    Example 3 - Conjunction:
    Hypothesis: "All confidential information must be marked and returned"
    If P_4 = "Information shall be marked" and P_11 = "Information must be returned"
    Output: {{"formula": "P_4 ∧ P_11", "query_mode": "entailment", "translation": "Information is marked AND returned", "reasoning": "'Must' indicates obligation - check if both conditions are entailed"}}

    Example 4 - Disjunction:
    Hypothesis: "Some information may be destroyed or returned"
    If P_11 = "must return information" and P_12 = "may destroy information"
    Output: {{"formula": "P_11 ∨ P_12", "query_mode": "consistency", "translation": "Information is returned OR destroyed", "reasoning": "'Some...may' suggests either option satisfies the hypothesis"}}

    Example 5 - Permission (consistency mode):
    Hypothesis: "Receiving Party may share Confidential Information with employees"
    If P_21 states "The Recipient discloses Confidential Information to need-to-know persons"
    Output: {{"formula": "P_21", "query_mode": "consistency", "translation": "Sharing with employees is permitted", "reasoning": "'May' indicates permission - check if this action is allowed (consistent with KB), not required"}}

    Example 6 - Conditional obligation:
    Hypothesis: "Receiving Party shall notify Disclosing Party in case disclosure is required by law"
    If P_29 = "Disclosure is required by law" and P_30 = "Recipient gives notice"
    Output: {{"formula": "P_29 ⟹ P_30", "query_mode": "entailment", "translation": "If legally required to disclose, then must notify", "reasoning": "'In case' creates a conditional - check if implication holds"}}

    === QUERY MODE ===
    First, determine the QUERY MODE based on the hypothesis wording:

    1. **entailment** (default): The hypothesis claims something MUST be true.
    - Keywords: "shall", "must", "is required", "will", "is obligated", "shall not"

    2. **consistency**: The hypothesis asks if something is ALLOWED or POSSIBLE.
    - Keywords: "may", "can", "could", "is allowed", "is permitted", "is possible"

    === NEGATION HANDLING ===

    Query polarity: {polarity_str}

    When translating negative queries ("shall not X", "only include Y"):
    - If query is NEGATIVE and proposition is AFFIRMATIVE → use negation: ¬P_i
    - If query is NEGATIVE and proposition is NEGATIVE → use directly: P_i
    - If query is AFFIRMATIVE and proposition is AFFIRMATIVE → use directly: P_i

    Examples:
    - Query: "Party shall not disclose" + P_1="Party discloses" [AFFIRMATIVE] → Formula: ¬P_1
    - Query: "Party shall not disclose" + P_1="Party does not disclose" [NEGATIVE] → Formula: P_1
    - Query: "Info includes only X" + P_2="Info includes X and Y" [AFFIRMATIVE] → Formula: ¬P_2

    === TRANSLATION GUIDELINES ===

    1. "Shall"/"Must" obligations → Use proposition directly: P_i (mode: entailment)
    2. "Shall not"/"Must not" prohibitions → Check proposition polarity:
    - If proposition is AFFIRMATIVE, apply negation: ¬P_i
    - If proposition is NEGATIVE, use directly: P_i
    - Mode: entailment
    3. "May"/"Can" permissions → Use proposition for the permitted action: P_i (mode: consistency)
    4. Conditionals "If A then B" / "in case" / "when" → Use implication: P_a ⟹ P_b (mode: entailment)
    5. "Some"/"Any" (existential) → Use disjunction: P_1 ∨ P_2
    6. "All"/"Every" (universal) → Use conjunction: P_1 ∧ P_2

    IMPORTANT:
    - Choose the SIMPLEST formula that preserves semantic intent
    - ALWAYS match hypothesis polarity with formula polarity
    - Check [Polarity: ...] annotations above

    === OUTPUT FORMAT ===
    Return ONLY a JSON object (no other text):
    {{"formula": "<formula using {available_ids}>", 
    "query_mode": "<entailment or consistency>", 
    "translation": "<plain English meaning>", 
    "reasoning": "<brief explanation>"}}"""
    
    return prompt


def translate_query(
    query: str,
    json_path: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 64000,
    k: int = 20,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True
    ) -> Dict[str, Any]:
    """
    Main Interface Function.
    Replaces the old logic with the Generate -> Verbalize -> Verify loop.
    Arguments match exactly the old interface.
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
            "explanation": "No documents found."
        }

    # 3. Build Prompt Variables (matching translate_old.py style)
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
    """

    # Create available IDs string
    available_ids = ", ".join(prop_ids[:10])
    if len(prop_ids) > 10:
        available_ids += f", ... ({len(prop_ids)} total)"
    
    # Build prop_map for verbalization
    prop_map = {p['id']: p['translation'].strip(".") for p in retrieved}
    
    # Format constraints section
    constraints_text = ""
    hard_constraints = logified_structure.get("hard_constraints", [])
    soft_constraints = logified_structure.get("soft_constraints", [])

    if hard_constraints:
        constraints_text += "HARD CONSTRAINTS (must hold):\n"
        for c in hard_constraints:
            formula = c.get("formula", "")
            if formula:
                constraints_text += f"- {formula}\n"

    if soft_constraints:
        constraints_text += "\nSOFT CONSTRAINTS (likely hold):\n"
        for c in soft_constraints:
            formula = c.get("formula", "")
            weight = c.get("weight", "")
            if formula:
                if weight:
                    constraints_text += f"- {formula} (weight: {weight})\n"
                else:
                    constraints_text += f"- {formula}\n"

    constraints_section = ""
    if constraints_text:
        constraints_section = f"""
    ESTABLISHED CONSTRAINTS:
    {constraints_text}
    """

    # Detect query polarity
    query_is_negative = negation_detection.detect_negation_in_hypothesis(query)
    
    # Build the prompt
    prompt = build_prompt(query, props_text, constraints_section, available_ids, query_is_negative)

    # 4. Generate Candidates (Step A)
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

    # 5. Verbalize & Verify (Step B & C)
    if verbose:
        print("Step B & C: Verbalizing and Verifying with NLI...")
    nli_model = load_nli_model_singleton()
    
    valid_candidates = []
    verbalized_texts = []
    
    for c in candidates:
        try:
            # Deterministic Verbalization (now uses infix parser)
            v_text = verbalize_from_string(c['formula'], prop_map)
            valid_candidates.append(c)
            verbalized_texts.append(v_text)
        except Exception as e:
            if verbose:
                print(f"  Skipped invalid formula {c.get('formula')}: {e}")
                print(f"  [PARSE ERROR] Formula: {c.get('formula')}")
                print(f"    Error type: {type(e).__name__}")
                print(f"    Error message: {e}")
            continue

    if not valid_candidates:
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "All candidates failed syntax parsing."
        }

    # Score Pairs
    pairs = [(query, v_text) for v_text in verbalized_texts]
    logits = nli_model.predict(pairs)
    
    # Softmax
    exp_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    best_net_score = -999.0
    best_idx = 0
    
    debug_trace = []

    for i, (prob, c) in enumerate(zip(probs, valid_candidates)):
        # Entailment is idx 2, Contradiction is idx 0
        entailment = float(prob[2])
        contradiction = float(prob[0])
        net_score = entailment - contradiction
        
        debug_trace.append(f"{c['formula']} (Score: {net_score:.2f})")
        
        if verbose:
            print(f"  Cand {i}: {c['formula']}")
            print(f"    -> Verbal: {verbalized_texts[i][:60]}...")
            print(f"    -> Score: {net_score:.2f} (Ent: {entailment:.2f}, Con: {contradiction:.2f})")
            
        if net_score > best_net_score:
            best_net_score = net_score
            best_idx = i

    winner = valid_candidates[best_idx]
    winning_text = verbalized_texts[best_idx]

    # 6. Final Result Construction (Matching old interface)
    return {
        "formula": winner['formula'],
        "translation": winning_text,
        "query": query,  # The statement version
        "original_query": original_query,
        "explanation": f"Selected via NLI (Confidence: {best_net_score:.2f}). LLM Reasoning: {winner.get('reasoning', '')}",
        "confidence": best_net_score,
        "debug_trace": debug_trace
    }


# ==========================================
# 4. MAIN ENTRY POINT
# ==========================================

def main():
    """Command-line interface for query translation."""
    parser = argparse.ArgumentParser(
        description="Neuro-Symbolic Logic Translator (Drop-in Replacement)",
        epilog="Example: python translate.py \"Can info be shared?\" logified.json --api-key sk-xxx"
    )
    # Exact same arguments as your original file
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("json_path", help="Path to logified JSON")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--model", default="gpt-4o", help="LLM model (default: gpt-4o)")
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temp")
    parser.add_argument("--reasoning-effort", default="medium", help="Reasoning effort (for reasoning models)")
    parser.add_argument("--max-tokens", type=int, default=64000, help="Max tokens")
    parser.add_argument("--k", type=int, default=20, help="Retrieval K")
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