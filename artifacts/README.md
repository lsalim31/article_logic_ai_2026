# Artifacts Directory

This directory contains test outputs, analyses, and documentation for the logify2 pipeline and OpenIE extraction system.

## Directory Structure

```
artifacts/
├── README.md                    (this file)
│
├── logify2_testing/            # Logify2 pipeline test files
│   ├── run_logify2_lab_safety.py      # Test runner for lab safety example
│   ├── lab_safety_input.txt           # Input text for lab safety rules
│   ├── lab_safety_llm_input.txt       # Formatted input sent to LLM
│   ├── lab_safety_output.json         # LLM output (standard)
│   ├── lab_safety_output_high.json    # LLM output (high reasoning)
│   └── lab_safety_triples.json        # OpenIE triples extracted
│
├── openie_testing/             # OpenIE extraction test files
│   ├── test_array_format.py           # Test script for array format
│   ├── verify_openie_fix.py           # Verification script for fixes
│   ├── openie_array_format_output.json    # New array format output
│   ├── openie_old_format_output.json      # Old dict format output
│   └── openie_output.txt              # Human-readable output
│
├── analyses/                   # Analysis documents and reports
│   ├── LOGIFICATION_ANALYSIS.md           # Quality analysis of lab safety output
│   ├── LAB_SAFETY_LOGIFY2_EXECUTION_REPORT.md  # Execution report
│   ├── LOGIFY2_EXECUTION_SUMMARY.md       # Summary of execution results
│   ├── STAGE2_EXECUTION_REPORT.md         # Stage 2 (LLM) report
│   └── array_format_comparison.md         # Format comparison analysis
│
├── documentation/              # Implementation documentation
│   ├── EXEMPLAR_ADDITION_SUMMARY.md       # Lab safety exemplar addition
│   ├── COREFERENCE_FIX_SUMMARY.md         # Coreference resolution fix
│   ├── JSON_OUTPUT_USAGE.md               # JSON output format guide
│   ├── NEW_ARRAY_FORMAT_SUMMARY.md        # Array format documentation
│   ├── OUTPUT_FORMAT_RECOMMENDATIONS.md   # Format recommendations
│   ├── README_LAB_SAFETY_DEMO.md          # Lab safety demo guide
│   ├── logify2_implementation_summary.md  # Implementation overview
│   ├── stanford_openie_integration_summary.md  # Stanford OpenIE integration
│   ├── stanza_openie_integration_summary.md    # Stanza integration
│   ├── openie_coreference_fix.md          # Coreference fix details
│   └── bibliography_update_jan21.md       # Bibliography updates
│
├── code/                       # Test code and demos
│   ├── README.md                          # Code directory documentation
│   ├── coref_test_analysis.md             # Coreference test analysis
│   ├── test_coref_resolution.py           # Coref resolution test
│   ├── test_stanza_extractor.py           # Stanza extractor test
│   ├── test_logify2_demo.py               # Logify2 demo test
│   ├── stanford_openie_demo.py            # Stanford OpenIE demo
│   ├── stanza_openie_demo.py              # Stanza OpenIE demo
│   ├── logify2_full_demo.py               # Full pipeline demo
│   ├── logify2_demo_output.json           # Demo output
│   ├── logify2_full_demo.json             # Full demo output
│   ├── stanford_openie_full_demo.json     # Stanford demo output
│   └── test_text.txt                      # Test input text
│
├── few_shot_examples/          # Few-shot learning examples
│   ├── inputs/                            # Example input texts
│   │   └── example_01_medical_policy.txt
│   ├── outputs/                           # Example outputs and templates
│   │   ├── example_01_few_shot_complete.json
│   │   ├── example_01_for_prompt.txt
│   │   ├── example_01_logify_output.json
│   │   ├── example_01_medical_policy_openie_input.txt
│   │   ├── example_01_medical_policy_output.json
│   │   └── example_01_medical_policy_output_template.json
│   └── run_logify_simple.py               # Simple runner script
│
├── notes/                      # Research notes and analysis
│   ├── implementation_status_analysis.md  # Implementation status
│   ├── logical_representation_analysis.md # Logic representation notes
│   ├── project_report.md                  # Project report
│   ├── proposition_extraction_research.md # Proposition extraction research
│   └── weight_assignment_report.md        # Weight assignment research
│
├── reports/                    # Comparative reports
│   └── weight_assignment_comparative_analysis.md
│
├── reviews/                    # Paper reviews and critiques
│   ├── icml_2026_review_jan23.md          # ICML 2026 review
│   ├── logify_review.md                   # Logify system review
│   ├── review.md                          # General review
│   └── weight_methods_analysis.md         # Weight methods analysis
│
└── old_files/                  # Deprecated or temporary files
    ├── test.txt                           # Old test file
    ├── json_format_example.json           # Old format example
    └── PROOF_OF_EXECUTION.txt             # Old proof file

```

## Quick Reference

### Running Tests

**Logify2 Full Pipeline:**
```bash
cd /workspace/repo/artifacts/logify2_testing
python run_logify2_lab_safety.py
```

**OpenIE Array Format Test:**
```bash
cd /workspace/repo/artifacts/openie_testing
python test_array_format.py
```

**Coreference Resolution Test:**
```bash
cd /workspace/repo/artifacts/code
python test_coref_resolution.py
```

### Key Files

- **Main prompt**: `/workspace/repo/code/prompts/prompt_logify2`
- **OpenIE extractor**: `/workspace/repo/code/from_text_to_logic/openie_extractor.py`
- **Logify2 pipeline**: `/workspace/repo/code/from_text_to_logic/logify2.py`

### Analysis Documents

- **Lab safety quality analysis**: `analyses/LOGIFICATION_ANALYSIS.md`
- **Exemplar addition summary**: `documentation/EXEMPLAR_ADDITION_SUMMARY.md`
- **Array format comparison**: `analyses/array_format_comparison.md`

## File Naming Conventions

- **Test scripts**: `test_*.py` or `*_test.py`
- **Demo scripts**: `*_demo.py`
- **Runner scripts**: `run_*.py`
- **Input files**: `*_input.txt`
- **Output files**: `*_output.json`
- **Analysis documents**: `*_ANALYSIS.md` or `*_analysis.md`
- **Summary documents**: `*_SUMMARY.md`
- **Reports**: `*_REPORT.md` or `*_report.md`

## Notes

- Test outputs are versioned (e.g., `lab_safety_output.json` vs `lab_safety_output_high.json`)
- Old or deprecated files are moved to `old_files/`
- All test scripts include paths relative to `/workspace/repo/`
- OpenIE triples use the new array format: `[subject, predicate, object, sentence_index]`
