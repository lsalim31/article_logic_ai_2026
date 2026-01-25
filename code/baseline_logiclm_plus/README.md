# LOGIC-LM++ Baseline Implementation

Implementation of LOGIC-LM++ baseline for comparison with logification system.

## Overview

LOGIC-LM++ is a neuro-symbolic reasoning system that:
1. Translates natural language to propositional logic (SAT)
2. Iteratively refines formulations via LLM-based self-correction
3. Solves using SAT solver to determine entailment

This implementation follows the "as-published" methodology from the LOGIC-LM++ paper (2024), including:
- Per-query formalization (no caching)
- Fixed 3 refinement iterations
- Pairwise comparison for candidate selection
- SAT-only formulation (propositional logic)

## Architecture

```
Input (text + query)
    ↓
[Formalizer] NL → SAT
    ↓
[Refiner] Multi-step refinement (3 iterations)
    ↓
[Solver] SAT solving + entailment checking
    ↓
Output (Entailed/Contradicted/Unknown)
```

## Modules

- **config.py**: Configuration and prompt templates
- **formalizer.py**: Natural language → SAT translation
- **refiner.py**: Iterative refinement with pairwise comparison
- **solver_interface.py**: SAT solver integration (python-sat)
- **evaluator.py**: Metrics computation
- **main.py**: End-to-end pipeline orchestration
- **test_logiclm.py**: Unit tests

## Key Design Decisions

1. **SAT only** (not FOL): Matches propositional logic system
2. **No caching**: Per-query formalization (as-published)
3. **Fixed iterations**: Always 3 refinement steps, no early stopping
4. **Failure handling**: Malformed outputs counted as failures, no retry
5. **JSON output**: Structured LLM responses for reliable parsing

## Comparison to Other Baselines

| Feature | RAG Baseline | LOGIC-LM++ | Main System |
|---------|--------------|------------|-------------|
| Reasoning | Neural (LLM) | Symbolic (SAT) | Symbolic (SAT + soft) |
| Caching | Retrieval index | None | Full logification |
| Soft constraints | No | No | Yes |
| Iterations | 1-shot | 3 refinement | Self-refinement |
| LLM calls/query | 1 | ~10 | ~1 (amortized) |

## Usage

See main.py for pipeline execution.

## Metrics Tracked

**Accuracy**:
- Overall accuracy
- Per-class precision/recall/F1
- Confusion matrix

**LOGIC-LM++ Specific**:
- Formalization success rate
- Solver execution rate
- Average refinement iterations
- Refinement improvement rate

**Efficiency**:
- Time per query (total, breakdown)
- LLM calls per query
- Token usage and cost
