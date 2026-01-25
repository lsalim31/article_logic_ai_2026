# Questions Answered - 2026-01-25

---

## Question 1: Does OpenIE extraction output triples in the simplified array format?

### Answer: ✅ YES

The OpenIE extraction system outputs triples in the simplified array format as shown in `test_array_format.py`.

### Evidence

**Location**: `/workspace/repo/code/from_text_to_logic/openie_extractor.py`

**Method**: `format_triples_json()` (lines 539-567)

```python
def format_triples_json(self, triples: List[Dict[str, Any]], indent: int = 2) -> str:
    """
    Format OpenIE triples as JSON array format without field names to save tokens.

    Returns:
        JSON string of triples as arrays: [subject, predicate, object, sentence_index]
        Format optimized to minimize token usage by avoiding repeated field names.
    """
    # Convert to compact array format
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

### Format Comparison

**Old Format (Dict with field names)**:
```json
{
  "subject": "Alice",
  "predicate": "studies",
  "object": "math",
  "sentence_index": 0
}
```
- ~68 characters per triple (including formatting)

**New Format (Array without field names)**:
```json
["Alice", "studies", "math", 0]
```
- ~28 characters per triple (including formatting)

### Token Savings

- **Per triple**: ~40 characters saved
- **For 16 triples** (typical): ~640 characters = ~160 tokens saved
- **Percentage reduction**: ~60% fewer tokens for triple representation

### Test Script

**Location**: `artifacts/openie_testing/test_array_format.py`

This script:
1. Extracts triples using OpenIE
2. Compares old dict format vs new array format
3. Calculates token savings
4. Shows both compact and indented outputs

### Usage in Logify2 Pipeline

The new array format is used in:
- `logify2.py` - Main pipeline (sends triples to LLM)
- `prompt_logify2` - Exemplars use array format
- All test outputs in `artifacts/logify2_testing/`

### Example Output

**File**: `artifacts/logify2_testing/lab_safety_llm_input.txt`

```
ORIGINAL TEXT:
<<<
Before entering the laboratory, all researchers must wear protective equipment...
>>>

OPENIE TRIPLES:
<<<
researchers	sign	safety logbook
equipment	is	protective
researchers	entering	laboratory
...
>>>
```

Note: The triples are shown in tab-separated format in the prompt (even more compact), but the internal representation and JSON exports use the array format.

---

## Question 2: Organize artifacts folder - remove old files and use specific subfolders

### Answer: ✅ COMPLETED

The artifacts folder has been reorganized into 10 logical subdirectories with clear separation of concerns.

### New Structure

```
artifacts/
├── README.md                    ← New documentation
├── CLEANUP_SUMMARY.md           ← New cleanup log
│
├── logify2_testing/            ← New: Logify2 test files (6 files)
│   ├── run_logify2_lab_safety.py
│   ├── lab_safety_input.txt
│   ├── lab_safety_llm_input.txt
│   ├── lab_safety_output.json
│   ├── lab_safety_output_high.json
│   └── lab_safety_triples.json
│
├── openie_testing/             ← New: OpenIE test files (5 files)
│   ├── test_array_format.py
│   ├── verify_openie_fix.py
│   ├── openie_array_format_output.json
│   ├── openie_old_format_output.json
│   └── openie_output.txt
│
├── analyses/                   ← New: Analysis documents (5 files)
│   ├── LOGIFICATION_ANALYSIS.md
│   ├── LAB_SAFETY_LOGIFY2_EXECUTION_REPORT.md
│   ├── LOGIFY2_EXECUTION_SUMMARY.md
│   ├── STAGE2_EXECUTION_REPORT.md
│   └── array_format_comparison.md
│
├── documentation/              ← New: Implementation docs (11 files)
│   ├── EXEMPLAR_ADDITION_SUMMARY.md
│   ├── COREFERENCE_FIX_SUMMARY.md
│   ├── JSON_OUTPUT_USAGE.md
│   ├── NEW_ARRAY_FORMAT_SUMMARY.md
│   ├── OUTPUT_FORMAT_RECOMMENDATIONS.md
│   ├── README_LAB_SAFETY_DEMO.md
│   ├── logify2_implementation_summary.md
│   ├── stanford_openie_integration_summary.md
│   ├── stanza_openie_integration_summary.md
│   ├── openie_coreference_fix.md
│   └── bibliography_update_jan21.md
│
├── old_files/                  ← New: Deprecated files (3 files)
│   ├── test.txt
│   ├── json_format_example.json
│   └── PROOF_OF_EXECUTION.txt
│
├── code/                       ← Existing: Test code (12 files)
├── few_shot_examples/          ← Existing: Examples (8 files)
├── notes/                      ← Existing: Research notes (5 files)
├── reports/                    ← Existing: Reports (1 file)
└── reviews/                    ← Existing: Reviews (4 files)
```

### Files Reorganized

**Total**: 30+ files moved from root to appropriate subfolders

**Breakdown**:
- 6 files → `logify2_testing/`
- 5 files → `openie_testing/`
- 5 files → `analyses/`
- 11 files → `documentation/`
- 3 files → `old_files/`

### Key Improvements

1. **Logify2 Testing**: All lab safety test files grouped together
   - Input text, OpenIE triples, LLM outputs, runner script
   - Complete test case in one location

2. **OpenIE Testing**: All OpenIE-related tests and format comparisons
   - Array format tests
   - Format comparison outputs
   - Verification scripts

3. **Analyses**: Quality analyses and execution reports
   - LOGIFICATION_ANALYSIS.md (identifies 6 issues)
   - Execution reports and summaries

4. **Documentation**: Implementation summaries and guides
   - EXEMPLAR_ADDITION_SUMMARY.md (added today)
   - Integration summaries for Stanford/Stanza
   - Fix documentation

5. **Old Files**: Deprecated or temporary files
   - No longer actively used
   - Kept for reference

### File Statistics

```
analyses/                   5 files
code/                      12 files
documentation/             11 files
few_shot_examples/          8 files
logify2_testing/            6 files
notes/                      5 files
old_files/                  3 files
openie_testing/             5 files
reports/                    1 files
reviews/                    4 files
─────────────────────────────────
TOTAL:                     62 files
```

### Navigation Guide

| Need to... | Go to... |
|------------|----------|
| Run logify2 test | `logify2_testing/run_logify2_lab_safety.py` |
| Test OpenIE array format | `openie_testing/test_array_format.py` |
| Review quality analysis | `analyses/LOGIFICATION_ANALYSIS.md` |
| Check exemplar changes | `documentation/EXEMPLAR_ADDITION_SUMMARY.md` |
| Compare formats | `analyses/array_format_comparison.md` |
| View test code | `code/` directory |
| Check old files | `old_files/` directory |

---

## Summary

Both questions have been fully answered:

1. ✅ **OpenIE uses simplified array format** - Confirmed with code references and examples
2. ✅ **Artifacts folder organized** - 30+ files moved to 5 new specific subdirectories

The artifacts folder now has a clean, maintainable structure with clear separation between:
- Testing files (logify2 and OpenIE)
- Analysis documents
- Implementation documentation
- Deprecated files

All changes documented in `README.md` and `CLEANUP_SUMMARY.md`.

---

## Latest Update - 2026-01-25 (Session 2)

### Task: Fix EXEMPLAR 2 Triple Format and "Should" Classifications

#### Part 1: Updated INPUT TRIPLES Format ✅

**Changed**: EXEMPLAR 2 INPUT TRIPLES from tab-separated to JSON array format

**Before**:
```
researchers	sign	safety logbook
equipment	is	protective
...
```

**After**:
```json
[ ["researchers", "sign", "safety logbook", 0],
  ["equipment", "is", "protective", 0],
  ...
]
```

**Source**: `artifacts/logify2_testing/lab_safety_triples.json` (actual OpenIE extraction output)

**Rationale**: Consistency with Exemplar 1 and prompt specification (line 117-118)

---

#### Part 2: Fixed "Should" Constraint Classifications ✅

**User Guidance**: "The word 'should' is usually a HARD constraint, not a soft constraint. It depends on the context though, but when a policy says should then it is an obligation to be followed."

**Changes Made**:

1. **S_2 → H_7**: "Lab equipment should be inspected weekly"
   - Context: Policy obligation (baseline requirement)
   - Classification: HARD (institutional requirement)

2. **S_5 → H_8**: "Experiments with hazardous materials should be conducted with a partner"
   - Context: Safety policy for hazardous materials
   - Classification: HARD (safety obligation)

3. **Renumbered remaining soft constraints**: S_3 → S_2, S_4 → S_3

**Final Counts (EXEMPLAR 2)**:
- Hard Constraints: 8 (was 6)
- Soft Constraints: 3 (was 5)
- Net change: +2 hard constraints

**Key Insight**: "Should" in policy/safety contexts = obligation (HARD), unless explicitly weakened by hedges like "typically", "not always enforced", or "encouraged but not mandatory".

---

### Documentation Created

1. **`documentation/EXEMPLAR2_TRIPLE_FORMAT_AND_SHOULD_FIX.md`**
   - Complete analysis of changes
   - Linguistic analysis of "should" in context
   - Comparison with Exemplar 1
   - Impact on LLM behavior

2. **`documentation/PROMPT_LOGIFY2_CHANGELOG.md`**
   - Version history of prompt changes
   - Key design principles
   - Future considerations

---

### Files Modified

- **`code/prompts/prompt_logify2`**
  - Lines 278-297: INPUT TRIPLES updated to array format
  - Lines 478-491: Added H_7 and H_8 (moved from soft)
  - Lines 493-515: Updated soft constraints (removed old S_2, S_5; renumbered)

---

### Status: All Tasks Complete ✅

1. ✅ Found OpenIE extraction output
2. ✅ Updated INPUT TRIPLES to JSON array format
3. ✅ Reclassified "should" constraints based on context
4. ✅ Updated constraint numbering
5. ✅ Created comprehensive documentation
