# OpenIE Output Format Recommendations

## Executive Summary

**Best format depends on your use case:**

| Use Case | Recommended Format | Why |
|----------|-------------------|-----|
| **Text-to-Logic Pipeline** | JSON or Prolog | Preserves metadata, easy to parse |
| **Machine Learning/Training** | JSON or TSV | Standard formats, metadata preserved |
| **Human Review** | Verbose | Most readable |
| **Database Import** | TSV or JSON | Standard interchange formats |
| **Semantic Web/RDF** | N-Triples | Standard RDF format |
| **Quick Inspection** | Verbose | Best readability |

---

## Format Comparison

### 1. **TSV (Tab-Separated Values)** ⭐ Best for simplicity

**Format:**
```
subject\tpredicate\tobject
```

**Example:**
```
hospital 's emergency protocol	requires	attention
attention	is	immediate
immediate attention	is for	patients with chest pain
```

**Pros:**
- ✅ Simple, clean, minimal
- ✅ Easy to import into Excel, databases
- ✅ Standard format for data processing
- ✅ Small file size
- ✅ Easy to grep/awk/process with Unix tools

**Cons:**
- ❌ Loses metadata (sentence_index, source)
- ❌ Tab characters can cause issues in some tools
- ❌ No type information

**When to use:**
- Quick export for spreadsheets
- Training data for ML models (simple triples)
- Minimal storage requirements

---

### 2. **JSON** ⭐⭐⭐ Best for most use cases

**Format:**
```json
[
  {
    "subject": "hospital 's emergency protocol",
    "predicate": "requires",
    "object": "attention",
    "sentence_index": 0,
    "source": "openie"
  }
]
```

**Pros:**
- ✅ Preserves all metadata
- ✅ Standard interchange format
- ✅ Easy to parse in all languages
- ✅ Can add custom fields without breaking parsers
- ✅ Human-readable with formatting
- ✅ Supports nested structures

**Cons:**
- ❌ Larger file size than TSV
- ❌ More verbose

**When to use:**
- **Text-to-logic pipeline** (preserves provenance)
- API responses
- Configuration/pipeline data
- When you need metadata for downstream processing

---

### 3. **Verbose Format** ⭐⭐ Best for human inspection

**Format:**
```
1. (hospital 's emergency protocol) --[requires]--> (attention)  [src: openie]
2. (attention) --[is]--> (immediate)  [src: openie]
```

**Pros:**
- ✅ Most human-readable
- ✅ Shows metadata inline
- ✅ Graph-like visualization
- ✅ Easy to scan visually

**Cons:**
- ❌ Hard to parse programmatically
- ❌ Not a standard format
- ❌ Requires custom parser

**When to use:**
- Debugging
- Demo outputs
- Reports/documentation
- Human review of extractions

---

### 4. **Prolog-Style Facts** ⭐⭐⭐ Best for logic programming

**Format:**
```prolog
requires(hospital_emergency_protocol, attention).
is(attention, immediate).
is_for(immediate_attention, patients_with_chest_pain).
```

**Pros:**
- ✅ Direct input to Prolog/logic solvers
- ✅ Clean logical representation
- ✅ Easy to query with logic programming
- ✅ Compact syntax

**Cons:**
- ❌ Loses metadata unless encoded
- ❌ Whitespace/special chars need escaping
- ❌ Predicate naming can be ambiguous

**When to use:**
- **Feeding into Prolog/ASP/logic solvers**
- Text-to-logic conversion
- Formal reasoning pipelines

---

### 5. **N-Triples (RDF)** ⭐ Best for semantic web

**Format:**
```
<hospital_emergency_protocol> <requires> <attention> .
<attention> <is> <immediate> .
```

**Pros:**
- ✅ Standard RDF format
- ✅ Interoperable with semantic web tools
- ✅ Can add namespaces/URIs

**Cons:**
- ❌ Verbose for simple use cases
- ❌ Requires URI naming scheme
- ❌ Limited metadata without reification

**When to use:**
- Semantic web applications
- Knowledge graph construction
- Integration with RDF stores

---

### 6. **Raw Python Dict** - Best for in-memory processing

**Format:**
```python
{'subject': 'hospital', 'predicate': 'requires', 'object': 'attention',
 'sentence_index': 0, 'source': 'openie'}
```

**Pros:**
- ✅ Native Python format
- ✅ No serialization overhead
- ✅ All metadata preserved

**Cons:**
- ❌ Not portable outside Python
- ❌ Hard to inspect/debug

**When to use:**
- In-memory processing within Python
- Passing between Python functions

---

## Recommendations by Use Case

### For Text-to-Logic Pipeline (Your Use Case)

**Primary: JSON**
```python
import json

with OpenIEExtractor() as extractor:
    triples = extractor.extract_triples(text)

    # Save to JSON
    with open('output.json', 'w') as f:
        json.dump(triples, f, indent=2)
```

**Why:**
- Preserves `sentence_index` for tracking
- Preserves `source` (openie vs stanza_depparse)
- Easy to extend with confidence scores later
- Standard format for pipeline data

**Secondary: Prolog Facts**
```python
def to_prolog(triples):
    facts = []
    for t in triples:
        subj = normalize(t['subject'])
        pred = normalize(t['predicate'])
        obj = normalize(t['object'])
        facts.append(f"{pred}({subj}, {obj}).")
    return '\n'.join(facts)
```

**Why:**
- Direct input to logic solvers
- Clean logical representation

---

### For Machine Learning Training Data

**Primary: TSV or JSONL**

**TSV:**
```
hospital emergency protocol	requires	attention
attention	is	immediate
```

**JSONL (JSON Lines):**
```json
{"subject": "hospital", "predicate": "requires", "object": "attention"}
{"subject": "attention", "predicate": "is", "object": "immediate"}
```

**Why:**
- Standard ML data formats
- Easy to stream/process large files
- Compatible with pandas, sklearn

---

### For Human Review/Debugging

**Primary: Verbose Format**
```python
output = extractor.format_triples_verbose(triples)
print(output)
```

**Why:**
- Most readable
- Shows source metadata
- Easy to spot errors

---

## Recommended Implementation

### Add JSON Export Method

Add this to `openie_extractor.py`:

```python
def format_triples_json(self, triples: List[Dict[str, Any]],
                        indent: int = 2) -> str:
    """
    Format OpenIE triples as JSON.

    Args:
        triples: List of relation triples
        indent: JSON indentation (0 for compact, 2 for readable)

    Returns:
        JSON string of triples with all metadata
    """
    import json
    return json.dumps(triples, indent=indent, ensure_ascii=False)

def format_triples_prolog(self, triples: List[Dict[str, Any]]) -> str:
    """
    Format OpenIE triples as Prolog facts.

    Args:
        triples: List of relation triples

    Returns:
        Prolog facts (one per line)
    """
    def normalize(text: str) -> str:
        # Convert to valid Prolog atom
        text = text.lower().replace(' ', '_')
        text = text.replace("'", '').replace('"', '')
        text = ''.join(c for c in text if c.isalnum() or c == '_')
        return text

    facts = []
    for triple in triples:
        subj = normalize(triple['subject'])
        pred = normalize(triple['predicate'])
        obj = normalize(triple['object'])
        facts.append(f"{pred}({subj}, {obj}).")

    return '\n'.join(facts)
```

---

## File Format Recommendations

### For Pipeline Output Files

```
output/
├── raw_triples.json          # Full metadata, primary format
├── triples.tsv               # Simple triples for quick processing
├── triples_verbose.txt       # Human-readable for review
└── facts.pl                  # Prolog facts for logic solver
```

### Usage Example

```python
from openie_extractor import OpenIEExtractor
import json

text = "The hospital requires immediate attention."

with OpenIEExtractor(enable_coref=True) as extractor:
    # Extract
    result = extractor.extract_triples_with_coref_info(text)
    triples = result['triples']

    # Save in multiple formats

    # 1. JSON (primary, preserves everything)
    with open('output/raw_triples.json', 'w') as f:
        json.dump(result, f, indent=2)

    # 2. TSV (simple, for spreadsheets)
    with open('output/triples.tsv', 'w') as f:
        f.write(extractor.format_triples(triples))

    # 3. Verbose (human review)
    with open('output/triples_verbose.txt', 'w') as f:
        f.write(extractor.format_triples_verbose(triples))

    # 4. Prolog (if you add the method)
    # with open('output/facts.pl', 'w') as f:
    #     f.write(extractor.format_triples_prolog(triples))
```

---

## Special Considerations

### Handling Special Characters

**Issue:** Subjects/objects may contain:
- Apostrophes: `hospital 's emergency protocol`
- Quotes: `patient said "I'm fine"`
- Newlines, tabs

**Solutions:**

1. **JSON**: Handles automatically ✅
2. **TSV**: Escape tabs, use CSV if needed
3. **Prolog**: Normalize to atoms (lowercase, underscores)
4. **Verbose**: Quote strings if needed

### Preserving Sentence Context

If you need to trace triples back to sentences:

**JSON is best** - preserves `sentence_index`:
```json
{
  "triples": [...],
  "sentences": [
    {"index": 0, "text": "The hospital..."},
    {"index": 1, "text": "Dr. Martinez..."}
  ]
}
```

---

## Final Recommendation

### Primary Format: **JSON**

**Reasons:**
1. ✅ Preserves all metadata (source, sentence_index, pos)
2. ✅ Standard, interoperable format
3. ✅ Easy to extend (add confidence, spans, etc.)
4. ✅ Works with all downstream tools
5. ✅ Human-readable with formatting

### Secondary Format: **TSV**

**Reasons:**
1. ✅ Simple, minimal
2. ✅ Good for quick exports
3. ✅ Compatible with spreadsheets

### For Display: **Verbose**

**Reasons:**
1. ✅ Best human readability
2. ✅ Shows provenance inline

---

## Code Example - Best Practice

```python
def save_extraction_results(text: str, output_dir: str):
    """Save extraction results in recommended formats."""
    import json
    from pathlib import Path

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    with OpenIEExtractor(enable_coref=True) as extractor:
        result = extractor.extract_triples_with_coref_info(text)

        # Primary: JSON with full metadata
        with open(output_dir / 'extraction.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Secondary: Simple TSV
        with open(output_dir / 'triples.tsv', 'w') as f:
            f.write(extractor.format_triples(result['triples']))

        # For human review
        with open(output_dir / 'report.txt', 'w') as f:
            f.write(f"Input Text:\n{text}\n\n")
            f.write(f"Resolved Text:\n{result['resolved_text']}\n\n")
            f.write("Extracted Triples:\n")
            f.write(extractor.format_triples_verbose(result['triples']))
            f.write(f"\n\nTotal: {len(result['triples'])} triples\n")
            f.write(f"Coref chains: {len(result['coref_chains'])}\n")
```

---

## Summary Table

| Format | Efficiency | Clarity | Metadata | Interop | Best For |
|--------|-----------|---------|----------|---------|----------|
| **JSON** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Pipelines** |
| TSV | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | Spreadsheets |
| Verbose | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | **Human review** |
| Prolog | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | **Logic solvers** |
| N-Triples | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | Semantic web |

**Recommendation: Use JSON as primary format, generate others as needed.**
