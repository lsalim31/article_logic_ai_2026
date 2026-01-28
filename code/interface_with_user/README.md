# Interface with User

**Natural language query translation and result interpretation**

## Overview

Bridges natural language and propositional logic.

## Files

| File | Purpose | Status |
|------|---------|--------|
| `translate.py` | Query → formula translation | ✅ Implemented |
| `interpret.py` | Result → NL interpretation | 🚧 Stub |
| `refine.py` | Query refinement | 🚧 Stub |

## Main Module: `translate.py`

### Features

✅ **Yes/No Question Handling**
- Auto-detects: "Is...", "Can...", "Does...", "Will..."
- Converts to declarative statements using LLM

✅ **SBERT-Based Retrieval**
- Retrieves top-k propositions (default k=20)

✅ **LLM Translation**
- Translates to propositional formula
- Supports reasoning models (gpt-5.2, o1, o3)

## Quick Start

```bash
python translate.py "Is Alice a student?" logified.json --api-key sk-xxx
```

## Python API

```python
from interface_with_user.translate import translate_query

result = translate_query(
    query="Is Alice a student?",
    json_path="logified_weighted.json",
    api_key="sk-xxx"
)
```

## Dependencies

```bash
pip install sentence-transformers openai numpy
```
