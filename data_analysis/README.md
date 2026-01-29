# Data Analysis for Neuro-Symbolic Reasoning (ICML Submission)

This folder contains the data analysis pipeline for our neuro-symbolic reasoning experiments, following the methodology established by LOGIC-LM (Pan et al., EMNLP 2023) and adapted for ICML standards.

## Overview

The analysis notebook (`neuro_symbolic_analysis.ipynb`) provides comprehensive evaluation of neuro-symbolic reasoning experiments, generating publication-ready tables and figures.

## Quick Start

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn scipy jupyter

# Launch Jupyter
jupyter notebook neuro_symbolic_analysis.ipynb
```

## Directory Structure

```
data_analysis/
├── README.md                          # This file
├── neuro_symbolic_analysis.ipynb      # Main analysis notebook
└── outputs/                           # Generated outputs (created on first run)
    ├── figures/                       # PNG/PDF figures
    │   ├── main_comparison.png
    │   ├── execution_metrics.png
    │   ├── accuracy_by_axiom.png
    │   ├── refinement_analysis.png
    │   ├── error_distribution.png
    │   └── time_breakdown.png
    ├── tables/                        # CSV and LaTeX tables
    │   ├── main_results.csv
    │   ├── main_results.tex
    │   ├── execution_analysis.csv
    │   ├── axiom_accuracy.csv
    │   ├── efficiency_metrics.csv
    │   └── confidence_intervals.csv
    └── summary_report.txt             # Text summary of results
```

## Input Data Format

The analysis expects JSON result files with the following structure (matching our experiment output format):

```json
{
  "metadata": {
    "dataset": "LogicBench-v1.0",
    "logic_type": "propositional_logic",
    "task_type": "BQA",
    "model": "gpt-4",
    "solver": "z3",
    "timestamp": "2026-01-27T23:54:53.274113",
    "total_examples": 100
  },
  "metrics": {
    "overall_accuracy": 0.75,
    "execution_rate_Er": 0.95,
    "execution_accuracy_Ea": 0.79,
    "correct_count": 75,
    "execution_success_count": 95
  },
  "results": [
    {
      "example_id": "modus_tollens_1",
      "rule_type": "propositional_logic",
      "axiom": "modus_tollens",
      "ground_truth": "yes",
      "answer": "Proved",
      "converted_answer": "yes",
      "is_correct": true,
      "formalization_success": true,
      "execution_success": true,
      "num_refinement_iterations": 0,
      "total_llm_calls": 2,
      "total_time": 10.5,
      "time_breakdown": {
        "formalization": 2.5,
        "refinement": 7.8,
        "solving": 0.002
      },
      "error": null
    }
  ]
}
```

## Analysis Sections

### 1. Main Results Table (Table 2 Style)
- Overall accuracy across datasets and methods
- Comparison with baselines (Standard, CoT, LOGIC-LM)
- Multiple LLM backbones (GPT-3.5, GPT-4)

### 2. Execution Analysis (Table 3 Style)
| Metric | Description |
|--------|-------------|
| **Exe_Rate** | % of formulations that are syntactically valid and executable |
| **Exe_Acc** | Accuracy only on executable examples (semantic correctness) |

### 3. Performance by Reasoning Depth (Figure 3 Style)
- Accuracy curves stratified by problem complexity
- Demonstrates robustness as reasoning depth increases

### 4. Self-Refinement Analysis (Figure 4 Style)
- Impact of iterative refinement rounds
- Trade-off between Exe_Rate improvement and accuracy

### 5. Per-Rule/Axiom Breakdown
- Heatmap of accuracy by logical axiom
- Identifies strengths and weaknesses by rule type

### 6. Error Analysis
Error categories:
1. **Formalization Error** - Failed to generate valid logical form
2. **Execution Error** - Valid form but solver failed
3. **Semantic Error** - Executed correctly but wrong answer

### 7. Time & Efficiency Analysis
- Time breakdown by component (formalization, refinement, solving)
- LLM call statistics
- Processing time distributions

### 8. Statistical Significance Tests
- Bootstrap confidence intervals (95%)
- Paired t-tests between methods
- Wilcoxon signed-rank tests (non-parametric)

## Key Functions

### Data Loading

```python
# Load single experiment
results = load_experiment_results('path/to/results.json')
df = results_to_dataframe(results)

# Load all experiments from directory
experiments = load_all_experiments('../code/baseline_logiclm_plus/', '*.json')
```

### Metrics Computation

```python
# Accuracy metrics
metrics = compute_accuracy_metrics(df)

# Execution metrics (Exe_Rate, Exe_Acc)
exe_metrics = compute_execution_metrics(df)

# Efficiency metrics
eff_metrics = analyze_efficiency(df)
```

### Visualization

```python
# Main comparison figure
create_main_comparison_figure(experiments, 'outputs/figures/main.png')

# Execution metrics plot
plot_execution_metrics(experiments, 'outputs/figures/exe.png')

# Per-axiom heatmap
create_per_axiom_heatmap(experiments, 'outputs/figures/heatmap.png')
```

### Statistical Tests

```python
# Confidence intervals
ci_lower, ci_upper = compute_confidence_interval(df['is_correct'].values)

# Paired significance test
results = paired_significance_test(df1, df2, metric='is_correct')
```

## Configuration

Edit the `CONFIG` dictionary in the notebook to customize:

```python
CONFIG = {
    'results_dir': '../code/baseline_logiclm_plus/',  # Input directory
    'output_dir': './outputs/',                       # Output directory
    'experiment_name': 'neuro_symbolic_icml_2026',

    # Method names for labeling
    'method_names': {
        'standard': 'Standard Prompting',
        'cot': 'Chain-of-Thought',
        'ours': 'Our Method'
    },

    # Color scheme
    'colors': {
        'standard': '#1f77b4',
        'cot': '#ff7f0e',
        'ours': '#d62728'
    }
}
```

## Adding New Experiments

1. Place your result JSON file in the results directory
2. Update `experiment_files` list in Section 1:
   ```python
   experiment_files = [
       '../code/baseline_logiclm_plus/results_with_refinement.json',
       '../code/baseline_logiclm_plus/results_standard.json',  # Add new
       '../code/baseline_logiclm_plus/results_cot.json',       # Add new
   ]
   ```
3. Re-run all cells

## Expected Outputs for ICML

Based on LOGIC-LM methodology, your submission should include:

### Tables
- [ ] **Table 1**: Dataset statistics (reasoning type, size, # options)
- [ ] **Table 2**: Main results (accuracy across methods × datasets × LLMs)
- [ ] **Table 3**: Execution analysis (Exe_Rate, Exe_Acc, with/without refinement)

### Figures
- [ ] **Figure 1**: Method overview diagram (not generated here)
- [ ] **Figure 2**: Detailed symbolic formulation examples (qualitative)
- [ ] **Figure 3**: Accuracy vs. reasoning depth curves
- [ ] **Figure 4**: Self-refinement round analysis
- [ ] **Figure 5/6**: Error case examples (qualitative, appendix)

## Metrics Reference (LOGIC-LM Paper)

| Metric | LOGIC-LM GPT-3.5 | LOGIC-LM GPT-4 | Target |
|--------|------------------|----------------|--------|
| Avg improvement over Standard | +39.2% | +24.98% | > baseline |
| Avg improvement over CoT | +18.4% | +10.44% | > baseline |
| Exe_Rate (synthetic data) | ~100% | ~100% | > 95% |
| Exe_Rate (real-world data) | 66.7-84.3% | 79.9-85.8% | > 80% |

## Dependencies

```
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
seaborn>=0.12.0
scipy>=1.9.0
jupyter>=1.0.0
```

## Citation

If you use this analysis pipeline, please cite:

```bibtex
@inproceedings{pan2023logiclm,
  title={LOGIC-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning},
  author={Pan, Liangming and Albalak, Alon and Wang, Xinyi and Wang, William Yang},
  booktitle={Findings of EMNLP},
  year={2023}
}
```

## Troubleshooting

### No experiments loaded
- Check that JSON files exist in `results_dir`
- Verify JSON format matches expected structure

### Missing columns in DataFrame
- Some analyses require specific fields (e.g., `axiom`, `rule_type`)
- Check your JSON output includes these fields

### Plot rendering issues
- Ensure matplotlib backend is properly configured
- For headless servers: `matplotlib.use('Agg')` before imports

## Contact

For questions about this analysis pipeline, contact the project maintainers.
