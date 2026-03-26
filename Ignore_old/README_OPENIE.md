# OpenIE Extractor - Native Stanza Implementation

## Overview

Modernized OpenIE relation triple extractor using **native Stanza 1.7.0+** features:
- ✅ **Native Python coreference resolution** (no Java server for coref)
- ✅ **Universal Dependencies** with UPOS tags for better POS disambiguation
- ✅ **No confidence scores** (cleaner output)
- ✅ **13+ language support** through Stanza coref models
- ✅ **Lemmatized predicates** for normalized verb forms

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_openie.txt
```

This installs:
- `stanza>=1.7.0` - Native Python NLP library
- `torch>=1.13.0` - Neural network backend for Stanza
- `protobuf>=3.20.0` - Protocol buffers for CoreNLP client

### 2. Install Java (for CoreNLP OpenIE)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y default-jdk

# Verify
java -version  # Should show Java 8+
```

### 3. Download Stanza Models (First-Time Only)

```python
import stanza

# Download English coref models
stanza.download('en', processors='tokenize,coref')

# Download English dependency parsing models
stanza.download('en', processors='tokenize,pos,lemma,depparse')
```

Or let the extractor download automatically:

```python
from openie_extractor import OpenIEExtractor

extractor = OpenIEExtractor(download_models=True)  # Auto-download
```

---

## Quick Start

### Basic Usage

```python
from openie_extractor import OpenIEExtractor

# Initialize extractor
extractor = OpenIEExtractor(
    enable_coref=True,           # Native Stanza coref
    use_depparse_fallback=True,  # Stanza UD fallback
    download_models=False        # Set True for first run
)

# Extract triples
text = "Alice is a student. She studies mathematics."
triples = extractor.extract_triples(text)

# Print results
for triple in triples:
    print(f"({triple['subject']} ; {triple['predicate']} ; {triple['object']})")
    print(f"  Source: {triple['source']}")

# Output:
# (Alice ; be ; student)
#   Source: openie
# (Alice ; study ; mathematics)
#   Source: openie

# Clean up
extractor.close()
```

### Extract with Coreference Info

```python
result = extractor.extract_triples_with_coref_info(text)

# Access components
triples = result['triples']
coref_chains = result['coref_chains']
resolved_text = result['resolved_text']

# Print coref chains
for chain in coref_chains:
    print(f"Representative: {chain['representative']}")
    for mention in chain['mentions']:
        marker = "⭐" if mention['is_representative'] else "  "
        print(f"  {marker} {mention['text']} (sentence {mention['sentence_index']})")
```

---

## API Reference

### `OpenIEExtractor.__init__(...)`

Initialize the extractor with native Stanza and CoreNLP.

**Parameters:**
- `memory` (str): JVM memory for CoreNLP, default '8G'
- `timeout` (int): Server timeout in ms, default 60000
- `enable_coref` (bool): Use native Stanza coref, default True
- `use_depparse_fallback` (bool): Use Stanza UD fallback, default True
- `port` (int): CoreNLP server port, default 9000
- `language` (str): Stanza language code, default 'en'
- `download_models` (bool): Auto-download Stanza models, default False

### `extract_triples(text: str) -> List[Dict]`

Extract relation triples from text.

**Returns:** List of triple dictionaries:
```python
{
    'subject': str,        # Subject entity
    'predicate': str,      # Relation (lemmatized for fallback)
    'object': str,         # Object entity
    'sentence_index': int, # Sentence number (0-indexed)
    'source': str,         # 'openie' or 'stanza_depparse'
    'pos': str            # UPOS tag (only for fallback triples)
}
```

**Note:** No `confidence` field (removed in modernization)

### `extract_triples_with_coref_info(text: str) -> Dict`

Extract triples with detailed coreference information.

**Returns:** Dictionary:
```python
{
    'triples': List[Dict],      # Relation triples
    'coref_chains': List[Dict], # Coreference chains
    'resolved_text': str,       # Text with pronouns resolved
    'original_text': str        # Original input text
}
```

### `format_triples(triples: List[Dict]) -> str`

Format triples as tab-separated values.

**Returns:** String with format: `subject\tpredicate\tobject`

### `format_triples_verbose(triples: List[Dict]) -> str`

Format triples in human-readable format with source tags.

---

## Architecture

```
INPUT TEXT
    ↓
┌─────────────────────────────┐
│ Native Stanza Coref         │  ← Pure Python, transformer-based
│ - Replaces pronouns         │
│ - Returns coref chains      │
└─────────────────────────────┘
    ↓
RESOLVED TEXT
    ↓
┌─────────────────────────────┐
│ CoreNLP OpenIE              │  ← Java server, industry standard
│ - Extract triples           │
│ - No coref needed           │
└─────────────────────────────┘
    ↓
OPENIE TRIPLES
    ↓
┌─────────────────────────────┐
│ Stanza UD Fallback          │  ← Universal Dependencies
│ - UPOS for verb detection   │
│ - Lemmatized predicates     │
└─────────────────────────────┘
    ↓
FINAL TRIPLES (no confidence scores)
```

---

## POS Disambiguation: Verb vs Noun

### Problem: "studies" can be a noun or verb

- "Alice **studies** mathematics" → VERB
- "Multiple **studies** show..." → NOUN

### Old Approach (CoreNLP BasicDeps)

Penn Treebank tags: VB, VBZ, VBP, VBD, VBG, VBN, NN, NNS

```python
# Heuristic: check if starts with 'VB'
is_verb = pos.startswith('VB')

# Fallback: check lemma
is_potential_verb = pos in ['NNS', 'NN'] and lemma != word.lower()
```

**Issues:**
- "studies" sometimes tagged as NNS (plural noun)
- Requires manual fallback logic
- Not reliable across contexts

### New Approach (Stanza UPOS)

Universal POS: 17 tags, unambiguous VERB tag

```python
# Direct check
is_verb = word.upos == 'VERB'

# Always get lemma
predicate = word.lemma  # "studies" → "study"
```

**Benefits:**
- ✅ "studies" correctly tagged as VERB with lemma "study"
- ✅ Single tag for all verb forms
- ✅ Cross-lingual consistency
- ✅ No heuristics needed

---

## Multi-Language Support

### Supported Languages (Stanza Coref)

**European:** Catalan (ca), Czech (cs), German (de), English (en), Spanish (es), French (fr), Norwegian Bokmål (nb), Norwegian Nynorsk (nn), Polish (pl), Russian (ru)

**Middle Eastern:** Hebrew (he)

**South Asian:** Hindi (hi), Tamil (ta)

### Usage

```python
# Spanish example
extractor = OpenIEExtractor(
    language='es',
    download_models=True  # Download Spanish models
)

text_es = "María es estudiante. Ella estudia matemáticas."
triples = extractor.extract_triples(text_es)
```

---

## Comparison: Old vs New

| Feature | Old (CoreNLP Coref) | New (Native Stanza) |
|---------|---------------------|---------------------|
| **Coref Speed** | 2-3s | 1-2s |
| **Coref Implementation** | Java server | Pure Python |
| **POS Tags** | Penn Treebank (36) | Universal (17) |
| **Verb Detection** | Heuristic | Direct (UPOS) |
| **Languages** | English, Chinese | 13+ languages |
| **Confidence Scores** | Yes (arbitrary) | No (removed) |
| **Lemmatization** | Separate lookup | Built-in |
| **Debugging** | Java traces | Python traces |

---

## Troubleshooting

### "FileNotFoundError: en_coref.pt"

**Cause:** Stanza models not downloaded

**Solution:**
```python
import stanza
stanza.download('en', processors='tokenize,coref')
stanza.download('en', processors='tokenize,pos,lemma,depparse')
```

### "RuntimeError: Failed to initialize CoreNLP"

**Cause:** Java not installed or CoreNLP download failed

**Solution:**
```bash
# Install Java
sudo apt-get install default-jdk
java -version

# CoreNLP auto-downloads on first use
# If memory issues, reduce memory parameter:
extractor = OpenIEExtractor(memory='4G')
```

### Different triple counts from old version

**Cause:** Better POS tagging and coref resolution

**Expected behavior:** Stanza's transformer-based models are more accurate, leading to different (usually better) extractions.

---

## Examples

### Example 1: Pronoun Resolution

```python
text = "Alice is a student. She studies hard."

# With coref enabled (default)
triples = extractor.extract_triples(text)
# Output: (Alice, study, hard) - "she" resolved to "Alice"

# With coref disabled
extractor = OpenIEExtractor(enable_coref=False)
triples = extractor.extract_triples(text)
# Output: (she, study, hard) - pronoun not resolved
```

### Example 2: Verb/Noun Disambiguation

```python
text = "Alice studies mathematics. Research studies show results."

triples = extractor.extract_triples(text)

# First "studies" - VERB (study)
# (Alice, study, mathematics) [source: openie]

# Second "studies" - NOUN (not extracted as predicate)
# (Research studies, show, results) [source: openie]
```

### Example 3: Fallback Extraction

```python
text = "Bob runs quickly."

triples = extractor.extract_triples(text)

# OpenIE may miss this, fallback catches it:
# (Bob, run, quickly) [source: stanza_depparse, pos: VERB]
```

---

## Files

- `openie_extractor.py` - Main implementation (modernized)
- `requirements_openie.txt` - Python dependencies
- `README_OPENIE.md` - This file
- `/workspace/repo/artifacts/code/stanza_openie_demo.py` - Demo script
- `/workspace/repo/artifacts/code/test_stanza_extractor.py` - Verification tests
- `/workspace/repo/artifacts/stanza_openie_integration_summary.md` - Detailed changes

---

## References

- [Stanza Documentation](https://stanfordnlp.github.io/stanza/)
- [Stanza Coref](https://stanfordnlp.github.io/stanza/coref.html)
- [Universal Dependencies](https://universaldependencies.org/)
- [CoreNLP OpenIE](https://stanfordnlp.github.io/CoreNLP/openie.html)

---

## License

Part of the text-to-logic pipeline project.
