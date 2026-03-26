# Review Report (Feb 2)

Scope: Python files in `code/from_text_to_logic` (`logic_converter.py`, `logify.py`, `openie_extractor.py`, `weights.py`). The goal is to identify (i) errors, (ii) input/output mismatches, and (iii) possible improvements. Each item below includes file, function, lines, and a concrete fix with code.

## 1) Errors / Likely Runtime Failures

1. **`message.content` may be a list, not a string**
File: `code/from_text_to_logic/logic_converter.py`
Function: `LogicConverter.convert`
Lines: 154-161
Issue: `response.choices[0].message.content` can be a list of content parts; calling `.strip()` on a list raises `AttributeError`.
Solution: Normalize content to a string before `.strip()` and JSON parsing.
Code:
```python
content = response.choices[0].message.content
if isinstance(content, list):
    parts = []
    for part in content:
        if isinstance(part, dict) and "text" in part:
            parts.append(part["text"])
        elif hasattr(part, "text"):
            parts.append(part.text)
        elif isinstance(part, str):
            parts.append(part)
    response_text = "".join(parts)
else:
    response_text = content

if response_text is None:
    raise ValueError("LLM returned empty response")
response_text = response_text.strip()
```

ANSWER Errors (1): I think there is message error that will be trigger. I edited the error mesggge to include your feedback. I will not do your edit because response.choices[0].message.content is the outcome of a LLM, so I am expecting it to be string. 

2. **Default `max_tokens` / `max_completion_tokens` likely exceed model limits**
File: `code/from_text_to_logic/logic_converter.py`, `code/from_text_to_logic/logify.py`
Function: `LogicConverter.__init__`, `LogifyConverter.__init__`, `main`
Lines: `logic_converter.py` 18-27, `logify.py` 92-107, 175-179
Issue: Defaults of `32000` and `128000` are likely to trigger API errors for many models.
Solution: Clamp or reject values above an explicit, configurable ceiling to prevent immediate failures.
Code:
```python
# logic_converter.py (near __init__)
import os
MAX_COMPLETION_TOKENS = int(os.getenv("LOGIFY_MAX_COMPLETION_TOKENS", "32768"))
if max_tokens > MAX_COMPLETION_TOKENS:
    raise ValueError(
        f"max_tokens={max_tokens} exceeds LOGIFY_MAX_COMPLETION_TOKENS={MAX_COMPLETION_TOKENS}"
    )
self.max_tokens = max_tokens
```

ANSWER Errors (2): I defined some constants and I added to /config/retrieval_config.py. Then, I am important that file to logic_converter.py and logify.py

3. **CoreNLP client start/connect semantics can conflict with `endpoint`**
File: `code/from_text_to_logic/openie_extractor.py`
Function: `OpenIEExtractor.__init__`, `OpenIEExtractor._start_client`
Lines: 112-144
Issue: Providing `endpoint` plus calling `__enter__()` can attempt to start a server even when you want to connect to an existing one, or fail if nothing is running.
Solution: Add an optional `endpoint` parameter and only start a server when no external endpoint is supplied.
Code:
```python
# __init__ signature
endpoint: Optional[str] = None

# __init__ body
self.endpoint = endpoint

# _start_client
endpoint = self.endpoint or f"http://localhost:{self.port}"
start_server = self.endpoint is None
self.client = CoreNLPClient(
    annotators=self.openie_annotators,
    timeout=self.timeout,
    memory=self.memory,
    properties=self.openie_properties,
    be_quiet=True,
    endpoint=endpoint,
    start_server=start_server,
)
self.client.__enter__()
```

ANSWER Errors (3) Is this really necessary? I am running this in my computer. When would it be a problem?

4. **Coref pipeline uses minimal processors and can fail unexpectedly**
File: `code/from_text_to_logic/openie_extractor.py`
Function: `OpenIEExtractor.__init__`
Lines: 80-96
Issue: Some Stanza coref models require `pos`/`lemma`; using only `tokenize,coref` can cause initialization failures and silently disable coref.
Solution: Use a broader processor list that satisfies coref dependencies.
Code:
```python
self.coref_pipeline = stanza.Pipeline(
    language,
    processors="tokenize,pos,lemma,coref",
    verbose=False
)
```

Error (4) Done!

## 2) Input / Output Mismatches

1. **`formatted_triples` docstring says tab-separated, but JSON is passed**
File: `code/from_text_to_logic/logic_converter.py`, `code/from_text_to_logic/logify.py`
Function: `LogicConverter.convert`, `LogifyConverter.convert_text_to_logic`
Lines: `logic_converter.py` 63-70, `logify.py` 119-122
Issue: `convert()` says tab-separated triples, but `logify.py` passes JSON arrays via `format_triples_json(indent=-1)`.
Solution: Update the docstring to match the actual JSON array format.
Code:
```python
# logic_converter.py docstring
formatted_triples (str): Pre-formatted OpenIE triples (JSON array format)
```
ANSWER Input/output mismaches (2): I changed the docstring. Is it good to send the LLM the JSON array? Is it better than sending text?


2. **`weights.py` assumes `llm_weight` exists but it is not enforced upstream**
File: `code/from_text_to_logic/weights.py`
Function: `assign_weights`
Lines: 175-232
Issue: If `llm_weight` is missing, it silently defaults to `0.5`, which can misclassify constraints.
Solution: Validate schema and fail fast when required fields are absent.
Code:
```python
required_fields = {"id", "translation", "formula", "llm_weight"}
missing = [c for c in constraints if not required_fields.issubset(c.keys())]
if missing:
    raise ValueError("constraints missing required fields: id, translation, formula, llm_weight")
```

3. **`extract_triples_with_coref_info()` returns triples not aligned with `resolved_text`**
File: `code/from_text_to_logic/openie_extractor.py`
Function: `extract_triples_with_coref_info`
Lines: 444-472
Issue: It computes `resolved_text` but calls `extract_triples(text)` which re-runs coref and uses the original input; outputs can diverge.
Solution: Reuse the resolved text for triple extraction.
Code:
```python
# Add a helper
def _extract_triples_from_resolved_text(self, resolved_text: str) -> List[Dict[str, Any]]:
    annotation = self.client.annotate(resolved_text)
    # reuse existing extraction logic from extract_triples (sentences/openie/fallback)
    ...

# In extract_triples_with_coref_info
resolved_text, coref_chains = self._resolve_coreferences(text)
triples = self._extract_triples_from_resolved_text(resolved_text)
```
answer input.mistmatch (2) please read the code again and write the complete function that you want me to replace. Keep the same name, input and output for compatbility with the rest of the code

## 3) Possible Improvements (Concrete Fixes)

1. **Add JSON schema validation after parsing LLM output**
File: `code/from_text_to_logic/logic_converter.py`
Function: `LogicConverter.convert`
Lines: 170-173
Issue: `json.loads` can succeed while the schema is wrong, leading to downstream errors.
Solution: Validate the top-level keys and constraint fields immediately after parsing.
Code:
```python
logic_structure = json.loads(response_text)
if "primitive_props" not in logic_structure or "constraints" not in logic_structure:
    raise ValueError("LLM output missing required keys: primitive_props, constraints")
for c in logic_structure.get("constraints", []):
    if "id" not in c or "formula" not in c or "translation" not in c:
        raise ValueError("Constraint missing required fields: id, formula, translation")
return logic_structure
```

2. **Clamp `max_tokens` passed from CLI**
File: `code/from_text_to_logic/logify.py`
Function: `main`
Lines: 175-206
Issue: CLI allows values that cause API errors.
Solution: Enforce the same ceiling used in `LogicConverter` before constructing the converter.
Code:
```python
MAX_COMPLETION_TOKENS = int(os.getenv("LOGIFY_MAX_COMPLETION_TOKENS", "32768"))
if args.max_tokens > MAX_COMPLETION_TOKENS:
    raise ValueError(
        f"--max-tokens={args.max_tokens} exceeds LOGIFY_MAX_COMPLETION_TOKENS={MAX_COMPLETION_TOKENS}"
    )
```

3. **Make CoreNLP connectivity errors explicit**
File: `code/from_text_to_logic/openie_extractor.py`
Function: `_start_client`
Lines: 133-144
Issue: Connection failures are only visible as a generic exception.
Solution: Check the endpoint before starting and raise a clear error.
Code:
```python
import requests
endpoint = self.endpoint or f"http://localhost:{self.port}"
if self.endpoint is not None:
    try:
        requests.get(f"{endpoint}")
    except Exception as e:
        raise RuntimeError(f"CoreNLP endpoint unreachable: {endpoint}") from e
```

Answer possible improvements (3). Check the code added in def_start_client(self)

4. **Surface coref initialization failures more clearly**
File: `code/from_text_to_logic/openie_extractor.py`
Function: `OpenIEExtractor.__init__`
Lines: 92-96
Issue: Coref silently disables; users may not notice quality drop.
Solution: Raise a clear warning and expose a flag in output or logs.
Code:
```python
except Exception as e:
    self.coref_enabled = False
    raise RuntimeError(
        f"Stanza coref initialization failed; set download_models=True. Error: {e}"
    )
```

5. **Limit debug output size**
File: `code/from_text_to_logic/logic_converter.py`
Function: `LogicConverter.convert`
Lines: 139-152
Issue: `response.model_dump()` can be huge and spam logs.
Solution: Log only essential metadata unless verbose debug is enabled.
Code:
```python
if os.getenv("LOGIFY_DEBUG", "0") == "1":
    print(f"  DEBUG - Complete response dict: {response.model_dump()}")
```

6. **Make debug files deterministic and avoid CWD pollution**
File: `code/from_text_to_logic/logic_converter.py`
Function: `LogicConverter.convert`
Lines: 179-183
Issue: `debug_llm_response.txt` is written into the working directory.
Solution: Save to a fixed subfolder near the module or in `outputs/`.
Code:
```python
debug_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(debug_dir, exist_ok=True)
debug_file = os.path.join(debug_dir, "debug_llm_response.txt")
with open(debug_file, "w", encoding="utf-8") as f:
    f.write(response_text)
```

7. **Use context manager for deterministic cleanup**
File: `code/from_text_to_logic/logify.py`
Function: `LogifyConverter` usage in `main`
Lines: 199-236
Issue: `__del__` may run late or not at all during shutdown.
Solution: Add `__enter__/__exit__` and use `with` in `main`.
Code:
```python
# in LogifyConverter
def __enter__(self):
    return self

def __exit__(self, exc_type, exc, tb):
    self.close()
    return False

# in main
with LogifyConverter(...) as converter:
    logic_structure = converter.convert_text_to_logic(text)
    converter.save_output(logic_structure, str(output_path))
```

8. **Cache embeddings in `weights.py` to avoid recomputation**
File: `code/from_text_to_logic/weights.py`
Function: `assign_weights`
Lines: 203-216
Issue: Large documents re-embed on every run.
Solution: Cache chunk embeddings on disk by document hash.
Code:
```python
import hashlib
cache_key = hashlib.md5(document_text.encode("utf-8")).hexdigest()
cache_path = Path(json_path).parent / f"chunk_embeds_{cache_key}.npy"
if cache_path.exists():
    chunk_embeddings = np.load(cache_path)
else:
    chunk_embeddings = encode_chunks(chunks, sbert_model)
    np.save(cache_path, chunk_embeddings)
```

---

If you want, I can apply any of these changes directly or prepare a minimal patch set.
