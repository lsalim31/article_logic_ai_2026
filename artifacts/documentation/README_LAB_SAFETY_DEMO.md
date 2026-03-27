# Lab Safety Rules - Logify2 Demo Files

This directory contains all files generated from executing logify2.py on laboratory safety regulations text.

## Files Overview

### Input
- **`lab_safety_input.txt`** (954 B)
  Original laboratory safety rules text with 8 sentences containing mixed obligation levels (must, should, encouraged).

### Stage 1 Output (OpenIE Extraction) ✅
- **`lab_safety_triples.json`** (2.5 KB)
  17 extracted relation triples in JSON format with subject-predicate-object structure, sentence indices, and source tags.

- **`lab_safety_llm_input.txt`** (1.6 KB)
  Formatted input combining original text and extracted triples, ready to send to LLM for Stage 2 processing.

### Execution Script
- **`run_logify2_lab_safety.py`** (4.2 KB)
  Python script that runs Stage 1 (OpenIE extraction) and displays results. Can be reused for similar text-to-logic tasks.

### Documentation
- **`LOGIFY2_EXECUTION_SUMMARY.md`** (9.9 KB)
  Quick reference guide with pipeline visualization, sample triples, expected logic rules, and execution instructions.

- **`LAB_SAFETY_LOGIFY2_EXECUTION_REPORT.md`** (9.8 KB)
  Comprehensive technical report with detailed analysis, extraction quality assessment, and neuro-symbolic reasoning insights.

- **`README_LAB_SAFETY_DEMO.md`** (THIS FILE)
  Index of all generated files.

---

## Quick Start

### View Extracted Triples
```bash
cat lab_safety_triples.json | jq
```

### View Formatted LLM Input
```bash
cat lab_safety_llm_input.txt
```

### Re-run OpenIE Extraction
```bash
python run_logify2_lab_safety.py
```

### Complete Full Pipeline (Requires OpenAI API Key)
```bash
cd /workspace/repo/code/from_text_to_logic

python logify2.py \
    --api-key YOUR_API_KEY \
    --file /workspace/repo/artifacts/lab_safety_input.txt \
    --output /workspace/repo/artifacts/lab_safety_output.json \
    --model gpt-4
```

---

## Sample Results

### Extracted Triple Example
```json
{
  "subject": "researchers",
  "predicate": "sign",
  "object": "safety logbook",
  "sentence_index": 0,
  "source": "openie"
}
```

### Expected Logic Rule (After Stage 2)
```
entering_lab → (wear_protective_equipment ∧ sign_logbook)
```

---

## Pipeline Status

| Stage | Status | Tool |
|-------|--------|------|
| Stage 1: OpenIE Extraction | ✅ Complete | Stanza + CoreNLP |
| Stage 2: LLM Logic Conversion | ⏳ Pending | GPT-4 (requires API key) |

---

## Related Files

- System prompt: `/workspace/repo/code/prompts/prompt_logify2`
- Logify2 source: `/workspace/repo/code/from_text_to_logic/logify2.py`
- OpenIE extractor: `/workspace/repo/code/from_text_to_logic/openie_extractor.py`
- Logic converter: `/workspace/repo/code/from_text_to_logic/logic_converter.py`

---

**Generated**: 2026-01-25
**Purpose**: Demonstrate text-to-logic pipeline for neuro-symbolic reasoning
