# How to Use: Interface with User

## Quick Start

```python
from interface_with_user.translate import translate_query

result = translate_query(
    query="Is Alice a student?",
    json_path="logified_weighted.json",
    api_key="sk-or-v1-xxx"
)

print(f"Formula: {result['formula']}")
```

## Command Line

```bash
python code/interface_with_user/translate.py \
    "Is Alice a student?" \
    logified_weighted.json \
    --api-key sk-xxx
```

## Yes/No Questions

Automatically handles Yes/No questions:
- "Is Alice a student?" → "Alice is a student"
- "Can info be shared?" → "Info can be shared"
- "Does the policy allow X?" → "The policy allows X"

## Full Pipeline

```python
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver

# Translate query
translation = translate_query(query, logified_path, api_key)

# Solve
solver = LogicSolver(logified)
result = solver.query(translation['formula'])

print(f"Answer: {result.answer}")
print(f"Confidence: {result.confidence:.2f}")
```
