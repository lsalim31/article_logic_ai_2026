#!/usr/bin/env python3
"""
translate.py - Neuro-Symbolic Logic Translator

A drop-in replacement for the previous translation logic.
Input: User Query + JSON Logified Data
Output: Propositional Formula (verified via NLI)

Architecture:
1. Retrieval: SBERT/Hybrid search (Preserved from original)
2. Generation: LLM generates 3-5 diverse candidate formulas
3. Verbalization: Python recursively converts Logic -> "Structured English"
4. Verification: NLI model scores candidates to find the best semantic match
"""

import sys
import os
import re
import json
import argparse
import textwrap
import numpy as np
import time as time_module
from pathlib import Path
from typing import Dict, List, Any, Union, Tuple, Optional

# Add code directory to Python path
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

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
# 1. NEW: DETERMINISTIC VERBALIZER & PARSER
# ==========================================

Formula = Union[str, Tuple[str, ...]]

def parse_formula(formula_str: str) -> Formula:
    """Parses logical strings into nested tuples strictly."""
    formula_str = formula_str.strip()
    
    # Match P_123 pattern
    if re.match(r'^P_\d+$', formula_str):
        return formula_str
    
    # Match Operator(...)
    match = re.match(r'^(NOT|AND|OR|IMPLIES|IFF)\((.+)\)$', formula_str)
    if not match:
        # Fallback for simple tokens or errors
        if re.match(r'^\w+$', formula_str): return formula_str 
        # Attempt to clean up common LLM artifacts like "Formula: ..."
        clean = re.sub(r'^Formula:\s*', '', formula_str)
        if clean != formula_str: return parse_formula(clean)
        raise ValueError(f"Syntax Error: {formula_str}")
    
    operator = match.group(1)
    inner = match.group(2)
    args = split_arguments(inner)
    
    # Arity Validation
    if operator == "NOT":
        if len(args) != 1: raise ValueError(f"NOT needs 1 arg, got {len(args)}")
        return (operator, parse_formula(args[0]))
    else:
        if len(args) != 2: raise ValueError(f"{operator} needs 2 args, got {len(args)}")
        return (operator, parse_formula(args[0]), parse_formula(args[1]))

def split_arguments(s: str) -> list:
    """Splits comma-separated args respecting nested parenthesis."""
    args = []
    depth = 0
    current = ""
    for char in s:
        if char == '(': depth += 1
        elif char == ')': depth -= 1
        elif char == ',' and depth == 0:
            args.append(current.strip())
            current = ""
            continue
        current += char
    if current.strip(): args.append(current.strip())
    return args

def verbalize(formula: Formula, prop_map: Dict[str, str]) -> str:
    """Recursively converts logic to NLI-ready English."""
    if isinstance(formula, str):
        if formula not in prop_map:
            raise ValueError(f"Unknown proposition ID: {formula}")
        return prop_map[formula]
    
    op = formula[0]
    if op == "NOT": return f"it is not the case that {verbalize(formula[1], prop_map)}"
    elif op == "AND": return f"{verbalize(formula[1], prop_map)}, and {verbalize(formula[2], prop_map)}"
    elif op == "OR": return f"{verbalize(formula[1], prop_map)}, or {verbalize(formula[2], prop_map)}"
    elif op == "IMPLIES": return f"if {verbalize(formula[1], prop_map)}, then {verbalize(formula[2], prop_map)}"
    elif op == "IFF": return f"{verbalize(formula[1], prop_map)} if and only if {verbalize(formula[2], prop_map)}"
    return ""

def verbalize_from_string(formula_str: str, prop_map: Dict[str, str]) -> str:
    return verbalize(parse_formula(formula_str), prop_map)

# ==========================================
# 2. EXISTING: RETRIEVAL & HELPERS
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
        if similarities[idx] < 0.1: break 
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

def convert_yes_no_to_statement(query: str, api_key: str, model: str = "gpt-4o", **kwargs) -> str:
    """Preserved: Convert Yes/No to statement."""
    client, model = get_configured_client(api_key, model)
    prompt = f"Convert this Yes/No question to a declarative statement: '{query}'. Return JSON: {{'statement': ...}}"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)['statement']
    except:
        return query

# ==========================================
# 3. NEW: NEURO-SYMBOLIC CORE
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
    """Call LLM to get JSON list of candidates."""
    client, model = get_configured_client(api_key, model)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content).get('candidates', [])
    except Exception as e:
        print(f"  Warning: LLM generation failed or returned invalid JSON: {e}")
        return []

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
    Arguments matches exactly the old interface.
    """
    
    # 1. Pre-process (Yes/No Handling)
    original_query = query
    if is_yes_no_question(query):
        if verbose: print(f"Detected Yes/No question. Converting...")
        try:
            query = convert_yes_no_to_statement(query, api_key, model)
            if verbose: print(f"  → Statement: {query}")
        except:
            if verbose: print("  → Conversion failed, proceeding with original.")

    # 2. Retrieval
    if verbose: print(f"Loading propositions from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        logified_structure = json.load(f)

    chunks = extract_proposition_chunks(logified_structure)
    sbert_model = load_sbert_model(sbert_model_name)
    retrieved = retrieve_top_k_propositions(query, chunks, sbert_model, k=k)

    if not retrieved:
        return {"formula": "NONE", "translation": "No relevant props", "query": query, "explanation": "No documents found."}

    # 3. Build Prompt for Candidate Generation
    prop_map = {p['id']: p['translation'].strip(".") for p in retrieved}
    props_formatted = "\n".join([f"- {p['id']}: {p['translation']}" for p in retrieved])
    
    prompt = textwrap.dedent(f"""
        You are a logic translation assistant.
        
        TASK: Translate the Hypothesis into 3-5 diverse Boolean formulas using ONLY the provided Propositions.
        
        PROPOSITIONS:
        {props_formatted}
        
        HYPOTHESIS: "{query}"
        
        RULES:
        1. Use operators: NOT, AND, OR, IMPLIES, IFF
        2. Format: Functional syntax e.g., IMPLIES(P_1, NOT(P_2))
        3. Generate diverse interpretations:
           - "Literal": Word-for-word mapping.
           - "Contextual": Resolving 'unless', 'only if', etc.
           - "Relaxed": The closest approximation.
        
        OUTPUT JSON:
        {{
          "candidates": [
            {{ "formula": "IMPLIES(P_1, NOT(P_2))", "reasoning": "Contextual interpretation..." }}
          ]
        }}
    """)

    # 4. Generate Candidates (Step A)
    if verbose: print("\nStep A: Generating logical candidates...")
    # NOTE: We use the 'model' passed in CLI, but the helper will prefix it for OpenRouter if needed
    candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature)
    
    if not candidates:
        return {"formula": "ERROR", "translation": "", "query": query, "explanation": "LLM failed to generate valid candidates."}

    # 5. Verbalize & Verify (Step B & C)
    if verbose: print("Step B & C: Verbalizing and Verifying with NLI...")
    nli_model = load_nli_model_singleton()
    
    valid_candidates = []
    verbalized_texts = []
    
    for c in candidates:
        try:
            # Deterministic Verbalization
            v_text = verbalize_from_string(c['formula'], prop_map)
            valid_candidates.append(c)
            verbalized_texts.append(v_text)
        except Exception as e:
            if verbose: print(f"  Skipped invalid formula {c.get('formula')}: {e}")
            continue

    if not valid_candidates:
        return {"formula": "ERROR", "translation": "", "query": query, "explanation": "All candidates failed syntax parsing."}

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
        "query": query, # The statement version
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
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temp (ignored in new pipeline)")
    parser.add_argument("--reasoning-effort", default="medium", help="Reasoning effort (ignored)")
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