import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
from itertools import combinations

# Directory containing the results
results_dir = Path("/workspace/repo/experiments/claude_constructed/results")

# Initialize data collection
data = []

# Read all JSON files
for json_file in results_dir.glob("*.json"):
    try:
        with open(json_file, 'r') as f:
            content = json.load(f)

            # Extract configuration parameters
            config = content.get('retrieval_config', {})
            metadata = content.get('metadata', {})

            # Extract the 4 binary parameters and accuracy
            row = {
                'file': json_file.name,
                'run': json_file.name.split('_')[1],  # Extract run number
                'use_openie': config.get('USE_OPENIE', None),
                'use_enrichment_kb': config.get('USE_ENRICHMENT_KB', None),
                'use_shortcuts': config.get('USE_SUBSET', None),  # USE_SUBSET appears to be shortcuts
                'expand_query': config.get('ON_EXPAND_QUERY_SYN', None),
                'accuracy': metadata.get('overall_accuracy', None),
                'total_correct': metadata.get('total_correct', None),
                'total_evaluated': metadata.get('total_evaluated', None),
            }

            data.append(row)
    except Exception as e:
        print(f"Error processing {json_file.name}: {e}")

# Create DataFrame
df = pd.DataFrame(data)

# Display the data
print("=" * 80)
print("RAW DATA EXTRACTED")
print("=" * 80)
print(df.to_string(index=False))
print("\n")

# Convert boolean to int for easier analysis
for col in ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']:
    df[col] = df[col].astype(int)

# Basic statistics
print("=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"Total runs: {len(df)}")
print(f"Accuracy range: {df['accuracy'].min():.4f} to {df['accuracy'].max():.4f}")
print(f"Mean accuracy: {df['accuracy'].mean():.4f}")
print(f"Std accuracy: {df['accuracy'].std():.4f}")
print("\n")

# Group by each parameter individually
print("=" * 80)
print("INDIVIDUAL PARAMETER EFFECTS")
print("=" * 80)

for param in ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']:
    print(f"\n{param.upper()}:")
    grouped = df.groupby(param)['accuracy'].agg(['mean', 'std', 'count', 'min', 'max'])
    print(grouped.to_string())

    # Calculate effect size (difference in means)
    if len(grouped) == 2:
        effect = grouped.loc[1, 'mean'] - grouped.loc[0, 'mean']
        print(f"  → Effect size (enabled - disabled): {effect:+.4f}")

print("\n")

# Group by all combinations of 2 parameters
print("=" * 80)
print("TWO-PARAMETER INTERACTIONS")
print("=" * 80)

params = ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']
for param1, param2 in combinations(params, 2):
    print(f"\n{param1.upper()} × {param2.upper()}:")
    grouped = df.groupby([param1, param2])['accuracy'].agg(['mean', 'count'])
    print(grouped.to_string())

print("\n")

# Group by all 4 parameters (configuration profiles)
print("=" * 80)
print("FULL CONFIGURATION PROFILES")
print("=" * 80)
grouped = df.groupby(['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query'])['accuracy'].agg(['mean', 'count', 'std'])
grouped = grouped.sort_values('mean', ascending=False)
print(grouped.to_string())

print("\n")

# Find best and worst configurations
print("=" * 80)
print("BEST AND WORST CONFIGURATIONS")
print("=" * 80)

best_idx = df['accuracy'].idxmax()
worst_idx = df['accuracy'].idxmin()

print("BEST:")
print(f"  File: {df.loc[best_idx, 'file']}")
print(f"  Accuracy: {df.loc[best_idx, 'accuracy']:.4f}")
print(f"  use_openie: {df.loc[best_idx, 'use_openie']}")
print(f"  use_enrichment_kb: {df.loc[best_idx, 'use_enrichment_kb']}")
print(f"  use_shortcuts: {df.loc[best_idx, 'use_shortcuts']}")
print(f"  expand_query: {df.loc[best_idx, 'expand_query']}")

print("\nWORST:")
print(f"  File: {df.loc[worst_idx, 'file']}")
print(f"  Accuracy: {df.loc[worst_idx, 'accuracy']:.4f}")
print(f"  use_openie: {df.loc[worst_idx, 'use_openie']}")
print(f"  use_enrichment_kb: {df.loc[worst_idx, 'use_enrichment_kb']}")
print(f"  use_shortcuts: {df.loc[worst_idx, 'use_shortcuts']}")
print(f"  expand_query: {df.loc[worst_idx, 'expand_query']}")

print("\n")

# Correlation analysis
print("=" * 80)
print("CORRELATION WITH ACCURACY")
print("=" * 80)

correlations = {}
for param in ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']:
    corr = df[param].corr(df['accuracy'])
    correlations[param] = corr
    print(f"{param}: {corr:+.4f}")

print("\n")

# Save data to CSV for reference
df.to_csv('/workspace/repo/config_analysis_data.csv', index=False)
print("Data saved to config_analysis_data.csv")
