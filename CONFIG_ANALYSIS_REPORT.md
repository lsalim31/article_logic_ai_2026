# Configuration Analysis Report

**Experimental Dataset Analysis: Claude Constructed Results**

***

## Executive Summary

This report analyzes the relationship between model configuration parameters and accuracy across 7 experimental runs. Four binary configuration parameters were varied across experiments:

1. **use_openie**: Use OpenIE for information extraction

2. **use_enrichment_kb**: Use knowledge base enrichment

3. **use_shortcuts**: Use subset/shortcut mechanisms

4. **expand_query**: Expand queries with synonyms

**Key Finding**: The best configuration achieved **46.88%** accuracy, while the worst achieved **38.75%** accuracy - a difference of **8.12%**.

***

## 1. Dataset Overview

### 1.1 Runs Summary

* **Total experimental runs**: 8

* **Completed runs with accuracy data**: 7

* **Incomplete runs**: 1 (run3 - appears to be interrupted)

### 1.2 Accuracy Statistics

* **Mean accuracy**: 0.4262 (42.62%)

* **Standard deviation**: 0.0341

* **Minimum accuracy**: 0.3875 (38.75%)

* **Maximum accuracy**: 0.4688 (46.88%)

* **Range**: 0.0812 (8.12 percentage points)

### 1.3 All Experimental Runs

| Run  | OpenIE | KB Enrichment | Shortcuts | Query Expansion | Accuracy | Correct/Total |
| ---- | ------ | ------------- | --------- | --------------- | -------- | ------------- |
| run1 | ✗      | ✗             | ✗         | ✗               | 45.91%   | 73/159        |
| run2 | ✗      | ✓             | ✗         | ✗               | 43.40%   | 69/159        |
| run3 | ✗      | ✓             | ✗         | ✓               | N/A      | N/A           |
| run4 | ✗      | ✗             | ✗         | ✓               | 44.65%   | 71/159        |
| run5 | ✓      | ✓             | ✗         | ✗               | 39.38%   | 63/160        |
| run6 | ✓      | ✗             | ✗         | ✗               | 39.38%   | 63/160        |
| run7 | ✓      | ✗             | ✗         | ✓               | 38.75%   | 62/160        |
| run8 | ✓      | ✓             | ✗         | ✓               | 46.88%   | 75/160        |

***

## 2. Individual Parameter Effects

This section examines how each configuration parameter individually affects model accuracy.

### 2.1 OpenIE

| OpenIE   | Mean Accuracy   | Std Dev | Count | Min    | Max    |
| -------- | --------------- | ------- | ----- | ------ | ------ |
| Disabled | 0.4465 (44.65%) | 0.0126  | 3     | 0.4340 | 0.4591 |
| Enabled  | 0.4109 (41.09%) | 0.0387  | 4     | 0.3875 | 0.4688 |

**Effect size**: -0.0356 (-3.56 percentage points) - **negative**

**Interpretation**: Enabling openie **decreases** accuracy by an average of 3.56 percentage points.

### 2.2 KB Enrichment

| KB Enrichment | Mean Accuracy   | Std Dev | Count | Min    | Max    |
| ------------- | --------------- | ------- | ----- | ------ | ------ |
| Disabled      | 0.4217 (42.17%) | 0.0364  | 4     | 0.3875 | 0.4591 |
| Enabled       | 0.4322 (43.22%) | 0.0375  | 3     | 0.3937 | 0.4688 |

**Effect size**: +0.0104 (+1.04 percentage points) - **positive**

**Interpretation**: Enabling kb enrichment **increases** accuracy by an average of 1.04 percentage points.

### 2.3 Shortcuts

| Shortcuts | Mean Accuracy   | Std Dev | Count | Min    | Max    |
| --------- | --------------- | ------- | ----- | ------ | ------ |
| Disabled  | 0.4262 (42.62%) | 0.0341  | 7     | 0.3875 | 0.4688 |

**Note**: This parameter has only one setting across all runs (always 0). Cannot compute effect size.

### 2.4 Query Expansion

| Query Expansion | Mean Accuracy   | Std Dev | Count | Min    | Max    |
| --------------- | --------------- | ------- | ----- | ------ | ------ |
| Disabled        | 0.4201 (42.01%) | 0.0322  | 4     | 0.3937 | 0.4591 |
| Enabled         | 0.4343 (43.43%) | 0.0420  | 3     | 0.3875 | 0.4688 |

**Effect size**: +0.0141 (+1.41 percentage points) - **positive**

**Interpretation**: Enabling query expansion **increases** accuracy by an average of 1.41 percentage points.

***

## 3. Correlation Analysis

Pearson correlation coefficients between each parameter and accuracy:

| Parameter       | Correlation with Accuracy | Interpretation                     |
| --------------- | ------------------------- | ---------------------------------- |
| OpenIE          | -0.5583                   | Strong negative relationship       |
| KB Enrichment   | +0.1635                   | Weak positive relationship         |
| Shortcuts       | N/A (no variance)         | Parameter constant across all runs |
| Query Expansion | +0.2214                   | Weak positive relationship         |

**Note**: Correlation ranges from -1 (perfect negative) to +1 (perfect positive). Zero indicates no linear relationship.

***

## 4. Parameter Interactions

Analysis of how parameter combinations affect accuracy.

### 4.1 OpenIE × KB Enrichment

| OpenIE | KB Enrichment | Mean Accuracy   | Count |
| ------ | ------------- | --------------- | ----- |
| Off    | Off           | 0.4528 (45.28%) | 2     |
| Off    | On            | 0.4340 (43.40%) | 1     |
| On     | Off           | 0.3906 (39.06%) | 2     |
| On     | On            | 0.4313 (43.12%) | 2     |

**Best combination**: OpenIE=Off, KB Enrichment=Off (45.28%)

### 4.2 OpenIE × Shortcuts

| OpenIE | Shortcuts | Mean Accuracy   | Count |
| ------ | --------- | --------------- | ----- |
| Off    | Off       | 0.4465 (44.65%) | 3     |
| On     | Off       | 0.4109 (41.09%) | 4     |

**Best combination**: OpenIE=Off, Shortcuts=Off (44.65%)

### 4.3 OpenIE × Query Expansion

| OpenIE | Query Expansion | Mean Accuracy   | Count |
| ------ | --------------- | --------------- | ----- |
| Off    | Off             | 0.4465 (44.65%) | 2     |
| Off    | On              | 0.4465 (44.65%) | 1     |
| On     | Off             | 0.3937 (39.38%) | 2     |
| On     | On              | 0.4281 (42.81%) | 2     |

**Best combination**: OpenIE=Off, Query Expansion=Off (44.65%)

### 4.4 KB Enrichment × Shortcuts

| KB Enrichment | Shortcuts | Mean Accuracy   | Count |
| ------------- | --------- | --------------- | ----- |
| Off           | Off       | 0.4217 (42.17%) | 4     |
| On            | Off       | 0.4322 (43.22%) | 3     |

**Best combination**: KB Enrichment=On, Shortcuts=Off (43.22%)

### 4.5 KB Enrichment × Query Expansion

| KB Enrichment | Query Expansion | Mean Accuracy   | Count |
| ------------- | --------------- | --------------- | ----- |
| Off           | Off             | 0.4264 (42.64%) | 2     |
| Off           | On              | 0.4170 (41.70%) | 2     |
| On            | Off             | 0.4139 (41.39%) | 2     |
| On            | On              | 0.4688 (46.88%) | 1     |

**Best combination**: KB Enrichment=On, Query Expansion=On (46.88%)

### 4.6 Shortcuts × Query Expansion

| Shortcuts | Query Expansion | Mean Accuracy   | Count |
| --------- | --------------- | --------------- | ----- |
| Off       | Off             | 0.4201 (42.01%) | 4     |
| Off       | On              | 0.4343 (43.43%) | 3     |

**Best combination**: Shortcuts=Off, Query Expansion=On (43.43%)

***

## 5. Full Configuration Profiles

Complete analysis of all 4-parameter configurations tested:

| Rank | OpenIE | KB Enrich | Shortcuts | Query Exp | Mean Accuracy   | Count | Std Dev |
| ---- | ------ | --------- | --------- | --------- | --------------- | ----- | ------- |
| 1    | ✓      | ✓         | ✗         | ✓         | 0.4688 (46.88%) | 1     | 0.0000  |
| 2    | ✗      | ✗         | ✗         | ✗         | 0.4591 (45.91%) | 1     | 0.0000  |
| 3    | ✗      | ✗         | ✗         | ✓         | 0.4465 (44.65%) | 1     | 0.0000  |
| 4    | ✗      | ✓         | ✗         | ✗         | 0.4340 (43.40%) | 1     | 0.0000  |
| 5    | ✓      | ✗         | ✗         | ✗         | 0.3937 (39.38%) | 1     | 0.0000  |
| 6    | ✓      | ✓         | ✗         | ✗         | 0.3937 (39.38%) | 1     | 0.0000  |
| 7    | ✓      | ✗         | ✗         | ✓         | 0.3875 (38.75%) | 1     | 0.0000  |

***

## 6. Best and Worst Performing Configurations

### 6.1 Best Configuration

**Run**: run8 **Accuracy**: 0.4688 (46.88%) **Correct/Total**: 75/160

**Configuration**:

* OpenIE: **Enabled**

* KB Enrichment: **Enabled**

* Shortcuts: **Disabled**

* Query Expansion: **Enabled**

### 6.2 Worst Configuration

**Run**: run7 **Accuracy**: 0.3875 (38.75%) **Correct/Total**: 62/160

**Configuration**:

* OpenIE: **Enabled**

* KB Enrichment: **Disabled**

* Shortcuts: **Disabled**

* Query Expansion: **Enabled**

### 6.3 Key Differences

Comparing best vs. worst configurations:

* **OpenIE**: **Same** (both enabled)

* **KB Enrichment**: **Different** (best: enabled, worst: disabled)

* **Shortcuts**: **Same** (both disabled)

* **Query Expansion**: **Same** (both enabled)

***

## 7. Key Insights and Recommendations

### 7.1 Main Findings

**Parameter Impact (by correlation strength)**:

1. **OpenIE** (-0.5583): Most negatively associated with accuracy

2. **Query Expansion** (+0.2214): Most positively associated with accuracy

3. **KB Enrichment** (+0.1635): Most positively associated with accuracy

### 7.2 Specific Insights

1. **OpenIE appears detrimental**: Enabling OpenIE consistently reduces accuracy by 3.56 percentage points on average. This suggests that the OpenIE extraction may introduce noise or irrelevant information.

2. **KB Enrichment shows slight benefit**: Enabling knowledge base enrichment provides a small improvement of 1.04 percentage points.

3. **Query Expansion helps marginally**: Expanding queries with synonyms improves accuracy by 1.41 percentage points.

4. **Optimal configuration**: The best-performing configuration combines OpenIE=enabled, KB enrichment=enabled, shortcuts=disabled, and query expansion=enabled.

### 7.3 Recommendations

Based on the analysis:

1. **Disable OpenIE**: Shows moderate to strong negative correlation (-0.558) with accuracy

2. **For optimal performance**: Use the configuration from run run8, which achieved the highest accuracy of 46.88%.

3. **Further investigation**: Given the relatively small sample size (7 complete runs), consider:

   * Running additional experiments to confirm these findings

   * Testing configurations not yet explored (e.g., with shortcuts enabled)

   * Investigating why OpenIE appears to hurt performance

***

## 8. Limitations and Caveats

1. **Small sample size**: Only 7 complete experimental runs limits statistical power

2. **Missing configurations**: The 'shortcuts' parameter was never enabled, preventing full factorial analysis

3. **Single replication**: Most configurations tested only once, making it impossible to assess measurement variability

4. **Incomplete data**: Run 3 appears to have failed or been interrupted

5. **Confounding factors**: Other parameters (models, prompts, etc.) were held constant and may interact with these configuration choices

***

*Report generated automatically from experimental results*
