# Experiment: Logify on DocNLI Dataset

## Overview

Evaluate the Logify neuro-symbolic pipeline on the DocNLI document-level NLI dataset.

## Dataset

- **Source**: [Salesforce DocNLI](https://github.com/salesforce/DocNLI) (ACL 2021)
- **Split**: Test set
- **Sample**: 100 examples
- **Filtering criteria**:
  - Premise length: 200-500 words
  - Balanced: 50 entailment, 50 not-entailment
  - Priority: FEVER/SQuAD sources (if metadata available)

## Task

Given a premise (document) and hypothesis, predict:
- **entailment**: hypothesis is supported by premise
- **not_entailment**: hypothesis is not supported by premise

## Pipeline

1. **Logification**: Convert premise text to weighted logical structure
2. **Query translation**: Convert hypothesis to logical formula
3. **Solving**: Evaluate formula against logical structure
4. **Mapping**: Map solver output (TRUE/FALSE/UNCERTAIN) to binary labels

### Label Mapping

| Solver Output | DocNLI Label |
|---------------|--------------|
| TRUE | entailment |
| FALSE | not_entailment |
| UNCERTAIN | not_entailment |

## Models

| Role | Model |
|------|-------|
| Logification | `openai/gpt-5.2` (fixed) |
| Query translation | `openai/gpt-5-nano` |
| Weight assignment | `gpt-4o` |

## Files

```
code/experiments/DocNLI/
├── DESCRIPTION_EXPERIMENT_DOCNLI_LOGIFY.md   # This file
├── experiment_logify_DocNLI.py               # Main experiment script
├── download_sample.py                        # Script to download 100 examples
├── cache/                                    # Cached logified structures
├── doc-nli/
│   └── sample_100.json                       # 100 filtered test examples
└── results_logify_DocNLI/                    # Experiment results
```

## Output Format

```json
{
  "metadata": {
    "timestamp": "...",
    "logify_model": "openai/gpt-5.2",
    "query_model": "openai/gpt-5-nano",
    "weights_model": "gpt-4o",
    "temperature": 0.1,
    "reasoning_effort": "medium",
    "num_examples": 100,
    "total_correct": ...,
    "total_evaluated": ...,
    "overall_accuracy": ...
  },
  "document_metrics": [
    {
      "example_id": 0,
      "original_idx": 4523,
      "premise_length": 312,
      "logify_latency_sec": 45.2,
      "logify_cached": false,
      "logify_error": null
    }
  ],
  "results": [
    {
      "example_id": 0,
      "original_idx": 4523,
      "hypothesis_text": "...",
      "prediction": "TRUE",
      "prediction_binary": "entailment",
      "confidence": 0.85,
      "ground_truth": "entailment",
      "formula": "P_1 ∧ P_3",
      "error": null
    }
  ]
}
```

## Usage

```bash
# Download sample data
python download_sample.py

# Run experiment
python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY

# Or with custom parameters
python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY --temperature 0.0
```

## References

- Yin, W., Radev, D., & Xiong, C. (2021). DocNLI: A Large-scale Dataset for Document-level Natural Language Inference. ACL-IJCNLP 2021.
- https://github.com/salesforce/DocNLI
