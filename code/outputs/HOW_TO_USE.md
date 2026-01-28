# How to Use: Outputs Directory

## Directory Structure

```
outputs/
├── logified/          # Logified JSON files
│   └── active.json   # Currently active structure
└── results/           # Experiment results
```

## Save Logified Structure

```python
import json

with open('outputs/logified/my_document.json', 'w') as f:
    json.dump(logified, f, indent=2)

# Set as active
import shutil
shutil.copy(
    'outputs/logified/my_document.json',
    'outputs/logified/active.json'
)
```

## Load Active Structure

```python
with open('outputs/logified/active.json') as f:
    logified = json.load(f)
```

## File Naming

- `<name>_logified.json` - Logified structure
- `<name>_weighted.json` - With weights
- `<experiment>_results.json` - Experiment results
- `active.json` - Current active structure

## Cleanup

```bash
# Remove files older than 30 days
find outputs/ -name "*.json" -mtime +30 -delete

# Archive
tar -czf outputs_backup.tar.gz outputs/
```
