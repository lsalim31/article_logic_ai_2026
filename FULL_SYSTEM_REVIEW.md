
# FULL SYSTEM REVIEW - ISSUES & MISSING COMPONENTS

## Executive Summary

**Status**: System has all core files but CANNOT RUN due to:
1. Missing dependencies (5 packages)
2. Weight format mismatch between weights.py and logic_solver
3. Import path issues

---

## CRITICAL ISSUES

### Issue 1: Missing Dependencies ❌

The following packages are required but NOT in requirements.txt:

1. **python-sat** (pysat)
   - Required by: `logic_solver/encoding.py`
   - Purpose: MaxSAT solving
   - Fix: `pip install python-sat`

2. **stanza**
   - Required by: `from_text_to_logic/openie_extractor.py`
   - Purpose: OpenIE triple extraction
   - Fix: `pip install stanza`

3. **sentence-transformers**
   - Required by: `from_text_to_logic/weights.py`, `interface_with_user/translate.py`
   - Purpose: SBERT embeddings for retrieval
   - Fix: `pip install sentence-transformers`

4. **PyMuPDF** (fitz)
   - Required by: `from_text_to_logic/logify.py`, `from_text_to_logic/weights.py`
   - Purpose: PDF reading
   - Fix: `pip install PyMuPDF`

5. **python-docx**
   - Required by: `from_text_to_logic/logify.py`, `from_text_to_logic/weights.py`
   - Purpose: DOCX reading
   - Fix: `pip install python-docx`

**Current requirements.txt only has:**
```
python-sat>=0.1.8.dev0  # Present but maybe wrong name
stanza>=1.7.0  # Listed but not installed
openai>=1.0.0  # ✓ Works
numpy>=1.24.0  # ✓ Works
```

**Missing from requirements.txt:**
- sentence-transformers
- PyMuPDF
- python-docx
- datasets (optional)

---

### Issue 2: Weight Format Mismatch ❌ CRITICAL

**Problem**: `weights.py` and `logic_solver` expect different weight formats!

**weights.py output (line 448-451):**
```python
constraint['weight'] = [
    result_original['prob_yes'],    # P(constraint is true)
    result_negated['prob_yes']      # P(negation is true)
]
```
Returns: `[0.8, 0.2]` (2-element array)

**logic_solver expects (encoding.py line 307):**
```python
weight = constraint.get('weight', 0.5)  # Expects single float!
```
Expects: `0.8` (single value)

**User's Comment**: "when you run weights.py, you will choose the third weight to be the correct one"

**Analysis**: 
- weights.py outputs 2 values: [prob_original, prob_negated]
- Logic solver expects 1 value
- User mentions "third weight" - this suggests there might be a THIRD option we're missing
- Possible interpretations:
  1. Take the first weight: `prob_yes_original`
  2. Take the second weight: `prob_yes_negated`  
  3. **Compute a third weight**: Maybe `1 - prob_yes_negated` or some combination?

**This will cause a runtime error** when logic_solver tries to process the weight array!

---

### Issue 3: Import Path Issues ⚠️

**Problem**: `logify.py` imports are relative but should be absolute

**Current (line 18-19):**
```python
from openie_extractor import OpenIEExtractor
from logic_converter import LogicConverter
```

**Should be:**
```python
from from_text_to_logic.openie_extractor import OpenIEExtractor
from from_text_to_logic.logic_converter import LogicConverter
```

**Impact**: Won't work when run from outside the from_text_to_logic directory

---

## WARNINGS

### Warning 1: weights.py Weight Interpretation Unclear

The comment about "third weight" is confusing given the code structure:

**What weights.py computes:**
1. `P(YES | original_constraint)` - Probability document supports constraint
2. `P(YES | negated_constraint)` - Probability document supports negation

**What logic_solver needs:**
- Single weight in [0, 1] representing constraint confidence

**Possible solutions:**
1. Use `prob_yes_original` directly (seems most logical)
2. Use `prob_yes_original - prob_yes_negated` (difference)
3. Use `prob_yes_original / (prob_yes_original + prob_yes_negated)` (normalization)
4. There's a THIRD verification we're not seeing in the code

**User needs to clarify**: What is the "third weight"?

---

### Warning 2: baseline_rag Dependencies

The `translate.py` and `weights.py` import from `baseline_rag`:
```python
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import load_sbert_model, encode_chunks, encode_query
```

These imports will fail if `sentence-transformers` is not installed.

---

## COMPLETE DEPENDENCY LIST

For Google Cloud deployment, install:

```bash
pip install python-sat
pip install stanza
pip install sentence-transformers
pip install PyMuPDF
pip install python-docx
pip install datasets
pip install openai
pip install numpy
```

Or update requirements.txt to:

```
# Core dependencies
python-sat>=0.1.8.dev0
stanza>=1.7.0  
sentence-transformers>=2.2.0
openai>=1.0.0
numpy>=1.24.0

# Document processing
PyMuPDF>=1.23.0
python-docx>=0.8.11

# Experiments
datasets>=2.14.0
```

---

## FILE STRUCTURE STATUS

✓ All code files exist:
- `from_text_to_logic/logify.py` ✓
- `from_text_to_logic/weights.py` ✓
- `from_text_to_logic/openie_extractor.py` ✓
- `from_text_to_logic/logic_converter.py` ✓
- `logic_solver/encoding.py` ✓
- `logic_solver/__init__.py` ✓
- `interface_with_user/translate.py` ✓
- `baseline_rag/chunker.py` ✓
- `baseline_rag/retriever.py` ✓

✓ Test data exists:
- `artifacts/code/logify2_full_demo.json` ✓

---

## PIPELINE FLOW ANALYSIS

### Current Pipeline:

```
1. Input: document.txt + API_KEY
   ↓
2. logify.py
   - Extract OpenIE triples (needs stanza)
   - Convert to logic (needs openai)
   → Output: logified.json
   ↓
3. weights.py  
   - Retrieve chunks (needs sentence-transformers)
   - Verify with LLM logprobs (needs openai)
   → Output: logified_weighted.json
   ↓
4. translate.py
   - Retrieve props (needs sentence-transformers)
   - Translate query (needs openai)
   → Output: formula (e.g., "P_3 => P_4")
   ↓
5. logic_solver
   - Encode to MaxSAT (needs pysat)
   - Solve and return result
   → Output: {"answer": "TRUE", "confidence": 0.95, "explanation": "..."}
```

### Missing Connections:

- ❌ weights.py → logic_solver: **Weight format mismatch!**
- ⚠️ Import paths need fixing for package-level imports

---

## WHAT WORKS

✓ All Python files exist and are syntactically correct
✓ Path computation is machine-independent
✓ Test data (logify2_full_demo.json) exists
✓ Cross-platform compatible (Windows/Linux/Mac)

---

## WHAT DOESN'T WORK

❌ **Cannot import any module** (missing dependencies)
❌ **Weight format incompatible** between weights.py and logic_solver  
❌ **Relative imports** in logify.py will fail from other directories
⚠️ "Third weight" comment unclear - needs clarification

---

## RECOMMENDED FIXES

### Priority 1: Install Dependencies
```bash
pip install python-sat stanza sentence-transformers PyMuPDF python-docx
```

### Priority 2: Fix Weight Format Mismatch

**Option A**: Modify logic_solver to accept array
```python
# encoding.py line 307
weight = constraint.get('weight', 0.5)
if isinstance(weight, list):
    weight = weight[0]  # Take first element (or specify which one!)
```

**Option B**: Modify weights.py to output single value
```python
# weights.py line 448
# Instead of array, compute single weight
weight_value = result_original['prob_yes']  # Or clarify what "third weight" means
constraint['weight'] = weight_value
```

### Priority 3: Fix Imports

Change logify.py lines 18-19:
```python
from from_text_to_logic.openie_extractor import OpenIEExtractor
from from_text_to_logic.logic_converter import LogicConverter
```

---

## TESTING CHECKLIST

After fixes, test each component:

```bash
# 1. Test logify
cd code
python from_text_to_logic/logify.py input.txt --api-key YOUR_KEY

# 2. Test weights
python from_text_to_logic/weights.py input.txt logified.json --api-key YOUR_KEY

# 3. Test translate  
cd interface_with_user
python translate.py "test query" ../artifacts/code/logify2_full_demo.json --api-key YOUR_KEY

# 4. Test logic_solver
cd ../logic_solver
python demo_complete_system.py
```

---

## QUESTIONS FOR USER

1. **What is the "third weight"?**
   - weights.py computes 2 values: [prob_original, prob_negated]
   - You mentioned "choose the third weight"
   - Should we compute a third value? If so, what formula?

2. **Which weight should logic_solver use?**
   - prob_yes_original?
   - prob_yes_negated?
   - Some combination?

3. **Should we fix this in weights.py or logic_solver?**
   - Change weights.py to output single value?
   - Change logic_solver to accept array?

---

## DEPLOYMENT READINESS

**Current Status**: ❌ NOT READY

**Blockers**:
1. Missing 5 dependencies
2. Weight format mismatch will cause runtime error
3. Import paths need adjustment

**After fixes**: ✓ READY for Google Cloud deployment
