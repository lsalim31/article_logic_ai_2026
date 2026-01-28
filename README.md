# Logify: Neuro-Symbolic Reasoning Framework

A neuro-symbolic reasoning framework that translates natural language documents into propositional logic with hard and soft constraints, enabling efficient **"logify once, query many"** reasoning via MaxSAT solvers.

## Quick Start

### Installation

```bash
cd code
pip install -r requirements.txt
pip install -e .  # Optional: install as package
```

### Usage

**Step 1: Logify a document**

Convert a document (PDF, DOCX, or TXT) into weighted propositional logic:

```bash
# Set your API key (OpenRouter or OpenAI)
export OPENROUTER_API_KEY="sk-or-v1-..."

# Logify the document
python main.py logify --fpath path/to/document.pdf

# With custom output directory
python main.py logify --fpath document.pdf --opath ./outputs
```

This produces two files:
- `document.json` - Logified structure (propositions + constraints)
- `document_weighted.json` - With soft constraint confidence weights

**Step 2: Query the document**

Ask natural language questions:

```bash
python main.py query --fpath document.pdf --query "Is data sharing allowed?"
```

Output (JSON):
```json
{
  "query": "Is data sharing allowed?",
  "formula": "P_3 ∨ P_5",
  "answer": "TRUE",
  "confidence": 0.85,
  "explanation": "Query is entailed by the knowledge base"
}
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LOGIFY                                      │
│                                                                          │
│   Document ──▶ OpenIE ──▶ LLM ──▶ Logic JSON ──▶ SBERT+LLM ──▶ Weighted │
│   (PDF/DOCX)   (Stanza)  (gpt-5.2) (props+constraints) (gpt-4o)  JSON   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              QUERY                                       │
│                                                                          │
│   NL Query ──▶ SBERT Retrieve ──▶ LLM Translate ──▶ MaxSAT ──▶ Answer   │
│               (top-k props)      (to formula)      (RC2)     (JSON)     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
repo/
├── README.md                      # This file
├── code/                          # Implementation
│   ├── main.py                    # Unified CLI entry point
│   │
│   ├── from_text_to_logic/        # Stage 1: Document → Logic
│   │   ├── logify.py              # Two-stage pipeline orchestrator
│   │   ├── openie_extractor.py    # OpenIE triple extraction (Stanza)
│   │   ├── logic_converter.py     # LLM-based logic conversion
│   │   └── weights.py             # SBERT + LLM logprob weight assignment
│   │
│   ├── logic_solver/              # Stage 2: Symbolic Reasoning
│   │   ├── encoding.py            # Propositional logic → WCNF encoding
│   │   └── maxsat.py              # MaxSAT solver (RC2/PySAT)
│   │
│   ├── interface_with_user/       # Stage 3: Query Interface
│   │   └── translate.py           # NL query → propositional formula
│   │
│   ├── baseline_rag/              # Baseline: RAG + Chain-of-Thought
│   ├── baseline_logiclm_plus/     # Baseline: Logic-LM++
│   │
│   ├── prompts/                   # LLM prompt templates
│   ├── outputs/                   # Generated outputs
│   ├── requirements.txt           # Python dependencies
│   └── setup.py                   # Package installation
│
├── article/                       # Paper manuscript and appendix
└── artifacts/                     # Generated artifacts
```

## Command Reference

### `logify` - Convert Document to Logic

```bash
python main.py logify --fpath <document> [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--fpath` | Required | Input document (PDF, DOCX, TXT) |
| `--opath` | Same dir | Output directory for JSON files |
| `--key` | Env var | API key (or set `OPENROUTER_API_KEY`) |
| `--model` | `gpt-5.2` | Model for logic conversion |
| `--weights-model` | `gpt-4o` | Model for weight assignment |
| `--reasoning-effort` | `medium` | `none`/`low`/`medium`/`high`/`xhigh` |
| `--k` | `10` | Chunks to retrieve for weighting |
| `--quiet` | False | Suppress progress messages |

### `query` - Query a Logified Document

```bash
python main.py query --fpath <document> --query "<question>" [options]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--fpath` | Required | Original document path |
| `--query` | Required | Natural language query |
| `--jpath` | Auto | Path to weighted JSON (auto-derived from fpath) |
| `--key` | Env var | API key |
| `--model` | `gpt-5.2` | Model for query translation |
| `--k` | `20` | Propositions to retrieve |
| `--quiet` | False | Suppress progress (JSON only) |

## Output Schema

### Logified Structure

```json
{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "Users must provide consent",
      "evidence": "Section 2.1: '...'",
      "explanation": "Atomic proposition"
    }
  ],
  "hard_constraints": [
    {
      "id": "H_1",
      "formula": "P_1 ⟹ P_2",
      "translation": "Consent implies data collection",
      "reasoning": "Explicit conditional"
    }
  ],
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "P_3 ⟹ P_4",
      "translation": "Data is typically anonymized",
      "weight": [0.89, 0.15, 0.86]
    }
  ]
}
```

### Query Result

```json
{
  "query": "Can data be shared?",
  "formula": "P_5 ∨ P_8",
  "answer": "TRUE",
  "confidence": 0.85,
  "explanation": "Query is entailed by the knowledge base"
}
```

## Key Features

- **Logify Once, Query Many**: Convert document once, answer unlimited questions
- **Hard + Soft Constraints**: Distinguish definite rules from probabilistic tendencies
- **Evidence-Based Weights**: SBERT retrieval + LLM logprobs for confidence scoring
- **MaxSAT Reasoning**: Optimal weighted constraint satisfaction via RC2 solver
- **Yes/No Question Handling**: Automatic conversion to declarative statements
- **Multiple Document Formats**: PDF, DOCX, TXT support

## Requirements

```bash
pip install -r code/requirements.txt
```

Core dependencies:
- `python-sat` - PySAT MaxSAT solver
- `stanza` - OpenIE extraction
- `openai` - LLM API client
- `sentence-transformers` - SBERT retrieval
- `PyMuPDF` - PDF reading
- `python-docx` - DOCX reading

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key (alternative) |

## Baselines

### RAG + Chain-of-Thought

```bash
cd code/baseline_rag
python main.py --dataset folio --output results.json
```

See [code/baseline_rag/USAGE_GUIDE.md](code/baseline_rag/USAGE_GUIDE.md)

### Logic-LM++

```bash
cd code/baseline_logiclm_plus
python main.py --dataset folio --output results.json
```

See [code/baseline_logiclm_plus/README_LOGICLM_PLUS.md](code/baseline_logiclm_plus/README_LOGICLM_PLUS.md)

## Supported Datasets

| Dataset | Task | Labels |
|---------|------|--------|
| FOLIO | FOL reasoning | True/False/Uncertain |
| ProofWriter | Proof generation | Proved/Disproved/Unknown |
| ContractNLI | Contract entailment | Entailed/Contradicted/NotMentioned |

## Documentation

- [code/README.md](code/README.md) - Detailed code documentation
- [code/from_text_to_logic/HOW_TO_USE_FROM_TEXT_TO_LOGIC.md](code/from_text_to_logic/HOW_TO_USE_FROM_TEXT_TO_LOGIC.md) - Logify/weights API
- [code/interface_with_user/HOW_TO_USE.md](code/interface_with_user/HOW_TO_USE.md) - Query translation
- [code/logic_solver/HOW_TO_USE.md](code/logic_solver/HOW_TO_USE.md) - Solver API

## Citation

If you use this code, please cite the accompanying paper (details in `article/`).

## License

See LICENSE file for details.
