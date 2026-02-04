# Final Report Feb 3 (Re-Scanned)

Scope: `code/from_text_to_logic`, `code/config`, `code/interface_with_user`, `code/logic_solver`, `code/prompts`, `code/main.py`, `code/experiments/contractNLI/experiment_logify_contract_NLI.py`. Docstrings ignored. Findings below reflect the **current** code shown by `nl -ba`.

## Issues

1) **`endpoint` argument is ignored (never stored), so external CoreNLP endpoint cannot be used**
Severity: Medium
File: `code/from_text_to_logic/openie_extractor.py`
Function: `OpenIEExtractor.__init__`
Lines: 37-74
Problem: `endpoint` is accepted in the signature (line 46) but `self.endpoint` is commented out (line 68). `_start_client` uses `getattr(self, 'endpoint', None)` so the provided endpoint is ignored.
Proposed solution (minimal change):
```python
self.endpoint = endpoint
```

2) **`extract_triples_with_coref_info` uses original text for triples (mismatch with returned `resolved_text`)**
Severity: Medium
File: `code/from_text_to_logic/openie_extractor.py`
Function: `extract_triples_with_coref_info`
Lines: 452-479 (from previous listing; unchanged in this scan)
Problem: It computes `resolved_text` but calls `extract_triples(text)`, which re-runs coref on the original text. Returned `resolved_text` and `triples` can diverge.
Proposed solution (minimal replacement function):
```python
def extract_triples_with_coref_info(self, text: str) -> Dict[str, Any]:
    print("Extracting triples with native Stanza coref information...")

    if self.client is None:
        raise RuntimeError("CoreNLP client not initialized.")

    try:
        resolved_text, coref_chains = self._resolve_coreferences(text)

        annotation = self.client.annotate(resolved_text)

        triples = []
        sentence_texts = []
        for sentence in annotation.sentence:
            tokens = [token.word for token in sentence.token]
            sentence_texts.append(' '.join(tokens))

        for sent_idx, sentence in enumerate(annotation.sentence):
            sentence_triples = []
            existing_subjects = set()

            if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                for triple in sentence.openieTriple:
                    subject = triple.subject.strip()
                    predicate = triple.relation.strip()
                    obj = triple.object.strip()
                    if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                        sentence_triples.append({
                            'subject': subject,
                            'predicate': predicate,
                            'object': obj,
                            'sentence_index': sent_idx,
                            'source': 'openie'
                        })
                        existing_subjects.add(subject)

            triples.extend(sentence_triples)

            if self.use_depparse_fallback and not sentence_triples:
                fallback_triples = self._extract_stanza_depparse_triples(
                    sentence_texts[sent_idx], sent_idx, existing_subjects
                )
                triples.extend(fallback_triples)

        return {
            'triples': triples,
            'coref_chains': coref_chains,
            'resolved_text': resolved_text,
            'original_text': text
        }

    except Exception as e:
        print(f"Error extracting triples with coref info: {e}")
        import traceback
        traceback.print_exc()
        return {
            'triples': [],
            'coref_chains': [],
            'resolved_text': text,
            'original_text': text
        }
```

3) **`assign_weights` validates required fields inside the loop (and uses sentinel weight)**
Severity: Low
File: `code/from_text_to_logic/weights.py`
Function: `assign_weights`
Lines: 230-239
Problem: `required_fields` check is repeated for every constraint and recomputes `missing` each time. Also sets `llm_weight` default to `-100` even though missing fields should already raise, which is inconsistent.
Proposed solution (minimal change):
```python
required_fields = {"id", "translation", "formula", "llm_weight"}
missing = [c for c in constraints if not required_fields.issubset(c.keys())]
if missing:
    raise ValueError("constraints missing required fields: id, translation, formula, llm_weight")

for i, constraint in enumerate(constraints):
    constraint_id = constraint.get('id', f'C_{i+1}')
    constraint_text = constraint.get('translation', '')
    llm_weight = constraint.get('llm_weight')
```

4) **Duplicate `_parse_implies` definition breaks parsing (`self` parameter at module scope)**
Severity: High
File: `code/interface_with_user/translate.py`
Functions: `_parse_implies` (duplicate)
Lines: 126-135 and 196-209
Problem: A second `_parse_implies(self, tokens)` is defined at module scope. This overwrites the earlier correct `_parse_implies(tokens)` and causes `TypeError` when called (missing positional argument).
Proposed solution (minimal replacement of the correct `_parse_implies` and remove the duplicate):
```python
def _parse_implies(tokens: List[str]) -> Tuple[Formula, List[str]]:
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
```

5) **`translate_query` ignores `reasoning_effort` and `max_tokens`**
Severity: Medium
File: `code/interface_with_user/translate.py`
Functions: `translate_query`, `generate_candidates_llm`
Lines: 577-690, 435-447
Problem: `translate_query` accepts `reasoning_effort` and `max_tokens` but does not pass them to `convert_yes_no_to_statement` or `generate_candidates_llm`.
Proposed solution (minimal changes):
```python
query = convert_yes_no_to_statement(query, api_key, model, temperature, reasoning_effort, max_tokens)
...
candidates = generate_candidates_llm(prompt, api_key, model, temperature=temperature, reasoning_effort=reasoning_effort, max_tokens=max_tokens)
```

6) **`extract_proposition_chunks` can raise KeyError on missing fields**
Severity: Medium
File: `code/interface_with_user/translate.py`
Function: `extract_proposition_chunks`
Lines: 241-256
Problem: Uses `prop['translation']` and `prop['id']` without checks.
Proposed solution (minimal replacement):
```python
def extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = ENABLE_HYBRID_EMBEDDING) -> List[Dict]:
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

7) **`LogicEncoder.encode` ignores `constraints` when only unweighted constraints exist**
Severity: Medium
File: `code/logic_solver/encoding.py`
Function: `encode`
Lines: 365-394
Problem: Only `hard_constraints`/`soft_constraints` are read. If input is the pre-weighted JSON (only `constraints`), all constraints are ignored.
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

8) **Confidence values outside [0, 1]**
Severity: High
File: `code/logic_solver/maxsat.py`
Functions: `check_entailment`, `check_consistency`
Lines: 109-116, 198-204
Problem: `confidence=10` and `confidence=-10` are returned, violating the expected [0,1] range used elsewhere.
Proposed solution (minimal change):
```python
# in check_entailment when optimal_cost is None
confidence=1.0

# in check_consistency when UNSAT
confidence=0.0
```

9) **`main.py` imports modules/functions that do not exist**
Severity: High
File: `code/main.py`
Lines: 19-28
Problem: Imports (`from_text_to_logic.propositions`, `constraints`, `schema`, `update`, `logic_solver.encoding.encode_to_maxsat`, `logic_solver.maxsat.solve`, `interface_with_user.interpret`, `interface_with_user.refine`) are not present. Running `main.py` fails immediately.
Proposed solution: Remove or replace with existing modules (e.g., `from_text_to_logic.logify`, `from_text_to_logic.weights`, `logic_solver.maxsat.solve_query`).

10) **`logify_document` ignores `weights_model` parameter**
Severity: Low
File: `code/experiments/contractNLI/experiment_logify_contract_NLI.py`
Function: `logify_document`
Lines: 72-137
Problem: `weights_model` is accepted but never used; `assign_weights` has no model parameter.
Proposed solution: remove `weights_model` from signature and call sites, or pass it through if you extend `assign_weights` to accept a model.

11) **Prompt/convert input delimiter mismatch is resolved**
Severity: None
File: `code/prompts/prompt_logify`, `code/from_text_to_logic/logic_converter.py`
Lines: prompt 107-115; logic_converter 77-85
Note: Both now use `<<<` and `>>>`. No action required.

---

No tests included as requested.
