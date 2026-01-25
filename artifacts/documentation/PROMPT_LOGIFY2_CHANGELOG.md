# prompt_logify2 Changelog

**File**: `/workspace/repo/code/prompts/prompt_logify2`

---

## 2026-01-25 - Session 2: Triple Format and "Should" Fix

### Changes Made

1. **Updated EXEMPLAR 2 INPUT TRIPLES format** (lines 278-297)
   - Changed from tab-separated format to JSON array format
   - Now matches Exemplar 1 format specification
   - Uses actual OpenIE extraction output from test run

2. **Reclassified "should" constraints in EXEMPLAR 2**
   - Moved S_2 → H_7: Weekly equipment inspection (policy obligation)
   - Moved S_5 → H_8: Partner for hazardous materials (safety obligation)
   - Updated reasoning to reflect policy context interpretation
   - Renumbered remaining soft constraints (S_3 → S_2, S_4 → S_3)

### Constraint Counts (EXEMPLAR 2)
- **Before**: 6 hard, 5 soft
- **After**: 8 hard, 3 soft
- **Net change**: +2 hard constraints

### Key Learning
"Should" in policy/safety contexts indicates obligation (hard constraint), unless weakened by explicit hedges ("typically", "not enforced", "encouraged but not mandatory").

---

## 2026-01-25 - Session 1: Lab Safety Exemplar Addition

### Changes Made

1. **Added EXEMPLAR 2: Lab Safety Protocol** (lines 264-516)
   - Complete exemplar with 22 propositions, 8 hard constraints, 3 soft constraints
   - Demonstrates temporal decomposition, generic propositions, modal interpretation
   - Shows "belief → policy/action" translation

2. **Corrected exemplar based on user feedback**
   - P_9/P_10 properly decomposed (not labeled 9a/9b)
   - All propositions renumbered sequentially
   - Director's belief treated as policy expectation
   - Generic propositions maintained (no flattening)

### Structure Added
- INPUT TEXT (8 sentences, lab safety rules)
- INPUT TRIPLES (17 triples in JSON array format)
- OUTPUT JSON (22 props, 8 hard, 3 soft)

---

## Original Version

### EXEMPLAR 1: Hospital Triage Protocol
- 11 propositions (P_1 through P_11)
- 4 hard constraints (H_1 through H_4)
- 1 soft constraint (S_1)
- Demonstrates mutual exclusivity, exception handling, belief vs action

---

## Current State

**Total Exemplars**: 2
- Exemplar 1: Hospital Triage Protocol
- Exemplar 2: Lab Safety Protocol

**Format Consistency**: ✅
- Both exemplars use JSON array format for triples
- Both follow identical OUTPUT JSON schema
- Both provide detailed explanations and reasoning

**Total Lines**: 516 (was 262 before first exemplar addition)

---

## Next Steps / Future Considerations

1. **Additional exemplars**: Consider adding exemplars for:
   - Legal text (contractual obligations)
   - Academic policy (grading, attendance)
   - Technical specifications (system requirements)

2. **Modal logic coverage**: Add exemplars demonstrating:
   - "may" (permission)
   - "can" (ability vs permission)
   - "shall" (legal obligation)
   - Temporal modalities (before, after, during, until)

3. **Complex patterns**: Add exemplars for:
   - Nested conditionals (if X then if Y then Z)
   - Exclusive or (either X or Y but not both)
   - Universal quantification with exceptions (all X except Y)
   - Probabilistic statements (likely, rarely, often)

---

## Version History

| Date | Version | Changes | Lines |
|------|---------|---------|-------|
| 2026-01-25 | 3.0 | Fixed EXEMPLAR 2 triples format and "should" classification | 516 |
| 2026-01-25 | 2.0 | Added EXEMPLAR 2 (Lab Safety Protocol) | 516 |
| Initial | 1.0 | Single exemplar (Hospital Triage Protocol) | 262 |

---

## Key Design Principles (Reflected in Exemplars)

1. **Atomicity**: Propositions are timeless, context in constraints
2. **Decomposition**: Break compound statements into independent atoms
3. **Modal interpretation**: Context determines hard vs soft
4. **Specificity**: Propositions must be specific and complete
5. **Exhaustiveness**: All constraints must be expressible from propositions
6. **Evidence grounding**: Every element traced back to source text

---

## Contact / Questions

For questions about these changes or the prompt design, see:
- `artifacts/documentation/EXEMPLAR_ADDITION_SUMMARY.md`
- `artifacts/documentation/EXEMPLAR2_TRIPLE_FORMAT_AND_SHOULD_FIX.md`
- `artifacts/analyses/LOGIFICATION_ANALYSIS.md`
