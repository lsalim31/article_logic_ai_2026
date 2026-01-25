# RAG Baseline: Usage Guide

## Overview

This baseline implements **Reasoning LLM + RAG** for logical reasoning over documents. It retrieves relevant chunks via SBERT and performs Chain-of-Thought reasoning with an LLM, serving as a comparison baseline for the Logify neuro-symbolic system.

---

## Table of Contents

1. [Where Documents and Questions Are Located](#1-where-documents-and-questions-are-located)
2. [Requirements](#2-requirements)
3. [How to Run the Baseline](#3-how-to-run-the-baseline)
4. [Where Output Is Saved](#4-where-output-is-saved)
5. [Complete Workflow Example](#5-complete-workflow-example)

---

## 1. Where Documents and Questions Are Located

### Documents and Questions: HuggingFace Datasets

**The baseline does NOT use local files.** Instead, it automatically downloads benchmark datasets from HuggingFace:

| Dataset | Source | Document Field | Query Field | Label Field |
|---------|--------|----------------|-------------|-------------|
| **FOLIO** | `yafu/FOLIO` | `premises` | `conclusion` | `label` |
| **ProofWriter** | `allenai/proofwriter` (depth-5) | `theory` | `question` | `answer` |
| **ContractNLI** | `koreeda/contractnli` | `document` | `hypothesis` | `label` |

### How It Works

When you run:
```bash
python main.py --dataset folio
```

The code automatically:
1. Downloads the dataset from HuggingFace (cached locally after first download)
2. Extracts document text and queries from the dataset schema
3. Processes each example through the RAG pipeline

### Custom Documents (Not Currently Supported)

To use your own documents, you would need to:
- Modify `load_dataset()` in `main.py` to read from local files
- Ensure your data has fields: `document`, `query`, `label`

---

## 2. Requirements

### Dependencies

Install required packages:

```bash
pip install sentence-transformers>=2.2.0
pip install openai>=1.0.0
pip install datasets>=2.0.0
pip install numpy>=1.21.0
```

Or create a `requirements.txt`:
```txt
sentence-transformers>=2.2.0
openai>=1.0.0
datasets>=2.0.0
numpy>=1.21.0
```

Then install:
```bash
pip install -r requirements.txt
```

### API Key

You need an **OpenAI API key** for LLM reasoning:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or set it in your shell profile (`.bashrc`, `.zshrc`):
```bash
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: ~4GB RAM (for SBERT model and embeddings)
- **Network**: Internet connection for dataset/model downloads

---

## 3. How to Run the Baseline

### Basic Usage

```bash
python main.py --dataset DATASET_NAME --model MODEL_NAME --output OUTPUT_FILE
```

### Parameters

| Parameter | Required | Options | Default | Description |
|-----------|----------|---------|---------|-------------|
| `--dataset` | **Yes** | `folio`, `proofwriter`, `contractnli` | None | Dataset to evaluate |
| `--model` | No | Any OpenAI model | `gpt-4` | LLM for reasoning |
| `--output` | No | Any `.json` path | `results.json` | Output file path |

### Example Commands

#### Run on FOLIO dataset:
```bash
python main.py --dataset folio --model gpt-4 --output results_folio.json
```

#### Run on ProofWriter:
```bash
python main.py --dataset proofwriter --model gpt-4 --output results_proofwriter.json
```

#### Run on ContractNLI with different model:
```bash
python main.py --dataset contractnli --model gpt-4-turbo --output results_cnli.json
```

### Configuration Settings

The baseline uses **fixed hyperparameters** defined in `config.py`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `SBERT_MODEL` | `all-MiniLM-L6-v2` | Sentence encoder for retrieval |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `CHUNK_SIZE` | `512` | Tokens per chunk |
| `OVERLAP` | `50` | Overlapping tokens between chunks |
| `TEMPERATURE` | `0` | LLM temperature (deterministic) |

To change these, edit `config.py` directly.

---

## 4. Where Output Is Saved

### Output File Location

Results are saved to the path specified by `--output` (default: `results.json`).

### Output Format

The output is a **JSON file** containing:

```json
{
  "metrics": {
    "accuracy": 0.853,
    "precision": 0.841,
    "recall": 0.838,
    "f1": 0.839,
    "confusion_matrix": {
      "True__True": 120,
      "True__False": 15,
      "False__True": 10,
      "False__False": 95,
      ...
    },
    "per_class_metrics": {
      "True": {
        "precision": 0.89,
        "recall": 0.88,
        "f1": 0.88
      },
      "False": {
        "precision": 0.86,
        "recall": 0.90,
        "f1": 0.88
      },
      ...
    }
  },
  "predictions": ["True", "False", "Unknown", ...],
  "examples": [
    {
      "id": 0,
      "query": "Is X true?",
      "prediction": "True",
      "ground_truth": "True",
      "reasoning": "Step-by-step reasoning trace..."
    },
    ...
  ]
}
```

### Console Output

During execution, you'll see:
```
Loading dataset: folio
Loading SBERT model
Processing example 1/1430
Processing example 2/1430
...
Evaluating results

==================================================
Results for folio
==================================================

Overall Metrics:
  Accuracy:  0.853
  Precision: 0.841
  Recall:    0.838
  F1 Score:  0.839

Per-Class Metrics:
  True:
    Precision: 0.890
    Recall:    0.880
    F1:        0.885
  ...

Results saved to results_folio.json
```

---

## 5. Complete Workflow Example

### Step-by-Step: Running on FOLIO

#### Step 1: Install Dependencies
```bash
pip install sentence-transformers openai datasets numpy
```

#### Step 2: Set API Key
```bash
export OPENAI_API_KEY="sk-..."
```

#### Step 3: Run the Baseline
```bash
cd /workspace/repo/code/baseline_rag
python main.py --dataset folio --model gpt-4 --output folio_results.json
```

#### Step 4: Wait for Completion
The script will:
1. Download FOLIO dataset (~2-5 minutes first time)
2. Load SBERT model (~1 minute first time)
3. Process all examples (time depends on dataset size and API rate limits)
4. Save results to `folio_results.json`

#### Step 5: Inspect Results
```bash
cat folio_results.json | jq '.metrics'
```

### Running Tests (Optional)

Verify the baseline works correctly:

```bash
python test_baseline.py
```

Expected output:
```
Running baseline RAG tests...

✓ Chunker tests passed
✓ Evaluator tests passed
✓ Main function tests passed
✓ Response parsing tests passed
✓ Retriever tests passed

==================================================
All tests passed successfully!
==================================================
```

---

## Pipeline Architecture

The baseline follows this flow:

```
1. Load Dataset (HuggingFace)
   ↓
2. For each example:
   a. Preprocess document (normalize whitespace)
   b. Chunk document (512 tokens, 50 overlap)
   c. Encode chunks with SBERT
   d. Encode query with SBERT
   e. Retrieve top-5 chunks (cosine similarity)
   f. Construct Chain-of-Thought prompt
   g. Call LLM (temperature=0)
   h. Parse response → Extract answer
   ↓
3. Evaluate predictions vs ground truth
   ↓
4. Save metrics + examples to JSON
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'sentence_transformers'`
**Solution**: Install dependencies:
```bash
pip install sentence-transformers
```

### Error: `openai.error.AuthenticationError`
**Solution**: Set your API key:
```bash
export OPENAI_API_KEY="your-key"
```

### Error: Dataset download fails
**Solution**: Check internet connection and HuggingFace access:
```bash
pip install --upgrade datasets
```

### Warning: Slow execution
**Expected behavior**: Processing large datasets with API calls takes time. For ContractNLI (607 examples), expect ~2-3 hours with API rate limits.

---

## Summary

### Quick Start
```bash
# Install
pip install sentence-transformers openai datasets numpy

# Set API key
export OPENAI_API_KEY="sk-..."

# Run
python main.py --dataset folio --output results.json
```

### Key Points
- **Documents/Questions**: Automatically loaded from HuggingFace datasets
- **Requirements**: Python 3.8+, OpenAI API key, ~4GB RAM
- **Run**: `python main.py --dataset DATASET --output OUTPUT.json`
- **Output**: JSON file with metrics, predictions, and example traces
- **Location**: Current directory or specified `--output` path
