# Logify: Text to Logic Converter

Convert documents (PDF, DOCX, TXT) or raw text into structured propositional logic using OpenIE + LLM.

## Requirements

* **Python 3.8+**

* **Java 11+** (for Stanford CoreNLP)

* **OpenAI API key**

## Setup (macOS)

```bash
# 1. Install Java (if not installed) brew install openjdk@11 # 2. Install Python dependencies pip install -r requirements_openie.txt # 3. Set OpenAI API key export OPENAI_API_KEY="your-api-key-here"
```

## Usage

```bash
# Basic usage (from code directory) python3 from_text_to_logic/logify.py path/to/document.pdf --api-key $OPENAI_API_KEY # With custom settings python3 from_text_to_logic/logify.py document.pdf \ --api-key $OPENAI_API_KEY \ --model gpt-5.2 \ --reasoning-effort xhigh \ --max-tokens 64000 # Raw text input python3 from_text_to_logic/logify.py "Your text here" --api-key $OPENAI_API_KEY
```

## Output

Auto-generated filename: `{input}_logified_{model}_effort-{level}_tokens-{count}.JSON`

Example: `contract_logified_gpt-5_2_effort-xhigh_tokens-64000.JSON`

## Options

* `--model` - Model name (default: `gpt-5.2`)

* `--reasoning-effort` - Reasoning level: `none`, `low`, `medium`, `high`, `xhigh` (default: `medium`)

* `--max-tokens` - Max response tokens (default: `64000`)

* `--temperature` - Sampling temperature (default: `0.1`)

* `--output` - Custom output path (optional)
