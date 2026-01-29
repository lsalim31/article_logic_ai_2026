#!/usr/bin/env python3
"""
download_sample.py

Download and filter 100 examples from DocNLI test set.

Filtering criteria:
- Premise length: 200-500 words
- Balanced: 50 entailment, 50 not-entailment
- Priority: FEVER/SQuAD sources if metadata available

Output:
- doc-nli/sample_100.json

TODO:
1. Load DocNLI test set from TensorFlow Datasets
2. Filter by premise word count (200-500)
3. Separate into entailment and not-entailment pools
4. Sample 50 from each pool
5. Store original_idx for traceability
6. Save as JSON with structure:
   {
     "metadata": {
       "source": "DocNLI test split",
       "filter_criteria": {...},
       "download_timestamp": "..."
     },
     "examples": [
       {
         "example_id": 0,
         "original_idx": 4523,
         "premise": "...",
         "hypothesis": "...",
         "label": "entailment" or "not_entailment"
       },
       ...
     ]
   }
"""

# TODO: Implement
pass
