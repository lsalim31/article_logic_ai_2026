#!/usr/bin/env python3
"""
experiment_logify_logicBench.py

Evaluates the Logify neuro-symbolic pipeline on LogicBench (BQA).

Pipeline per sample:
  1. Logify: context -> weighted propositional logic (cached)
  2. Query: for each QA pair, translate + solve
  3. Record: predicted_answer, confidence, latency, errors

Usage:
  python experiment_logify_logicBench.py --api_key $OPENAI_API_KEY
  python experiment_logify_logicBench.py --api_key $OPENAI_API_KEY --logic_type propositional_logic
  python experiment_logify_logicBench.py --api_key $OPENAI_API_KEY --max_samples 5
"""

import sys
import os
import json
import time
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add code directory to path
_script_dir = Path(__file__).resolve().parent
_code_dir = _script_dir.parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

# Import Logify components
from from_text_to_logic.logify import LogifyConverter
from from_text_to_logic.weights import assign_weights
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver

# Import PATTERNS from LogicBench loader
from fol_vs_boolean.updated_load_logicbench import PATTERNS


# Directory paths
CACHE_DIR = _script_dir / "cache"
RESULTS_DIR = _script_dir / "results_logify_LOGICBENCH"


def load_logicbench_grouped(dataset_type='eval', task_type='BQA', logic_type='all',
                            patterns=None, max_samples_per_pattern=None):
    """
    Load LogicBench with samples grouped by context (all QA pairs together).

    Returns:
        List of samples, each with:
            - id: sample id
            - text: context/premises
            - logic_type: propositional_logic, first_order_logic, or nm_logic
            - pattern: reasoning pattern name
            - qa_pairs: list of {query, ground_truth}
    """
    import urllib.request
    import urllib.error

    BASE_URL = "https://raw.githubusercontent.com/Mihir3009/LogicBench/main/data"

    if dataset_type == 'eval':
        dataset_folder = f"LogicBench(Eval)/{task_type}"
    else:
        dataset_folder = "LogicBench(Aug)/BQA"

    if logic_type == 'all':
        logic_types = list(PATTERNS.keys())
    else:
        logic_types = [logic_type]

    samples = []

    for lt in logic_types:
        available_patterns = PATTERNS.get(lt, [])

        if patterns:
            target_patterns = [p for p in patterns if p in available_patterns]
        else:
            target_patterns = available_patterns

        for pattern in target_patterns:
            folder_name = f"{dataset_folder}/{lt}/{pattern}"
            url = f"{BASE_URL}/{folder_name}/data_instances.json"

            try:
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read().decode())

                pattern_samples = data.get('samples', [])
                count = 0

                for sample in pattern_samples:
                    if max_samples_per_pattern and count >= max_samples_per_pattern:
                        break

                    sample_id = sample.get('id', f"{pattern}_{count}")
                    context = sample.get('context', '')
                    qa_pairs_raw = sample.get('qa_pairs', [])

                    if not qa_pairs_raw:
                        continue

                    qa_pairs = [
                        {'query': qa.get('question', ''), 'ground_truth': qa.get('answer', '')}
                        for qa in qa_pairs_raw
                    ]

                    samples.append({
                        'id': f"{lt}_{pattern}_{sample_id}",
                        'text': context,
                        'logic_type': lt,
                        'pattern': pattern,
                        'qa_pairs': qa_pairs
                    })
                    count += 1

                print(f"  Loaded {count} samples from {lt}/{pattern}")

            except urllib.error.HTTPError as e:
                print(f"  Error loading {pattern}: HTTP {e.code}")
            except Exception as e:
                print(f"  Error loading {pattern}: {e}")

    print(f"Total loaded: {len(samples)} samples")
    return samples


def get_cache_path(sample_id: str) -> Path:
    """Return cache path for a sample's logified structure."""
    safe_id = sample_id.replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"doc_{safe_id}_weighted.json"


def run_logify(text: str, sample_id: str, api_key: str,
               model: str = "gpt-4o", verbose: bool = True) -> Tuple[Optional[Dict], float, bool, Optional[str]]:
    """
    Run logify pipeline on text, with caching.

    Returns:
        (logified_structure, latency_sec, cached, error)
    """
    cache_path = get_cache_path(sample_id)

    # Check cache
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            if verbose:
                print(f"    [CACHE HIT] Loaded from {cache_path}")
            return structure, 0.0, True, None
        except Exception as e:
            if verbose:
                print(f"    [CACHE ERROR] {e}, regenerating...")

    # Run logify
    start_time = time.time()

    try:
        # Create temp file for text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text)
            temp_path = f.name

        try:
            # Step 1: Convert text to logic
            if verbose:
                print(f"    Converting to logic structure...")

            converter = LogifyConverter(
                api_key=api_key,
                model=model,
                temperature=0.1,
                reasoning_effort="medium",
                max_tokens=128000
            )

            try:
                logic_structure = converter.convert_text_to_logic(text)

                # Save intermediate JSON (before weights)
                json_path = cache_path.with_suffix('.json').with_name(
                    cache_path.stem.replace('_weighted', '') + '.json'
                )
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(logic_structure, f, indent=2, ensure_ascii=False)

            finally:
                converter.close()

            # Step 2: Assign weights
            if verbose:
                print(f"    Assigning weights...")

            assign_weights(
                pathfile=temp_path,
                json_path=str(json_path),
                api_key=api_key,
                model="gpt-4o",  # Must use model with logprobs
                temperature=0.0,
                max_tokens=5,
                k=10,
                verbose=False
            )

            # Load weighted structure
            with open(cache_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)

            latency = time.time() - start_time

            if verbose:
                print(f"    Logify completed in {latency:.1f}s")

            return structure, latency, False, None

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        latency = time.time() - start_time
        error_msg = str(e)
        if verbose:
            print(f"    [LOGIFY ERROR] {error_msg}")
        return None, latency, False, error_msg


def run_query(query: str, logified_structure: Dict, api_key: str,
              model: str = "gpt-4o", verbose: bool = True) -> Tuple[str, float, float, Optional[str]]:
    """
    Run query translation and solving.

    Returns:
        (predicted_answer, confidence, latency_sec, error)
    """
    start_time = time.time()

    try:
        # Save structure to temp file for translate_query
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(logified_structure, f)
            temp_json_path = f.name

        try:
            # Translate query to formula
            if verbose:
                print(f"      Translating query...")

            translation_result = translate_query(
                query=query,
                json_path=temp_json_path,
                api_key=api_key,
                model=model,
                temperature=0.1,
                reasoning_effort="medium",
                max_tokens=64000,
                k=20,
                verbose=False
            )

            formula = translation_result.get('formula')
            if not formula:
                raise ValueError("Failed to translate query to formula")

            if verbose:
                print(f"      Formula: {formula}")

            # Solve
            if verbose:
                print(f"      Solving...")

            solver = LogicSolver(logified_structure)
            solver_result = solver.query(formula)

            latency = time.time() - start_time

            if verbose:
                print(f"      Result: {solver_result.answer} (confidence={solver_result.confidence:.3f})")

            return solver_result.answer, solver_result.confidence, latency, None

        finally:
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)

    except Exception as e:
        latency = time.time() - start_time
        error_msg = str(e)
        if verbose:
            print(f"      [QUERY ERROR] {error_msg}")
        return "UNCERTAIN", 0.5, latency, error_msg


def run_experiment(
    logic_type: str = 'all',
    patterns: Optional[List[str]] = None,
    max_samples_per_pattern: Optional[int] = None,
    api_key: str = None,
    model: str = "gpt-4o",
    verbose: bool = True
) -> List[Dict]:
    """
    Run the full experiment on LogicBench.

    Returns:
        List of result dicts
    """
    # Ensure directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load samples
    print(f"\n{'='*60}")
    print("Loading LogicBench samples...")
    print(f"{'='*60}")

    samples = load_logicbench_grouped(
        dataset_type='eval',
        task_type='BQA',
        logic_type=logic_type,
        patterns=patterns,
        max_samples_per_pattern=max_samples_per_pattern
    )

    if not samples:
        print("No samples loaded!")
        return []

    # Process samples
    print(f"\n{'='*60}")
    print(f"Processing {len(samples)} samples...")
    print(f"{'='*60}")

    results = []

    for i, sample in enumerate(samples):
        print(f"\n[{i+1}/{len(samples)}] Sample: {sample['id']}")
        print(f"  Pattern: {sample['pattern']}")
        print(f"  Logic type: {sample['logic_type']}")
        print(f"  Context: {sample['text'][:100]}...")

        # Run logify
        logified_structure, logify_latency, logify_cached, logify_error = run_logify(
            text=sample['text'],
            sample_id=sample['id'],
            api_key=api_key,
            model=model,
            verbose=verbose
        )

        # Build result
        result = {
            'id': sample['id'],
            'text': sample['text'],
            'logic_type': sample['logic_type'],
            'pattern': sample['pattern'],
            'logify_latency_sec': logify_latency,
            'logify_cached': logify_cached,
            'logify_error': logify_error,
            'questions': []
        }

        # Process questions if logify succeeded
        if logified_structure is not None:
            for j, qa in enumerate(sample['qa_pairs']):
                print(f"  Question {j+1}/{len(sample['qa_pairs'])}: {qa['query'][:60]}...")

                predicted_answer, confidence, query_latency, query_error = run_query(
                    query=qa['query'],
                    logified_structure=logified_structure,
                    api_key=api_key,
                    model=model,
                    verbose=verbose
                )

                result['questions'].append({
                    'query': qa['query'],
                    'predicted_answer': predicted_answer,
                    'confidence': confidence,
                    'ground_truth': qa['ground_truth'],
                    'query_latency_total_sec': query_latency,
                    'query_error': query_error
                })
        else:
            # Logify failed, mark all questions as errors
            for qa in sample['qa_pairs']:
                result['questions'].append({
                    'query': qa['query'],
                    'predicted_answer': 'UNCERTAIN',
                    'confidence': 0.0,
                    'ground_truth': qa['ground_truth'],
                    'query_latency_total_sec': 0.0,
                    'query_error': f"Logify failed: {logify_error}"
                })

        results.append(result)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"experiment_{timestamp}.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Experiment completed!")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}")

    # Print summary
    total_questions = sum(len(r['questions']) for r in results)
    correct = sum(
        1 for r in results for q in r['questions']
        if (q['predicted_answer'] == 'TRUE' and q['ground_truth'] == 'yes') or
           (q['predicted_answer'] == 'FALSE' and q['ground_truth'] == 'no')
    )

    print(f"\nSummary:")
    print(f"  Total samples: {len(results)}")
    print(f"  Total questions: {total_questions}")
    print(f"  Correct: {correct}")
    print(f"  Accuracy: {correct/total_questions*100:.1f}%" if total_questions > 0 else "  Accuracy: N/A")

    return results


def get_api_key(args_key: Optional[str] = None) -> str:
    """
    Get API key from arguments or environment variables.

    Priority:
      1. --api_key argument
      2. OPENROUTER_API_KEY environment variable
      3. OPENAI_API_KEY environment variable

    Returns:
        API key string

    Raises:
        ValueError: If no API key found
    """
    if args_key:
        return args_key

    key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')

    if not key:
        raise ValueError(
            "No API key provided. Use --api_key argument or set "
            "OPENROUTER_API_KEY or OPENAI_API_KEY environment variable."
        )

    return key


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Logify on LogicBench (BQA)"
    )
    parser.add_argument(
        "--api_key",
        default=None,
        help="API key (default: OPENROUTER_API_KEY or OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--logic_type",
        default="all",
        choices=["all", "propositional_logic", "first_order_logic", "nm_logic"],
        help="Logic type to test (default: all)"
    )
    parser.add_argument(
        "--patterns",
        default=None,
        help="Comma-separated list of patterns (default: all)"
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Max samples per pattern (default: all)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model (default: gpt-4o)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    # Get API key
    try:
        api_key = get_api_key(args.api_key)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    patterns = args.patterns.split(",") if args.patterns else None

    run_experiment(
        logic_type=args.logic_type,
        patterns=patterns,
        max_samples_per_pattern=args.max_samples,
        api_key=api_key,
        model=args.model,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
