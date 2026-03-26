# From Text to Logic

A neuro-symbolic pipeline for converting natural language documents into structured propositional logic.

## Overview

This module implements a two-stage pipeline that transforms natural language text into a formal logical representation:

1. **Stage 1 (OpenIE Extraction)**: Extract relation triples using Stanford CoreNLP OpenIE with Stanza coreference resolution
2. **Stage 2 (LLM Conversion)**: Convert text + triples into structured propositional logic using an LLM

An optional post-processing step assigns confidence weights to soft constraints using SBERT retrieval and LLM logprob verification.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Input Document                           │
│                    (PDF, DOCX, TXT, or raw text)                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     logify.py (Orchestrator)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────┐      ┌─────────────────────────┐   │
│  │  openie_extractor.py    │      │  logic_converter.py     │   │
│  │  ──────────────────     │      │  ─────────────────      │   │
│  │  • Stanza Coref         │ ───▶ │  • Prompt Engineering   │   │
│  │  • CoreNLP OpenIE       │      │  • JSON Parsing         │   │
│  │  • DepParse Fallback    │      │  • OpenAI/OpenRouter    │   │
│  └─────────────────────────┘      └─────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      logified.json (Output)                     │
│         {primitive_props, hard_constraints, soft_constraints}   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼ (optional)
┌─────────────────────────────────────────────────────────────────┐
│                     weights.py (Post-processing)                │
│  ────────────────────────────────────────────────────────────   │
│  • SBERT Retrieval of relevant chunks                           │
│  • LLM YES/NO verification with logprobs                        │
│  • Binary softmax confidence scoring                            │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  logified_weighted.json (Output)                │
│              soft_constraints now include weight field          │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

| File | Purpose |
|------|---------|
| `logify.py` | Pipeline orchestrator; CLI entry point for text-to-logic conversion |
| `openie_extractor.py` | Stage 1: OpenIE triple extraction with coreference resolution |
| `logic_converter.py` | Stage 2: LLM-based conversion to propositional logic |
| `weights.py` | Post-processing: Assign confidence weights to soft constraints |
| `__init__.py` | Package marker |

## Requirements

### System Requirements

- **Python 3.8+**
- **Java 11+** (required for Stanford CoreNLP)

### Python Dependencies

```
openai>=1.0.0
stanza>=1.7.0
sentence-transformers
numpy
PyMuPDF (optional, for PDF support)
python-docx (optional, for DOCX support)
```

Install dependencies:
```bash
pip install -r requirements_openie.txt
```

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Usage

```bash
# Convert a document to logic
python from_text_to_logic/logify.py document.txt --api-key $OPENAI_API_KEY

# Assign weights to soft constraints
python from_text_to_logic/weights.py document.txt logified.json --api-key $OPENAI_API_KEY
```

### Python API

```python
from from_text_to_logic.logify import LogifyConverter

# Initialize converter
converter = LogifyConverter(api_key="sk-...")

# Convert text to logic
logic_structure = converter.convert_text_to_logic("Your text here...")

# Save output
converter.save_output(logic_structure, "output.json")

# Clean up
converter.close()
```

## Output Format

The pipeline produces a JSON structure with three main components:

```json
{
  "primitive_props": [
    {
      "id": "P_1",
      "translation": "Natural language meaning",
      "evidence": "Location in source text",
      "explanation": "Why this is atomic"
    }
  ],
  "hard_constraints": [
    {
      "id": "H_1",
      "formula": "P_1 ∧ P_2 ⟹ P_3",
      "translation": "Natural language meaning",
      "evidence": "Location in source text",
      "reasoning": "Why this is a hard constraint"
    }
  ],
  "soft_constraints": [
    {
      "id": "S_1",
      "formula": "P_1 ⟹ P_2",
      "translation": "Natural language meaning",
      "evidence": "Textual evidence or common-sense justification",
      "reasoning": "Why this is a soft constraint",
      "weight": [0.95, 0.12, 0.89]  // Added by weights.py
    }
  ]
}
```

## Logic Grammar

The output uses zeroth-order propositional logic:

| Symbol | Meaning |
|--------|---------|
| `P_1, P_2, ...` | Atomic propositions |
| `¬` | Negation (NOT) |
| `∧` | Conjunction (AND) |
| `∨` | Disjunction (OR) |
| `⟹` | Implication (IF...THEN) |
| `⟺` | Biconditional (IF AND ONLY IF) |

## Related Documentation

- `HOW_TO_USE_FROM_TEXT_TO_LOGIC.md` - Detailed usage guide for LLM agents
- `README_OPENIE.md` - OpenIE extractor documentation
- `weights_how_it_works.md` - Detailed explanation of the weighting algorithm

## License

See repository root for license information.
