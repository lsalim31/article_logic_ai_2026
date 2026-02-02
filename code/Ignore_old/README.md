# Interface with User

**Natural language query translation and result interpretation for neuro-symbolic reasoning**

## Overview

This module bridges natural language and propositional logic, enabling users to query logified documents using natural language hypotheses. It uses SBERT-based retrieval to find relevant propositions and LLM-powered translation to convert hypotheses into propositional formulas.

## Files

| File | Purpose | Status |
|------|---------|--------|
| `translate.py` | Query → formula translation | ✅ Implemented |
| `README.md` | This documentation | ✅ Current |
| `HOW_TO_USE.md` | Quick start guide | ✅ Current |

## Main Module: `translate.py`

### Features

#### Yes/No Question Handling
- Auto-detects question patterns: "Is...", "Can...", "Does...", "Will...", "Should...", "May..."
- Converts questions to declarative statements using LLM before translation
- Example: "Can the receiving party share information?" → "The receiving party can share information"

#### SBERT-Based Retrieval
- Uses `all-MiniLM-L6-v2` by default for efficient semantic search
- Retrieves top-k most relevant propositions (default k=20)
- Supports any sentence-transformer model

#### LLM Translation
- Translates natural language to propositional formulas
- Supports reasoning models (gpt-5.2, o1, o3) and standard models (gpt-4o, gpt-4-turbo)
- Includes concrete examples in prompt for better reliability
- Automatic retry logic for transient failures
- Fallback formula extraction for non-JSON responses

#### Robust Error Handling
- Validates proposition IDs exist in the document
- Multiple retry attempts with increasing temperature
- Regex-based formula extraction as fallback
- Clear error messages for debugging

## Quick Start

### Command Line

```bash
# Basic usage
python translate.py "The receiving party shall not disclose confidential information" \
    logified_weighted.json --api-key sk-or-v1-xxx

# With custom model
python translate.py "Some information may be shared with employees" \
    logified.json --api-key sk-xxx --model gpt-4o

# Quiet mode (JSON output only)
python translate.py "Is reverse engineering allowed?" \
    logified.json --api-key sk-xxx --quiet
```

### Python API

```python
from interface_with_user.translate import translate_query

# Basic translation
result = translate_query(
    query="The receiving party shall not reverse engineer any confidential information",
    json_path="logified_weighted.json",
    api_key="sk-or-v1-xxx"
)

print(f"Formula: {result['formula']}")
print(f"Query Mode: {result['query_mode']}")  # "entailment" or "consistency"
print(f"Translation: {result['translation']}")
print(f"Reasoning: {result.get('reasoning', result.get('explanation', 'N/A'))}")

# Use query_mode to select solver method
from logic_solver import LogicSolver

solver = LogicSolver(logified_structure)

if result['query_mode'] == "consistency":
    # "May X?" → Check if X is consistent (possible/allowed)
    solver_result = solver.check_consistency(result['formula'])
else:
    # "Shall X?" → Check if X is entailed (required)
    solver_result = solver.query(result['formula'])
```

## Query Modes

The translator detects the semantic type of each hypothesis and outputs a `query_mode`:

| Query Mode   | Hypothesis Keywords                          | Solver Method               | Semantics                    |
|--------------|----------------------------------------------|----------------------------|------------------------------|
| `entailment` | "shall", "must", "is required", "shall not"  | `solver.query()`           | Is X necessarily true?       |
| `consistency`| "may", "can", "could", "is allowed"          | `solver.check_consistency()` | Is X possible/permitted?   |

This distinction is critical: "may" questions ask about *permission* (is it allowed?), not *obligation* (is it required?). Using entailment for permission queries incorrectly returns UNCERTAIN.

### Examples

- **Entailment**: "The receiving party **shall** return all documents" → `query_mode: "entailment"`
- **Consistency**: "The receiving party **may** share information with employees" → `query_mode: "consistency"`
- **Conditional**: "The party **shall** notify **in case** of legal requirement" → `query_mode: "entailment"` with formula `P_condition ⟹ P_action`

## Output Format

```json
{
    "formula": "P_9",
    "query_mode": "entailment",
    "translation": "The receiving party shall not reverse engineer information",
    "reasoning": "P_9 directly captures the prohibition on reverse engineering",
    "query": "The receiving party shall not reverse engineer any confidential information",
    "original_query": "Can reverse engineering be done?"
}
```

## API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | (required) | Natural language query/hypothesis |
| `json_path` | str | (required) | Path to logified JSON with `primitive_props` |
| `api_key` | str | (required) | OpenRouter or OpenAI API key |
| `model` | str | `"gpt-5.2"` | LLM model for translation |
| `temperature` | float | `0.1` | Sampling temperature |
| `reasoning_effort` | str | `"medium"` | For reasoning models |
| `max_tokens` | int | `64000` | Maximum response tokens |
| `k` | int | `20` | Number of propositions to retrieve |

## Error Handling

The module includes robust error handling:

1. **Empty Response**: Retries with increased temperature
2. **JSON Parse Failure**: Extracts JSON from response, falls back to regex formula extraction
3. **Missing Formula**: Clear error message
4. **Invalid Proposition IDs**: Warns but continues

## Troubleshooting

### "Failed to translate hypothesis to formula"

This error occurs when the LLM doesn't return a valid formula. Solutions:

1. Use `gpt-4o` or `gpt-5.2` for better reliability (smaller models may fail)
2. Rephrase ambiguous hypotheses to be more specific
3. Check that the logified JSON contains relevant propositions

## Dependencies

```bash
pip install sentence-transformers openai numpy
```
