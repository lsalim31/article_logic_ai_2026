# Coreference Resolution Test Analysis

## Test Setup

The `openie_extractor.py` has been modified to enable coreference resolution using Stanford OpenIE's built-in API property:

```python
properties = {
    'openie.resolve_coref': True
}
self.openie = StanfordOpenIE(properties=properties)
```

## What This Property Does

According to Stanford CoreNLP documentation, `openie.resolve_coref` tells the OpenIE system to:
1. Run coreference resolution **before** extracting relation triples
2. Replace pronouns and references with their antecedents (the actual entities they refer to)
3. Return triples with specific entity names instead of generic pronouns

## Expected Test Results

### Test Case 1: Simple Pronoun Resolution
**Input:**
```
"Alice is a student. She studies hard."
```

**Without coref resolution:**
- `("Alice", "is", "student")`
- `("She", "studies", "hard")`  ← Pronoun remains

**With coref resolution (EXPECTED):**
- `("Alice", "is", "student")`
- `("Alice", "studies", "hard")`  ← Pronoun resolved to "Alice"

---

### Test Case 2: Company Reference (Your Example)
**Input:**
```
"TechCorp was founded in 2020. It became profitable by 2023."
```

**Without coref resolution:**
- `("TechCorp", "was founded", "in 2020")`
- `("It", "became", "profitable by 2023")`  ← Generic pronoun

**With coref resolution (EXPECTED):**
- `("TechCorp", "was founded", "in 2020")`
- `("TechCorp", "became", "profitable by 2023")`  ← Resolved to "TechCorp"

This directly addresses your requirement for more specific triples!

---

### Test Case 3: Multiple Pronouns
**Input:**
```
"Bob met Sarah at the library. He was studying math. She was reading a novel."
```

**Without coref resolution:**
- `("Bob", "met", "Sarah at the library")`
- `("He", "was studying", "math")`
- `("She", "was reading", "novel")`

**With coref resolution (EXPECTED):**
- `("Bob", "met", "Sarah at the library")`
- `("Bob", "was studying", "math")`  ← "He" → "Bob"
- `("Sarah", "was reading", "novel")`  ← "She" → "Sarah"

---

## How to Run the Actual Test

To run this test in an environment with Stanford OpenIE installed:

```bash
cd /workspace/repo/artifacts/code
python3 test_coref_resolution.py
```

### Prerequisites:
1. Java JDK installed (required for Stanford CoreNLP)
2. `stanford-openie` Python package installed:
   ```bash
   pip install stanford-openie
   ```
3. Stanford CoreNLP JAR files (auto-downloaded on first run)

---

## Success Indicators

The test will confirm coreference resolution is working if:

✓ **No pronouns appear as subjects** in extracted triples (she, he, it, they)
✓ **Entity names are consistently used** across related triples
✓ **Temporal/contextual information is preserved** (e.g., "by 2023" stays in the object)

---

## Known Limitations

Based on GitHub issues and documentation:

1. **Version Compatibility**: Some versions of Stanford CoreNLP (e.g., 3.9.2) had issues with `openie.resolve_coref`
2. **Annotator Requirements**: Coref resolution requires the `coref` annotator to be loaded, which the OpenIE wrapper should handle automatically
3. **Performance**: Coreference resolution adds processing time since it must analyze the entire document before extraction

---

## Fallback Plan (If Issues Occur)

If `openie.resolve_coref: True` causes initialization errors, we can try Option 2:

```python
properties = {
    'openie.resolve_coref': True,
    'annotators': 'tokenize,ssplit,pos,lemma,ner,coref,openie'
}
```

This explicitly loads all required annotators including the coreference resolver.

---

## Impact on Paper

With coreference resolution working:

1. **More specific triples** → Better logical representations
2. **Clearer entity tracking** → Easier to build consistent propositions
3. **Reduced ambiguity** → Fewer errors in Stage 2 (LLM processing)
4. **Professional pipeline** → Uses Stanford's state-of-the-art coref resolution

This aligns perfectly with your goal of making triples "as specific as possible to the underlying text."
