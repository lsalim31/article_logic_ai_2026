# How to Use Logic-LM++: Complete Usage Guide

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Configuration Options](#4-configuration-options)
5. [Running on Datasets](#5-running-on-datasets)
6. [Understanding Output](#6-understanding-output)
7. [Testing](#7-testing)
8. [Customization](#8-customization)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: ~8GB RAM (for LLM API calls and theorem provers)
- **Storage**: ~500MB for datasets and models
- **Network**: Internet connection for API calls and dataset downloads

### External Dependencies

#### Required: OpenAI API
Logic-LM++ requires an OpenAI API key for LLM-based formalization and refinement.

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

Or add to your shell profile (`.bashrc`, `.zshrc`):
```bash
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.bashrc
source ~/.bashrc
```

#### Required: Theorem Provers

**Prover9** (primary FOL theorem prover):
```bash
# On Ubuntu/Debian
sudo apt-get install prover9

# On macOS (Homebrew)
brew install prover9

# Verify installation
prover9 -help
```

**Z3** (fallback SMT solver):
```bash
# Via pip (recommended)
pip install z3-solver

# Or via system package manager
# Ubuntu/Debian
sudo apt-get install z3

# macOS
brew install z3
```

---

## 2. Installation

### Step 1: Clone Repository
```bash
cd /workspace/repo/code/baseline_logiclm_plus
```

### Step 2: Install Python Dependencies
```bash
pip install openai>=1.0.0
pip install datasets>=2.0.0
pip install z3-solver>=4.12.0
pip install numpy>=1.21.0
pip install tqdm  # For progress bars
```

Or use a requirements file:
```bash
cat > requirements.txt <<EOF
openai>=1.0.0
datasets>=2.0.0
z3-solver>=4.12.0
numpy>=1.21.0
tqdm>=4.65.0
EOF

pip install -r requirements.txt
```

### Step 3: Verify Installation
```bash
python test_logiclm.py
```

Expected output:
```
Running Logic-LM++ tests...

✓ Formalizer tests passed
✓ Refiner tests passed
✓ Backtracking tests passed
✓ Solver interface tests passed
✓ Evaluator tests passed

==================================================
All tests passed successfully!
==================================================
```

---

## 3. Quick Start

### Single Query Example

```python
from main import run_logiclm_plus
from config import MODEL_NAME, MAX_REFINEMENT_ITERATIONS

# Define input
text = """
All students are humans.
No young person teaches.
Rose is a young student.
"""

query = "Is Rose a human?"
ground_truth = "True"

# Run Logic-LM++ pipeline
result = run_logiclm_plus(
    text=text,
    query=query,
    model_name=MODEL_NAME,
    config={
        'max_iterations': MAX_REFINEMENT_ITERATIONS,
        'num_candidates': 2,
        'max_consecutive_backtracks': 2
    },
    ground_truth=ground_truth
)

# Inspect results
print(f"Answer: {result['answer']}")
print(f"Correct: {result['correct']}")
print(f"Refinement iterations: {result['num_refinement_iterations']}")
print(f"Backtracking history: {result['backtracking_history']}")
print(f"Total LLM calls: {result['total_llm_calls']}")
print(f"Total time: {result['total_time']:.2f}s")
```

### Command-Line Usage

```bash
# Run on FOLIO dataset
python main.py --dataset folio --output results_folio.json

# Run on ProofWriter dataset
python main.py --dataset proofwriter --output results_proofwriter.json

# Run on AR-LSAT dataset
python main.py --dataset ar-lsat --output results_arlsat.json
```

---

## 4. Configuration Options

### File: `config.py`

All hyperparameters are defined in `config.py`. You can edit this file or override values programmatically.

#### Model Configuration

```python
MODEL_NAME = "openai/gpt-4"       # LLM for formalization/refinement
TEMPERATURE = 0                    # Deterministic generation
MAX_TOKENS = 2048                  # Max tokens per LLM response
```

**Options for MODEL_NAME**:
- `"openai/gpt-4"` (recommended, best performance)
- `"openai/gpt-4-turbo"` (faster, slightly lower accuracy)
- `"openai/gpt-3.5-turbo"` (cheaper, lower accuracy)

#### Refinement Hyperparameters

```python
MAX_REFINEMENT_ITERATIONS = 4      # Max refinement iterations (0-4 tested in paper)
NUM_REFINEMENT_CANDIDATES = 2      # Candidates per iteration (N=2 for pairwise)
MAX_CONSECUTIVE_BACKTRACKS = 2     # Early stop threshold (consecutive REVERTs)
```

**Tuning guidance**:
- **MAX_REFINEMENT_ITERATIONS**:
  - `0`: No refinement (baseline)
  - `1-2`: Fast, may miss convergence
  - `3-4`: Recommended (tested in paper)
  - `>4`: Diminishing returns, higher cost

- **NUM_REFINEMENT_CANDIDATES**:
  - Must be `≥2` for pairwise comparison
  - Paper uses `N=2` (optimal cost-benefit)
  - Higher N increases cost without significant gains

- **MAX_CONSECUTIVE_BACKTRACKS**:
  - `1`: Aggressive early stopping
  - `2`: Recommended (balanced)
  - `≥3`: May waste iterations after convergence

#### Solver Configuration

```python
SOLVER_TIMEOUT = 30                # Seconds (per proof attempt)
SYMBOLIC_TARGET = "FOL"            # First-order logic
```

**Tuning guidance**:
- **SOLVER_TIMEOUT**:
  - `10s`: Fast, may timeout on complex proofs
  - `30s`: Recommended (balanced)
  - `60s`: For complex AR-LSAT problems
  - `>60s`: Rarely needed, risk of hanging

#### Prompt Templates

Defined in `config.py`:
- `FORMALIZATION_PROMPT`: NL → FOL translation
- `REFINEMENT_PROMPT`: Context-rich refinement with self-reflection
- `PAIRWISE_COMPARISON_PROMPT`: Semantic comparison of candidates
- `BACKTRACKING_PROMPT`: IMPROVED vs. REVERT decision

**Customization**: Edit prompts in `config.py` if needed, but default prompts match paper methodology.

---

## 5. Running on Datasets

### Supported Datasets

| Dataset | Examples | Task | Labels | Source |
|---------|----------|------|--------|--------|
| **FOLIO** | 204 (test) | FOL reasoning | True/False/Uncertain | HuggingFace: `yale-nlp/FOLIO` |
| **ProofWriter** | 600 (OWA 5-hop) | Proof generation | Proved/Disproved/Unknown | HuggingFace: `allenai/proofwriter` |
| **AR-LSAT** | 231 | Multiple-choice FOL | A/B/C/D/E | HuggingFace: `allenai/ar-lsat` |

### Basic Usage

```bash
python main.py --dataset DATASET_NAME --output OUTPUT_FILE
```

**Parameters**:
- `--dataset`: Required. One of: `folio`, `proofwriter`, `ar-lsat`
- `--output`: Optional. JSON output file path (default: `results.json`)
- `--model`: Optional. LLM model name (default: from `config.py`)
- `--max-iterations`: Optional. Override `MAX_REFINEMENT_ITERATIONS`
- `--num-candidates`: Optional. Override `NUM_REFINEMENT_CANDIDATES`
- `--verbose`: Optional. Print detailed progress

### Examples

#### Example 1: FOLIO with defaults
```bash
python main.py --dataset folio --output folio_results.json
```

**Expected runtime**: ~2-4 hours (204 examples × ~1-2 min/example)

**Expected output snippet**:
```
Loading dataset: folio (204 test examples)
Processing example 1/204: [Student-Teacher reasoning]
  - Formalization: success (3 predicates, 5 premises)
  - Refinement iteration 1: IMPROVED
  - Refinement iteration 2: REVERT (backtrack)
  - Early stop: consecutive backtracks (2)
  - Solver: Proved (0.8s)
  - Answer: True, Ground truth: True ✓
Processing example 2/204: ...
...
Evaluation complete.
Overall accuracy: 84.80%
Execution rate (Er): 92.16%
Execution accuracy (Ea): 92.02%
Results saved to: folio_results.json
```

#### Example 2: ProofWriter with GPT-3.5 (faster/cheaper)
```bash
python main.py \
  --dataset proofwriter \
  --output proofwriter_gpt35.json \
  --model openai/gpt-3.5-turbo
```

**Expected runtime**: ~8-12 hours (600 examples, slower with GPT-3.5 refinements)

#### Example 3: AR-LSAT with fewer iterations
```bash
python main.py \
  --dataset ar-lsat \
  --output arlsat_fast.json \
  --max-iterations 2
```

**Expected runtime**: ~2-3 hours (231 examples × 2 iterations max)

#### Example 4: Small subset for testing
```python
# In Python shell
from main import load_dataset, run_batch

# Load full dataset
examples = load_dataset('folio')

# Take first 10 examples
subset = examples[:10]

# Run on subset
results = run_batch(
    examples=subset,
    model_name='openai/gpt-4',
    config={
        'max_iterations': 4,
        'num_candidates': 2,
        'max_consecutive_backtracks': 2
    },
    output_dir='test_output'
)

print(f"Accuracy on subset: {results['accuracy_metrics']['overall_accuracy']:.2%}")
```

---

## 6. Understanding Output

### Output File Structure

Results are saved as JSON in the specified output file:

```json
{
  "metadata": {
    "dataset": "folio",
    "model": "openai/gpt-4",
    "config": {
      "max_iterations": 4,
      "num_candidates": 2,
      "max_consecutive_backtracks": 2
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "num_examples": 204
  },
  "accuracy_metrics": {
    "overall_accuracy": 0.848,
    "per_class": {
      "True": {"precision": 0.89, "recall": 0.85, "f1": 0.87},
      "False": {"precision": 0.83, "recall": 0.88, "f1": 0.85},
      "Uncertain": {"precision": 0.79, "recall": 0.82, "f1": 0.80}
    },
    "confusion_matrix": [[120, 10, 5], [8, 95, 7], [5, 6, 48]]
  },
  "logiclm_metrics": {
    "execution_rate_Er": 0.9216,
    "execution_accuracy_Ea": 0.9202,
    "formalization_success_rate": 0.9608,
    "avg_refinement_iterations": 2.34,
    "backtracking_rate": 0.31,
    "early_stopping_rate": 0.45
  },
  "backtracking_stats": {
    "num_formulations_corrected_per_iteration": [45, 28, 12, 5],
    "with_backtracking": 90,
    "without_backtracking": 78,
    "winning_cases": 67,
    "losing_cases": 12
  },
  "efficiency_metrics": {
    "avg_time_per_query": 85.3,
    "avg_llm_calls_per_query": 9.7,
    "time_breakdown": {
      "formalization": 12.1,
      "refinement": 58.4,
      "backtracking": 8.2,
      "solving": 6.6
    },
    "total_cost_estimate": 45.60
  },
  "examples": [
    {
      "id": 0,
      "text": "All students are humans. No young person teaches. Rose is a young student.",
      "query": "Is Rose a human?",
      "ground_truth": "True",
      "answer": "Proved",
      "correct": true,
      "initial_formulation": {
        "predicates": {"Student(x)": "x is a student", "Human(x)": "x is a human", ...},
        "premises": ["∀x (Student(x) → Human(x))", "¬∃x (Young(x) ∧ Teach(x))", ...],
        "conclusion": "Human(rose)"
      },
      "final_formulation": { ... },
      "num_refinement_iterations": 2,
      "backtracking_history": ["IMPROVED", "REVERT"],
      "num_backtracks": 1,
      "early_stop_reason": "consecutive_backtracks",
      "total_llm_calls": 7,
      "total_time": 78.5,
      "time_breakdown": { ... },
      "formalization_success": true,
      "execution_success": true,
      "execution_accuracy": true,
      "formulation_history": [ ... ]
    },
    ...
  ]
}
```

### Key Metrics Explained

#### Accuracy Metrics
- **overall_accuracy**: % examples with correct final answer
- **per_class**: Precision, recall, F1 per label (True/False/Uncertain, etc.)
- **confusion_matrix**: Row=ground truth, Column=prediction

#### Logic-LM++ Specific Metrics

**Execution Rate (Er)**:
- **Definition**: % formulations that execute without syntax/runtime errors
- **Formula**: `Er = executed_formulations / total_queries`
- **Note**: Includes semantically wrong but syntactically correct formulations

**Execution Accuracy (Ea)**:
- **Definition**: % correct answers among executed formulations
- **Formula**: `Ea = correct_answers / executed_formulations` (NOT total_queries)
- **Interpretation**: Quality of successfully executed formulations

**Other Metrics**:
- **formalization_success_rate**: % initial formalizations that parse correctly
- **avg_refinement_iterations**: Mean iterations actually run (≤ MAX due to early stopping)
- **backtracking_rate**: % iterations where REVERT occurred
- **early_stopping_rate**: % examples stopped before max iterations

#### Backtracking Statistics
- **num_formulations_corrected_per_iteration**: List showing corrections at each iteration
- **with_backtracking**: Total corrections with backtracking enabled
- **without_backtracking**: Hypothetical corrections without backtracking (for comparison)
- **winning_cases**: Examples where refinement improved final answer
- **losing_cases**: Examples where refinement would degrade without backtracking

#### Efficiency Metrics
- **avg_time_per_query**: Mean time (seconds) per example
- **avg_llm_calls_per_query**: Mean API calls per example
  - Formula: `1 (formalization) + 2×iterations (candidates) + iterations (pairwise) + iterations (backtracking)`
  - Example: 4 iterations = 1 + 8 + 4 + 4 = 17 calls
- **time_breakdown**: Time spent in each stage
- **total_cost_estimate**: Estimated API cost (USD) for entire run

---

## 7. Testing

### Unit Tests

Run all unit tests:
```bash
python test_logiclm.py
```

### Test Individual Modules

#### Test Formalizer
```python
from formalizer import formalize_to_fol

result = formalize_to_fol(
    text="All students are humans.",
    query="Is Rose a human?",
    model_name="openai/gpt-4"
)

print(result['predicates'])
print(result['premises'])
print(result['conclusion'])
```

#### Test Refiner
```python
from refiner import refine_loop

initial_formulation = {
    'predicates': {'Student(x)': 'x is a student'},
    'premises': ['∀x Student(x)'],  # Intentionally incomplete
    'conclusion': 'Student(rose)'
}

result = refine_loop(
    initial_formulation=initial_formulation,
    original_text="All students are humans. Rose is a student.",
    original_query="Is Rose a human?",
    max_iterations=4
)

print(f"Iterations: {result['num_iterations']}")
print(f"Backtracks: {result['num_backtracks']}")
print(f"Backtracking history: {result['backtracking_history']}")
```

#### Test Solver Interface
```python
from solver_interface import solve_fol

result = solve_fol(
    premises=['∀x (Student(x) → Human(x))', 'Student(rose)'],
    conclusion='Human(rose)',
    solver='prover9',
    timeout=30
)

print(f"Answer: {result['answer']}")  # Should be 'Proved'
print(f"Solver time: {result['solver_time']:.2f}s")
```

### Integration Test

```bash
# Run on single example
python -c "
from main import run_logiclm_plus

result = run_logiclm_plus(
    text='All students are humans. Rose is a student.',
    query='Is Rose a human?',
    model_name='openai/gpt-4',
    config={'max_iterations': 2, 'num_candidates': 2, 'max_consecutive_backtracks': 2},
    ground_truth='True'
)

print(f'Answer: {result[\"answer\"]}')
print(f'Correct: {result[\"correct\"]}')
"
```

---

## 8. Customization

### Modify Prompts

Edit `config.py` to customize prompts:

```python
# Example: Add domain-specific guidance to formalization prompt
FORMALIZATION_PROMPT = """You are a formal logician specializing in LEGAL reasoning.

[Rest of prompt...]
"""
```

### Add Custom Dataset

```python
from main import run_batch

# Define custom examples
custom_examples = [
    {
        'text': 'All contracts require consideration. This agreement lacks consideration.',
        'query': 'Is this a valid contract?',
        'ground_truth': 'False'
    },
    # ... more examples
]

# Run Logic-LM++
results = run_batch(
    examples=custom_examples,
    model_name='openai/gpt-4',
    config={'max_iterations': 4, 'num_candidates': 2, 'max_consecutive_backtracks': 2},
    output_dir='custom_output'
)
```

### Adjust Refinement Strategy

Override refinement parameters programmatically:

```python
from main import run_logiclm_plus

# More aggressive early stopping
result = run_logiclm_plus(
    text=text,
    query=query,
    model_name='openai/gpt-4',
    config={
        'max_iterations': 6,                    # More iterations allowed
        'num_candidates': 3,                     # More candidates (higher cost)
        'max_consecutive_backtracks': 1          # Aggressive early stop
    }
)
```

### Use Different Solver

Edit `solver_interface.py` to prefer Z3 over Prover9:

```python
def solve_fol(premises, conclusion, solver='z3', timeout=30):  # Changed default
    if solver == 'z3':
        return test_entailment_z3(premises, conclusion, timeout)
    elif solver == 'prover9':
        return test_entailment_prover9(premises, conclusion, timeout)
```

---

## 9. Troubleshooting

### Common Issues

#### Issue 1: `ModuleNotFoundError: No module named 'openai'`
**Solution**: Install dependencies
```bash
pip install openai datasets z3-solver numpy
```

#### Issue 2: `openai.error.AuthenticationError`
**Solution**: Set API key
```bash
export OPENAI_API_KEY="sk-your-key"
```

Verify:
```bash
echo $OPENAI_API_KEY
```

#### Issue 3: `Command 'prover9' not found`
**Solution**: Install Prover9
```bash
# Ubuntu/Debian
sudo apt-get install prover9

# macOS
brew install prover9
```

Verify:
```bash
prover9 -help
```

#### Issue 4: Solver timeouts on complex proofs
**Solution**: Increase timeout in `config.py`
```python
SOLVER_TIMEOUT = 60  # Increase from 30 to 60 seconds
```

#### Issue 5: High API costs
**Solution**: Use fewer iterations or GPT-3.5
```bash
python main.py --dataset folio --model openai/gpt-3.5-turbo --max-iterations 2
```

#### Issue 6: Formalization failures (high Er, low Ea)
**Solution**: Check prompt alignment with dataset
- Review `FORMALIZATION_PROMPT` in `config.py`
- Ensure predicates match dataset domain
- Try adding few-shot examples (contradicts paper, but may help)

#### Issue 7: Backtracking always REVERTs
**Solution**: Check `BACKTRACKING_PROMPT` sensitivity
- May be too conservative
- Try adjusting prompt wording in `config.py`
- Increase `MAX_CONSECUTIVE_BACKTRACKS` threshold

### Debugging Tips

#### Enable verbose output
```bash
python main.py --dataset folio --verbose
```

#### Inspect intermediate formulations
```python
from main import run_logiclm_plus

result = run_logiclm_plus(text, query, model_name, config)

# Print all formulations tried
for i, formulation in enumerate(result['formulation_history']):
    print(f"Iteration {i}:")
    print(f"  Premises: {formulation['premises']}")
    print(f"  Conclusion: {formulation['conclusion']}")
```

#### Check solver output
```python
from solver_interface import solve_fol

result = solve_fol(premises, conclusion, solver='prover9')

if result['error']:
    print(f"Solver error: {result['error']}")
if result['proof']:
    print(f"Proof trace:\n{result['proof']}")
```

#### Monitor API usage
```python
result = run_logiclm_plus(...)
print(f"LLM calls: {result['total_llm_calls']}")
print(f"Estimated cost: ${result['total_time'] * 0.03 / 60:.2f}")  # Rough estimate
```

---

## Summary: Typical Workflow

### For Reproducing Paper Results

```bash
# Install dependencies
pip install openai datasets z3-solver numpy
sudo apt-get install prover9  # or brew install on macOS

# Set API key
export OPENAI_API_KEY="sk-your-key"

# Run on all three datasets
python main.py --dataset folio --output folio_results.json
python main.py --dataset proofwriter --output proofwriter_results.json
python main.py --dataset ar-lsat --output arlsat_results.json

# Compare results to Table 1 in paper
python -c "
import json
for dataset in ['folio', 'proofwriter', 'arlsat']:
    with open(f'{dataset}_results.json') as f:
        data = json.load(f)
        acc = data['accuracy_metrics']['overall_accuracy']
        print(f'{dataset.upper()}: {acc:.2%}')
"
```

### For Quick Testing

```bash
# Test on small subset
python -c "
from main import load_dataset, run_batch

examples = load_dataset('folio')[:5]
results = run_batch(examples, 'openai/gpt-4', {
    'max_iterations': 2,
    'num_candidates': 2,
    'max_consecutive_backtracks': 2
})
print(f'Accuracy: {results[\"accuracy_metrics\"][\"overall_accuracy\"]:.2%}')
"
```

### For Ablation Studies

```bash
# Without backtracking (set threshold to 999, effectively disabling it)
python main.py --dataset folio --output folio_no_backtrack.json --max-consecutive-backtracks 999

# Compare with backtracking enabled
python main.py --dataset folio --output folio_with_backtrack.json --max-consecutive-backtracks 2
```

---

## Getting Help

- **Code issues**: Check module docstrings in each `.py` file
- **Paper methodology**: See `readme_logiclm_plus.md` for detailed explanations
- **Metric definitions**: See Section 6 (Understanding Output) above
- **Configuration**: See `config.py` comments

For further questions, refer to the original Logic-LM++ paper: https://arxiv.org/abs/2407.02514v3
