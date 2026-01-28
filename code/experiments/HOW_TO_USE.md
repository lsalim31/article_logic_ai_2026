# How to Use: Experiments

## Quick Test on NDA

```bash
# 1. Logify
python code/from_text_to_logic/logify.py \
    experiments/SINTEC-UK-LTD-Non-disclosure-agreement-2017.pdf \
    --output outputs/logified/nda.json

# 2. Assign weights
python code/from_text_to_logic/weights.py \
    --pathfile experiments/SINTEC-UK-LTD-Non-disclosure-agreement-2017.pdf \
    --json-path outputs/logified/nda.json

# 3. Query
python code/interface_with_user/translate.py \
    "Can the receiving party share information?" \
    outputs/logified/nda_weighted.json
```

## Test Queries

- "Can the receiving party share confidential information?"
- "Is the disclosing party required to mark information?"
- "Does the confidentiality obligation have a time limit?"

## Adding New Experiments

1. Place document in `experiments/`
2. Create test queries
3. Run full pipeline
4. Document results in `experiments/<name>_notes.md`
