import json
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from itertools import combinations

# Manual entry for run3 based on provided data
run3_data = {
    'accuracy': 0.41875,
    'total_correct': 67,
    'total_evaluated': 160
}

# Read configuration files
config_dir = Path("/__modal/volumes/vo-zgDfQaQAguuvOdVtv6Kypr/repo/code/config/profiles")
results_dir = Path("/workspace/repo/experiments/claude_constructed/results")

# Parse configurations
configs = {}
for i in range(1, 9):
    config_file = config_dir / f"config_run{i}_openAI.yaml"
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        features = config.get('features', {})

        configs[f"run{i}"] = {
            'use_shortcuts': features.get('use_shortcuts', False),
            'use_openie': features.get('use_openie', False),
            'use_enrichment_kb': features.get('use_enrichment_kb', False),
            'expand_query': features.get('expand_query_synonyms', False),
        }

# Read results
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

# Combine data
data = []
for run in sorted(configs.keys(), key=lambda x: int(x.replace('run', ''))):
    row = {
        'run': run,
        **configs[run],
        **results.get(run, {'accuracy': None, 'total_correct': None, 'total_evaluated': None})
    }
    data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Convert boolean to int for easier analysis
for col in ['use_shortcuts', 'use_openie', 'use_enrichment_kb', 'expand_query']:
    df[col] = df[col].astype(int)

# Remove rows with missing accuracy (should be none now)
df_complete = df[df['accuracy'].notna()].copy()

print("=" * 80)
print("COMPLETE DATA WITH ALL 8 RUNS")
print("=" * 80)
print(df.to_string(index=False))
print("\n")

# Verify the binary encoding from comments
print("=" * 80)
print("VERIFICATION: Binary Encoding Pattern")
print("=" * 80)
print("According to config comments, the encoding should be:")
print("Format: Q1(shortcuts) Q2(expand_query) T1(openie) T2(kb_enrichment)")
print("\nExpected vs Actual:")
expected = {
    'run1': '0000', 'run2': '1001', 'run3': '0101', 'run4': '1100',
    'run5': '0011', 'run6': '1010', 'run7': '0110', 'run8': '1111'
}
for _, row in df.iterrows():
    binary = f"{row['use_shortcuts']}{row['expand_query']}{row['use_openie']}{row['use_enrichment_kb']}"
    match = "✓" if binary == expected[row['run']] else "✗"
    print(f"{row['run']}: Expected {expected[row['run']]} | Actual {binary} {match}")
print("\n")

# Summary statistics
print("=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"Total runs: {len(df)}")
print(f"Completed runs: {len(df_complete)}")
print(f"Mean accuracy: {df_complete['accuracy'].mean():.4f} ({df_complete['accuracy'].mean()*100:.2f}%)")
print(f"Std accuracy: {df_complete['accuracy'].std():.4f}")
print(f"Min accuracy: {df_complete['accuracy'].min():.4f} ({df_complete['accuracy'].min()*100:.2f}%)")
print(f"Max accuracy: {df_complete['accuracy'].max():.4f} ({df_complete['accuracy'].max()*100:.2f}%)")
print(f"Range: {df_complete['accuracy'].max() - df_complete['accuracy'].min():.4f} ({(df_complete['accuracy'].max() - df_complete['accuracy'].min())*100:.2f} pp)")
print("\n")

# Full ranking table
print("=" * 80)
print("FULL CONFIGURATION RANKING")
print("=" * 80)

df_sorted = df_complete.sort_values('accuracy', ascending=False)
print("| Rank | Run | Q1 | Q2 | T1 | T2 | Config | Accuracy | Correct/Total |")
print("|------|-----|----|----|----|----|--------|----------|---------------|")

for rank, (idx, row) in enumerate(df_sorted.iterrows(), 1):
    q1 = "✓" if row['use_shortcuts'] == 1 else "✗"
    q2 = "✓" if row['expand_query'] == 1 else "✗"
    t1 = "✓" if row['use_openie'] == 1 else "✗"
    t2 = "✓" if row['use_enrichment_kb'] == 1 else "✗"

    binary = f"{row['use_shortcuts']}{row['expand_query']}{row['use_openie']}{row['use_enrichment_kb']}"
    acc = f"{row['accuracy']:.2%}"
    ct = f"{int(row['total_correct'])}/{int(row['total_evaluated'])}"

    print(f"| {rank} | {row['run']} | {q1} | {q2} | {t1} | {t2} | {binary} | {acc} | {ct} |")

print("\n")

# Individual parameter effects
print("=" * 80)
print("INDIVIDUAL PARAMETER EFFECTS")
print("=" * 80)

params_info = {
    'use_shortcuts': 'Q1: Shortcuts',
    'expand_query': 'Q2: Query Expansion',
    'use_openie': 'T1: OpenIE',
    'use_enrichment_kb': 'T2: KB Enrichment'
}

effects_summary = []
for param, param_name in params_info.items():
    print(f"\n{param_name}:")
    grouped = df_complete.groupby(param)['accuracy'].agg(['mean', 'std', 'count', 'min', 'max'])
    print(grouped.to_string())

    if len(grouped) == 2:
        effect = grouped.loc[1, 'mean'] - grouped.loc[0, 'mean']
        effects_summary.append((param, param_name, effect))
        print(f"  → Effect size (enabled - disabled): {effect:+.4f} ({effect*100:+.2f} pp)")

print("\n")

# Correlation analysis
print("=" * 80)
print("CORRELATION WITH ACCURACY")
print("=" * 80)

correlations = {}
for param, param_name in params_info.items():
    corr = df_complete[param].corr(df_complete['accuracy'])
    correlations[param] = corr
    print(f"{param_name}: {corr:+.4f}")

print("\n")

# Effect summary ranked
print("=" * 80)
print("PARAMETER EFFECTS RANKED BY MAGNITUDE")
print("=" * 80)
effects_summary_sorted = sorted(effects_summary, key=lambda x: abs(x[2]), reverse=True)
for i, (param, param_name, effect) in enumerate(effects_summary_sorted, 1):
    direction = "increases" if effect > 0 else "decreases"
    print(f"{i}. {param_name}: {direction} accuracy by {abs(effect)*100:.2f} pp (effect = {effect:+.4f})")

print("\n")

# Two-way interactions
print("=" * 80)
print("KEY TWO-WAY INTERACTIONS")
print("=" * 80)

params = ['use_shortcuts', 'use_openie', 'use_enrichment_kb', 'expand_query']

# Focus on most important interactions
important_pairs = [
    ('use_openie', 'use_enrichment_kb'),
    ('use_shortcuts', 'expand_query'),
    ('use_openie', 'expand_query'),
]

for param1, param2 in important_pairs:
    param1_name = params_info[param1]
    param2_name = params_info[param2]

    print(f"\n{param1_name} × {param2_name}:")
    grouped = df_complete.groupby([param1, param2])['accuracy'].agg(['mean', 'count'])

    print("\n| " + param1.split('_')[-1][:3].upper() + " | " + param2.split('_')[-1][:3].upper() + " | Mean Accuracy | Count |")
    print("|-----|-----|---------------|-------|")

    for (val1, val2), row in grouped.iterrows():
        status1 = "On " if val1 == 1 else "Off"
        status2 = "On " if val2 == 1 else "Off"
        mean_acc = row['mean']
        count = int(row['count'])
        print(f"| {status1} | {status2} | {mean_acc:.4f} ({mean_acc*100:.2f}%) | {count} |")

print("\n")

# Best and worst
print("=" * 80)
print("BEST VS WORST CONFIGURATIONS")
print("=" * 80)

best_idx = df_complete['accuracy'].idxmax()
worst_idx = df_complete['accuracy'].idxmin()

print("BEST CONFIGURATION:")
print(f"  Run: {df_complete.loc[best_idx, 'run']}")
print(f"  Accuracy: {df_complete.loc[best_idx, 'accuracy']:.4f} ({df_complete.loc[best_idx, 'accuracy']*100:.2f}%)")
print(f"  Binary: {df_complete.loc[best_idx, 'use_shortcuts']}{df_complete.loc[best_idx, 'expand_query']}{df_complete.loc[best_idx, 'use_openie']}{df_complete.loc[best_idx, 'use_enrichment_kb']}")
print(f"  Q1 Shortcuts: {'ON' if df_complete.loc[best_idx, 'use_shortcuts'] == 1 else 'OFF'}")
print(f"  Q2 Query Expansion: {'ON' if df_complete.loc[best_idx, 'expand_query'] == 1 else 'OFF'}")
print(f"  T1 OpenIE: {'ON' if df_complete.loc[best_idx, 'use_openie'] == 1 else 'OFF'}")
print(f"  T2 KB Enrichment: {'ON' if df_complete.loc[best_idx, 'use_enrichment_kb'] == 1 else 'OFF'}")

print("\nWORST CONFIGURATION:")
print(f"  Run: {df_complete.loc[worst_idx, 'run']}")
print(f"  Accuracy: {df_complete.loc[worst_idx, 'accuracy']:.4f} ({df_complete.loc[worst_idx, 'accuracy']*100:.2f}%)")
print(f"  Binary: {df_complete.loc[worst_idx, 'use_shortcuts']}{df_complete.loc[worst_idx, 'expand_query']}{df_complete.loc[worst_idx, 'use_openie']}{df_complete.loc[worst_idx, 'use_enrichment_kb']}")
print(f"  Q1 Shortcuts: {'ON' if df_complete.loc[worst_idx, 'use_shortcuts'] == 1 else 'OFF'}")
print(f"  Q2 Query Expansion: {'ON' if df_complete.loc[worst_idx, 'expand_query'] == 1 else 'OFF'}")
print(f"  T1 OpenIE: {'ON' if df_complete.loc[worst_idx, 'use_openie'] == 1 else 'OFF'}")
print(f"  T2 KB Enrichment: {'ON' if df_complete.loc[worst_idx, 'use_enrichment_kb'] == 1 else 'OFF'}")

print("\nDifference: {:.4f} ({:.2f} pp)".format(
    df_complete.loc[best_idx, 'accuracy'] - df_complete.loc[worst_idx, 'accuracy'],
    (df_complete.loc[best_idx, 'accuracy'] - df_complete.loc[worst_idx, 'accuracy']) * 100
))

print("\n")

# Save to CSV
df.to_csv('/workspace/repo/complete_config_data.csv', index=False)
print("=" * 80)
print("Data saved to complete_config_data.csv")
print("=" * 80)
