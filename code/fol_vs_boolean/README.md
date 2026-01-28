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
├── load_logicbench.py                    # Reusable LogicBench loader
├── extract_propositional.py              # Propositional wrapper
├── extract_fol.py                        # FOL wrapper
├── run_dual_extraction.py                # Main extraction script
├── analyze_errors.py                     # Error analysis
├── run_logicbench_experiment.py          # Single-file LogicBench experiment
└── README.md                             # This file
```

## Usage

### Quick Start: LogicBench Experiment (Recommended)

Run the single-file experiment with LogicBench dataset:

```bash
# Set your API key (required for propositional extraction)
# Use OPENROUTER_API_KEY or OPENAI_API_KEY
export OPENROUTER_API_KEY='your-key-here'

# Run the experiment (no additional dependencies needed - loads from GitHub)
python run_logicbench_experiment.py
```

This will:
- Load LogicBench dataset directly from GitHub (no HuggingFace account needed)
- Uses propositional logic examples (modus_tollens, disjunctive_syllogism patterns)
- Run both propositional and FOL extraction on same examples
- Analyze and compare error rates
- Save results to `data/logicbench_results/`

**Advantages**: No manual data preparation, no external accounts needed, uses standardized benchmark, all-in-one script.

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

## Reusing LogicBench Data in Other Scripts

The `load_logicbench.py` module provides reusable functions for loading LogicBench data:

```python
# Import the loader
from load_logicbench import load_logicbench, load_all_propositional, load_all_fol

# Example 1: Load specific patterns
examples = load_logicbench(
    logic_type='propositional_logic',
    reasoning_patterns=['modus_tollens', 'disjunctive_syllogism'],
    max_examples_per_pattern=10
)

# Example 2: Load all propositional logic patterns
examples = load_all_propositional(max_examples_per_pattern=5)

# Example 3: Load all FOL patterns
examples = load_all_fol(max_examples_per_pattern=5)

# Each example is a dict with:
# {
#   'id': str,
#   'text': str,           # Context/premises
#   'query': str,          # Question
#   'ground_truth': bool,  # Answer
#   'pattern': str,        # Reasoning pattern (e.g., 'modus_tollens')
#   'logic_type': str      # 'propositional_logic' or 'first_order_logic'
# }
```

This module can be imported from any script in your codebase. Just add the appropriate path:

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'path', 'to', 'fol_vs_boolean'))
from load_logicbench import load_logicbench
```

## Timeline

- Setup + data prep: 1 hour
- Run extraction: 30 min (depends on # examples)
- Analysis: 5 min
- **Total: ~1.5-2 hours**
