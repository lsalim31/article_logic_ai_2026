# How to Use: From Text to Logic

## Quick Start

```python
from from_text_to_logic.logify import logify_document

# Logify document
logified = logify_document(
    document_path="document.pdf",
    api_key="sk-or-v1-xxx"
)

# Assign weights
from from_text_to_logic.weights import assign_weights

weighted = assign_weights(
    pathfile="document.pdf",
    json_path="logified.json",
    api_key="sk-or-v1-xxx"
)
```

## Command Line

```bash
# Logify
python code/from_text_to_logic/logify.py document.pdf --api-key sk-xxx

# Add weights
python code/from_text_to_logic/weights.py \
    --pathfile document.pdf \
    --json-path logified.json \
    --api-key sk-xxx
```

## Output Format

The output is a JSON file with:
- `primitive_props`: Atomic propositions
- `hard_constraints`: Must-hold constraints
- `soft_constraints`: May-hold constraints with weights

Weights are 3-element arrays: `[prob_orig, prob_neg, confidence]`
