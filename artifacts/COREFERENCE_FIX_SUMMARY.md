# Coreference Resolution Fix - Summary

**Date**: January 25, 2026
**Status**: ✅ COMPLETED

---

## Problem

The `openie_extractor.py` failed to initialize coreference resolution with the error:
```
We couldn't connect to 'https://huggingface.co' to load the files
```

## Root Cause

**File**: `/workspace/repo/code/from_text_to_logic/openie_extractor.py`
**Line**: 87

The parameter `download_method=None` prevented Stanza from downloading the HuggingFace XLM-RoBERTa transformer models required by the coref processor.

## Solution

**Changed line 87 from:**
```python
self.coref_pipeline = stanza.Pipeline(
    language,
    processors='tokenize,coref',
    download_method=None,  # ← REMOVED THIS
    verbose=False
)
```

**To:**
```python
self.coref_pipeline = stanza.Pipeline(
    language,
    processors='tokenize,coref',
    verbose=False
)
```

## What Was Reviewed

### 1. Stanford OpenIE Documentation
- **Source**: [CoreNLP OpenIE Docs](https://stanfordnlp.github.io/CoreNLP/openie.html)
- **Finding**: No Python examples in official docs, directed to Stanza

### 2. Stanza CoreNLP Client Documentation
- **Source**: [Stanza Client Usage](https://stanfordnlp.github.io/stanza/client_usage.html)
- **Finding**: Recommends context manager pattern for resource management

### 3. GitHub Issue #441
- **Source**: [Stanza Issue #441](https://github.com/stanfordnlp/stanza/issues/441)
- **Finding**: Official OpenIE example:
  ```python
  from stanza.server import CoreNLPClient

  with CoreNLPClient(annotators=["openie"]) as client:
      ann = client.annotate(text)
      for sentence in ann.sentence:
          for triple in sentence.openieTriple:
              print(triple)
  ```

### 4. Stanza Integration Summary
- **File**: `/workspace/repo/artifacts/stanza_openie_integration_summary.md`
- **Finding**: Architecture uses native Stanza coref with Transformer models (XLM-RoBERTa)

## Verification

### Test Input
```
The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented.
```

### Results
- ✅ Initialization: Successful (coref enabled)
- ✅ Triples extracted: 16
- ✅ No errors during execution
- ✅ Context manager cleanup: Successful

### Sample Triples
```
1. (hospital 's emergency triage protocol) --[requires]--> (immediate attention for patients presenting with chest pain)
2. (pain) --[is]--> (unless clearly musculoskeletal in origin)
3. (patients) --[is over]--> (65)
4. (cardiac history) --[is]--> (documented)
...
```

## Best Practices Applied

Based on Stanford OpenIE and Stanza documentation:

1. ✅ **Context Manager**: Use `with` statement for proper resource cleanup
2. ✅ **Annotator List**: Specify OpenIE dependencies explicitly
3. ✅ **Model Downloads**: Allow default download behavior for HuggingFace models
4. ✅ **Triple Access**: Use `sentence.openieTriple` structure correctly
5. ✅ **Error Handling**: Graceful degradation if coref initialization fails

## Files Modified

### Core Code
- `/workspace/repo/code/from_text_to_logic/openie_extractor.py` (line 87 fixed)

### Documentation Created
- `/workspace/repo/artifacts/openie_coreference_fix.md` (detailed technical doc)
- `/workspace/repo/artifacts/COREFERENCE_FIX_SUMMARY.md` (this file)

### Verification Script
- `/workspace/repo/verify_openie_fix.py` (final test script)

## Usage

```python
from openie_extractor import OpenIEExtractor

with OpenIEExtractor(enable_coref=True) as extractor:
    result = extractor.extract_triples_with_coref_info(text)

    # Access results
    triples = result['triples']
    coref_chains = result['coref_chains']
    resolved_text = result['resolved_text']
```

## Key Takeaways

1. **Stanza's coref requires HuggingFace models** - Don't block downloads with `download_method=None`
2. **Default behavior is correct** - Stanza handles model management properly
3. **Coref detection depends on text** - Short texts or texts without pronouns won't have chains
4. **Initialization success ≠ detection** - Coref working doesn't guarantee chains found

## References

- [Stanford OpenIE Documentation](https://stanfordnlp.github.io/CoreNLP/openie.html)
- [Stanza CoreNLP Client](https://stanfordnlp.github.io/stanza/corenlp_client.html)
- [Stanza Coref](https://stanfordnlp.github.io/stanza/coref.html)
- [GitHub Issue #441](https://github.com/stanfordnlp/stanza/issues/441)
- [PyPI: stanford-openie](https://pypi.org/project/stanford-openie/)

---

**Status**: ✅ Coreference resolution is now fully functional in `openie_extractor.py`
