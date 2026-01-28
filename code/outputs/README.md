# Outputs

**Storage for generated files and experiment results**

## Structure

```
outputs/
├── logified/          # Logified JSON structures
│   └── active.json    # Active structure
└── results/           # Experiment results
```

## File Types

- `<name>_logified.json` - Logic structure
- `<name>_weighted.json` - With weights
- `<experiment>_results.json` - Results
- `<experiment>_metrics.json` - Metrics

## Usage

```python
import json
with open('outputs/logified/active.json') as f:
    logified = json.load(f)
```

## Git Integration

This directory is excluded from git (see `.gitignore`).
