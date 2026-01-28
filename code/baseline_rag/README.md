# Baseline RAG System

**Retrieval-Augmented Generation baseline for logical reasoning**

## Overview

Traditional RAG approach: SBERT retrieval + LLM reasoning.

## Architecture

```
Document → Chunker → SBERT → Retriever → LLM (CoT) → Answer
```

## Files

- `main.py` - Main orchestration
- `chunker.py` - Document chunking
- `retriever.py` - SBERT retrieval
- `reasoner.py` - Chain-of-Thought reasoning
- `evaluator.py` - Performance metrics

## Quick Start

```python
from baseline_rag.main import run_rag_pipeline

results = run_rag_pipeline(dataset_name='folio', model='gpt-4o')
```

## Comparison

| Aspect | RAG | Logic System |
|--------|-----|--------------|
| Reasoning | Soft (LLM) | Hard (SAT) |
| Guarantees | None | Provable |
| Cost | High (per query) | Low (logify once) |

## Documentation

- `USAGE_GUIDE.md` - Detailed usage
- `CODE_REPORT.md` - Implementation details
