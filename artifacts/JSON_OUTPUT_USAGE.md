# JSON Output Format - Usage Guide

## Overview

The `format_triples_json()` method outputs clean JSON with only essential triple data:
- `subject`: The subject of the relation
- `predicate`: The relation/verb
- `object`: The object of the relation
- `sentence_index`: Which sentence this triple came from (0-based)

**Note**: The `source` field (openie, stanza_depparse) and `pos` field are removed for cleaner output.

---

## Output Format

```json
[
  {
    "subject": "hospital 's emergency triage protocol",
    "predicate": "requires",
    "object": "immediate attention for patients presenting with chest pain",
    "sentence_index": 0
  },
  {
    "subject": "attention",
    "predicate": "is",
    "object": "immediate",
    "sentence_index": 0
  }
]
```

---

## Usage Examples

### Basic Usage

```python
from openie_extractor import OpenIEExtractor

text = "The hospital requires immediate attention for patients with chest pain."

with OpenIEExtractor(enable_coref=True) as extractor:
    triples = extractor.extract_triples(text)

    # Get JSON output
    json_output = extractor.format_triples_json(triples)
    print(json_output)
```

### Save to File

```python
from openie_extractor import OpenIEExtractor

text = "Your input text here..."

with OpenIEExtractor(enable_coref=True) as extractor:
    triples = extractor.extract_triples(text)

    # Save to file
    with open('output.json', 'w') as f:
        f.write(extractor.format_triples_json(triples))
```

### Compact vs Readable

```python
# Readable (default, indent=2)
json_readable = extractor.format_triples_json(triples, indent=2)

# Compact (no indentation)
json_compact = extractor.format_triples_json(triples, indent=0)

# More indentation
json_extra = extractor.format_triples_json(triples, indent=4)
```

### Load and Process

```python
import json
from openie_extractor import OpenIEExtractor

text = "Your text..."

with OpenIEExtractor(enable_coref=True) as extractor:
    triples = extractor.extract_triples(text)
    json_str = extractor.format_triples_json(triples)

    # Parse back to Python objects
    triples_list = json.loads(json_str)

    # Process
    for triple in triples_list:
        print(f"{triple['subject']} --{triple['predicate']}--> {triple['object']}")
```

---

## Comparison with Other Formats

### JSON (Clean)
```json
{
  "subject": "hospital",
  "predicate": "requires",
  "object": "attention",
  "sentence_index": 0
}
```

### Raw Dict (Internal)
```python
{
  'subject': 'hospital',
  'predicate': 'requires',
  'object': 'attention',
  'sentence_index': 0,
  'source': 'openie'  # ← Removed in JSON output
}
```

### TSV Format
```
hospital	requires	attention
```

### Verbose Format
```
1. (hospital) --[requires]--> (attention)  [src: openie]
```

---

## Complete Example

```python
from openie_extractor import OpenIEExtractor
import json

# Medical triage text
text = """The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez believes that patients over 65 should always receive an ECG regardless of symptoms.
The official guidelines only mandate this when cardiac history is documented."""

# Extract and format
with OpenIEExtractor(enable_coref=True) as extractor:
    # Extract triples
    triples = extractor.extract_triples(text)

    # Get JSON output
    json_output = extractor.format_triples_json(triples)

    # Save to file
    with open('triples.json', 'w', encoding='utf-8') as f:
        f.write(json_output)

    # Also parse and process
    triples_list = json.loads(json_output)

    print(f"Extracted {len(triples_list)} triples")

    # Group by sentence
    by_sentence = {}
    for triple in triples_list:
        sent_idx = triple['sentence_index']
        if sent_idx not in by_sentence:
            by_sentence[sent_idx] = []
        by_sentence[sent_idx].append(triple)

    for sent_idx, sent_triples in sorted(by_sentence.items()):
        print(f"\nSentence {sent_idx}: {len(sent_triples)} triples")
        for t in sent_triples:
            print(f"  ({t['subject']}) --[{t['predicate']}]--> ({t['object']})")
```

**Output:**
```
Extracted 16 triples

Sentence 0: 8 triples
  (40 years) --[is under]--> (old)
  (attention) --[is]--> (immediate)
  (hospital) --[has]--> (emergency triage protocol)
  ...

Sentence 1: 2 triples
  (shifts) --[is]--> (double)
  (patients) --[is over]--> (65)

Sentence 2: 6 triples
  (history) --[is]--> (documented)
  (guidelines) --[is]--> (official)
  ...
```

---

## API Reference

### `format_triples_json(triples, indent=2)`

**Parameters:**
- `triples` (List[Dict]): List of triple dictionaries from `extract_triples()`
- `indent` (int, optional): JSON indentation level
  - `0`: Compact, single-line output
  - `2`: Readable with 2-space indent (default)
  - `4`: Extra readable with 4-space indent

**Returns:**
- `str`: JSON-formatted string

**Output Fields:**
- `subject` (str): Subject entity/phrase
- `predicate` (str): Relation/action
- `object` (str): Object entity/phrase
- `sentence_index` (int): Sentence number (0-based)

**Removed Fields:**
- `source`: Whether from 'openie' or 'stanza_depparse'
- `pos`: Part-of-speech tag (only in stanza fallback)

---

## Why Remove Source Field?

The `source` field is removed because:

1. **Cleaner output** - Focused on actual triple data
2. **Pipeline agnostic** - Downstream consumers don't need to know extraction method
3. **Simpler schema** - Easier to validate and process
4. **Provenance optional** - If needed, use `extract_triples_with_coref_info()` which returns full metadata

**If you need source information**, use the raw triples:

```python
# Get triples with metadata
triples = extractor.extract_triples(text)

# Access source directly
for triple in triples:
    print(triple['source'])  # 'openie' or 'stanza_depparse'

# Or save full metadata as JSON
import json
with open('full_triples.json', 'w') as f:
    json.dump(triples, f, indent=2)
```

---

## Example Output File

See: `/workspace/repo/artifacts/json_format_example.json`

This file contains the JSON output from the medical triage text example.

---

## Integration with Text-to-Logic Pipeline

```python
from openie_extractor import OpenIEExtractor
import json

def text_to_triples_pipeline(input_text, output_file):
    """
    Extract triples from text and save as clean JSON.

    Args:
        input_text: Input natural language text
        output_file: Path to save JSON output

    Returns:
        List of triple dictionaries
    """
    with OpenIEExtractor(enable_coref=True, use_depparse_fallback=True) as extractor:
        # Extract triples
        triples = extractor.extract_triples(input_text)

        # Save as JSON
        json_output = extractor.format_triples_json(triples)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)

        # Parse and return
        return json.loads(json_output)

# Usage
triples = text_to_triples_pipeline(
    "The hospital requires immediate attention for patients.",
    "output/triples.json"
)

print(f"Saved {len(triples)} triples to output/triples.json")
```

---

## Summary

✅ **Use `format_triples_json()`** for:
- Pipeline output
- API responses
- Clean triple data
- Downstream processing

✅ **Fields included:**
- subject, predicate, object, sentence_index

❌ **Fields removed:**
- source, pos (use raw triples if needed)

📁 **Example output:**
- `/workspace/repo/artifacts/json_format_example.json`
