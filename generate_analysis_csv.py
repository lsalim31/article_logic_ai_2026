"""
Generate CSV file for fractional factorial analysis
Extracts configuration parameters and results from the experimental data
"""

import json
import yaml
from pathlib import Path
import pandas as pd

# Manual entry for run3 based on provided data (since the file in results was incomplete)
run3_data = {
    'accuracy': 0.41875,
    'total_correct': 67,
    'total_evaluated': 160
}

# Paths
config_dir = Path("/__modal/volumes/vo-zgDfQaQAguuvOdVtv6Kypr/repo/code/config/profiles")
results_dir = Path("/workspace/repo/experiments/claude_constructed/results")

print("=" * 80)
print("GENERATING CSV FOR FRACTIONAL FACTORIAL ANALYSIS")
print("=" * 80)
print()

# Step 1: Extract configurations from YAML files
print("Step 1: Reading configuration files...")
configs = {}
for i in range(1, 9):
    config_file = config_dir / f"config_run{i}_openAI.yaml"

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        features = config.get('features', {})

        configs[f"run{i}"] = {
            'run_id': i,
            'run_name': f"run{i}",
            'use_shortcuts': features.get('use_shortcuts', False),
            'expand_query': features.get('expand_query_synonyms', False),
            'use_openie': features.get('use_openie', False),
            'use_enrichment_kb': features.get('use_enrichment_kb', False),
        }

print(f"  ✓ Loaded {len(configs)} configuration files")
print()

# Step 2: Extract results from JSON files
print("Step 2: Reading results files...")
results = {}
for json_file in results_dir.glob("*.json"):
    run_name = json_file.name.split('_')[1]  # Extract 'run1', 'run2', etc.

    with open(json_file, 'r') as f:
        content = json.load(f)
        metadata = content.get('metadata', {})

        results[run_name] = {
            'accuracy': metadata.get('overall_accuracy', None),
            'total_correct': metadata.get('total_correct', None),
            'total_evaluated': metadata.get('total_evaluated', None),
        }

# Override run3 with correct data
results['run3'] = run3_data

print(f"  ✓ Loaded {len(results)} result files")
print()

# Step 3: Combine data
print("Step 3: Combining configuration and results...")
data = []
for run in sorted(configs.keys(), key=lambda x: int(x.replace('run', ''))):
    row = {
        **configs[run],
        **results.get(run, {'accuracy': None, 'total_correct': None, 'total_evaluated': None})
    }
    data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Add binary encoding column
df['binary_config'] = (
    df['use_shortcuts'].astype(int).astype(str) +
    df['expand_query'].astype(int).astype(str) +
    df['use_openie'].astype(int).astype(str) +
    df['use_enrichment_kb'].astype(int).astype(str)
)

# Reorder columns for clarity
df = df[[
    'run_id',
    'run_name',
    'binary_config',
    'use_shortcuts',
    'expand_query',
    'use_openie',
    'use_enrichment_kb',
    'accuracy',
    'total_correct',
    'total_evaluated'
]]

print("  ✓ Data combined successfully")
print()

# Step 4: Verify data
print("Step 4: Verifying binary encoding...")
expected = {
    1: '0000', 2: '1001', 3: '0101', 4: '1100',
    5: '0011', 6: '1010', 7: '0110', 8: '1111'
}

all_correct = True
for idx, row in df.iterrows():
    run_id = row['run_id']
    expected_binary = expected[run_id]
    actual_binary = row['binary_config']

    match = "✓" if actual_binary == expected_binary else "✗ ERROR"
    status = "OK" if actual_binary == expected_binary else "MISMATCH"

    print(f"  Run {run_id}: Expected {expected_binary} | Actual {actual_binary} | {match}")

    if actual_binary != expected_binary:
        all_correct = False

print()

if all_correct:
    print("  ✓ All binary encodings verified!")
else:
    print("  ✗ ERROR: Binary encoding mismatch detected!")
    print()

# Step 5: Display summary
print("=" * 80)
print("DATA SUMMARY")
print("=" * 80)
print()
print(df.to_string(index=False))
print()

# Step 6: Save to CSV
output_file = '/workspace/repo/fractional_factorial_data.csv'
df.to_csv(output_file, index=False)

print("=" * 80)
print("CSV FILE GENERATED")
print("=" * 80)
print(f"File saved to: {output_file}")
print()
print("Column descriptions:")
print("  - run_id: Run number (1-8)")
print("  - run_name: Run identifier (run1-run8)")
print("  - binary_config: Binary encoding (Q1 Q2 T1 T2)")
print("  - use_shortcuts: Q1 factor (0/1)")
print("  - expand_query: Q2 factor (0/1)")
print("  - use_openie: T1 factor (0/1)")
print("  - use_enrichment_kb: T2 factor (0/1)")
print("  - accuracy: Overall accuracy (0-1 scale)")
print("  - total_correct: Number of correct predictions")
print("  - total_evaluated: Total number of test cases")
print()

# Step 7: Generate factor analysis table
print("=" * 80)
print("FRACTIONAL FACTORIAL DESIGN VERIFICATION")
print("=" * 80)
print()
print("This is a 2^4 fractional factorial design with 8 runs.")
print("Each factor (Q1, Q2, T1, T2) appears 4 times as ON and 4 times as OFF.")
print()

for factor in ['use_shortcuts', 'expand_query', 'use_openie', 'use_enrichment_kb']:
    on_runs = df[df[factor] == True]['run_id'].tolist()
    off_runs = df[df[factor] == False]['run_id'].tolist()

    factor_label = {
        'use_shortcuts': 'Q1 (Shortcuts)',
        'expand_query': 'Q2 (Query Expansion)',
        'use_openie': 'T1 (OpenIE)',
        'use_enrichment_kb': 'T2 (KB Enrichment)'
    }[factor]

    print(f"{factor_label}:")
    print(f"  ON  (1): Runs {on_runs}")
    print(f"  OFF (0): Runs {off_runs}")
    print()

print("=" * 80)
print("READY FOR ANALYSIS!")
print("=" * 80)
print()
print("You can now load this CSV file in your .ipynb notebook:")
print()
print("import pandas as pd")
print("df = pd.read_csv('fractional_factorial_data.csv')")
print()
print("For factorial analysis, you can use libraries like:")
print("  - statsmodels.formula.api for regression")
print("  - pyDOE2 for design of experiments")
print("  - scipy.stats for statistical tests")
print()
