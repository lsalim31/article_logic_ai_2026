# How to Use: Interface with User

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip install sentence-transformers openai numpy
```

### Step 2: Prepare Your Logified JSON

Ensure your JSON file has a `primitive_props` array:

```json
{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "The receiving party shall keep information confidential",
      "evidence": "Section 3(a)"
    }
  ]
}
```

### Step 3: Translate Your Query

```python
from interface_with_user.translate import translate_query

result = translate_query(
    query="Can information be shared with employees?",
    json_path="logified_weighted.json",
    api_key="sk-or-v1-xxx"
)

print(f"Formula: {result['formula']}")
```

## Command Line Usage

```bash
# Basic
python code/interface_with_user/translate.py \
    "The receiving party shall not disclose information" \
    path/to/logified.json \
    --api-key sk-xxx

# With options
python code/interface_with_user/translate.py \
    "Some information may be shared with third parties" \
    logified.json \
    --api-key sk-xxx \
    --model gpt-4o \
    --quiet
```

## Yes/No Questions

The module automatically handles Yes/No questions:

```python
result = translate_query(
    query="Is the receiving party allowed to share information?",
    json_path="logified.json",
    api_key="sk-xxx"
)
# result['original_query'] = "Is the receiving party allowed to share information?"
# result['query'] = "The receiving party is allowed to share information"
```

## Full Pipeline Example

```python
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver
import json

# 1. Load the logified document
with open('logified_weighted.json') as f:
    logified = json.load(f)

# 2. Translate a hypothesis to a formula
translation = translate_query(
    query="Receiving Party may share Confidential Information with employees",
    json_path='logified_weighted.json',
    api_key='sk-or-v1-xxx',
    model='gpt-4o'  # Recommended for reliability
)

print(f"Formula: {translation['formula']}")

# 3. Query the logic solver
solver = LogicSolver(logified)
answer = solver.query(translation['formula'])

print(f"Answer: {answer.answer}")  # TRUE, FALSE, or UNCERTAIN
print(f"Confidence: {answer.confidence:.2%}")
```

## Model Recommendations

| Model | Reliability | Use Case |
|-------|-------------|----------|
| `gpt-4o` | High | Production, experiments |
| `gpt-5.2` | Very High | Complex legal language |
| `gpt-5-nano` | Medium | Quick testing only |

**Note**: Smaller models may fail to produce valid JSON. Use `gpt-4o` or better for reliable results.

## Error Handling

```python
try:
    result = translate_query(query, json_path, api_key)
    if result.get('formula'):
        print(f"Success: {result['formula']}")
except ValueError as e:
    print(f"Translation failed: {e}")
```

## Troubleshooting

### No formula returned
1. Use `gpt-4o` instead of smaller models
2. Verify JSON file has `primitive_props` field
3. Check API key is valid

### Slow performance
1. Reduce `k` parameter
2. Use `gpt-4o` instead of `gpt-5.2`
3. Set `verbose=False`
