# Logify2.py Execution Summary - Lab Safety Rules

## Quick Reference

**Status**: ✅ Stage 1 Complete | ⏳ Stage 2 Pending (requires OpenAI API key)

**Input**: Laboratory safety regulations (8 sentences, 954 chars)

**Output Files**:
- `lab_safety_input.txt` - Original input text
- `lab_safety_triples.json` - 17 extracted OpenIE triples
- `lab_safety_llm_input.txt` - Formatted prompt for LLM
- `LAB_SAFETY_LOGIFY2_EXECUTION_REPORT.md` - Full technical report
- `run_logify2_lab_safety.py` - Execution script

---

## Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT TEXT: Laboratory Safety Regulations                      │
│ • 8 sentences with mixed obligation levels                     │
│ • Temporal constraints (5 minutes, weekly, monthly)            │
│ • Exception clauses ("not always enforced")                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: OpenIE Extraction ✅ COMPLETE                         │
│                                                                 │
│ Tools:                                                          │
│  • Stanza 1.11.0 (coreference resolution)                      │
│  • Stanford CoreNLP (OpenIE extraction)                        │
│  • Stanza dependency parser (fallback)                         │
│                                                                 │
│ Results:                                                        │
│  • 17 relation triples extracted                               │
│  • Subject-Predicate-Object format                             │
│  • Sentence indices preserved                                  │
│  • Sources tagged (openie vs. depparse)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: LLM Logic Conversion ⏳ PENDING                       │
│                                                                 │
│ Requirements:                                                   │
│  • OpenAI API key (GPT-4)                                      │
│  • Prompt: /workspace/repo/code/prompts/prompt_logify2        │
│                                                                 │
│ Expected Output:                                                │
│  • Primitive propositions (p1, p2, ...)                        │
│  • Hard constraints (MUST rules)                               │
│  • Soft constraints (SHOULD/ENCOURAGED rules)                  │
│  • Formal logic expressions                                    │
│  • JSON structured format                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: Structured Logic (JSON) ⏳ AWAITING COMPLETION         │
│                                                                 │
│ File: lab_safety_output.json                                   │
│                                                                 │
│ {                                                               │
│   "primitive_propositions": [...],                             │
│   "hard_constraints": [...],                                   │
│   "soft_constraints": [...]                                    │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sample Extracted Triples

### Hard Constraints (MUST)

| Subject | Predicate | Object | Sentence |
|---------|-----------|--------|----------|
| researchers | sign | safety logbook | 0 |
| workspace | must | must cleaned | 1 |
| chemicals | must | must properly stored | 1 |
| safety officer | must | must notified within 5 minutes | 5 |

### Descriptive Relations

| Subject | Predicate | Object | Sentence |
|---------|-----------|--------|----------|
| equipment | is | protective | 0 |
| students | is | undergraduate | 3 |
| researchers | is | Senior | 3 |
| safety meetings | is | monthly | 6 |

### Soft Constraints (SHOULD/ENCOURAGED)

| Subject | Predicate | Object | Sentence |
|---------|-----------|--------|----------|
| equipment | inspect | weekly | 4 |
| Researchers | attend | safety meetings | 6 |
| Researchers | are encouraged | not mandatory for experienced personnel | 6 |

---

## How to Complete Stage 2

### Method 1: Direct Execution

```bash
cd /workspace/repo/code/from_text_to_logic

python logify2.py \
    --api-key YOUR_OPENAI_API_KEY \
    --file /workspace/repo/artifacts/lab_safety_input.txt \
    --output /workspace/repo/artifacts/lab_safety_output.json \
    --model gpt-4
```

### Method 2: Environment Variable

```bash
export OPENAI_API_KEY="sk-proj-XXXXXXXX"

cd /workspace/repo/code/from_text_to_logic

python logify2.py \
    --file /workspace/repo/artifacts/lab_safety_input.txt \
    --output /workspace/repo/artifacts/lab_safety_output.json
```

---

## Expected Logic Rules (Post-Stage 2)

Based on the extracted triples, the LLM should generate:

### Hard Constraints (MUST)
1. `entering_lab → (wear_protective_equipment ∧ sign_logbook)`
2. `experiment_complete → (clean_workspace ∧ store_chemicals)`
3. `fume_hood_running → ¬turn_off_ventilation`
4. `chemical_spill → (evacuate_immediately ∧ notify_safety_officer ∧ within(5_minutes))`

### Soft Constraints (SHOULD - weight: 0.7-0.9)
5. `(undergraduate_student ∧ first_month) → supervised_by_senior` [weight: 0.7]
6. `inspect(equipment, weekly) ∨ (inspect(equipment, monthly) ∧ low_risk)` [weight: 0.8]

### Soft Constraints (ENCOURAGED - weight: 0.4-0.6)
7. `attend(safety_meetings) ∧ ¬MUST(experienced → attend)` [weight: 0.5]
8. `(hazardous_materials ∧ ¬after_hours) → partner_present` [weight: 0.6]

---

## Key Insights from Extraction

### Obligation Levels Detected
- **MUST** (hard): "must wear", "must be cleaned", "cannot be turned off", "must be notified"
- **SHOULD** (soft): "should be inspected", "typically supervise"
- **ENCOURAGED** (weak): "encouraged to attend", "believes that"

### Temporal Constraints
- "within 5 minutes" → hard deadline
- "weekly" vs "monthly" → frequency preference with exception
- "first month" → time-bounded condition

### Exception Handling
- "though this is not always enforced" → reduces constraint weight
- "but monthly inspections are acceptable for low-risk items" → conditional exception
- "but researchers working after hours sometimes work alone" → exception to recommendation

### Conditional Logic
- "Before entering..." → precondition
- "After completing..." → postcondition
- "While running..." → during condition
- "If spill occurs..." → event-triggered condition

---

## Technical Achievement

✅ **Successfully completed**:
1. Installed all dependencies (Stanza, CoreNLP, Java)
2. Initialized OpenIE extraction pipeline
3. Processed complex regulatory text with mixed obligation levels
4. Extracted 17 structured triples
5. Formatted input for LLM processing
6. Generated comprehensive documentation

⏳ **Awaiting**:
- OpenAI API key to complete Stage 2 (LLM logic conversion)

---

## Files Generated

```
/workspace/repo/artifacts/
├── lab_safety_input.txt                        (954 B) - Original text
├── lab_safety_triples.json                   (2.5 KB) - Extracted triples
├── lab_safety_llm_input.txt                  (1.6 KB) - LLM prompt input
├── run_logify2_lab_safety.py                 (4.7 KB) - Execution script
├── LAB_SAFETY_LOGIFY2_EXECUTION_REPORT.md   (13.4 KB) - Full report
└── LOGIFY2_EXECUTION_SUMMARY.md              (THIS FILE) - Quick reference
```

---

## Quick Statistics

| Metric | Value |
|--------|-------|
| Input sentences | 8 |
| Input characters | 954 |
| Extracted triples | 17 |
| OpenIE triples | 15 |
| Depparse triples | 2 |
| Hard constraints | ~4 |
| Soft constraints | ~4 |
| Coreference chains | Multiple |
| Processing time | ~3 seconds |

---

## Next Steps

1. **Obtain OpenAI API key**: https://platform.openai.com/api-keys
2. **Run Stage 2**: Execute command above with API key
3. **Verify output**: Check `lab_safety_output.json` for structured logic
4. **Validate logic**: Ensure constraints match original text semantics
5. **Test reasoning**: Use output with solver (Z3, Prover9) for inference

---

**Execution Date**: 2026-01-25
**Pipeline Version**: logify2.py
**Status**: ✅ OpenIE Complete | ⏳ LLM Pending
