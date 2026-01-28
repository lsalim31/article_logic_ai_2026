# How to Use: Prompts

## Main Prompt: `prompt_logify`

The primary system prompt for text-to-logic conversion.

## Loading Prompt

```python
# Load prompt
with open('code/prompts/prompt_logify', 'r') as f:
    prompt = f.read()

# Use in logification
from from_text_to_logic.logic_converter import LogicConverter

converter = LogicConverter(api_key=api_key)
# Prompt is automatically loaded
```

## Customizing for Domains

```python
# Load base prompt
with open('code/prompts/prompt_logify', 'r') as f:
    base_prompt = f.read()

# Add domain context
legal_context = """
DOMAIN: Legal Contracts
Focus on:
- Obligations vs permissions
- Temporal constraints
- Exception clauses
"""

custom_prompt = base_prompt.replace('ROLE', f'ROLE\n{legal_context}')

# Use custom prompt
converter = LogicConverter(api_key=api_key)
converter.system_prompt = custom_prompt
```

## Prompt Structure

1. **ROLE**: Defines LLM identity
2. **INTENDED TASK**: What to extract
3. **METHODOLOGY**: 5-step process
4. **GUIDELINES**: Key principles
5. **GRAMMAR**: Logic operators
6. **OUTPUT**: JSON schema
7. **EXEMPLARS**: Quality examples

See `README.md` for detailed documentation.

## Version Control

```bash
# Before modifying
cp code/prompts/prompt_logify code/prompts/prompt_logify.backup

# Edit and test
nano code/prompts/prompt_logify
python test_prompt.py
```
