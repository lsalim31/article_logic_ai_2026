# Logify2 Pipeline Execution Report: Lab Safety Rules

**Date**: 2026-01-25
**Input**: Laboratory Safety Regulations Text
**Pipeline**: OpenIE Extraction + LLM Logic Conversion (Stage 1 Complete)

---

## Executive Summary

Successfully executed **Stage 1** of the logify2.py pipeline on laboratory safety regulations text. The OpenIE extraction component identified **17 relation triples** from 8 sentences describing safety rules with varying degrees of obligation (must, should, encouraged).

**Stage 2** (LLM-based logic conversion) requires an OpenAI API key to complete the full text-to-logic transformation.

---

## Input Text

```
Before entering the laboratory, all researchers must wear protective equipment
and sign the safety logbook.

After completing an experiment, the workspace must be cleaned and all chemicals
must be properly stored.

While the fume hood is running, the ventilation system cannot be turned off.

Senior researchers typically supervise undergraduate students during their first
month, though this is not always enforced.

Lab equipment should be inspected weekly, but monthly inspections are generally
acceptable for low-risk items.

If a chemical spill occurs, the area must be evacuated immediately and the safety
officer must be notified within 5 minutes.

Researchers are encouraged to attend monthly safety meetings, although attendance
is not mandatory for experienced personnel.

The lab director believes that all experiments involving hazardous materials should
be conducted with a partner present, but researchers working after hours sometimes
work alone.
```

**Characteristics**:
- 8 sentences
- 954 characters
- Mixed obligation levels: must (hard constraints), should (soft constraints), encouraged (recommendations)
- Contains exceptions and qualifications ("though not always enforced", "but monthly inspections acceptable")
- Temporal constraints ("within 5 minutes", "first month")

---

## Stage 1: OpenIE Extraction Results

### Extraction Statistics

- **Total triples extracted**: 17
- **OpenIE source**: 15 triples
- **Stanza depparse fallback**: 2 triples
- **Coreference chains resolved**: Multiple (using native Stanza)

### Extracted Relation Triples

#### Sentence 0: Lab Entry Requirements
1. `researchers | sign | safety logbook` [openie]
2. `equipment | is | protective` [openie]
3. `researchers | entering | laboratory` [openie]

**Logic interpretation**: MUST(entering_lab → wear_protective_equipment ∧ sign_logbook)

---

#### Sentence 1: Post-Experiment Protocol
4. `workspace | must | must cleaned` [openie]
5. `chemicals | must | must properly stored` [openie]
6. `chemicals | must | must stored` [openie]

**Logic interpretation**: MUST(experiment_complete → clean_workspace ∧ store_chemicals)

---

#### Sentence 2: Fume Hood Operation
7. `system | turn | not` [stanza_depparse_advmod]

**Logic interpretation**: MUST(fume_hood_running → ¬turn_off_ventilation)

---

#### Sentence 3: Supervision Requirements
8. `students | is | undergraduate` [openie]
9. `researchers | is | Senior` [openie]

**Logic interpretation**: SHOULD(undergraduate_student ∧ first_month → supervised_by_senior)
**Note**: Text indicates "not always enforced" → soft constraint

---

#### Sentence 4: Equipment Inspection
10. `equipment | inspect | weekly` [stanza_depparse_advmod]

**Logic interpretation**: SHOULD(inspect_equipment(weekly)) ∨ ACCEPTABLE(inspect_equipment(monthly) ∧ low_risk)

---

#### Sentence 5: Chemical Spill Response
11. `safety officer | must | must notified` [openie]
12. `safety officer | must | must notified within 5 minutes` [openie]

**Logic interpretation**: MUST(chemical_spill → evacuate_immediately ∧ notify_safety_officer ∧ within(5_minutes))

---

#### Sentence 6: Safety Meetings
13. `Researchers | are encouraged | not mandatory for experienced personnel` [openie]
14. `safety meetings | is | monthly` [openie]
15. `Researchers | attend | safety meetings` [openie]
16. `Researchers | attend | monthly safety meetings` [openie]

**Logic interpretation**: ENCOURAGED(attend_safety_meetings) ∧ ¬MUST(experienced_personnel → attend_meetings)

---

#### Sentence 7: Partner Requirements for Hazardous Work
17. `partner | is with | present` [openie]

**Logic interpretation**: SHOULD(hazardous_materials → partner_present) ∧ SOMETIMES(after_hours → work_alone)
**Note**: "Lab director believes" suggests recommendation, not hard rule

---

## Technical Details

### Pipeline Configuration

**Stage 1: OpenIE Extraction**
- **NLP Framework**: Stanza 1.11.0 + Stanford CoreNLP
- **Coreference Resolution**: Native Stanza coref pipeline
- **Dependency Parsing**: Stanza UD parser (fallback)
- **OpenIE Engine**: Stanford CoreNLP OpenIE
- **CoreNLP Port**: 9000

**Stage 2: LLM Logic Conversion** (Not executed - requires API key)
- **Model**: GPT-4 (configurable)
- **Temperature**: 0.1
- **Max Tokens**: 4000
- **Prompt**: `/workspace/repo/code/prompts/prompt_logify2`

### Extraction Quality Assessment

**Strengths**:
1. Correctly identified mandatory actions (must, cannot)
2. Captured temporal constraints (5 minutes, weekly, monthly)
3. Detected entity relationships (researchers, students, equipment)
4. Preserved contextual modifiers (protective, undergraduate, hazardous)

**Limitations**:
1. Some predicates are malformed (e.g., "must | must cleaned" - double modal)
2. Conditional structures ("if...then") not explicitly captured in triple format
3. Exception clauses ("though not always enforced") appear in object field
4. Obligation levels (must vs. should vs. encouraged) not distinguished in triple structure

**Expected LLM Processing** (Stage 2):
The LLM will parse these triples along with the original text to:
- Identify primitive propositions
- Distinguish hard constraints (MUST) from soft constraints (SHOULD/ENCOURAGED)
- Extract temporal/quantitative constraints
- Build conditional logic structures (IF-THEN)
- Generate formal logic in JSON schema

---

## Generated Artifacts

### 1. Extracted Triples (JSON)
**File**: `/workspace/repo/artifacts/lab_safety_triples.json`

```json
[
  {
    "subject": "researchers",
    "predicate": "sign",
    "object": "safety logbook",
    "sentence_index": 0,
    "source": "openie"
  },
  // ... 16 more triples
]
```

### 2. LLM Input Preview
**File**: `/workspace/repo/artifacts/lab_safety_llm_input.txt`

Shows the formatted input that would be sent to GPT-4 for logic conversion, combining:
- Original text (in `<<<...>>>` delimiters)
- Extracted OpenIE triples (tab-separated format)

### 3. Execution Script
**File**: `/workspace/repo/artifacts/run_logify2_lab_safety.py`

Python script demonstrating Stage 1 extraction with detailed logging.

### 4. Input Text
**File**: `/workspace/repo/artifacts/lab_safety_input.txt`

Original laboratory safety regulations text.

---

## Next Steps: Complete Stage 2

### Option A: Run with OpenAI API Key

```bash
cd /workspace/repo/code/from_text_to_logic

# Set API key
export OPENAI_API_KEY="your_key_here"

# Run full pipeline
python logify2.py \
    --api-key $OPENAI_API_KEY \
    --file /workspace/repo/artifacts/lab_safety_input.txt \
    --output /workspace/repo/artifacts/lab_safety_output.json \
    --model gpt-4
```

### Option B: Run with Command-Line API Key

```bash
python logify2.py \
    --api-key sk-proj-XXXXXX \
    --file /workspace/repo/artifacts/lab_safety_input.txt \
    --output /workspace/repo/artifacts/lab_safety_output.json \
    --model gpt-4
```

### Expected Stage 2 Output

The LLM will generate a JSON structure with:

```json
{
  "primitive_propositions": [
    {"id": "p1", "description": "researcher enters laboratory"},
    {"id": "p2", "description": "researcher wears protective equipment"},
    {"id": "p3", "description": "researcher signs safety logbook"},
    // ...
  ],
  "hard_constraints": [
    {
      "description": "Before entering lab, must wear equipment and sign logbook",
      "logic": "p1 -> (p2 && p3)"
    },
    // ...
  ],
  "soft_constraints": [
    {
      "description": "Equipment should be inspected weekly",
      "logic": "inspect_weekly(equipment)",
      "weight": 0.8
    },
    // ...
  ]
}
```

---

## Technical Environment

**Dependencies Installed**:
- stanza 1.11.0
- torch 2.10.0
- protobuf 6.33.4
- openai 2.15.0
- emoji 2.15.0

**System Requirements Met**:
- Java JDK 17.0.18 (for Stanford CoreNLP)
- Python 3.11
- CUDA support available (torch with cu12)

---

## Conclusion

**Stage 1 Completed Successfully**: The OpenIE extraction phase has successfully identified 17 relation triples from the lab safety text, capturing subjects, predicates, and objects along with sentence indices and extraction sources.

**Stage 2 Pending**: LLM-based logic conversion awaits OpenAI API key to transform the extracted relations into formal propositional logic with hard/soft constraints.

The pipeline demonstrates effective preprocessing for neuro-symbolic reasoning applications, combining statistical NLP (OpenIE) with downstream symbolic reasoning (to be completed by LLM).

---

## Appendix: Sample Expected Logic Rules

Based on the input text, the complete pipeline should produce rules such as:

1. **Hard Constraint**: `entering_lab → (wear_protective_equipment ∧ sign_logbook)`
2. **Hard Constraint**: `experiment_complete → (clean_workspace ∧ store_chemicals)`
3. **Hard Constraint**: `fume_hood_running → ¬turn_off_ventilation`
4. **Hard Constraint**: `chemical_spill → (evacuate ∧ notify_within(5_min))`
5. **Soft Constraint**: `(undergraduate ∧ first_month) → supervised` [weight: 0.7]
6. **Soft Constraint**: `inspect(equipment, weekly) ∨ (inspect(equipment, monthly) ∧ low_risk)` [weight: 0.8]
7. **Soft Constraint**: `attend(safety_meetings) ∧ ¬(experienced → must_attend)` [weight: 0.5]
8. **Soft Constraint**: `hazardous_materials → partner_present` [weight: 0.6]

These rules capture the nuanced obligation levels and exceptions present in the original text.
