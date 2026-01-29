#!/usr/bin/env python3
"""
translate.py - Translate Natural Language Query to Propositional Formula

Given a user query Q and a logified JSON file (containing primitive propositions),
this module retrieves the most relevant propositions using SBERT and asks an LLM
to translate Q into a propositional formula over those propositions.

Input:
    - Q: User query in natural language
    - json_path: Path to weighted logified JSON file
    - api_key: OpenRouter API key
    - Model parameters (model, temperature, reasoning_effort, max_tokens)
    - k: Number of top propositions to retrieve (default: 20)
    - max_tokens: Maximum tokens in response (default: 64000)

Output:
    {
        "formula": "<propositional formula using P_1, P_2, etc.>",
        "translation": "<natural language translation of the formula>",
        "query": "<original user query>",
        "explanation": "<1-2 sentence reasoning>"
    }

Usage (CLI):
    python translate.py "Can the receiving party share info with third parties?" \\
        path/to/logified.json --api-key sk-or-v1-xxx

Usage (Python):
    from interface_with_user.translate import translate_query

    result = translate_query(
        query="Can the receiving party share info with third parties?",
        json_path="path/to/logified.json",
        api_key="sk-or-v1-xxx"
    )
"""

import sys
import os
import re
import time as time_module
from pathlib import Path

# Add code directory to Python path (for imports to work from anywhere)
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import json
import argparse
import numpy as np
from typing import Dict, List, Any, Optional

# Reuse existing RAG infrastructure
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    compute_cosine_similarity
)

# OpenAI client for LLM calls
from openai import OpenAI


def extract_proposition_chunks(logified_structure: Dict[str, Any]) -> List[Dict]:
    """
    Extract primitive propositions from logified JSON as chunks.

    Each proposition becomes one chunk with fields: id, translation, evidence, explanation.

    Args:
        logified_structure: Loaded JSON with 'primitive_props' field

    Returns:
        List of chunk dicts, each with 'text' field (for SBERT encoding)
        and original proposition data
    """
    primitive_props = logified_structure.get('primitive_props', [])

    if not primitive_props:
        raise ValueError("JSON file has no 'primitive_props' field or it is empty")

    chunks = []
    for prop in primitive_props:
        # Validate required fields
        if 'id' not in prop or 'translation' not in prop:
            raise ValueError(f"Proposition missing required fields (id, translation): {prop}")

        # Create chunk with 'text' field for SBERT (use translation as the text to embed)
        chunk = {
            'text': prop['translation'],  # This is what SBERT encodes
            'id': prop['id'],
            'translation': prop['translation'],
            'evidence': prop.get('evidence', ''),
            'explanation': prop.get('explanation', '')
        }
        chunks.append(chunk)

    return chunks


def retrieve_top_k_propositions(
    query: str,
    chunks: List[Dict],
    sbert_model,
    k: int = 20,
    use_reranking: bool = True
) -> List[Dict]:
    """
    Retrieve top-K most relevant propositions for the query using SBERT.

    Optionally uses cross-encoder reranking for more accurate retrieval.

    Args:
        query: User query string
        chunks: List of proposition chunks (each with 'text' field)
        sbert_model: Loaded SBERT model
        k: Number of propositions to retrieve
        use_reranking: Whether to use cross-encoder reranking (default: True)

    Returns:
        List of top-K chunks sorted by relevance (most relevant first)
    """
    # Encode all chunks
    chunk_embeddings = encode_chunks(chunks, sbert_model)

    # Encode query
    query_embedding = encode_query(query, sbert_model)

    # Compute similarities
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    # Get top-2K candidates for potential reranking
    candidate_k = min(k * 2, len(chunks))
    top_candidate_indices = np.argsort(similarities)[::-1][:candidate_k]

    # Try cross-encoder reranking if enabled
    if use_reranking and len(top_candidate_indices) > k:
        try:
            from sentence_transformers import CrossEncoder
            reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

            # Create pairs for reranking
            candidates = [chunks[idx] for idx in top_candidate_indices]
            pairs = [(query, c['text']) for c in candidates]

            # Get reranking scores
            rerank_scores = reranker.predict(pairs)

            # Sort by rerank score and take top-K
            sorted_indices = np.argsort(rerank_scores)[::-1][:k]

            retrieved = []
            for rank, idx in enumerate(sorted_indices):
                chunk = candidates[idx].copy()
                chunk['similarity'] = float(rerank_scores[idx])
                chunk['original_similarity'] = float(similarities[top_candidate_indices[idx]])
                chunk['reranked'] = True
                retrieved.append(chunk)

            return retrieved

        except ImportError:
            # Fall back to bi-encoder only if cross-encoder not available
            pass
        except Exception as e:
            # Fall back on any reranking error
            import sys
            print(f"  Warning: Reranking failed ({e}), using bi-encoder only", file=sys.stderr)

    # Standard bi-encoder retrieval (no reranking)
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Return top-K chunks with their similarity scores
    retrieved = []
    for idx in top_k_indices:
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
        chunk['reranked'] = False
        retrieved.append(chunk)

    return retrieved


def is_yes_no_question(query: str) -> bool:
    """
    Detect if a query is a Yes/No question.

    Args:
        query: User query string

    Returns:
        True if it's likely a Yes/No question, False otherwise
    """
    query_lower = query.lower().strip()

    # Check for common Yes/No question patterns
    yes_no_starters = [
        'is ', 'are ', 'was ', 'were ', 'will ', 'would ', 'should ', 'could ',
        'can ', 'may ', 'might ', 'must ', 'has ', 'have ', 'had ', 'does ',
        'do ', 'did '
    ]

    for starter in yes_no_starters:
        if query_lower.startswith(starter):
            return True

    return False


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


def build_prompt(query: str, retrieved_chunks: List[Dict], logified_structure: Dict = None) -> str:
    """
    Build the LLM prompt for translating query to propositional formula.

    Args:
        query: User query string
        retrieved_chunks: List of relevant proposition chunks
        logified_structure: Optional logified structure containing constraints

    Returns:
        Formatted prompt string
    """
    # Format the propositions for the prompt
    props_text = ""
    prop_ids = []
    for chunk in retrieved_chunks:
        prop_id = chunk['id']
        prop_ids.append(prop_id)
        props_text += f"""
{prop_id}: {chunk['translation']}
  Evidence: {chunk['evidence']}
"""

    # Format constraints if available
    constraints_text = ""
    if logified_structure:
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

    # Build constraints section if available
    constraints_section = ""
    if constraints_text:
        constraints_section = f"""
ESTABLISHED CONSTRAINTS:
{constraints_text}
"""

    # Create available IDs string for the prompt
    available_ids = ", ".join(prop_ids[:10])
    if len(prop_ids) > 10:
        available_ids += f", ... ({len(prop_ids)} total)"

    prompt = f"""You are a logic translator for Natural Language Inference (NLI). Given a hypothesis and a set of atomic propositions from a legal document, translate the hypothesis into a propositional formula.

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
Output: {{"formula": "P_6", "translation": "The receiving party shall not disclose confidential information", "reasoning": "P_6 directly captures the confidentiality obligation"}}

Example 2 - Negation:
Hypothesis: "The receiving party shall not reverse engineer any information"
If P_9 states "The Receiving Party shall not alter, modify, disassemble, reverse engineer..."
Output: {{"formula": "P_9", "translation": "The receiving party shall not reverse engineer information", "reasoning": "P_9 prohibits reverse engineering, matching the hypothesis"}}

Example 3 - Conjunction:
Hypothesis: "All confidential information must be marked and returned"
If P_4 = "Information shall be marked" and P_11 = "Information must be returned"
Output: {{"formula": "P_4 ∧ P_11", "translation": "Information is marked AND returned", "reasoning": "Both conditions must hold for 'all...must be marked and returned'"}}

Example 4 - Disjunction:
Hypothesis: "Some information may be destroyed or returned"
If P_11 = "must return information" and P_12 = "may destroy information"
Output: {{"formula": "P_11 ∨ P_12", "translation": "Information is returned OR destroyed", "reasoning": "'Some...may' suggests either option satisfies the hypothesis"}}

=== TRANSLATION GUIDELINES ===

1. "Shall"/"Must" obligations → Use proposition directly: P_i
2. "Shall not" prohibitions → The proposition already captures the negation, use: P_i (if P_i states "shall not X")
3. "May"/"Can" permissions → Use proposition for the permission: P_i
4. Conditionals "If A then B" → Use implication: P_a ⟹ P_b
5. "Some"/"Any" (existential) → Use disjunction: P_1 ∨ P_2
6. "All"/"Every" (universal) → Use conjunction: P_1 ∧ P_2

IMPORTANT: Choose the SIMPLEST formula. If one proposition captures the hypothesis, use just that proposition.

=== OUTPUT FORMAT ===
Return ONLY a JSON object (no other text):
{{"formula": "<formula using {available_ids}>", "translation": "<plain English meaning>", "reasoning": "<brief explanation>"}}
"""

    return prompt


def extract_formula_from_text(response_text: str, available_prop_ids: List[str] = None) -> Optional[str]:
    """
    Attempt to extract a formula from non-JSON LLM response.

    This is a fallback when the LLM doesn't return proper JSON but may have
    included a formula somewhere in its response.

    Args:
        response_text: Raw LLM response
        available_prop_ids: List of valid proposition IDs (e.g., ['P_1', 'P_2', ...])

    Returns:
        Extracted formula string or None if extraction fails
    """
    # Pattern to match formulas like P_1, P_1 ∧ P_2, ¬P_3, P_1 ⟹ P_2, etc.
    # Includes Unicode logical operators and ASCII alternatives
    formula_pattern = r'[¬~!]?\s*P_\d+(?:\s*[∧∨⟹⟺&|→↔\-\>]+\s*[¬~!]?\s*P_\d+)*'

    # First, try to find formula in "formula": "..." pattern
    formula_field_match = re.search(r'"formula"\s*:\s*"([^"]+)"', response_text)
    if formula_field_match:
        candidate = formula_field_match.group(1).strip()
        if re.match(r'^[¬~!]?\s*P_\d+', candidate):
            return candidate

    # Try to find standalone formulas
    matches = re.findall(formula_pattern, response_text)
    if matches:
        # Return the longest match (most likely to be complete)
        return max(matches, key=len).strip()

    return None


def call_llm(
    prompt: str,
    api_key: str,
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 64000,
    max_retries: int = 2,
    retry_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Call LLM to translate query to propositional formula.

    Uses same API pattern as logic_converter.py for consistency.
    Includes retry logic for transient failures.

    Args:
        prompt: The formatted prompt
        api_key: OpenRouter API key
        model: Model name (default: gpt-5.2)
        temperature: Sampling temperature (default: 0.1)
        reasoning_effort: For reasoning models (default: medium)
        max_tokens: Max response tokens (default: 64000)
        max_retries: Number of retries on failure (default: 2)
        retry_delay: Seconds to wait between retries (default: 1.0)

    Returns:
        Parsed JSON response dict with at minimum a 'formula' field

    Raises:
        ValueError: If LLM response cannot be parsed after all retries
    """
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
                    {"role": "developer", "content": "You are a precise logic translator. Always respond with valid JSON only."},
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
                {"role": "system", "content": "You are a precise logic translator. Always respond with valid JSON only, no additional text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    last_error = None
    last_response_text = ""

    for attempt in range(max_retries + 1):
        try:
            # Call the API
            response = client.chat.completions.create(**api_params)

            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError("LLM returned empty response")

            response_text = response_text.strip()
            last_response_text = response_text

            # Parse JSON response
            try:
                result = json.loads(response_text)
                # Validate that we have a formula field
                if 'formula' in result and result['formula']:
                    return result
                else:
                    raise ValueError("Response missing 'formula' field")
            except json.JSONDecodeError as e:
                # Try to extract JSON from response (LLM may have added extra text)
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                    try:
                        result = json.loads(json_text)
                        if 'formula' in result and result['formula']:
                            return result
                    except json.JSONDecodeError:
                        pass

                # Last resort: try to extract formula from raw text
                extracted_formula = extract_formula_from_text(response_text)
                if extracted_formula:
                    return {
                        "formula": extracted_formula,
                        "translation": "(extracted from non-JSON response)",
                        "reasoning": "(formula extracted via regex fallback)"
                    }

                last_error = ValueError(f"Failed to parse LLM response as JSON: {e}")

        except Exception as e:
            last_error = e

        # Retry with delay if not the last attempt
        if attempt < max_retries:
            time_module.sleep(retry_delay)
            # Increase temperature slightly on retry to get different response
            if not is_reasoning_model and "temperature" in api_params:
                api_params["temperature"] = min(0.5, api_params["temperature"] + 0.1)

    # All retries exhausted
    raise ValueError(f"Failed to get valid formula after {max_retries + 1} attempts. Last error: {last_error}\nLast response: {last_response_text[:500]}")


def translate_query(
    query: str,
    json_path: str,
    api_key: str,
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 64000,
    k: int = 20,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Main function: Translate a natural language query to a propositional formula.

    Handles Yes/No questions by first converting them to statements, then proceeds
    with normal translation.

    Args:
        query: User query in natural language
        json_path: Path to logified JSON file with primitive_props
        api_key: OpenRouter API key
        model: LLM model (default: gpt-5.2)
        temperature: Sampling temperature (default: 0.1)
        reasoning_effort: For reasoning models (default: medium)
        max_tokens: Max response tokens (default: 64000)
        k: Number of propositions to retrieve (default: 20)
        sbert_model_name: SBERT model for retrieval (default: all-MiniLM-L6-v2)
        verbose: Print progress messages (default: True)

    Returns:
        Dict with formula, translation, query, explanation, original_query (if converted)
    """
    original_query = query

    # Step 1: Check if this is a Yes/No question and convert to statement
    if is_yes_no_question(query):
        if verbose:
            print(f"Detected Yes/No question: '{query}'")
            print("Converting to declarative statement...")

        try:
            query = convert_yes_no_to_statement(
                query=query,
                api_key=api_key,
                model=model,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
                max_tokens=1000
            )

            if verbose:
                print(f"  → Converted to: '{query}'")
        except Exception as e:
            if verbose:
                print(f"  Warning: Could not convert question to statement: {e}")
                print("  Proceeding with original query...")
            query = original_query

    # Load JSON file
    if verbose:
        print(f"\nLoading logified JSON from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        logified_structure = json.load(f)

    # Extract propositions as chunks
    if verbose:
        print("Extracting primitive propositions...")

    chunks = extract_proposition_chunks(logified_structure)

    if verbose:
        print(f"  Found {len(chunks)} propositions")

    # Adjust k if we have fewer propositions
    actual_k = min(k, len(chunks))
    if actual_k < k and verbose:
        print(f"  Note: Using k={actual_k} (fewer propositions than requested k={k})")

    # Load SBERT model
    if verbose:
        print("Loading SBERT model for retrieval...")

    sbert_model = load_sbert_model(sbert_model_name)

    # Retrieve top-K propositions
    if verbose:
        print(f"Retrieving top-{actual_k} relevant propositions...")

    retrieved = retrieve_top_k_propositions(query, chunks, sbert_model, k=actual_k)

    if verbose:
        print(f"  Top 5 retrieved propositions:")
        for i, chunk in enumerate(retrieved[:5]):
            print(f"    {i+1}. {chunk['id']} (sim={chunk['similarity']:.3f}): {chunk['translation'][:60]}...")

    # Validate we have propositions to work with
    if not retrieved:
        raise ValueError("No propositions retrieved - cannot translate query without available propositions")

    # Get valid proposition IDs for validation
    valid_prop_ids = {chunk['id'] for chunk in chunks}

    # Build prompt
    prompt = build_prompt(query, retrieved, logified_structure)

    # Call LLM
    if verbose:
        print(f"\nCalling LLM ({model}) to translate query...")

    result = call_llm(
        prompt=prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens
    )

    # Validate the formula contains valid proposition IDs
    formula = result.get('formula', '')
    if formula:
        # Extract P_N patterns from formula
        formula_props = re.findall(r'P_\d+', formula)
        invalid_props = [p for p in formula_props if p not in valid_prop_ids]
        if invalid_props and verbose:
            print(f"  Warning: Formula contains proposition IDs not in document: {invalid_props}")
            # Don't fail, just warn - the LLM might have hallucinated but formula may still be useful

    # Add original query if it was converted
    if original_query != query:
        result['original_query'] = original_query
        result['query'] = query  # Update to show the converted statement

    if verbose:
        print("\nResult:")
        if 'original_query' in result:
            print(f"  Original Query: {result['original_query']}")
            print(f"  Converted Query: {result['query']}")
        print(f"  Formula: {result.get('formula', 'N/A')}")
        print(f"  Translation: {result.get('translation', 'N/A')}")
        print(f"  Explanation: {result.get('explanation', result.get('reasoning', 'N/A'))}")

    return result


def main():
    """Command-line interface for query translation."""
    parser = argparse.ArgumentParser(
        description="Translate natural language query to propositional formula",
        epilog="Example: python translate.py \"Can info be shared?\" logified.json --api-key sk-or-v1-xxx"
    )
    parser.add_argument(
        "query",
        help="Natural language query to translate"
    )
    parser.add_argument(
        "json_path",
        help="Path to logified JSON file with primitive_props"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="OpenRouter API key"
    )
    parser.add_argument(
        "--model",
        default="gpt-5.2",
        help="LLM model (default: gpt-5.2)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (default: 0.1)"
    )
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["none", "low", "medium", "high", "xhigh"],
        help="Reasoning effort for gpt-5.2/o1/o3 models (default: medium)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64000,
        help="Maximum tokens in response (default: 64000)"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=20,
        help="Number of propositions to retrieve (default: 20)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (optional, prints to stdout if not specified)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    # Validate JSON path
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
            verbose=not args.quiet
        )

        # Output result
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
