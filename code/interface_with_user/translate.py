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

from config.retrieval_config import TEMPERATURE_LOGIC_CONVERTER, MAX_TOKENS, REASONING_EFFORT, SBERT_TOP_K, SBERT_MIN_SIMILARITY, ENABLE_HYBRID_EMBEDDING
from config.retrieval_config import REASONING_MODEL, TRANSLATE_MODEL, TEMPERATURE_TRANSLATE, REASONING_EFFORT_TRANSLATE, PROMPT_TRANSLATION

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
# 3. NEURO-SYMBOLIC CORE
# ==========================================

def load_nli_model_singleton():
    global _cached_nli_model
    if _cached_nli_model is None:
        print("  Loading NLI Model (cross-encoder/nli-deberta-v3-large)...")
        _cached_nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-large')
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

    # 5. Verbalize & Verify (Step B & C)
    if verbose:
        print("Step B & C: Verbalizing and Verifying with NLI...")
    nli_model = load_nli_model_singleton()
    
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
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "All candidates failed syntax parsing."
        }

    pairs = [(query, v_text) for v_text in verbalized_texts]
    logits = nli_model.predict(pairs)
    
    exp_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    best_net_score = -999.0
    best_idx = 0
    debug_trace = []

    for i, (prob, c) in enumerate(zip(probs, valid_candidates)):
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

    return {
        "formula": winner['formula'],
        "translation": winning_text,
        "query": query,
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
