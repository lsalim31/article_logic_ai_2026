# How to Use: From Text to Logic

This guide explains how to use the two main entry points: `logify.py` and `weights.py`. It is intended for LLM agents and developers who need to understand the codebase and integrate these tools.

---

## Table of Contents

1. [logify.py - Text to Logic Conversion](#logifypy---text-to-logic-conversion)
2. [weights.py - Soft Constraint Weighting](#weightspy---soft-constraint-weighting)
3. [Complete Workflow Example](#complete-workflow-example)
4. [Error Handling](#error-handling)
5. [Common Patterns](#common-patterns)

---

## logify.py - Text to Logic Conversion

### Purpose

Converts natural language documents into structured propositional logic by:
1. Extracting relation triples using OpenIE
2. Using an LLM to formalize the text into atomic propositions and constraints

### Command Line Interface

```bash
python from_text_to_logic/logify.py <input> --api-key <key> [options]
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `input` | Path to document file (PDF, DOCX, TXT) OR raw text string |
| `--api-key` | OpenAI API key (or OpenRouter key starting with `sk-or-`) |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--model` | `gpt-5.2` | Model to use. Options: `gpt-5.2`, `o1`, `gpt-4o`, `gpt-4-turbo`, etc. |
| `--temperature` | `0.1` | Sampling temperature (ignored for reasoning models) |
| `--reasoning-effort` | `medium` | For reasoning models: `none`, `low`, `medium`, `high`, `xhigh` |
| `--max-tokens` | `128000` | Maximum tokens in LLM response |
| `--output` | Auto-generated | Custom output JSON file path |

#### Output Filename Convention

If `--output` is not specified:
- File input: `{input_stem}.json` (same directory as input)
- Raw text input: `logified.json` (current directory)

### Python API

#### Class: `LogifyConverter`

```python
from from_text_to_logic.logify import LogifyConverter

converter = LogifyConverter(
    api_key: str,                    # Required: OpenAI/OpenRouter API key
    model: str = "gpt-5.2",          # LLM model to use
    temperature: float = 0.1,        # Sampling temperature
    reasoning_effort: str = "medium", # For reasoning models
    max_tokens: int = 128000         # Max response tokens
)
```

#### Methods

##### `convert_text_to_logic(text: str) -> Dict[str, Any]`

Converts input text to structured logic.

**Input:**
- `text` (str): Natural language text to convert

**Output:**
- Dict with keys: `primitive_props`, `hard_constraints`, `soft_constraints`

**Example:**
```python
logic = converter.convert_text_to_logic("""
    Students must complete either the written exam or the oral presentation.
    A student passes if they complete the requirement and attend 80% of lectures.
""")

print(logic["primitive_props"])  # List of atomic propositions
print(logic["hard_constraints"]) # List of hard constraints
print(logic["soft_constraints"]) # List of soft constraints
```

##### `save_output(logic_structure: Dict, output_path: str)`

Saves the logic structure to a JSON file.

**Input:**
- `logic_structure` (Dict): Output from `convert_text_to_logic()`
- `output_path` (str): Path to save JSON file

##### `close()`

Releases resources (CoreNLP server, Stanza pipelines). Always call when done.

#### Helper Function: `extract_text_from_document(file_path: str) -> str`

Extracts text from PDF, DOCX, or TXT files.

**Input:**
- `file_path` (str): Path to document

**Output:**
- str: Extracted text content

**Supported formats:**
- `.txt`, `.text` - Plain text
- `.pdf` - PDF (requires PyMuPDF)
- `.docx`, `.doc` - Word documents (requires python-docx)

### Output Schema

```json
{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "The student completes the written exam",
      "evidence": "Sentence 1: 'Students must complete either the written exam...'",
      "explanation": "Atomic action with no logical connectives"
    }
  ],
  "hard_constraints": [
    {
      "id": "H_1",
      "formula": "P_3 ⟺ ((P_1 ∨ P_2) ∧ ¬(P_1 ∧ P_2))",
      "translation": "A student satisfies the requirement iff they complete exactly one of the two options",
      "evidence": "Sentence 1: '...either the written exam or the oral presentation, but not both'",
      "reasoning": "Exclusive-or requirement stated explicitly"
    }
  ],
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "P_4 ⟹ P_5",
      "translation": "If a student is experienced, they typically skip orientation",
      "evidence": "Common-sense inference from context",
      "reasoning": "The word 'typically' indicates uncertainty, making this soft"
    }
  ]
}
```

---

## weights.py - Soft Constraint Weighting

### Purpose

Assigns confidence weights to soft constraints by:
1. Retrieving relevant document chunks using SBERT
2. Verifying each constraint (and its negation) via LLM logprobs
3. Computing binary softmax confidence scores

### Command Line Interface

```bash
python from_text_to_logic/weights.py <document> <json_file> --api-key <key> [options]
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `document` | Path to source document (PDF, DOCX, TXT) |
| `json_file` | Path to logified JSON file (output from logify.py) |
| `--api-key` | OpenAI API key |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--model` | `gpt-4o` | Model for verification (must support logprobs) |
| `--temperature` | `0.0` | Sampling temperature |
| `--max-tokens` | `5` | Max tokens in response |
| `--k` | `10` | Number of chunks to retrieve per constraint |
| `--chunk-size` | `512` | Tokens per chunk |
| `--chunk-overlap` | `50` | Overlapping tokens between chunks |
| `--quiet` | False | Suppress progress messages |

**Important:** Reasoning models (GPT-5.x, o1, o3) may not support logprobs. Use `gpt-4o` for this task.

### Python API

#### Function: `assign_weights(...) -> Dict[str, Any]`

```python
from from_text_to_logic.weights import assign_weights

result = assign_weights(
    pathfile: str,           # Required: Path to source document
    json_path: str,          # Required: Path to logified JSON
    api_key: str,            # Required: OpenAI API key
    model: str = "gpt-4o",   # Model (must support logprobs)
    temperature: float = 0.0,
    max_tokens: int = 5,
    reasoning_effort: str = "low",
    k: int = 10,             # Top-k chunks to retrieve
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True
) -> Dict[str, Any]
```

**Output:**
- Returns the logified structure with `weight` arrays added to each soft constraint
- Saves to `{json_stem}_weighted.json`

#### Function: `verify_single_constraint(...) -> Dict[str, float]`

Verifies a single constraint against document chunks.

```python
from from_text_to_logic.weights import verify_single_constraint

result = verify_single_constraint(
    constraint_text: str,      # Natural language constraint
    chunks: List[Dict],        # Document chunks
    chunk_embeddings: np.ndarray,
    sbert_model,
    client: OpenAI,
    model: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 5,
    k: int = 10
) -> Dict[str, float]
```

**Output:**
```python
{
    "logit_yes": -0.023,   # Log probability of YES
    "logit_no": -4.12,     # Log probability of NO
    "prob_yes": 0.977,     # P(YES) = exp(logit_yes)
    "prob_no": 0.016       # P(NO) = exp(logit_no)
}
```

### Weight Output Format

Each soft constraint receives a `weight` array with 3 values:

```json
{
  "id": "S_1",
  "formula": "P_1 ⟹ P_2",
  "translation": "If condition X, then Y",
  "weight": [0.95, 0.12, 0.89]
}
```

| Index | Meaning | Interpretation |
|-------|---------|----------------|
| `weight[0]` | P(YES \| original) | Probability document supports the constraint |
| `weight[1]` | P(YES \| negated) | Probability document supports the negation |
| `weight[2]` | Confidence | Binary softmax: `P(orig) / (P(orig) + P(neg))` |

**Confidence interpretation:**
- `> 0.6`: Document supports the constraint
- `≈ 0.5`: Ambiguous/uncertain
- `< 0.4`: Document likely contradicts the constraint

---

## Complete Workflow Example

### Step 1: Convert Document to Logic

```bash
# Using CLI
python from_text_to_logic/logify.py policy.pdf \
    --api-key $OPENAI_API_KEY \
    --model gpt-5.2 \
    --reasoning-effort high

# Output: policy.json
```

### Step 2: Assign Weights to Soft Constraints

```bash
# Using CLI
python from_text_to_logic/weights.py policy.pdf policy.json \
    --api-key $OPENAI_API_KEY \
    --model gpt-4o \
    --k 10

# Output: policy_weighted.json
```

### Complete Python Example

```python
from from_text_to_logic.logify import LogifyConverter, extract_text_from_document
from from_text_to_logic.weights import assign_weights

# Step 1: Extract text
text = extract_text_from_document("policy.pdf")

# Step 2: Convert to logic
converter = LogifyConverter(
    api_key="sk-...",
    model="gpt-5.2",
    reasoning_effort="high"
)

try:
    logic = converter.convert_text_to_logic(text)
    converter.save_output(logic, "policy.json")
finally:
    converter.close()

# Step 3: Assign weights
weighted = assign_weights(
    pathfile="policy.pdf",
    json_path="policy.json",
    api_key="sk-...",
    model="gpt-4o",
    k=10
)

# Step 4: Use the results
for constraint in weighted["soft_constraints"]:
    confidence = constraint["weight"][2]
    print(f"{constraint['id']}: {constraint['translation']}")
    print(f"  Confidence: {confidence:.2%}")
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | Document path invalid | Check file path exists |
| `ImportError: PyMuPDF` | PDF support not installed | `pip install PyMuPDF` |
| `ImportError: python-docx` | DOCX support not installed | `pip install python-docx` |
| `RuntimeError: CoreNLP` | Java not installed or CoreNLP failed | Install Java 11+, check memory |
| `JSONDecodeError` | LLM returned malformed JSON | Check `debug_llm_response.txt` |
| `ValueError: empty response` | LLM returned None | Check API key, model availability |

### Handling API Errors

```python
try:
    logic = converter.convert_text_to_logic(text)
except RuntimeError as e:
    if "LLM conversion" in str(e):
        # Check debug_llm_response.txt for raw output
        print("LLM failed. Check debug_llm_response.txt")
    raise
```

---

## Common Patterns

### Pattern 1: Batch Processing Multiple Documents

```python
from pathlib import Path
from from_text_to_logic.logify import LogifyConverter

converter = LogifyConverter(api_key="sk-...")

try:
    for doc_path in Path("documents/").glob("*.txt"):
        text = doc_path.read_text()
        logic = converter.convert_text_to_logic(text)
        output_path = doc_path.with_suffix(".json")
        converter.save_output(logic, str(output_path))
finally:
    converter.close()
```

### Pattern 2: Using OpenRouter Instead of OpenAI

```python
# OpenRouter keys start with 'sk-or-'
converter = LogifyConverter(
    api_key="sk-or-v1-...",  # OpenRouter key
    model="gpt-4o"           # Will be prefixed as openai/gpt-4o
)
```

### Pattern 3: Extracting Only Hard Constraints

```python
logic = converter.convert_text_to_logic(text)

# Filter to hard constraints only
hard_only = {
    "primitive_props": logic["primitive_props"],
    "hard_constraints": logic["hard_constraints"],
    "soft_constraints": []
}
```

### Pattern 4: Custom Confidence Threshold

```python
weighted = assign_weights(...)

# Filter soft constraints by confidence
HIGH_CONFIDENCE = 0.7
confident_soft = [
    c for c in weighted["soft_constraints"]
    if c.get("weight", [0, 0, 0])[2] >= HIGH_CONFIDENCE
]
```

---

## Notes for LLM Agents

1. **Always close the converter** when done to release CoreNLP resources
2. **Use gpt-4o for weights.py** - reasoning models don't support logprobs
3. **Check debug files** on JSON parse errors: `debug_llm_response.txt`
4. **The prompt file** is at `../prompts/prompt_logify` relative to the module
5. **Soft constraint weights** are only meaningful after running `weights.py`
6. **OpenRouter support** is automatic when API key starts with `sk-or-`
