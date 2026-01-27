# FOL vs Boolean Extraction Comparison

Minimal experiment to demonstrate that propositional (boolean) extraction has fewer formalization errors than FOL extraction.

## Goal

Show that propositional logic extraction is more reliable than FOL extraction by:
1. Running both extractors on the same texts
2. Counting automatic formalization failures
3. Comparing error rates

## Structure

```
fol_vs_boolean/
├── data/
│   ├── raw/source_examples.jsonl         # Input examples
│   ├── extractions/
│   │   ├── propositional.jsonl           # Propositional outputs
│   │   └── fol.jsonl                     # FOL outputs
│   └── results/error_analysis.json       # Final results
├── extract_propositional.py              # Propositional wrapper
├── extract_fol.py                        # FOL wrapper
├── run_dual_extraction.py                # Main extraction script
├── analyze_errors.py                     # Error analysis
└── README.md                             # This file
```

## Usage

### Quick Start: LogicBench Experiment (Recommended)

Run the single-file experiment with LogicBench dataset:

```bash
pip install datasets  # Install HuggingFace datasets library
python run_logicbench_experiment.py
```

This will:
- Load LogicBench dataset from HuggingFace (50 examples by default)
- Run both propositional and FOL extraction on same examples
- Analyze and compare error rates
- Save results to `data/logicbench_results/`

**Advantages**: No manual data preparation, uses standardized benchmark, all-in-one script.

### Alternative: Custom Data Pipeline

For custom datasets, use the modular pipeline:

#### Step 1: Prepare Data

Create `data/raw/source_examples.jsonl` with format:

```jsonl
{"id": "001", "text": "Alice is a student. All students are human.", "query": "Is Alice human?"}
{"id": "002", "text": "Bob teaches math. All teachers work hard.", "query": "Does Bob work hard?"}
```

#### Step 2: Run Dual Extraction

```bash
python run_dual_extraction.py
```

This will:
- Load examples from `data/raw/source_examples.jsonl`
- Extract propositional logic for each example
- Extract FOL for each example
- Save results to `data/extractions/`

#### Step 3: Analyze Errors

```bash
python analyze_errors.py
```

This will:
- Load extraction results
- Count failures for each mode
- Analyze error patterns
- Save comparison to `data/results/error_analysis.json`

## Success Detection

### Propositional (logify_text)
- **Success**: Function returns normally
- **Failure**: Raises `ValueError` or `RuntimeError`

### FOL (formalize_to_fol)
- **Success**: `result['formalization_error'] is None`
- **Failure**: `result['formalization_error']` contains error message

## Expected Output

```json
{
  "total_examples": 50,
  "propositional": {
    "failures": 2,
    "error_rate": 0.04
  },
  "fol": {
    "failures": 11,
    "error_rate": 0.22
  },
  "comparison": {
    "absolute_difference": 9,
    "percentage_point_difference": 0.18,
    "conclusion": "FOL has more errors"
  }
}
```

## Implementation Details

- **No code duplication**: Imports existing functions via `sys.path`
- **Thin wrappers**: ~40 lines each for standardized output
- **Simple analysis**: Just count failures, no complex statistics
- **Automatic detection**: Uses formalization success/failure only

## Data Sources

**Primary (Recommended)**:
- **LogicBench** (ACL 2024) - Use `run_logicbench_experiment.py`
  - Systematic reasoning benchmark with both PL and FOL subsets
  - Automatically loaded from HuggingFace

**Alternative** (for custom pipeline):
- FOLIO test set (50 examples)
- ProofWriter depth-5 (50 examples)
- Custom examples in JSONL format

## Timeline

- Setup + data prep: 1 hour
- Run extraction: 30 min (depends on # examples)
- Analysis: 5 min
- **Total: ~1.5-2 hours**
