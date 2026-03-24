A neuro-symbolic reasoning framework that translates natural language documents into propositional logic

This repository contains the Logify neuro-symbolic pipeline for:

1. converting natural language documents into propositional logic,
2. enriching and weighting constraints, and
3. translating user queries into executable logical formulas for downstream symbolic solving.

> Note: the codebase is organized around standalone stage-specific CLIs (`logify.py`, `weights.py`, `translate.py`).

---

## Quick Start

### Installation

```bash
cd code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Optional downloads (recommended for first run):

```bash
python -c "import stanza; stanza.install_corenlp()"
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

---

## Basic Usage

### Step 1: Logify a document/text into logic JSON

```bash
python from_text_to_logic/logify.py path/to/document.pdf --api-key "sk-..."

# custom model + output file
python from_text_to_logic/logify.py path/to/document.pdf \
  --api-key "sk-..." \
  --model gpt-5.2 \
  --reasoning-effort high \
  --output outputs/document.json
```

### Step 2: Assign weights and classify hard vs soft constraints

```bash
python from_text_to_logic/weights.py path/to/document.pdf outputs/document.json

# custom retrieval threshold + top-k
python from_text_to_logic/weights.py path/to/document.pdf outputs/document.json \
  --hardness-criterion 0.9 \
  --k 50
```

This writes `outputs/document_weighted.json`.

### Step 3: Translate a natural-language query into a propositional formula

```bash
python interface_with_user/translate.py \
  "Can employees share customer data with third parties?" \
  outputs/document_weighted.json \
  --api-key "sk-..."
```

---

## Commands

## `from_text_to_logic/logify.py` — Document/Text → Logic

Converts TXT/PDF/DOCX (or raw text) into a structured logic JSON.

```bash
python from_text_to_logic/logify.py <input> --api-key <key> [options]
```

**Required arguments**

| Argument | Description |
|---|---|
| `input` | Path to file (`.txt`, `.pdf`, `.docx`) OR raw text string |
| `--api-key` | OpenAI/OpenRouter API key |

**Optional arguments**

| Argument | Default | Description |
|---|---|---|
| `--model` | `gpt-5.2` | Logic conversion model |
| `--temperature` | `0.1` | Sampling temperature |
| `--reasoning-effort` | `medium` | `none`, `low`, `medium`, `high`, `xhigh` |
| `--max-tokens` | `42000` | Max completion tokens |
| `--output` | Auto-generated | Output JSON path |

**Output**
- `<stem>.json` (or custom path passed to `--output`)

---

## `from_text_to_logic/weights.py` — Logic JSON → Weighted JSON

Enriches logic structure and classifies constraints into hard/soft buckets.

```bash
python from_text_to_logic/weights.py <document_path> <logified_json> [options]
```

**Required arguments**

| Argument | Description |
|---|---|
| `pathfile` | Path to source document (`.txt/.pdf/.docx`) |
| `json_path` | Path to logified JSON from Step 1 |

**Optional arguments**

| Argument | Default | Description |
|---|---|---|
| `--hardness-criterion` | `0.9` | Threshold for hard constraints |
| `--k` | `50` | Retrieval top-k |
| `--chunk-size` | `512` | Chunk size |
| `--chunk-overlap` | `50` | Chunk overlap |
| `--quiet` | `False` | Suppress progress output |

**Output**
- `<stem>_weighted.json`

---

## `interface_with_user/translate.py` — NL Query → Formula

Translates a user query into a propositional formula (`P_i`, boolean connectives, implications, etc.) over the weighted logic structure.

```bash
python interface_with_user/translate.py <query> <weighted_json> --api-key <key> [options]
```

**Required arguments**

| Argument | Description |
|---|---|
| `query` | Natural-language query |
| `json_path` | Path to logified/weighted JSON |
| `--api-key` | OpenAI/OpenRouter API key |

**Optional arguments**

| Argument | Default | Description |
|---|---|---|
| `--model` | `openai/gpt-5-nano` | Query translation model |
| `--temperature` | `0.3` | Sampling temperature |
| `--reasoning-effort` | `medium` | Reasoning effort |
| `--max-tokens` | `42000` | Max completion tokens |
| `--k` | `50` | Retrieved proposition count |
| `--output` | stdout | Save JSON result |
| `--quiet` | `False` | Suppress wrapper prints |
| `--sbert-model-name` | `all-MiniLM-L6-v2` | Retrieval embedding model |

**Typical output (JSON)**

```json
{
  "formula": "P_12 & P_15",
  "translation": "Employees can share customer data and third-party transfer is authorized",
  "query": "Can employees share customer data with third parties?",
  "original_query": "Can employees share customer data with third parties?",
  "explanation": "Selected via NLI (Confidence: 0.81). ...",
  "confidence": 0.81,
  "sbert_confidence": 0.74
}
```

---

## Symbolic Solver (Programmatic)

The solver layer is available in `logic_solver/` (`LogicEncoder`, `LogicSolver`) and can be called from Python:

```python
import json
from logic_solver.maxsat import LogicSolver

with open("outputs/document_weighted.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

solver = LogicSolver(kb)
result = solver.query("P_12 & P_15")
print(result.to_dict())
```

---

## Pipeline Architecture

```
Document/Text
   │
   ▼
logify.py
(OpenIE optional + LLM conversion)
   │
   ▼
<stem>.json
   │
   ▼
weights.py
(enrichment + hard/soft classification)
   │
   ▼
<stem>_weighted.json
   │
   ├──► translate.py  (NL query -> formula)
   │
   └──► logic_solver/ (formula -> entailment/consistency via MaxSAT)
```

---

## Directory Structure

```text
code/
├── main.py                       # Scaffold entry point (not fully wired)
├── config/
│   └── retrieval_config.py       # Central model/retrieval settings
├── from_text_to_logic/
│   ├── logify.py                 # Stage 1: text/document to logic JSON
│   ├── weights.py                # Stage 2: enrichment + weighted constraints
│   ├── logic_converter.py
│   ├── openie_extractor.py
│   └── check_logic_structure.py
├── interface_with_user/
│   ├── translate.py              # Stage 3: NL query to logic formula
│   └── negation_detection.py
├── logic_solver/
│   ├── encoding.py               # Formula parsing + WCNF encoding
│   └── maxsat.py                 # RC2/PySAT solver wrapper
├── baseline_rag/                 # RAG baseline pipeline
├── baseline_logiclm_plus/        # LogicLM+ baseline
├── experiments/                  # Experiment scripts/results
├── prompts/                      # Prompt templates
├── requirements.txt
└── setup.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |

(You can also pass keys explicitly with `--api-key`.)

---

## Core Config Defaults (`config/retrieval_config.py`)

- **Logic conversion model:** `gpt-5.2`
- **Translation model:** `openai/gpt-5-nano`
- **SBERT model:** `all-MiniLM-L6-v2`
- **NLI reranker model:** `cross-encoder/nli-deberta-v3-large`
- **Hardness threshold:** `0.9`
- **Top-k retrieval:** `50`

---

## Troubleshooting

### Missing document dependencies

```bash
pip install PyMuPDF python-docx
```

### Missing NLP assets

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
python -c "import stanza; stanza.install_corenlp()"
```

### API/auth issues

```bash
echo $OPENAI_API_KEY
echo $OPENROUTER_API_KEY
```

### Weighted JSON not found

Run stages in order:

```bash
python from_text_to_logic/logify.py <input> --api-key <key>
python from_text_to_logic/weights.py <input> <generated_json>
```

---

## Related Documentation

- `code/baseline_rag/USAGE_GUIDE.md`
- `code/baseline_rag/README.md`
- `code/baseline_logiclm_plus/README_LOGICLM_PLUS.md`
- `code/baseline_logiclm_plus/HOW_TO_USE_LOGICLM_PLUS.md`
- `code/fol_vs_boolean/README.md`
