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
    k: int = 20
) -> List[Dict]:
    """
    Retrieve top-K most relevant propositions for the query using SBERT.

    Args:
        query: User query string
        chunks: List of proposition chunks (each with 'text' field)
        sbert_model: Loaded SBERT model
        k: Number of propositions to retrieve

    Returns:
        List of top-K chunks sorted by relevance (most relevant first)
    """
    # Encode all chunks
    chunk_embeddings = encode_chunks(chunks, sbert_model)

    # Encode query
    query_embedding = encode_query(query, sbert_model)

    # Compute similarities
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    # Get top-K indices
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Return top-K chunks with their similarity scores
    retrieved = []
    for idx in top_k_indices:
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
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


def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    """
    Build the LLM prompt for translating query to propositional formula.

    Args:
        query: User query string
        retrieved_chunks: List of relevant proposition chunks

    Returns:
        Formatted prompt string
    """
    # Format the propositions for the prompt
    props_text = ""
    for chunk in retrieved_chunks:
        props_text += f"""
{chunk['id']}: {chunk['translation']}
  Evidence: {chunk['evidence']}
"""

    prompt = f"""You are a logic translator. Given a natural language query and a set of atomic propositions, translate the query into a propositional formula.

AVAILABLE PROPOSITIONS:
{props_text}

USER QUERY:
"{query}"

TASK:
Translate the user query into a propositional formula using ONLY the proposition IDs listed above (P_1, P_2, etc.).

Use these logical connectives:
- ∧ (AND)
- ∨ (OR)
- ¬ (NOT)
- ⟹ (IMPLIES)
- ⟺ (IFF / biconditional)

If the query cannot be expressed using the available propositions, use the closest approximation and explain.

OUTPUT FORMAT (JSON only, no other text):
{{
    "formula": "<propositional formula using P_1, P_2, etc.>",
    "translation": "<natural language translation of your formula>",
    "query": "{query}",
    "explanation": "<1-2 sentence reasoning for the formula chosen>"
}}"""

    return prompt


def call_llm(
    prompt: str,
    api_key: str,
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 64000
) -> Dict[str, Any]:
    """
    Call LLM to translate query to propositional formula.

    Uses same API pattern as logic_converter.py for consistency.

    Args:
        prompt: The formatted prompt
        api_key: OpenRouter API key
        model: Model name (default: gpt-5.2)
        temperature: Sampling temperature (default: 0.1)
        reasoning_effort: For reasoning models (default: medium)
        max_tokens: Max response tokens (default: 64000)

    Returns:
        Parsed JSON response dict
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
                    {"role": "developer", "content": "You are a precise logic translator."},
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
                {"role": "system", "content": "You are a precise logic translator."},
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
        return result
    except json.JSONDecodeError as e:
        # Try to extract JSON from response
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
            try:
                result = json.loads(json_text)
                return result
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")


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

    # Build prompt
    prompt = build_prompt(query, retrieved)

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
        print(f"  Explanation: {result.get('explanation', 'N/A')}")

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
