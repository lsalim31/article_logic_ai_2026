#!/usr/bin/env python3
"""
experiment_logify_DocNLI.py

Experiment: Evaluate Logify on DocNLI dataset (100 filtered examples).

See DESCRIPTION_EXPERIMENT_DOCNLI_LOGIFY.md for details.

Usage:
    python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY
    python experiment_logify_DocNLI.py --api-key $OPENROUTER_API_KEY --temperature 0.0

Environment:
    OPENROUTER_API_KEY: API key (used if --api-key not provided)

Models:
    - Logification: openai/gpt-5.2 (fixed)
    - Query translation: openai/gpt-5-nano (configurable)
    - Weight assignment: gpt-4o (configurable)

Pipeline per example:
    1. Load premise from sample_100.json
    2. Check cache for logified structure
    3. If not cached: Logify premise -> assign weights -> cache
    4. Translate hypothesis to logical formula
    5. Solve formula against logified structure
    6. Map prediction (TRUE/FALSE/UNCERTAIN) to binary (entailment/not_entailment)
    7. Compare to ground truth, record metrics

Output:
    results_logify_DocNLI/experiment_YYYYMMDD_HHMMSS.json

TODO:
1. Setup paths and constants (CACHE_DIR, RESULTS_DIR, LOGIFY_MODEL, etc.)
2. Implement load_sample_data() - load doc-nli/sample_100.json
3. Implement get_ground_truth_label() - return "entailment" or "not_entailment"
4. Implement map_prediction_to_binary() - TRUE->entailment, FALSE/UNCERTAIN->not_entailment
5. Implement get_cached_logified_path() - use example_id for cache file naming
6. Implement logify_premise() - similar to logify_document() in ContractNLI
   - Check cache first
   - Run LogifyConverter
   - Assign weights
   - Save to cache
7. Implement query_hypothesis() - similar to ContractNLI
   - Translate hypothesis to formula
   - Run LogicSolver
   - Return prediction, confidence, formula
8. Implement run_experiment() - main loop
   - Load sample data
   - For each example:
     - Logify premise (with caching)
     - Query hypothesis
     - Map to binary
     - Compare to ground truth
     - Store results
   - Save intermediate results after each example
   - Compute final accuracy
9. Implement main() with argparse
   - --api-key
   - --query-model (default: openai/gpt-5-nano)
   - --weights-model (default: gpt-4o)
   - --temperature (default: 0.1)
   - --reasoning-effort (default: medium)
   - --max-tokens (default: 128000)
   - --query-max-tokens (default: 64000)
   - --k-weights (default: 10)
   - --k-query (default: 20)
"""

# TODO: Implement
pass
