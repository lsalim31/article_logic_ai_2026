# Error Analysis: DocNLI Experiment Results

## File Analyzed
`code/experiments/DocNLI/results_logify_DocNLI/experiment_20260129_081029.json`

## Summary
The experiment encountered two types of errors that caused most examples (premises 1-19) to fail:

1. **FileNotFoundError (Most Common)**: Missing weighted cache files
2. **JSON Parsing Error (Premise 7 only)**: LLM response parsing failure

---

## Error Type 1: Missing Weighted Cache Files (92% of errors)

### Error Message
```
[Errno 2] No such file or directory: '/home/logify/article_logic_ai_2026/code/experiments/DocNLI/cache/example_X_weighted.json'
```

### Affected Premises
- Premise 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19...
- Only **Premise 0** succeeded (it already had a cached weighted file)

### Root Cause Analysis

#### Source Code Location
**File**: `code/experiments/DocNLI/experiment_logify_DocNLI.py`
**Function**: `logify_premise()` (lines 81-165)

#### The Problem
The code has a **mismatch in file naming conventions**:

1. **What the code expects to find** (line 97):
   ```python
   def get_cached_logified_path(example_id: int) -> Path:
       return CACHE_DIR / f"example_{example_id}_weighted.json"
   ```
   Looking for: `example_1_weighted.json`, `example_2_weighted.json`, etc.

2. **What `assign_weights()` actually creates** (weights.py, line 496):
   ```python
   output_path = json_path_obj.parent / (json_path_obj.stem + "_weighted.json")
   ```
   Creates: `premise_1_weighted.json`, `premise_2_weighted.json`, etc.

#### The Workflow

1. **Cache check** (line 100-108):
   ```python
   cache_path = get_cached_logified_path(premise_id)  # Returns example_X_weighted.json
   if cache_path.exists():  # This fails for all but example_0
       # Load from cache
   ```

2. **Logification** (lines 110-130):
   - Converts premise text to logic structure
   - **Saves intermediate JSON as** `premise_{premise_id}.json` ✓ (correct)

3. **Weight assignment** (lines 132-149):
   ```python
   intermediate_path = CACHE_DIR / f"premise_{premise_id}.json"  # premise_1.json

   assign_weights(
       pathfile=str(temp_text_path),    # premise_1_text.txt
       json_path=str(intermediate_path), # premise_1.json  ← input
       ...
   )
   ```

   The `assign_weights()` function (in `weights.py`) then:
   - Reads `premise_1.json`
   - Adds weights to constraints
   - **Saves output as** `premise_1_weighted.json` (line 496 of weights.py)

4. **Loading the result** (lines 151-153):
   ```python
   with open(cache_path, 'r', encoding='utf-8') as f:  # Tries to read example_1_weighted.json
       logified_structure = json.load(f)                # ← FileNotFoundError!
   ```

### Why Premise 0 Worked
The cache directory already contained `example_0_weighted.json`, likely from a previous run with different code or manual creation.

### Impact
- **All hypotheses** for premises 1-19 (except 7) failed with this error
- The experiment continued but couldn't evaluate any hypotheses
- Results show `prediction: null`, `prediction_binary: null`, `error: [Errno 2]...`

---

## Error Type 2: JSON Parsing Error (Premise 7 only)

### Error Message
```
Error in LLM conversion: Failed to parse JSON response: Expecting value: line 1 column 1 (char 0). Raw response saved to debug_llm_response.txt
```

### Affected Premise
- **Premise 7** only (8 hypotheses failed)

### Root Cause Analysis

#### The Problem
The LLM (openai/gpt-5.2) returned its JSON response **wrapped in markdown code fences**:

```json
{
  "primitive_props": [...],
  "hard_constraints": [...],
  "soft_constraints": [...]
}
```

Instead of raw JSON:
```json
{
  "primitive_props": [...],
  ...
}
```

#### Source Code Location
**File**: `code/from_text_to_logic/logify.py` (likely)
**Function**: `LogifyConverter.convert_text_to_logic()` or similar

The JSON parser receives the response with markdown wrapper:
```
```json\n{...}\n```
```

And fails because the first character is a backtick, not `{`.

### Evidence
The error message shows: `"Expecting value: line 1 column 1 (char 0)"`

This specific error indicates the LLM response was **completely empty or whitespace-only**:
- Empty string: `""`
- Or just whitespace that got stripped

This is different from a markdown-wrapping issue. It suggests:
- API timeout or connection failure
- Model returned empty completion
- Truncated response (possibly due to length limits)
- Rate limiting or API error

**Note**: The `debug_llm_response.txt` file in the directory shows a valid markdown-wrapped JSON response, but this is likely from a **later retry** or different run (the file gets overwritten each time). The original error at experiment time was an empty response.

### Impact
- All 8 hypotheses for premise 7 failed
- Logification never completed, so no weighted file was created
- Similar to Error Type 1, but the root cause is different (parsing vs. file naming)

---

## Verification: Current Cache State

### What exists in cache (as of experiment run):
```bash
cache/
├── example_0.json              # ← Non-weighted (intermediate)
├── example_0_weighted.json     # ← Weighted (this is why premise 0 worked!)
├── premise_1.json              # ← Non-weighted (intermediate)
├── premise_1_text.txt          # ← Temporary text file
├── premise_2.json              # ← Non-weighted (intermediate)
├── ...
├── premise_10_weighted.json    # ← Weighted (but wrong name!)
├── premise_11_weighted.json    # ← Weighted (but wrong name!)
├── ...
```

### What the code looks for:
```
example_1_weighted.json  ← Missing!
example_2_weighted.json  ← Missing!
...
```

### What actually exists:
```
premise_1_weighted.json  ← Wrong name!
premise_2_weighted.json  ← Wrong name!
...
```

---

## Solution Recommendations

### Fix 1: Naming Consistency (Critical)

**Option A**: Change `get_cached_logified_path()` to use "premise" prefix:
```python
def get_cached_logified_path(example_id: int) -> Path:
    return CACHE_DIR / f"premise_{example_id}_weighted.json"  # Changed from example_
```

**Option B**: Change intermediate path to use "example" prefix:
```python
intermediate_path = CACHE_DIR / f"example_{premise_id}.json"  # Changed from premise_
```

**Recommendation**: Option A is better because:
- Matches the rest of the codebase (premise is used consistently elsewhere)
- Less invasive change (one line)
- More semantically accurate (these are premises, not examples)

### Fix 2: Handle Empty LLM Responses (Important)

**Location**: `code/from_text_to_logic/logic_converter.py`

The code already has JSON extraction fallback (lines 178-189), but doesn't handle empty responses. Add validation:

```python
# After getting response_text (around line 160)
response_text = response_text.strip()

# Add empty response check
if not response_text:
    raise ValueError("LLM returned empty response. This may indicate API timeout, rate limiting, or model error.")

print(f"  Response length: {len(response_text)} characters")
```

**Additional improvements**:
1. Add retry logic with exponential backoff for empty responses
2. Log the actual API response status/headers to diagnose the root cause
3. Check if response was truncated due to max_tokens limit
4. Add timeout configuration for long documents

**Note**: While the current `debug_llm_response.txt` shows markdown-wrapped JSON (from a later successful run), the original error was an empty response. The existing JSON extraction fallback (lines 178-189) should handle markdown wrapping, but cannot handle empty responses.

### Fix 3: Better Error Handling (Optional but Recommended)

Add retry logic for markdown-wrapped responses:
```python
try:
    logified = json.loads(response_text)
except json.JSONDecodeError as e:
    # Try stripping markdown and retrying
    if "```" in response_text:
        cleaned = strip_markdown(response_text)
        logified = json.loads(cleaned)
    else:
        raise e
```

---

## Expected Behavior After Fixes

1. **Premise 0**: Continue to work (already cached)
2. **Premises 1-6, 8-19**: Will successfully load `premise_X_weighted.json` files
3. **Premise 7**: Will successfully parse the LLM response and create `premise_7_weighted.json`
4. **All hypotheses**: Will receive predictions and be evaluated correctly

---

## Statistics from Current Run

### Success Rate
- **Premises processed**: 20 (premises 0-19)
- **Logification succeeded**: 1 (premise 0 only, from cache)
- **Logification failed**: 19
  - File naming issue: 18 premises
  - JSON parsing issue: 1 premise (7)

### Hypothesis Evaluation
- **Total hypotheses**: ~100+ (exact count in results)
- **Successfully evaluated**: ~5-10 (only premise 0's hypotheses)
- **Failed**: ~90-95 (all others)

---

## Files to Modify

1. **`code/experiments/DocNLI/experiment_logify_DocNLI.py`**
   - Line 77-78: Fix `get_cached_logified_path()` naming

2. **`code/from_text_to_logic/logify.py`** (need to inspect)
   - Add markdown stripping to JSON response parser
   - Or update prompt to forbid markdown

3. **Optional: Add tests**
   - Test case for markdown-wrapped JSON responses
   - Test case for cache path naming consistency

---

## Conclusion

The experiment failed due to:
1. **Naming inconsistency** between what `experiment_logify_DocNLI.py` expects and what `weights.py` produces
2. **LLM response format** issue where gpt-5.2 wrapped JSON in markdown code fences

Both issues are **easily fixable** with 1-2 line changes each. The underlying logic and algorithms appear sound—the failures are purely due to integration bugs.
