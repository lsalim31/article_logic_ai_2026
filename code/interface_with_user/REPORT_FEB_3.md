# Report Feb 3 — interface_with_user

Scope: `code/interface_with_user/*.py`. Docstrings ignored per request. Focus on concrete errors and input/output mismatches.

## Issues

1) **Unused inputs `reasoning_effort` and `max_tokens` (mismatch between inputs and behavior)**
Severity: Medium
File: `code/interface_with_user/translate.py`
Function: `translate_query`
Lines: 559-672 (params defined), 583-584 (call), 672 (call)
Problem: `translate_query` accepts `reasoning_effort` and `max_tokens` but never passes them to `convert_yes_no_to_statement` or `generate_candidates_llm`. User inputs are ignored.
Proposed solution: pass through these parameters and update `generate_candidates_llm` to accept them.
Minimal replacement (function signatures + calls):
```python
def generate_candidates_llm(
    prompt: str,
    api_key: str,
    model: str,
    temperature: float = 0.7,
    reasoning_effort: str = "medium",
    max_tokens: int = 1000,
) -> List[Dict]:
    client, model = get_configured_client(api_key, model)

    api_params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    base_model = model.replace("openai/", "")
    is_reasoning_model = base_model.startswith("gpt-5") or base_model.startswith("o1") or base_model.startswith("o3")
    if is_reasoning_model and not api_key.startswith("sk-or-"):
        api_params.pop("max_tokens", None)
        api_params["reasoning_effort"] = reasoning_effort
        api_params["max_completion_tokens"] = max_tokens

    try:
        response = client.chat.completions.create(**api_params)
        content = response.choices[0].message.content
        result = json.loads(content)
        if 'candidates' in result:
            return result['candidates']
        if 'formula' in result:
            return [result]
        print("  Warning: LLM response missing 'formula' or 'candidates' key")
        return []
    except Exception as e:
        print(f"  Warning: LLM generation failed or returned invalid JSON: {e}")
        print(f"  [LLM ERROR] Generation failed: {type(e).__name__}: {e}")
        return []

# In translate_query(), replace calls:
query = convert_yes_no_to_statement(query, api_key, model, temperature, reasoning_effort, max_tokens)
...
candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature, reasoning_effort=reasoning_effort, max_tokens=max_tokens)
```



2) **`retrieve_top_k_propositions` ignores configured thresholds (mismatch with config)**
Severity: Low
File: `code/interface_with_user/translate.py`
Function: `retrieve_top_k_propositions`
Lines: 242-256
Problem: Hard-coded similarity cutoff `0.1` and `k` default ignore `retrieval_config.SBERT_MIN_SIMILARITY` and `retrieval_config.SBERT_TOP_K`.
Proposed solution: use config values when provided.
Minimal replacement:
```python
def retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: Optional[int] = None) -> List[Dict]:
    chunk_embeddings = encode_chunks(chunks, sbert_model)
    query_embedding = encode_query(query, sbert_model)
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    k = k if k is not None else retrieval_config.SBERT_TOP_K
    min_sim = retrieval_config.SBERT_MIN_SIMILARITY

    top_k_indices = np.argsort(similarities)[::-1][:k]
    retrieved = []
    for idx in top_k_indices:
        if similarities[idx] < min_sim:
            break
        chunk = chunks[idx].copy()
        chunk['similarity'] = float(similarities[idx])
        retrieved.append(chunk)
    return retrieved
```

3) **Schema assumptions can throw `KeyError` on missing fields (input mismatch)**
Severity: Medium
File: `code/interface_with_user/translate.py`
Function: `extract_proposition_chunks`
Lines: 223-238
Problem: Uses `prop['translation']` and `prop['id']` without validation. If logified JSON lacks these keys, code crashes.
Proposed solution: skip invalid props with a clear warning.
Minimal replacement:
```python
def extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = True) -> List[Dict]:
    primitive_props = logified_structure.get('primitive_props', [])
    chunks = []
    for prop in primitive_props:
        if 'id' not in prop or 'translation' not in prop:
            continue
        translation = prop['translation']
        evidence = prop.get('evidence', '')
        text_to_embed = f"{translation} | Evidence: {evidence[:200]}" if hybrid_embedding and evidence else translation
        chunks.append({
            'text': text_to_embed,
            'id': prop['id'],
            'translation': translation,
            'evidence': evidence,
            'explanation': prop.get('explanation', '')
        })
    return chunks
```

4) **Potential `AttributeError` if `message.content` is not a string**
Severity: Low
File: `code/interface_with_user/translate.py`
Function: `convert_yes_no_to_statement`
Lines: 381-386
Problem: Assumes `response.choices[0].message.content` is a string and calls `.strip()`. If the SDK returns a list of parts, this fails.
Proposed solution: normalize to string before `strip()`.
Minimal replacement:
```python
response_text = response.choices[0].message.content
if isinstance(response_text, list):
    response_text = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in response_text)
if response_text is None:
    raise ValueError("LLM returned empty response")
response_text = response_text.strip()
```

5) **Unused config flags (mismatch between config and runtime behavior)**
Severity: Low
File: `code/interface_with_user/translate.py`
Functions: `extract_proposition_chunks`, `translate_query`
Lines: 223-239, 596-598
Problem: `retrieval_config.ENABLE_HYBRID_EMBEDDING` is defined but never used; `extract_proposition_chunks` always defaults to `hybrid_embedding=True`.
Proposed solution: pass the config flag into `extract_proposition_chunks`.
Minimal change:
```python
chunks = extract_proposition_chunks(logified_structure, hybrid_embedding=retrieval_config.ENABLE_HYBRID_EMBEDDING)
```

---

No tests included as requested.
