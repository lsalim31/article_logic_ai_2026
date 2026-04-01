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
                'run': json_file.name.split('_')[1],
                'use_openie': config.get('USE_OPENIE', None),
                'use_enrichment_kb': config.get('USE_ENRICHMENT_KB', None),
                'use_shortcuts': config.get('USE_SUBSET', None),
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

# Convert boolean to int for easier analysis
for col in ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']:
    df[col] = df[col].astype(int)

# Remove rows with missing accuracy
df_complete = df[df['accuracy'].notna()].copy()

# Create markdown report
md_lines = []

md_lines.append("# Configuration Analysis Report")
md_lines.append("")
md_lines.append("**Experimental Dataset Analysis: Claude Constructed Results**")
md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Executive Summary
md_lines.append("## Executive Summary")
md_lines.append("")
md_lines.append(f"This report analyzes the relationship between model configuration parameters and accuracy across {len(df_complete)} experimental runs. ")
md_lines.append("Four binary configuration parameters were varied across experiments:")
md_lines.append("")
md_lines.append("1. **use_openie**: Use OpenIE for information extraction")
md_lines.append("2. **use_enrichment_kb**: Use knowledge base enrichment")
md_lines.append("3. **use_shortcuts**: Use subset/shortcut mechanisms")
md_lines.append("4. **expand_query**: Expand queries with synonyms")
md_lines.append("")

best_idx = df_complete['accuracy'].idxmax()
worst_idx = df_complete['accuracy'].idxmin()

md_lines.append(f"**Key Finding**: The best configuration achieved **{df_complete.loc[best_idx, 'accuracy']:.2%}** accuracy, ")
md_lines.append(f"while the worst achieved **{df_complete.loc[worst_idx, 'accuracy']:.2%}** accuracy - ")
md_lines.append(f"a difference of **{(df_complete.loc[best_idx, 'accuracy'] - df_complete.loc[worst_idx, 'accuracy']):.2%}**.")
md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Dataset Overview
md_lines.append("## 1. Dataset Overview")
md_lines.append("")
md_lines.append("### 1.1 Runs Summary")
md_lines.append("")
md_lines.append(f"- **Total experimental runs**: {len(df)}")
md_lines.append(f"- **Completed runs with accuracy data**: {len(df_complete)}")
md_lines.append(f"- **Incomplete runs**: {len(df) - len(df_complete)} (run3 - appears to be interrupted)")
md_lines.append("")

md_lines.append("### 1.2 Accuracy Statistics")
md_lines.append("")
md_lines.append(f"- **Mean accuracy**: {df_complete['accuracy'].mean():.4f} ({df_complete['accuracy'].mean()*100:.2f}%)")
md_lines.append(f"- **Standard deviation**: {df_complete['accuracy'].std():.4f}")
md_lines.append(f"- **Minimum accuracy**: {df_complete['accuracy'].min():.4f} ({df_complete['accuracy'].min()*100:.2f}%)")
md_lines.append(f"- **Maximum accuracy**: {df_complete['accuracy'].max():.4f} ({df_complete['accuracy'].max()*100:.2f}%)")
md_lines.append(f"- **Range**: {df_complete['accuracy'].max() - df_complete['accuracy'].min():.4f} ({(df_complete['accuracy'].max() - df_complete['accuracy'].min())*100:.2f} percentage points)")
md_lines.append("")

# Configuration table
md_lines.append("### 1.3 All Experimental Runs")
md_lines.append("")
md_lines.append("| Run | OpenIE | KB Enrichment | Shortcuts | Query Expansion | Accuracy | Correct/Total |")
md_lines.append("|-----|--------|---------------|-----------|-----------------|----------|---------------|")

for idx, row in df.iterrows():
    openie = "✓" if row['use_openie'] == 1 else "✗"
    kb = "✓" if row['use_enrichment_kb'] == 1 else "✗"
    shortcuts = "✓" if row['use_shortcuts'] == 1 else "✗"
    expand = "✓" if row['expand_query'] == 1 else "✗"

    if pd.notna(row['accuracy']):
        acc_str = f"{row['accuracy']:.2%}"
        correct_total = f"{int(row['total_correct'])}/{int(row['total_evaluated'])}"
    else:
        acc_str = "N/A"
        correct_total = "N/A"

    md_lines.append(f"| {row['run']} | {openie} | {kb} | {shortcuts} | {expand} | {acc_str} | {correct_total} |")

md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Individual Parameter Analysis
md_lines.append("## 2. Individual Parameter Effects")
md_lines.append("")
md_lines.append("This section examines how each configuration parameter individually affects model accuracy.")
md_lines.append("")

params_info = {
    'use_openie': 'OpenIE',
    'use_enrichment_kb': 'KB Enrichment',
    'use_shortcuts': 'Shortcuts',
    'expand_query': 'Query Expansion'
}

for param, param_name in params_info.items():
    md_lines.append(f"### 2.{list(params_info.keys()).index(param) + 1} {param_name}")
    md_lines.append("")

    grouped = df_complete.groupby(param)['accuracy'].agg(['mean', 'std', 'count', 'min', 'max'])

    # Create table
    md_lines.append(f"| {param_name} | Mean Accuracy | Std Dev | Count | Min | Max |")
    md_lines.append("|-------------|---------------|---------|-------|-----|-----|")

    for val in sorted(grouped.index):
        status = "Enabled" if val == 1 else "Disabled"
        mean_acc = grouped.loc[val, 'mean']
        std_acc = grouped.loc[val, 'std'] if not pd.isna(grouped.loc[val, 'std']) else 0
        count = int(grouped.loc[val, 'count'])
        min_acc = grouped.loc[val, 'min']
        max_acc = grouped.loc[val, 'max']

        md_lines.append(f"| {status} | {mean_acc:.4f} ({mean_acc*100:.2f}%) | {std_acc:.4f} | {count} | {min_acc:.4f} | {max_acc:.4f} |")

    md_lines.append("")

    # Effect size
    if len(grouped) == 2:
        effect = grouped.loc[1, 'mean'] - grouped.loc[0, 'mean']
        effect_pct = effect * 100

        if effect > 0:
            direction = "**positive**"
            interpretation = f"Enabling {param_name.lower()} **increases** accuracy"
        else:
            direction = "**negative**"
            interpretation = f"Enabling {param_name.lower()} **decreases** accuracy"

        md_lines.append(f"**Effect size**: {effect:+.4f} ({effect_pct:+.2f} percentage points) - {direction}")
        md_lines.append("")
        md_lines.append(f"**Interpretation**: {interpretation} by an average of {abs(effect_pct):.2f} percentage points.")
        md_lines.append("")
    elif len(grouped) == 1:
        md_lines.append(f"**Note**: This parameter has only one setting across all runs (always {list(grouped.index)[0]}). Cannot compute effect size.")
        md_lines.append("")

md_lines.append("---")
md_lines.append("")

# Correlation Analysis
md_lines.append("## 3. Correlation Analysis")
md_lines.append("")
md_lines.append("Pearson correlation coefficients between each parameter and accuracy:")
md_lines.append("")
md_lines.append("| Parameter | Correlation with Accuracy | Interpretation |")
md_lines.append("|-----------|---------------------------|----------------|")

correlations = {}
for param, param_name in params_info.items():
    corr = df_complete[param].corr(df_complete['accuracy'])
    correlations[param] = corr

    if pd.isna(corr):
        corr_str = "N/A (no variance)"
        interp = "Parameter constant across all runs"
    else:
        corr_str = f"{corr:+.4f}"

        if abs(corr) < 0.1:
            strength = "negligible"
        elif abs(corr) < 0.3:
            strength = "weak"
        elif abs(corr) < 0.5:
            strength = "moderate"
        elif abs(corr) < 0.7:
            strength = "strong"
        else:
            strength = "very strong"

        direction = "positive" if corr > 0 else "negative"
        interp = f"{strength.capitalize()} {direction} relationship"

    md_lines.append(f"| {param_name} | {corr_str} | {interp} |")

md_lines.append("")
md_lines.append("**Note**: Correlation ranges from -1 (perfect negative) to +1 (perfect positive). ")
md_lines.append("Zero indicates no linear relationship.")
md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Interaction Effects
md_lines.append("## 4. Parameter Interactions")
md_lines.append("")
md_lines.append("Analysis of how parameter combinations affect accuracy.")
md_lines.append("")

params = ['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query']
interaction_num = 1

for param1, param2 in combinations(params, 2):
    param1_name = params_info[param1]
    param2_name = params_info[param2]

    md_lines.append(f"### 4.{interaction_num} {param1_name} × {param2_name}")
    md_lines.append("")

    grouped = df_complete.groupby([param1, param2])['accuracy'].agg(['mean', 'count'])

    if len(grouped) > 0:
        md_lines.append(f"| {param1_name} | {param2_name} | Mean Accuracy | Count |")
        md_lines.append("|-------------|---------------|---------------|-------|")

        for (val1, val2), row in grouped.iterrows():
            status1 = "On" if val1 == 1 else "Off"
            status2 = "On" if val2 == 1 else "Off"
            mean_acc = row['mean']
            count = int(row['count'])

            md_lines.append(f"| {status1} | {status2} | {mean_acc:.4f} ({mean_acc*100:.2f}%) | {count} |")

        md_lines.append("")

        # Find best combination
        best_combo = grouped['mean'].idxmax()
        best_acc = grouped.loc[best_combo, 'mean']
        best_str = f"{param1_name}={'On' if best_combo[0]==1 else 'Off'}, {param2_name}={'On' if best_combo[1]==1 else 'Off'}"

        md_lines.append(f"**Best combination**: {best_str} ({best_acc:.2%})")
        md_lines.append("")

    interaction_num += 1

md_lines.append("---")
md_lines.append("")

# Configuration Profiles
md_lines.append("## 5. Full Configuration Profiles")
md_lines.append("")
md_lines.append("Complete analysis of all 4-parameter configurations tested:")
md_lines.append("")

grouped_full = df_complete.groupby(['use_openie', 'use_enrichment_kb', 'use_shortcuts', 'expand_query'])['accuracy'].agg(['mean', 'count', 'std'])
grouped_full = grouped_full.sort_values('mean', ascending=False)

md_lines.append("| Rank | OpenIE | KB Enrich | Shortcuts | Query Exp | Mean Accuracy | Count | Std Dev |")
md_lines.append("|------|--------|-----------|-----------|-----------|---------------|-------|---------|")

rank = 1
for config, row in grouped_full.iterrows():
    openie, kb, shortcuts, expand = config
    openie_str = "✓" if openie == 1 else "✗"
    kb_str = "✓" if kb == 1 else "✗"
    shortcuts_str = "✓" if shortcuts == 1 else "✗"
    expand_str = "✓" if expand == 1 else "✗"

    mean_acc = row['mean']
    count = int(row['count'])
    std_acc = row['std'] if not pd.isna(row['std']) else 0

    md_lines.append(f"| {rank} | {openie_str} | {kb_str} | {shortcuts_str} | {expand_str} | {mean_acc:.4f} ({mean_acc*100:.2f}%) | {count} | {std_acc:.4f} |")
    rank += 1

md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Best and Worst Configurations
md_lines.append("## 6. Best and Worst Performing Configurations")
md_lines.append("")

md_lines.append("### 6.1 Best Configuration")
md_lines.append("")
md_lines.append(f"**Run**: {df_complete.loc[best_idx, 'run']}")
md_lines.append(f"**Accuracy**: {df_complete.loc[best_idx, 'accuracy']:.4f} ({df_complete.loc[best_idx, 'accuracy']*100:.2f}%)")
md_lines.append(f"**Correct/Total**: {int(df_complete.loc[best_idx, 'total_correct'])}/{int(df_complete.loc[best_idx, 'total_evaluated'])}")
md_lines.append("")
md_lines.append("**Configuration**:")
md_lines.append(f"- OpenIE: **{'Enabled' if df_complete.loc[best_idx, 'use_openie'] == 1 else 'Disabled'}**")
md_lines.append(f"- KB Enrichment: **{'Enabled' if df_complete.loc[best_idx, 'use_enrichment_kb'] == 1 else 'Disabled'}**")
md_lines.append(f"- Shortcuts: **{'Enabled' if df_complete.loc[best_idx, 'use_shortcuts'] == 1 else 'Disabled'}**")
md_lines.append(f"- Query Expansion: **{'Enabled' if df_complete.loc[best_idx, 'expand_query'] == 1 else 'Disabled'}**")
md_lines.append("")

md_lines.append("### 6.2 Worst Configuration")
md_lines.append("")
md_lines.append(f"**Run**: {df_complete.loc[worst_idx, 'run']}")
md_lines.append(f"**Accuracy**: {df_complete.loc[worst_idx, 'accuracy']:.4f} ({df_complete.loc[worst_idx, 'accuracy']*100:.2f}%)")
md_lines.append(f"**Correct/Total**: {int(df_complete.loc[worst_idx, 'total_correct'])}/{int(df_complete.loc[worst_idx, 'total_evaluated'])}")
md_lines.append("")
md_lines.append("**Configuration**:")
md_lines.append(f"- OpenIE: **{'Enabled' if df_complete.loc[worst_idx, 'use_openie'] == 1 else 'Disabled'}**")
md_lines.append(f"- KB Enrichment: **{'Enabled' if df_complete.loc[worst_idx, 'use_enrichment_kb'] == 1 else 'Disabled'}**")
md_lines.append(f"- Shortcuts: **{'Enabled' if df_complete.loc[worst_idx, 'use_shortcuts'] == 1 else 'Disabled'}**")
md_lines.append(f"- Query Expansion: **{'Enabled' if df_complete.loc[worst_idx, 'expand_query'] == 1 else 'Disabled'}**")
md_lines.append("")

md_lines.append("### 6.3 Key Differences")
md_lines.append("")
md_lines.append("Comparing best vs. worst configurations:")
md_lines.append("")

for param, param_name in params_info.items():
    best_val = df_complete.loc[best_idx, param]
    worst_val = df_complete.loc[worst_idx, param]

    if best_val == worst_val:
        diff = "**Same** (both " + ("enabled" if best_val == 1 else "disabled") + ")"
    else:
        best_status = "enabled" if best_val == 1 else "disabled"
        worst_status = "enabled" if worst_val == 1 else "disabled"
        diff = f"**Different** (best: {best_status}, worst: {worst_status})"

    md_lines.append(f"- **{param_name}**: {diff}")

md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Key Insights
md_lines.append("## 7. Key Insights and Recommendations")
md_lines.append("")

md_lines.append("### 7.1 Main Findings")
md_lines.append("")

# Sort correlations by absolute value
sorted_correlations = sorted(correlations.items(), key=lambda x: abs(x[1]) if not pd.isna(x[1]) else 0, reverse=True)

md_lines.append("**Parameter Impact (by correlation strength)**:")
md_lines.append("")
for i, (param, corr) in enumerate(sorted_correlations, 1):
    if pd.isna(corr):
        continue
    param_name = params_info[param]
    direction = "positively" if corr > 0 else "negatively"
    md_lines.append(f"{i}. **{param_name}** ({corr:+.4f}): Most {direction} associated with accuracy")

md_lines.append("")

# Specific insights
md_lines.append("### 7.2 Specific Insights")
md_lines.append("")

# OpenIE analysis
openie_effect = df_complete.groupby('use_openie')['accuracy'].mean()
if len(openie_effect) == 2:
    if openie_effect[1] < openie_effect[0]:
        md_lines.append(f"1. **OpenIE appears detrimental**: Enabling OpenIE consistently reduces accuracy by {(openie_effect[0] - openie_effect[1])*100:.2f} percentage points on average. This suggests that the OpenIE extraction may introduce noise or irrelevant information.")
    else:
        md_lines.append(f"1. **OpenIE appears beneficial**: Enabling OpenIE increases accuracy by {(openie_effect[1] - openie_effect[0])*100:.2f} percentage points on average.")
    md_lines.append("")

# KB enrichment analysis
kb_effect = df_complete.groupby('use_enrichment_kb')['accuracy'].mean()
if len(kb_effect) == 2:
    if kb_effect[1] > kb_effect[0]:
        md_lines.append(f"2. **KB Enrichment shows slight benefit**: Enabling knowledge base enrichment provides a small improvement of {(kb_effect[1] - kb_effect[0])*100:.2f} percentage points.")
    else:
        md_lines.append(f"2. **KB Enrichment shows slight detriment**: Enabling knowledge base enrichment reduces accuracy by {(kb_effect[0] - kb_effect[1])*100:.2f} percentage points.")
    md_lines.append("")

# Query expansion analysis
expand_effect = df_complete.groupby('expand_query')['accuracy'].mean()
if len(expand_effect) == 2:
    if expand_effect[1] > expand_effect[0]:
        md_lines.append(f"3. **Query Expansion helps marginally**: Expanding queries with synonyms improves accuracy by {(expand_effect[1] - expand_effect[0])*100:.2f} percentage points.")
    else:
        md_lines.append(f"3. **Query Expansion reduces performance**: Expanding queries with synonyms decreases accuracy by {(expand_effect[0] - expand_effect[1])*100:.2f} percentage points.")
    md_lines.append("")

# Best combination insight
md_lines.append(f"4. **Optimal configuration**: The best-performing configuration combines OpenIE={'enabled' if df_complete.loc[best_idx, 'use_openie'] == 1 else 'disabled'}, KB enrichment={'enabled' if df_complete.loc[best_idx, 'use_enrichment_kb'] == 1 else 'disabled'}, shortcuts={'enabled' if df_complete.loc[best_idx, 'use_shortcuts'] == 1 else 'disabled'}, and query expansion={'enabled' if df_complete.loc[best_idx, 'expand_query'] == 1 else 'disabled'}.")
md_lines.append("")

md_lines.append("### 7.3 Recommendations")
md_lines.append("")
md_lines.append("Based on the analysis:")
md_lines.append("")

# Generate recommendations based on correlations
recommendations = []

for param, corr in correlations.items():
    if pd.isna(corr):
        continue
    param_name = params_info[param]

    if corr < -0.3:
        recommendations.append(f"**Disable {param_name}**: Shows moderate to strong negative correlation ({corr:.3f}) with accuracy")
    elif corr > 0.3:
        recommendations.append(f"**Enable {param_name}**: Shows moderate to strong positive correlation ({corr:.3f}) with accuracy")

if recommendations:
    for i, rec in enumerate(recommendations, 1):
        md_lines.append(f"{i}. {rec}")
else:
    md_lines.append("1. **Limited parameter effects**: None of the individual parameters show strong correlation with accuracy. Performance may depend more on parameter interactions or other factors not captured in this configuration space.")

md_lines.append("")
md_lines.append(f"2. **For optimal performance**: Use the configuration from run {df_complete.loc[best_idx, 'run']}, which achieved the highest accuracy of {df_complete.loc[best_idx, 'accuracy']:.2%}.")
md_lines.append("")
md_lines.append("3. **Further investigation**: Given the relatively small sample size (7 complete runs), consider:")
md_lines.append("   - Running additional experiments to confirm these findings")
md_lines.append("   - Testing configurations not yet explored (e.g., with shortcuts enabled)")
md_lines.append("   - Investigating why OpenIE appears to hurt performance")
md_lines.append("")

md_lines.append("---")
md_lines.append("")

# Limitations
md_lines.append("## 8. Limitations and Caveats")
md_lines.append("")
md_lines.append("1. **Small sample size**: Only 7 complete experimental runs limits statistical power")
md_lines.append("2. **Missing configurations**: The 'shortcuts' parameter was never enabled, preventing full factorial analysis")
md_lines.append("3. **Single replication**: Most configurations tested only once, making it impossible to assess measurement variability")
md_lines.append("4. **Incomplete data**: Run 3 appears to have failed or been interrupted")
md_lines.append("5. **Confounding factors**: Other parameters (models, prompts, etc.) were held constant and may interact with these configuration choices")
md_lines.append("")

md_lines.append("---")
md_lines.append("")
md_lines.append("*Report generated automatically from experimental results*")

# Write markdown file
output_file = "/workspace/repo/CONFIG_ANALYSIS_REPORT.md"
with open(output_file, 'w') as f:
    f.write('\n'.join(md_lines))

print(f"Report saved to: {output_file}")
print(f"Total lines: {len(md_lines)}")
