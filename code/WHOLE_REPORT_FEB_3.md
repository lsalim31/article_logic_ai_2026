# Whole Report Feb 3

Scope: `code/from_text_to_logic`, `code/config`, `code/interface_with_user`, `code/logic_solver`, `code/prompts`, `code/main.py`, `code/experiments/contractNLI/experiment_logify_contract_NLI.py`. Docstrings ignored.

## Issues

1) **Coref pipeline initializes twice and can crash even when `enable_coref=False`**
Severity: High
File: `code/from_text_to_logic/openie_extractor.py`
Function: `OpenIEExtractor.__init__`
Lines: 68-92
Problem: `self.coref_pipeline = stanza.Pipeline(...)` runs unconditionally (line 70) and then is re-initialized in the guarded `try` block (lines 83-92). If models are missing, it raises before `enable_coref` logic can disable coref.
Proposed solution (minimal replacement of `__init__`):
```python
def __init__(
    self,
    memory: str = '8G',
    timeout: int = 60000,
    enable_coref: bool = True,
    use_depparse_fallback: bool = True,
    port: int = 9000,
    language: str = 'en',
    download_models: bool = False
):
    print("Initializing OpenIE Extractor with native Stanza...")

    self.coref_enabled = enable_coref
    self.use_depparse_fallback = use_depparse_fallback
    self.memory = memory
    self.timeout = timeout
    self.port = port
    self.language = language

    self.coref_pipeline: Optional[stanza.Pipeline] = None
    self.depparse_pipeline: Optional[stanza.Pipeline] = None
    self.client: Optional[CoreNLPClient] = None

    if download_models:
        print(f"Downloading Stanza models for '{language}'...")
        if enable_coref:
            stanza.download(language, processors='tokenize,pos,lemma,coref')
        if use_depparse_fallback:
            stanza.download(language, processors='tokenize,pos,lemma,depparse')

    if enable_coref:
        print("Initializing native Stanza coreference pipeline...")
        try:
            self.coref_pipeline = stanza.Pipeline(
                language,
                processors='tokenize,pos,lemma,coref',
                verbose=False
            )
            print("  ✓ Native Stanza coref initialized")
        except Exception as e:
            print(f"  ✗ Warning: Stanza coref initialization failed: {e}")
            self.coref_enabled = False

    if use_depparse_fallback:
        print("Initializing Stanza dependency parse pipeline...")
        try:
            self.depparse_pipeline = stanza.Pipeline(
                language,
                processors='tokenize,pos,lemma,depparse',
                download_method=None,
                verbose=False
            )
            print("  ✓ Stanza depparse initialized")
        except Exception as e:
            print(f"  ✗ Warning: Stanza depparse initialization failed: {e}")
            self.use_depparse_fallback = False

    print("Initializing CoreNLP client for OpenIE...")
    self.openie_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'depparse', 'natlog', 'openie']
    self.openie_properties = {
        'openie.triple.strict': 'true',
        'openie.triple.all_nominals': 'true',
        'openie.max_entailments_per_clause': '3',
        'openie.affinity_probability_cap': '0.33',
    }

    self._start_client()
```

2) **`self.endpoint` is undefined and endpoint check occurs after server start**
Severity: High
File: `code/from_text_to_logic/openie_extractor.py`
Function: `_start_client`
Lines: 135-152
Problem: `self.endpoint` is never defined; accessing it raises `AttributeError`. Also, the endpoint check happens after `__enter__()`, so it does not prevent starting the server.
Proposed solution (minimal replacement of `_start_client`):
```python
def _start_client(self):
    endpoint = getattr(self, 'endpoint', None) or f"http://localhost:{self.port}"

    if getattr(self, 'endpoint', None) is not None:
        try:
            requests.get(endpoint, timeout=2)
        except Exception as e:
            raise RuntimeError(f"CoreNLP endpoint unreachable: {endpoint}") from e

    self.client = CoreNLPClient(
        annotators=self.openie_annotators,
        timeout=self.timeout,
        memory=self.memory,
        properties=self.openie_properties,
        be_quiet=True,
        endpoint=endpoint,
        start_server=getattr(self, 'endpoint', None) is None,
    )
    self.client.__enter__()
```

3) **Prompt input format does not match actual input delimiters**
Severity: Low
File: `code/prompts/prompt_logify`
Lines: 104-116
Problem: Prompt specifies `ORIGINAL TEXT` and `RELATION TRIPLES` wrapped in `< ... >>>`, but `LogicConverter.convert()` sends `<<< ... >>>`. This mismatch can confuse parsing instructions.
Proposed solution: Update the prompt’s INPUT FORMAT to use `<<<` and `>>>` exactly, or update `LogicConverter.convert()` to use `<` and `>>>` consistently.

4) **`translate_query` ignores user-supplied `reasoning_effort` and `max_tokens`**
Severity: Medium
File: `code/interface_with_user/translate.py`
Functions: `translate_query`, `generate_candidates_llm`
Lines: 559-672 (translate_query), 417-447 (generate_candidates_llm)
Problem: `translate_query` accepts `reasoning_effort` and `max_tokens`, but never passes them to `convert_yes_no_to_statement` or `generate_candidates_llm`.
Proposed solution (minimal replacement of `generate_candidates_llm` and call sites):
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

# In translate_query:
query = convert_yes_no_to_statement(query, api_key, model, temperature, reasoning_effort, max_tokens)
...
candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature, reasoning_effort=reasoning_effort, max_tokens=max_tokens)
```

5) **`retrieve_top_k_propositions` ignores retrieval_config thresholds**
Severity: Low
File: `code/interface_with_user/translate.py`
Function: `retrieve_top_k_propositions`
Lines: 242-256
Problem: Uses hardcoded similarity threshold `0.1` and ignores `retrieval_config.SBERT_TOP_K` and `SBERT_MIN_SIMILARITY`.
Proposed solution (minimal replacement):
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

6) **`extract_proposition_chunks` can raise KeyError on missing fields**
Severity: Medium
File: `code/interface_with_user/translate.py`
Function: `extract_proposition_chunks`
Lines: 223-238
Problem: Assumes every proposition has `id` and `translation` keys.
Proposed solution (minimal replacement):
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

7) **Reverse implication is normalized but not parsed**
Severity: Medium
File: `code/logic_solver/encoding.py`
Functions: `_tokenize`, `_parse_implies`
Lines: 81-110, 100-109
Problem: The parser only recognizes `=>` and `<=>`. If `<=` appears, it is ignored by the tokenizer and parsing fails or misparses.
Proposed solution (minimal replacements):
```python
def _tokenize(self, formula: str) -> List[str]:
    pattern = r'(P_\d+|<=>|=>|<=|[&|~()])'
    tokens = re.findall(pattern, formula)
    return [t.strip() for t in tokens if t.strip()]


def _parse_implies(self, tokens: List[str]) -> Tuple[Any, List[str]]:
    left, tokens = self._parse_or(tokens)

    while tokens and tokens[0] in ('=>', '<='):
        op = tokens[0]
        tokens = tokens[1:]
        right, tokens = self._parse_or(tokens)
        if op == '=>':
            left = ('=>', left, right)
        else:
            # A <= B  ==  B => A
            left = ('=>', right, left)

    return left, tokens
```

8) **`_compute_confidence_uncertain` treats valid zero cost as infinity**
Severity: High
File: `code/logic_solver/maxsat.py`
Function: `_compute_confidence_uncertain`
Lines: 345-365
Problem: `cost_not_q = ... or float('inf')` converts a valid `0` into `inf`.
Proposed solution (minimal replacement):
```python
def _compute_confidence_uncertain(self, query_formula: str) -> float:
    wcnf_with_q = self._copy_wcnf(self.base_wcnf)
    for clause in self.encoder.encode_query(query_formula, negate=False):
        wcnf_with_q.append(clause)
    cost_q = self._solve_maxsat(wcnf_with_q)
    if cost_q is None:
        cost_q = float('inf')

    wcnf_with_not_q = self._copy_wcnf(self.base_wcnf)
    for clause in self.encoder.encode_query(query_formula, negate=True):
        wcnf_with_not_q.append(clause)
    cost_not_q = self._solve_maxsat(wcnf_with_not_q)
    if cost_not_q is None:
        cost_not_q = float('inf')

    if cost_q == float('inf') and cost_not_q == float('inf'):
        return 0.5
    if cost_q + cost_not_q == 0:
        return 0.5
    return cost_not_q / (cost_q + cost_not_q)
```

9) **`LogicEncoder.encode` ignores `constraints` when no weighted fields exist**
Severity: Medium
File: `code/logic_solver/encoding.py`
Function: `LogicEncoder.encode`
Lines: 357-386
Problem: If logified JSON has only `constraints` (pre-weighting), they are ignored.
Proposed solution (minimal replacement):
```python
def encode(self) -> WCNF:
    hard_constraints = self.structure.get('hard_constraints')
    if hard_constraints is None:
        hard_constraints = self.structure.get('constraints', [])

    for constraint in hard_constraints:
        formula = constraint['formula']
        clauses = self.parser.parse(formula)
        for clause in clauses:
            self.wcnf.append(clause)

    next_var = len(self.prop_to_var) + 1
    for constraint in self.structure.get('soft_constraints', []):
        formula = constraint['formula']
        weight = self._extract_weight(constraint, default=0.5)
        int_weight = self._weight_to_int(weight)
        clauses = self.parser.parse(formula)
        selector = next_var
        next_var += 1
        for clause in clauses:
            self.wcnf.append([-selector] + clause)
        self.wcnf.append([selector], weight=int_weight)

    return self.wcnf
```

10) **`LOGIFY_MODEL` may be invalid for non-OpenRouter keys**
Severity: Medium
File: `code/experiments/contractNLI/experiment_logify_contract_NLI.py`
Function: `logify_document`
Lines: 45-109
Problem: `LOGIFY_MODEL = "openai/gpt-5.2"` is passed directly to `LogifyConverter`. For OpenAI keys, this model name is invalid.
Proposed solution (minimal change inside `logify_document` before creating `LogifyConverter`):
```python
model = LOGIFY_MODEL
if not api_key.startswith('sk-or-') and model.startswith('openai/'):
    model = model.replace('openai/', '', 1)

converter = LogifyConverter(
    api_key=api_key,
    model=model,
    temperature=temperature,
    reasoning_effort=reasoning_effort,
    max_tokens=max_tokens
)
```

11) **`main.py` imports modules and functions that do not exist**
Severity: High
File: `code/main.py`
Lines: 19-28
Problem: `from_text_to_logic.propositions`, `from_text_to_logic.constraints`, `from_text_to_logic.schema`, `from_text_to_logic.update`, `logic_solver.encoding.encode_to_maxsat`, `logic_solver.maxsat.solve`, `interface_with_user.interpret`, `interface_with_user.refine` are not present in the repository. Running `main.py` raises `ModuleNotFoundError`.
Proposed solution: Replace the imports with existing modules (`from_text_to_logic.logify`, `from_text_to_logic.weights`, `logic_solver.maxsat.solve_query`, etc.) or remove unused imports until implemented.

---

No tests included as requested.
