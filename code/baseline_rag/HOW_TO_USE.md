# How to Use: Baseline RAG System

Complete guide at: `USAGE_GUIDE.md`

## Quick Start

```bash
pip install sentence-transformers openai datasets
python baseline_rag/run_experiment_logicbench_rag.py --dataset folio
```

## Basic Usage

```python
from baseline_rag.main import run_rag_pipeline

results = run_rag_pipeline(dataset_name='folio', model='gpt-4o')
print(f"Accuracy: {results['accuracy']:.2%}")
```

See `USAGE_GUIDE.md` and `CODE_REPORT.md` for detailed documentation.
