# EXEMPLAR 2 Updates: Triple Format and "Should" Constraint Fix

**Date**: 2026-01-25
**File Modified**: `/workspace/repo/code/prompts/prompt_logify2`

---

## Summary of Changes

### 1. Updated INPUT TRIPLES Format ✅

**Changed from**: Tab-separated format (inconsistent with Exemplar 1)
```
researchers	sign	safety logbook
equipment	is	protective
...
```

**Changed to**: JSON array format (consistent with Exemplar 1)
```json
[ ["researchers", "sign", "safety logbook", 0],
  ["equipment", "is", "protective", 0],
  ["researchers", "entering", "laboratory", 0],
  ...
]
```

**Rationale**:
- Matches the format specification in line 117-118 of the prompt
- Consistent with Exemplar 1 (Hospital Triage)
- Uses actual OpenIE extraction output from `artifacts/logify2_testing/lab_safety_triples.json`

---

### 2. Reclassified "Should" Constraints ✅

**Problem**: The word "should" in policy contexts typically indicates **obligation**, not mere recommendation.

**User feedback**: "The word 'should' is usually a HARD constraint, not a soft constraint. It depends on the context though, but when a policy says should then it is an obligation to be followed."

---

## Constraint Reclassifications

### Moved to HARD CONSTRAINTS

#### **NEW H_7**: Weekly Equipment Inspection (was S_2)
```json
{
  "id": "H_7",
  "formula": "P_11",
  "translation": "Lab equipment should be inspected weekly",
  "evidence": "Sentence 4: 'Lab equipment should be inspected weekly...'",
  "reasoning": "The word 'should' in a policy context indicates an obligation that must be followed. This is a baseline safety requirement, though exceptions exist for low-risk items (see S_2)"
}
```

**Analysis**:
- **Context**: Lab safety policy (institutional requirement)
- **Modal**: "should" = obligation
- **Status**: Baseline requirement with documented exceptions
- **Classification**: HARD (policy obligation)

---

#### **NEW H_8**: Partner for Hazardous Materials (was S_5)
```json
{
  "id": "H_8",
  "formula": "P_19 ⟹ P_20",
  "translation": "If an experiment involves hazardous materials, it should be conducted with a partner present",
  "evidence": "Sentence 7: 'The lab director believes that all experiments involving hazardous materials should be conducted with a partner present...'",
  "reasoning": "The word 'should' in safety policy indicates a mandatory requirement. Although framed as the director's belief, it translates to policy/action obligations for hazardous material handling"
}
```

**Analysis**:
- **Context**: Safety policy for hazardous materials
- **Modal**: "should" = safety obligation
- **Framing**: Director's belief → translates to policy
- **Risk**: High (hazardous materials)
- **Classification**: HARD (safety obligation)

---

### Updated SOFT CONSTRAINTS

The soft constraints were renumbered after moving H_7 and H_8:

#### **S_1** (unchanged)
```json
{
  "id": "S_1",
  "formula": "P_9 ⟹ P_10",
  "translation": "If an undergraduate student is in their first month, a senior researcher should supervise them",
  "evidence": "Sentence 3: 'Senior researchers typically supervise undergraduate students during their first month, though this is not always enforced'",
  "reasoning": "The words 'typically' and 'not always enforced' indicate this is a soft constraint - expected but not strictly mandatory"
}
```

**Why SOFT**: "typically" + "not always enforced" override the "should" interpretation

---

#### **S_2** (was S_3) - Exception for Low-Risk Equipment
```json
{
  "id": "S_2",
  "formula": "P_12 ⟹ P_13",
  "translation": "If lab equipment is low-risk, monthly inspections are generally acceptable",
  "evidence": "Sentence 4: '...but monthly inspections are generally acceptable for low-risk items'",
  "reasoning": "The word 'generally' indicates this is an acceptable exception to the baseline weekly inspection requirement (H_7), not a hard rule"
}
```

**Changes**:
- Renumbered from S_3 → S_2
- Updated reasoning to reference H_7 (not old S_2)

**Why SOFT**: "generally acceptable" = flexible exception to H_7

---

#### **S_3** (was S_4) - Experienced Personnel Meetings
```json
{
  "id": "S_3",
  "formula": "P_18 ⟹ P_17",
  "translation": "If a researcher is experienced personnel, they are encouraged to attend monthly safety meetings",
  "evidence": "Sentence 6: 'Researchers are encouraged to attend monthly safety meetings, although attendance is not mandatory for experienced personnel'",
  "reasoning": "The word 'encouraged' for experienced personnel indicates this is a soft expectation, not a requirement. Contrasts with H_5 for non-experienced personnel"
}
```

**Changes**:
- Renumbered from S_4 → S_3

**Why SOFT**: "encouraged" + "not mandatory" = soft expectation

---

## Final Constraint Counts

### Before Changes
- **Hard Constraints**: 6 (H_1 through H_6)
- **Soft Constraints**: 5 (S_1 through S_5)
- **Total**: 11 constraints

### After Changes
- **Hard Constraints**: 8 (H_1 through H_8)
- **Soft Constraints**: 3 (S_1 through S_3)
- **Total**: 11 constraints

**Net effect**: 2 constraints reclassified from soft → hard

---

## Linguistic Analysis: "Should" in Policy Context

### When "Should" = HARD Constraint

1. **Policy statements** (institutional requirements)
   - "Lab equipment should be inspected weekly" → H_7
   - "All experiments involving hazardous materials should be conducted with a partner" → H_8

2. **Safety-critical contexts**
   - High risk scenarios (hazardous materials)
   - Baseline safety requirements

3. **Institutional obligations**
   - Director's policies that translate to action requirements

### When "Should" = SOFT Constraint

1. **Explicitly weakened by hedges**
   - "typically" (S_1: supervision)
   - "not always enforced" (S_1)
   - "generally acceptable" (exception context)

2. **Contrasted with "not mandatory"**
   - "encouraged" but "not mandatory" (S_3)

3. **Descriptive recommendations** (not prescriptive obligations)

---

## Comparison with Exemplar 1 (Hospital Triage)

### Exemplar 1 Usage of "Should"
```json
{
  "id": "H_3",
  "formula": "P_6 ⟹ P_7",
  "translation": "If the patient is over 65 years old, then Dr. Martinez makes sure the patient receives an ECG",
  "evidence": "'patients over 65 should always receive an ECG regardless of symptoms'",
  "reasoning": "The word 'always' indicates this is a hard constraint with no exceptions from Dr. Martinez's perspective"
}
```

**Note**: "should always" → HARD (reinforced by "always")

### Consistency Check ✅

Both exemplars now treat "should" in policy contexts as HARD:
- Exemplar 1: "should always receive" → H_3 (hard)
- Exemplar 2: "should be inspected" → H_7 (hard)
- Exemplar 2: "should be conducted" → H_8 (hard)

---

## Triple Format Consistency ✅

Both exemplars now use the same INPUT TRIPLES format:

**Exemplar 1**:
```json
[ ["40 years", "is under", "old", 0],
  ["attention", "is", "immediate", 0],
  ...
]
```

**Exemplar 2**:
```json
[ ["researchers", "sign", "safety logbook", 0],
  ["equipment", "is", "protective", 0],
  ...
]
```

Format: `[subject, predicate, object, sentence_index]`

---

## Impact on LLM Behavior

These changes improve the exemplar by:

1. **Format Consistency**: LLM sees uniform triple format across both exemplars
2. **Modal Logic Guidance**: Clear examples of when "should" indicates hard vs soft constraints
3. **Contextual Interpretation**: Shows importance of context (policy vs recommendation)
4. **Linguistic Cues**: Demonstrates hedge words that weaken obligations

### Expected LLM Learning

When the LLM processes new text with "should", it will now:
- ✅ Recognize policy "should" as obligation (hard constraint)
- ✅ Check for weakening hedges ("typically", "not always enforced")
- ✅ Consider risk context (safety-critical → hard)
- ✅ Look for explicit softeners ("encouraged", "not mandatory")

---

## Files Modified

1. **`/workspace/repo/code/prompts/prompt_logify2`**
   - Lines 278-297: INPUT TRIPLES updated to array format
   - Lines 478-491: Added H_7 and H_8 (moved from soft)
   - Lines 493-515: Updated soft constraints (removed old S_2, S_5; renumbered)

---

## Verification

### Triple Format
```bash
# View updated triples in prompt
sed -n '278,297p' /workspace/repo/code/prompts/prompt_logify2
```

### Hard Constraints (now 8)
```bash
# Count hard constraints
grep -c '"id": "H_' /workspace/repo/code/prompts/prompt_logify2
```

### Soft Constraints (now 3)
```bash
# Count soft constraints
grep -c '"id": "S_' /workspace/repo/code/prompts/prompt_logify2
```

---

## Summary

✅ **INPUT TRIPLES** updated to JSON array format matching Exemplar 1
✅ **H_7** added: Weekly equipment inspection (policy obligation)
✅ **H_8** added: Partner for hazardous materials (safety obligation)
✅ **S_2, S_3** renumbered and reasoning updated
✅ **Removed**: Old S_2 (now H_7) and S_5 (now H_8)
✅ **Consistency**: Both exemplars now demonstrate "should" in policy = HARD

The prompt is now ready for improved logification of policy texts with accurate modal logic interpretation.
