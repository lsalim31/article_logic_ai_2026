# Lab Safety Exemplar Addition Summary

**Date**: 2026-01-25
**File Updated**: `/workspace/repo/code/prompts/prompt_logify2`
**Lines Added**: 257 (262 → 519 lines)

---

## Summary

Successfully added **EXEMPLAR 2: Lab Safety Protocol** to `prompt_logify2` based on user corrections to the analysis in `LOGIFICATION_ANALYSIS.md`.

---

## User Corrections Applied

### Issue #1: Atomic Proposition Specificity ✅
**User Feedback**: "Issue #1 is not a problem, we want atomic props to be as specific as possible."

**Action**: Kept all propositions at their specific level without removing temporal/conditional context from the translations. For example:
- P_2: "The researcher wears protective equipment" (temporal context moved to constraint)
- P_9: "An undergraduate student is in their first month in the lab" (specific temporal condition)
- P_10: "A senior researcher supervises the undergraduate student" (action independent of time)

### Issue #2: Proposition Decomposition and Numbering ✅
**User Feedback**: "Issue #2 is a very good point. But instead of labeling it 9a and 9b, it needs to be labelled 9, 10 and then the rest of the numbers need to be edited."

**Action**: Decomposed compound proposition into:
- **P_9**: "An undergraduate student is in their first month in the lab"
- **P_10**: "A senior researcher supervises the undergraduate student"
- Renumbered all subsequent propositions (P_11 through P_22)
- Updated all constraint references to use new numbering

**Key Benefit**: This decomposition allows expressing violations where P_9 is true but P_10 is false (first month but no supervision).

### Issue #3: Director's Belief as Policy/Action ✅
**User Feedback**: "Assume the directors belief translates to policy/action."

**Action**: Kept P_20 and S_5 as they were designed:
- **P_20**: "The experiment is conducted with a partner present"
- **S_5**: `P_19 ⟹ P_20` with reasoning: "Although framed as the director's belief, it translates to policy/action expectations"

Did NOT create a separate "director holds belief" proposition. The belief is understood as manifesting in the policy expectation.

### Issue #4: Generic Propositions (No Flattening) ✅
**User Feedback**: "Follow option A. Since there are no named items we do not need to flatten."

**Action**: Kept generic propositions for equipment:
- P_11: "Lab equipment is inspected weekly"
- P_12: "An item of lab equipment is low-risk"
- P_13: "Low-risk lab equipment is inspected monthly"

Unlike Exemplar 1 (Hospital) which flattens for Dr. Martinez and Dr. Yang, Exemplar 2 maintains generic statements since no specific equipment items are named.

### Issue #5: Ignored Other Issues ✅
**User Feedback**: "Ignore the rest of the issues."

**Action**: Did not implement suggestions from Issues #5-6 in the analysis document.

---

## Final Exemplar Structure

### Primitive Propositions: 22 total (P_1 through P_22)

**Lab Entry (P_1-P_3)**:
- P_1: Researcher enters laboratory
- P_2: Researcher wears protective equipment
- P_3: Researcher signs safety logbook

**Post-Experiment Cleanup (P_4-P_6)**:
- P_4: Researcher completes experiment
- P_5: Workspace is cleaned
- P_6: Chemicals properly stored

**Ventilation System (P_7-P_8)**:
- P_7: Fume hood is running
- P_8: Ventilation system turned off

**Supervision (P_9-P_10)** ⭐ Decomposed per user feedback:
- P_9: Undergraduate in first month
- P_10: Senior researcher supervises

**Equipment Inspection (P_11-P_13)**:
- P_11: Equipment inspected weekly
- P_12: Equipment is low-risk
- P_13: Low-risk equipment inspected monthly

**Emergency Response (P_14-P_16)**:
- P_14: Chemical spill occurs
- P_15: Area evacuated immediately
- P_16: Safety officer notified within 5 minutes

**Safety Meetings (P_17-P_18)**:
- P_17: Researcher attends safety meetings
- P_18: Researcher is experienced personnel

**Hazardous Materials (P_19-P_22)**:
- P_19: Experiment involves hazardous materials
- P_20: Experiment conducted with partner
- P_21: Researcher works after hours
- P_22: Researcher works alone

### Hard Constraints: 6 (H_1 through H_6)

- **H_1**: `P_1 ⟹ (P_2 ∧ P_3)` - Lab entry requirements
- **H_2**: `P_4 ⟹ (P_5 ∧ P_6)` - Post-experiment cleanup
- **H_3**: `P_7 ⟹ ¬P_8` - Ventilation prohibition
- **H_4**: `P_14 ⟹ (P_15 ∧ P_16)` - Emergency response
- **H_5**: `¬P_18 ⟹ P_17` - Non-experienced must attend meetings
- **H_6**: `P_21 ⟹ P_22` - After-hours work alone (observed fact)

### Soft Constraints: 5 (S_1 through S_5)

- **S_1**: `P_9 ⟹ P_10` - Supervision expectation (typically, not enforced)
- **S_2**: `P_11` - Weekly inspection recommended
- **S_3**: `P_12 ⟹ P_13` - Monthly acceptable for low-risk
- **S_4**: `P_18 ⟹ P_17` - Experienced encouraged to attend
- **S_5**: `P_19 ⟹ P_20` - Partner for hazardous materials (director's policy)

---

## Key Design Principles Demonstrated

### 1. Temporal Context in Constraints, Not Propositions
- **Proposition**: "The researcher wears protective equipment" (timeless)
- **Constraint**: `P_1 ⟹ P_2` (temporal relationship "before entering")

This maintains atomicity and reusability.

### 2. Decomposition of Compound Statements
Original text: "Senior researchers typically supervise undergraduate students during their first month"

Could be encoded as one proposition, but decomposed into:
- P_9: Temporal condition (first month)
- P_10: Action (supervision)
- Constraint: `P_9 ⟹ P_10`

**Benefit**: Can express violations and exceptions more precisely.

### 3. Belief as Policy
"The lab director believes X should Y" → interpreted as policy expectation, not epistemic state.
- Creates P_20 (action), not "director holds belief"
- Soft constraint S_5 captures the policy expectation

### 4. Generic vs. Instantiated Propositions
- **Exemplar 1** (Hospital): Flattens "all doctors" to Dr. Martinez and Dr. Yang
- **Exemplar 2** (Lab): Keeps generic "lab equipment" since no specific items named

Choice depends on whether the text provides specific instances.

### 5. Hard vs. Soft Constraint Classification

**Hard (must/cannot/emergency)**:
- "must wear" → H_1
- "cannot be turned off" → H_3
- "must be evacuated" → H_4

**Soft (should/typically/encouraged)**:
- "typically supervise" + "not always enforced" → S_1
- "should be inspected" → S_2
- "encouraged to attend" + "not mandatory" → S_4
- "believes...should" → S_5

**Mixed (mandatory for some, not for others)**:
- Non-experienced must attend → H_5 (hard)
- Experienced encouraged to attend → S_4 (soft)

---

## Input Format in Exemplar

### Original Text
8 sentences covering:
0. Lab entry requirements
1. Post-experiment cleanup
2. Ventilation system rules
3. Undergraduate supervision
4. Equipment inspection
5. Chemical spill response
6. Safety meeting attendance
7. Hazardous materials partnership

### OpenIE Triples (Format Shown)
Simple tab-separated format:
```
researchers	sign	safety logbook
equipment	is	protective
researchers	entering	laboratory
...
```

These are preprocessing hints, not authoritative. The exemplar shows how to use them to guide extraction while always grounding logic in the original text.

---

## Files Modified

1. **`/workspace/repo/code/prompts/prompt_logify2`**
   - Added EXEMPLAR 2 after existing hospital exemplar
   - Now contains 2 complete exemplars
   - 519 lines total (was 262)

---

## Next Steps

The updated prompt is now ready for use in the logify2 pipeline. When run, the LLM will have access to both exemplars:

1. **Hospital Triage Protocol** - Shows complex exception handling, belief vs. action, flattening for named entities
2. **Lab Safety Protocol** - Shows temporal decomposition, generic propositions, mixed hard/soft classification, policy interpretation

These two exemplars provide complementary guidance for different types of rule text.

---

## Verification

To verify the prompt works correctly, you can:

1. **Test with the lab safety input**:
   ```bash
   cd /workspace/repo/code/from_text_to_logic
   python logify2.py \
       --api-key YOUR_KEY \
       --file /workspace/repo/artifacts/lab_safety_input.txt \
       --output test_output.json \
       --model gpt-5.2 \
       --reasoning-effort high
   ```

2. **Check that the output follows the corrected structure**:
   - P_9 and P_10 are decomposed (not compound)
   - Numbering is sequential (9, 10, 11... not 9a, 9b, 11...)
   - Generic propositions maintained
   - Director's belief translated to policy expectation

---

**Status**: ✅ Complete

All user corrections have been applied and the exemplar has been successfully added to `prompt_logify2`.
