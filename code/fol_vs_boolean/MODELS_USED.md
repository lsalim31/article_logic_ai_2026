# Models Used in FOL vs Boolean Extraction Experiment

This document describes which models are used by each extractor in the `fol_vs_boolean` experiment.

## Overview

The experiment compares two extraction approaches:
1. **Propositional (Boolean) Extraction** - Uses GPT-5.2 with reasoning
2. **FOL (First-Order Logic) Extraction** - Uses GPT-4

---

## 1. Propositional Extractor

### Model Configuration

**Location**: `code/from_text_to_logic/logify.py`

**Default Model**: `gpt-5.2` (OpenAI's reasoning model)

**Key Parameters**:
```python
def __init__(self, api_key: str,
             model: str = "gpt-5.2",           # Default model
             temperature: float = 0.1,          # Low temperature for consistency
             reasoning_effort: str = "medium",  # Reasoning depth
             max_tokens: int = 128000):         # Max output tokens
```

**Declared in**:
- Primary: `code/from_text_to_logic/logify.py` (line 104)
- Used by: `code/from_text_to_logic/logic_converter.py` (line 18)

**Supported Models**:
- `gpt-5.2` (default, with extended thinking)
- `o1`, `o3` (reasoning models)
- `gpt-4o`, `gpt-4-turbo` (standard models)

**Special Features**:
- Uses reasoning tokens for complex logic extraction
- `reasoning_effort` parameter controls thinking depth (none/low/medium/high/xhigh)
- Uses "developer" role for system prompts (GPT-5.2 requirement)

---

## 2. FOL Extractor

### Model Configuration

**Location**: `code/baseline_logiclm_plus/config.py`

**Default Model**: `gpt-4`

**Key Parameters**:
```python
MODEL_NAME = "gpt-4"  # Standard GPT-4 (not gpt-5.2)
TEMPERATURE = 0       # Deterministic output
```

**Declared in**:
- Primary: `code/baseline_logiclm_plus/config.py` (line 25)
- Used by:
  - `code/baseline_logiclm_plus/formalizer.py` (line 122)
  - `code/baseline_logiclm_plus/main.py` (line 129)
  - `code/baseline_logiclm_plus/refiner.py` (line 113)

**Supported Models**:
- `gpt-4` (default, best performance)
- `gpt-4-turbo` (faster, slightly lower accuracy)
- `gpt-3.5-turbo` (cheaper, lower accuracy)

**Special Features**:
- Uses symbolic refinement with Z3 solver
- Iterative formalization with error feedback
- Temperature = 0 for deterministic FOL generation

---

## 3. Model Invocation in Experiment Scripts

### `run_logicbench_experiment.py`

**Propositional**:
```python
# Line 40-46
api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
_logify_converter = LogifyConverter(api_key=api_key)
# Uses default: gpt-5.2
```

**FOL**:
```python
# Line 97
result = formalize_to_fol(text, query)
# Uses default from config.py: gpt-4
```

### `run_logicbench_fol_experiment.py`

Same model configuration as above (identical code).

---

## 4. Key Differences Between Models

| Aspect | Propositional (GPT-5.2) | FOL (GPT-4) |
|--------|------------------------|-------------|
| **Model** | gpt-5.2 | gpt-4 |
| **Reasoning** | Extended thinking enabled | Standard generation |
| **Temperature** | 0.1 | 0 |
| **Reasoning Effort** | medium (configurable) | N/A |
| **Max Tokens** | 128,000 | Default (~4096) |
| **Special Features** | Reasoning tokens, chain-of-thought | Symbolic refinement with Z3 |
| **Cost** | Higher (reasoning tokens) | Lower (standard tokens) |
| **Output Format** | Primitive props + constraints | FOL predicates + premises |

---

## 5. Why Different Models?

### Propositional uses GPT-5.2 because:
- Complex logic extraction benefits from extended reasoning
- Handles soft/hard constraints with nuanced thinking
- Better at capturing implicit logical relationships
- Can reason through ambiguous propositional structures

### FOL uses GPT-4 because:
- Symbolic FOL syntax is well-defined and deterministic
- Works well with iterative refinement (symbolic feedback)
- Z3 solver integration requires precise FOL syntax
- GPT-4 is sufficient for structured logical formalization

---

## 6. How to Change Models

### To change Propositional model:

**Option 1**: Modify default in code
```python
# In code/from_text_to_logic/logify.py, line 104
def __init__(self, api_key: str, model: str = "gpt-4o", ...):  # Change from gpt-5.2
```

**Option 2**: Pass model parameter
```python
converter = LogifyConverter(api_key=api_key, model="o1", reasoning_effort="high")
```

### To change FOL model:

**Option 1**: Modify config
```python
# In code/baseline_logiclm_plus/config.py, line 25
MODEL_NAME = "gpt-4-turbo"  # Change from gpt-4
```

**Option 2**: Pass model_name parameter
```python
result = formalize_to_fol(text, query, model_name="gpt-4-turbo")
```

---

## 7. Cost Implications

### Propositional (GPT-5.2):
- **Input**: ~$5/million tokens
- **Output**: ~$15/million tokens
- **Reasoning tokens**: ~$60/million tokens (hidden reasoning)
- **Typical cost per example**: $0.02-0.10 (depending on reasoning depth)

### FOL (GPT-4):
- **Input**: ~$30/million tokens
- **Output**: ~$60/million tokens
- **No reasoning tokens**
- **Typical cost per example**: $0.01-0.03

**For 20 examples**:
- Propositional: ~$0.40-2.00
- FOL: ~$0.20-0.60
- **Total: ~$0.60-2.60 per run**

---

## 8. API Key Configuration

Both models can use either:
- `OPENROUTER_API_KEY` (checked first)
- `OPENAI_API_KEY` (fallback)

Set with:
```bash
export OPENROUTER_API_KEY='your-key-here'
# or
export OPENAI_API_KEY='your-key-here'
```

---

## Summary

- **Propositional extractor**: GPT-5.2 (reasoning model) declared in `logify.py`
- **FOL extractor**: GPT-4 (standard model) declared in `config.py`
- Both models are invoked indirectly through their respective modules
- The `fol_vs_boolean` scripts themselves don't declare models - they import and use defaults
