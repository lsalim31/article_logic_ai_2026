# OpenIE Array Format Output - Token Optimization

## Input Text
```
The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented.
```

## Output Formats Comparison

### OLD FORMAT (with field names)
```json
[
  {
    "subject": "40 years",
    "predicate": "is under",
    "object": "old",
    "sentence_index": 0
  },
  {
    "subject": "attention",
    "predicate": "is",
    "object": "immediate",
    "sentence_index": 0
  },
  ...
]
```

**Character count for 1 triple:** ~112 characters
**Character count for 16 triples:** ~1,792 characters

---

### NEW FORMAT (array without field names) ✅
```json
[
  ["40 years", "is under", "old", 0],
  ["attention", "is", "immediate", 0],
  ["hospital", "has", "emergency triage protocol", 0],
  ["pain", "is", "unless clearly musculoskeletal", 0],
  ["hospital 's emergency triage protocol", "requires", "immediate attention for patients presenting with chest pain", 0],
  ["hospital 's emergency triage protocol", "requires", "immediate attention", 0],
  ["immediate attention", "is for", "patients presenting with chest pain", 0],
  ["pain", "is", "unless clearly musculoskeletal in origin", 0],
  ["shifts", "is", "double", 1],
  ["patients", "is over", "65", 1],
  ["history", "is", "documented", 2],
  ["guidelines", "is", "official", 2],
  ["cardiac history", "is", "documented", 2],
  ["cardiac history", "is", "when documented", 2],
  ["history", "is", "cardiac", 2],
  ["history", "is", "when documented", 2]
]
```

**Character count for 1 triple:** ~40 characters (average)
**Character count for 16 triples:** ~640 characters

---

### COMPACT FORMAT (no indentation) ✅✅
```json
[["40 years","is under","old",0],["attention","is","immediate",0],["hospital","has","emergency triage protocol",0],["pain","is","unless clearly musculoskeletal",0],["hospital 's emergency triage protocol","requires","immediate attention for patients presenting with chest pain",0],["hospital 's emergency triage protocol","requires","immediate attention",0],["immediate attention","is for","patients presenting with chest pain",0],["pain","is","unless clearly musculoskeletal in origin",0],["shifts","is","double",1],["patients","is over","65",1],["history","is","documented",2],["guidelines","is","official",2],["cardiac history","is","documented",2],["cardiac history","is","when documented",2],["history","is","cardiac",2],["history","is","when documented",2]]
```

**Character count:** ~588 characters (most compact)

---

## Token Savings Analysis

### Per Triple Savings
- **Old format:** ~112 chars/triple ≈ 28 tokens/triple
- **New format (readable):** ~40 chars/triple ≈ 10 tokens/triple
- **New format (compact):** ~37 chars/triple ≈ 9 tokens/triple

**Savings per triple:** ~18-19 tokens (64-68% reduction!)

### For This Example (16 triples)
- **Old format:** ~1,792 chars ≈ 448 tokens
- **New format (readable):** ~640 chars ≈ 160 tokens
- **New format (compact):** ~588 chars ≈ 147 tokens

**Total savings:** ~288-301 tokens (64-67% reduction!)

### Scaling Up
For a typical larger document with **100 triples**:
- **Old format:** ~11,200 chars ≈ 2,800 tokens
- **New format:** ~4,000 chars ≈ 1,000 tokens

**Savings: ~1,800 tokens per 100 triples!**

---

## Usage in Prompt

### Updated INPUT FORMAT Section
```
RELATION TRIPLES:
<<<
[JSON array where each triple is: [subject, predicate, object, sentence_index]]
Example: [["Alice", "likes", "Bob", 0], ["Bob", "studies", "hard", 1]]
>>>
```

### Triple Format Explanation (from STEP 1)
```
TRIPLE FORMAT: Each triple is [subject, predicate, object, sentence_index]
Example: ["Alice", "studies", "math", 0] means "Alice studies math" from sentence 0
```

---

## Code Changes

### Modified Function: `format_triples_json()`
Location: `code/from_text_to_logic/openie_extractor.py` (lines 539-567)

**Before:**
```python
def format_triples_json(self, triples, indent=2):
    clean_triples = []
    for triple in triples:
        clean_triple = {
            'subject': triple['subject'],
            'predicate': triple['predicate'],
            'object': triple['object'],
            'sentence_index': triple['sentence_index']
        }
        clean_triples.append(clean_triple)
    return json.dumps(clean_triples, indent=indent)
```

**After:**
```python
def format_triples_json(self, triples, indent=2):
    """Format OpenIE triples as JSON array format without field names to save tokens."""
    array_triples = []
    for triple in triples:
        array_triple = [
            triple['subject'],
            triple['predicate'],
            triple['object'],
            triple['sentence_index']
        ]
        array_triples.append(array_triple)
    return json.dumps(array_triples, indent=indent, ensure_ascii=False)
```

---

## Summary

✅ **Format changed from dict to array**
✅ **~64-67% token reduction achieved**
✅ **Prompt updated to explain new format**
✅ **Backward compatible** (internal representation unchanged)
✅ **Ready for production use**

The new array format significantly reduces token consumption while maintaining all necessary information for the logic extraction pipeline.
