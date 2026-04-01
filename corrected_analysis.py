import json
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from itertools import combinations

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
            'expand_query': features.get('expand_query_synonyms', False),  # This is the correct field
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

# Remove rows with missing accuracy
df_complete = df[df['accuracy'].notna()].copy()

print("=" * 80)
print("CORRECTED DATA EXTRACTED FROM CONFIG FILES")
print("=" * 80)
print(df.to_string(index=False))
print("\n")

# Verify the binary encoding from comments
print("=" * 80)
print("VERIFICATION: Binary Encoding Pattern")
print("=" * 80)
print("According to config comments, the encoding should be:")
print("run 1: 0000")
print("run 2: 1001")
print("run 3: 0101")
print("run 4: 1100")
print("run 5: 0011")
print("run 6: 1010")
print("run 7: 0110")
print("run 8: 1111")
print("\nActual extracted (Q1 Q2 T1 T2):")
for _, row in df.iterrows():
    binary = f"{row['use_shortcuts']}{row['expand_query']}{row['use_openie']}{row['use_enrichment_kb']}"
    print(f"{row['run']}: {binary}")
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

# Individual parameter effects
print("=" * 80)
print("INDIVIDUAL PARAMETER EFFECTS")
print("=" * 80)

params_info = {
    'use_shortcuts': 'Shortcuts (Q1)',
    'expand_query': 'Query Expansion (Q2)',
    'use_openie': 'OpenIE (T1)',
    'use_enrichment_kb': 'KB Enrichment (T2)'
}

for param, param_name in params_info.items():
    print(f"\n{param_name}:")
    grouped = df_complete.groupby(param)['accuracy'].agg(['mean', 'std', 'count', 'min', 'max'])
    print(grouped.to_string())

    if len(grouped) == 2:
        effect = grouped.loc[1, 'mean'] - grouped.loc[0, 'mean']
        print(f"  → Effect size (enabled - disabled): {effect:+.4f} ({effect*100:+.2f} pp)")
    elif len(grouped) == 1:
        print(f"  → Only one setting: always {list(grouped.index)[0]}")

print("\n")

# Correlation analysis
print("=" * 80)
print("CORRELATION WITH ACCURACY")
print("=" * 80)

correlations = {}
for param, param_name in params_info.items():
    corr = df_complete[param].corr(df_complete['accuracy'])
    correlations[param] = corr
    if pd.isna(corr):
        print(f"{param_name}: N/A (no variance)")
    else:
        print(f"{param_name}: {corr:+.4f}")

print("\n")

# Best and worst
print("=" * 80)
print("BEST AND WORST CONFIGURATIONS")
print("=" * 80)

best_idx = df_complete['accuracy'].idxmax()
worst_idx = df_complete['accuracy'].idxmin()

print("BEST:")
print(f"  Run: {df_complete.loc[best_idx, 'run']}")
print(f"  Accuracy: {df_complete.loc[best_idx, 'accuracy']:.4f} ({df_complete.loc[best_idx, 'accuracy']*100:.2f}%)")
print(f"  use_shortcuts (Q1): {df_complete.loc[best_idx, 'use_shortcuts']}")
print(f"  expand_query (Q2): {df_complete.loc[best_idx, 'expand_query']}")
print(f"  use_openie (T1): {df_complete.loc[best_idx, 'use_openie']}")
print(f"  use_enrichment_kb (T2): {df_complete.loc[best_idx, 'use_enrichment_kb']}")

print("\nWORST:")
print(f"  Run: {df_complete.loc[worst_idx, 'run']}")
print(f"  Accuracy: {df_complete.loc[worst_idx, 'accuracy']:.4f} ({df_complete.loc[worst_idx, 'accuracy']*100:.2f}%)")
print(f"  use_shortcuts (Q1): {df_complete.loc[worst_idx, 'use_shortcuts']}")
print(f"  expand_query (Q2): {df_complete.loc[worst_idx, 'expand_query']}")
print(f"  use_openie (T1): {df_complete.loc[worst_idx, 'use_openie']}")
print(f"  use_enrichment_kb (T2): {df_complete.loc[worst_idx, 'use_enrichment_kb']}")

print("\n")

# Full configuration ranking
print("=" * 80)
print("FULL CONFIGURATION RANKING")
print("=" * 80)

df_sorted = df_complete.sort_values('accuracy', ascending=False)
print("| Rank | Run | Q1 | Q2 | T1 | T2 | Accuracy | Correct/Total |")
print("|------|-----|----|----|----|----|----------|---------------|")

for rank, (idx, row) in enumerate(df_sorted.iterrows(), 1):
    q1 = "✓" if row['use_shortcuts'] == 1 else "✗"
    q2 = "✓" if row['expand_query'] == 1 else "✗"
    t1 = "✓" if row['use_openie'] == 1 else "✗"
    t2 = "✓" if row['use_enrichment_kb'] == 1 else "✗"
    acc = f"{row['accuracy']:.2%}"
    ct = f"{int(row['total_correct'])}/{int(row['total_evaluated'])}"

    print(f"| {rank} | {row['run']} | {q1} | {q2} | {t1} | {t2} | {acc} | {ct} |")

print("\n")

# Save to CSV
df.to_csv('/workspace/repo/corrected_config_data.csv', index=False)
print("Data saved to corrected_config_data.csv")
