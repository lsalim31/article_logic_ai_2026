# Experiments

**Test documents and experimental workspace**

## Contents

- **SINTEC-UK-LTD-Non-disclosure-agreement-2017.pdf** - Real NDA for testing

## Usage

```bash
# Test full pipeline
python code/from_text_to_logic/logify.py experiments/SINTEC-UK-LTD-Non-disclosure-agreement-2017.pdf
```

## Test Queries

- "Can the receiving party share confidential information?"
- "Does the confidentiality obligation have a time limit?"

## Adding Experiments

1. Place document in this directory
2. Create test queries
3. Run pipeline and document results
