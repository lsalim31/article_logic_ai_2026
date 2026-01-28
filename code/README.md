# Logify: Neuro-Symbolic Reasoning System

This directory contains the implementation of the Logify framework for converting natural language documents into propositional logic and answering queries using symbolic reasoning.

## Quick Start

### Installation

```bash
cd code
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

### Basic Usage

**Step 1: Logify a document (convert to weighted propositional logic)**

```bash
# Using environment variable for API key
export OPENROUTER_API_KEY="sk-or-v1-..."

python main.py logify --fpath path/to/document.pdf

# Or with explicit key
python main.py logify --fpath path/to/document.pdf --key "sk-or-v1-..."

# With custom output directory
python main.py logify --fpath document.pdf --opath ./outputs --key "sk-..."
```

**Step 2: Query the logified document**

```bash
python main.py query --fpath document.pdf --query "Is X allowed?"

# With explicit JSON path
python main.py query --fpath document.pdf --jpath outputs/document_weighted.json --query "Can users share data?"
```

## Commands

### `logify` - Convert Document to Logic

Converts a document (PDF, DOCX, or TXT) into a weighted propositional logic structure.

```bash
python main.py logify --fpath <document> [options]
```

**Required Arguments:**
| Argument | Description |
|----------|-------------|
| `--fpath` | Path to input document (PDF, DOCX, or TXT) |

**Optional Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `--opath` | Same as input | Output directory for JSON files |
| `--key` | Env var | API key (or set `OPENAI_API_KEY`/`OPENROUTER_API_KEY`) |
| `--model` | `gpt-5.2` | Model for logic conversion |
| `--temperature` | `0.1` | Sampling temperature (ignored for reasoning models) |
| `--reasoning-effort` | `medium` | Reasoning effort: `none`, `low`, `medium`, `high`, `xhigh` |
| `--max-tokens` | `128000` | Maximum tokens in LLM response |
| `--weights-model` | `gpt-4o` | Model for weight assignment (must support logprobs) |
| `--k` | `10` | Number of chunks to retrieve for weight assignment |
| `--quiet` | False | Suppress progress messages |

**Output Files:**
- `{document_stem}.json` - Logified structure (propositions + constraints)
- `{document_stem}_weighted.json` - Logified structure with soft constraint weights

### `query` - Query a Logified Document

Ask natural language questions about a logified document.

```bash
python main.py query --fpath <document> --query "<question>" [options]
```

**Required Arguments:**
| Argument | Description |
|----------|-------------|
| `--fpath` | Path to original document (used to find weighted JSON) |
| `--query` | Natural language query |

**Optional Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `--jpath` | Auto-derived | Path to weighted JSON file |
| `--key` | Env var | API key |
| `--model` | `gpt-5.2` | Model for query translation |
| `--temperature` | `0.1` | Sampling temperature |
| `--reasoning-effort` | `medium` | Reasoning effort for reasoning models |
| `--max-tokens` | `64000` | Maximum tokens in response |
| `--k` | `20` | Number of propositions to retrieve |
| `--quiet` | False | Suppress progress (only output JSON) |

**Output (JSON):**
```json
{
  "query": "Is data sharing allowed?",
  "converted_query": "Data sharing is allowed",
  "formula": "P_3 ∨ P_5",
  "formula_translation": "Data sharing is permitted or authorized",
  "formula_explanation": "Query maps to propositions about data sharing permissions",
  "answer": "TRUE",
  "confidence": 0.85,
  "explanation": "Query is entailed by the knowledge base"
}
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LOGIFY MODE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Document (PDF/DOCX/TXT)                                                │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐  │
│  │ OpenIE Extract  │────▶│  LLM Logify     │────▶│  {stem}.json     │  │
│  │ (Stanza)        │     │  (gpt-5.2)      │     │                  │  │
│  └─────────────────┘     └─────────────────┘     └────────┬─────────┘  │
│                                                            │            │
│                                                            ▼            │
│                          ┌─────────────────┐     ┌──────────────────┐  │
│                          │  SBERT + LLM    │────▶│{stem}_weighted   │  │
│                          │  Weight Assign  │     │    .json         │  │
│                          │  (gpt-4o)       │     │                  │  │
│                          └─────────────────┘     └──────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           QUERY MODE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Natural Language Query + Weighted JSON                                 │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐  │
│  │ SBERT Retrieve  │────▶│  LLM Translate  │────▶│  Propositional   │  │
│  │ Propositions    │     │  to Formula     │     │  Formula         │  │
│  └─────────────────┘     └─────────────────┘     └────────┬─────────┘  │
│                                                            │            │
│                                                            ▼            │
│                          ┌─────────────────┐     ┌──────────────────┐  │
│                          │  MaxSAT Solver  │────▶│  JSON Result     │  │
│                          │  (RC2/PySAT)    │     │  (answer + conf) │  │
│                          └─────────────────┘     └──────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
code/
├── main.py                      # Unified CLI entry point
│
├── from_text_to_logic/          # Stage 1: Document → Logic
│   ├── logify.py                # Two-stage pipeline orchestrator
│   ├── openie_extractor.py      # OpenIE triple extraction (Stanza)
│   ├── logic_converter.py       # LLM-based logic conversion
│   └── weights.py               # Soft constraint weight assignment
│
├── logic_solver/                # Stage 2: Symbolic Reasoning
│   ├── encoding.py              # Propositional logic → WCNF encoding
│   └── maxsat.py                # MaxSAT solver interface (RC2)
│
├── interface_with_user/         # Stage 3: Query Interface
│   └── translate.py             # NL query → propositional formula
│
├── baseline_rag/                # Baseline: RAG + Chain-of-Thought
├── baseline_logiclm_plus/       # Baseline: Logic-LM++
│
├── prompts/                     # LLM prompt templates
├── outputs/                     # Generated outputs
├── requirements.txt             # Python dependencies
└── setup.py                     # Package installation
```

## Examples

### Example 1: Logify a Policy Document

```bash
# Convert policy document to logic
python main.py logify --fpath policies/data_policy.pdf --opath outputs/

# Output files:
#   outputs/data_policy.json
#   outputs/data_policy_weighted.json
```

### Example 2: Query the Policy

```bash
# Ask a yes/no question
python main.py query \
    --fpath policies/data_policy.pdf \
    --jpath outputs/data_policy_weighted.json \
    --query "Can employees share customer data with third parties?"

# Output:
# {
#   "query": "Can employees share customer data with third parties?",
#   "converted_query": "Employees can share customer data with third parties",
#   "formula": "P_12 ∧ P_15",
#   "answer": "FALSE",
#   "confidence": 0.92,
#   "explanation": "Query is contradicted by the knowledge base"
# }
```

### Example 3: Using OpenRouter

```bash
# Set OpenRouter API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# Logify with specific models
python main.py logify \
    --fpath document.txt \
    --model gpt-5.2 \
    --weights-model gpt-4o \
    --reasoning-effort high
```

### Example 4: Quiet Mode for Scripting

```bash
# Only output JSON (suppress progress messages)
python main.py query \
    --fpath doc.pdf \
    --query "Is X permitted?" \
    --quiet > result.json
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (primary) |
| `OPENROUTER_API_KEY` | OpenRouter API key (fallback) |

## Supported Models

### For Logic Conversion (`--model`)
- `gpt-5.2` (default) - Reasoning model with extended thinking
- `o1`, `o3` - OpenAI reasoning models
- `gpt-4o`, `gpt-4-turbo` - Standard models

### For Weight Assignment (`--weights-model`)
- `gpt-4o` (default) - Required: must support logprobs
- Note: Reasoning models (gpt-5.x, o1, o3) do NOT support logprobs

## Output Schema

### Logified Structure (`{stem}.json`)

```json
{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "The user consents to data collection",
      "evidence": "Section 2.1: 'Users must provide explicit consent...'",
      "explanation": "Atomic proposition representing user consent"
    }
  ],
  "hard_constraints": [
    {
      "id": "H_1",
      "formula": "P_1 ⟹ P_2",
      "translation": "If user consents, data may be collected",
      "evidence": "Section 2.1",
      "reasoning": "Explicit conditional in the document"
    }
  ],
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "P_3 ⟹ P_4",
      "translation": "Data is typically anonymized before sharing",
      "evidence": "Section 3.2: 'We generally anonymize...'",
      "reasoning": "Hedged language ('generally') indicates soft constraint"
    }
  ]
}
```

### Weighted Structure (`{stem}_weighted.json`)

Same as above, but soft constraints include weights:

```json
{
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "P_3 ⟹ P_4",
      "translation": "Data is typically anonymized before sharing",
      "weight": [0.89, 0.15, 0.86]
    }
  ]
}
```

Weight array: `[P(YES|original), P(YES|negated), confidence]`

## Troubleshooting

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# For PDF support
pip install PyMuPDF

# For DOCX support
pip install python-docx
```

### API Key Errors

```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Or pass explicitly
python main.py logify --fpath doc.pdf --key "sk-or-v1-..."
```

### Weighted JSON Not Found

```bash
# Error: Weighted JSON file not found: doc_weighted.json
# Solution: Run logify first
python main.py logify --fpath doc.pdf
python main.py query --fpath doc.pdf --query "..."
```

## Related Documentation

- [from_text_to_logic/HOW_TO_USE_FROM_TEXT_TO_LOGIC.md](from_text_to_logic/HOW_TO_USE_FROM_TEXT_TO_LOGIC.md) - Detailed logify/weights API
- [interface_with_user/HOW_TO_USE.md](interface_with_user/HOW_TO_USE.md) - Query translation details
- [logic_solver/HOW_TO_USE.md](logic_solver/HOW_TO_USE.md) - Solver API and query syntax
- [baseline_rag/USAGE_GUIDE.md](baseline_rag/USAGE_GUIDE.md) - RAG baseline
- [baseline_logiclm_plus/README_LOGICLM_PLUS.md](baseline_logiclm_plus/README_LOGICLM_PLUS.md) - Logic-LM++ baseline
