# Baseline: Logic-LM++

**Neuro-symbolic reasoning baseline using first-order logic and self-refinement**

> **For detailed documentation, see [README_LOGICLM_PLUS.md](README_LOGICLM_PLUS.md)**

## Quick Overview

This directory implements the **Logic-LM++** baseline from [Kirtania et al., ACL 2024](https://arxiv.org/abs/2407.02514v3).

### Key Differences from Our System

| Aspect | Logic-LM++ | Our System (Logify) |
|--------|-----------|---------------------|
| Logic Type | First-Order Logic | Zeroth-Order (Propositional) |
| Reasoning | Theorem proving | SAT/MaxSAT solving |
| Queries | Per-query | Logify once, query many |

## Quick Start

```bash
python run_logicbench_with_refinement.py --dataset folio --model gpt-5.2
```

## Documentation

- [README_LOGICLM_PLUS.md](README_LOGICLM_PLUS.md) - Full documentation
- [HOW_TO_USE_LOGICLM_PLUS.md](HOW_TO_USE_LOGICLM_PLUS.md) - Usage guide
