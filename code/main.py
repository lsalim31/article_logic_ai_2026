#!/usr/bin/env python3
"""
main.py - Unified CLI for the Logify Neuro-Symbolic Reasoning System

Two modes:
  1. logify: Convert document to weighted propositional logic
  2. query: Ask natural language questions about a logified document

Usage:
    python main.py logify --fpath document.pdf --key sk-...
    python main.py query --fpath document.pdf --jpath document_weighted.json --query "Is X allowed?" --key sk-...

Environment Variables:
    OPENAI_API_KEY: Default API key if --key not provided
    OPENROUTER_API_KEY: Alternative API key source (checked if OPENAI_API_KEY not set)
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add code directory to Python path
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from from_text_to_logic.logify import LogifyConverter, extract_text_from_document
from from_text_to_logic.weights import assign_weights
from interface_with_user.translate import translate_query
from logic_solver import LogicSolver


def get_api_key(args_key: str = None) -> str:
    """
    Get API key from arguments or environment variables.

    Priority:
      1. --key argument
      2. OPENAI_API_KEY environment variable
      3. OPENROUTER_API_KEY environment variable

    Args:
        args_key: Key provided via command line argument

    Returns:
        API key string

    Raises:
        ValueError: If no API key found
    """
    if args_key:
        return args_key

    # Check environment variables
    key = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENROUTER_API_KEY')

    if not key:
        raise ValueError(
            "No API key provided. Use --key argument or set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable."
        )

    return key


def run_logify(args) -> int:
    """
    Run the logify pipeline: document -> logified JSON -> weighted JSON.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        api_key = get_api_key(args.key)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Validate input file
    fpath = Path(args.fpath)
    if not fpath.exists():
        print(f"Error: Input file not found: {args.fpath}")
        return 1

    # Determine output directory
    if args.opath:
        opath = Path(args.opath)
        opath.mkdir(parents=True, exist_ok=True)
    else:
        opath = fpath.parent

    # Output file paths
    stem = fpath.stem
    logified_path = opath / f"{stem}.json"
    weighted_path = opath / f"{stem}_weighted.json"

    try:
        # Step 1: Extract text from document
        print(f"Reading document: {fpath}")
        text = extract_text_from_document(str(fpath))
        print(f"  Extracted {len(text)} characters")

        # Step 2: Convert to logic structure
        print(f"\nConverting to logic structure...")
        print(f"  Model: {args.model}")
        print(f"  Reasoning effort: {args.reasoning_effort}")

        converter = LogifyConverter(
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens
        )

        try:
            logic_structure = converter.convert_text_to_logic(text)
            converter.save_output(logic_structure, str(logified_path))
            print(f"  Saved logified structure to: {logified_path}")
        finally:
            converter.close()

        # Step 3: Assign weights to soft constraints
        print(f"\nAssigning weights to soft constraints...")
        print(f"  Model: {args.weights_model}")
        print(f"  Top-k chunks: {args.k}")

        assign_weights(
            pathfile=str(fpath),
            json_path=str(logified_path),
            api_key=api_key,
            model=args.weights_model,
            temperature=0.0,  # Fixed for logprobs
            max_tokens=5,     # Fixed for YES/NO
            k=args.k,
            verbose=not args.quiet
        )

        print(f"\n{'='*50}")
        print(f"Logify completed successfully!")
        print(f"  Logified structure: {logified_path}")
        print(f"  Weighted structure: {weighted_path}")
        print(f"{'='*50}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_query(args) -> int:
    """
    Run the query pipeline: query + weighted JSON -> solver result.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        api_key = get_api_key(args.key)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Determine weighted JSON path
    if args.jpath:
        jpath = Path(args.jpath)
    else:
        # Auto-derive from fpath
        fpath = Path(args.fpath)
        jpath = fpath.parent / f"{fpath.stem}_weighted.json"

    # Validate weighted JSON exists
    if not jpath.exists():
        print(f"Error: Weighted JSON file not found: {jpath}")
        print(f"\nHint: Run 'python main.py logify --fpath {args.fpath}' first to create it.")
        return 1

    try:
        # Step 1: Load the weighted logified structure
        if not args.quiet:
            print(f"Loading weighted structure: {jpath}")

        with open(jpath, 'r', encoding='utf-8') as f:
            logified_structure = json.load(f)

        # Step 2: Translate natural language query to propositional formula
        if not args.quiet:
            print(f"\nTranslating query: \"{args.query}\"")
            print(f"  Model: {args.model}")

        translation_result = translate_query(
            query=args.query,
            json_path=str(jpath),
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens,
            k=args.k,
            verbose=not args.quiet
        )

        formula = translation_result.get('formula')
        if not formula:
            print("Error: Failed to translate query to formula")
            return 1

        if not args.quiet:
            print(f"\n  Formula: {formula}")

        # Step 3: Solve the query using MaxSAT
        if not args.quiet:
            print(f"\nSolving query...")

        solver = LogicSolver(logified_structure)
        solver_result = solver.query(formula)

        # Step 4: Build output JSON
        output = {
            "query": args.query,
            "converted_query": translation_result.get('query', args.query),
            "formula": formula,
            "formula_translation": translation_result.get('translation', ''),
            "formula_explanation": translation_result.get('explanation', ''),
            "answer": solver_result.answer,
            "confidence": solver_result.confidence,
            "explanation": solver_result.explanation
        }

        # Add original_query if it was a yes/no question that got converted
        if 'original_query' in translation_result:
            output['original_query'] = translation_result['original_query']

        # Output JSON
        print(json.dumps(output, indent=2, ensure_ascii=False))

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {jpath}: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Logify: Neuro-Symbolic Reasoning System",
        epilog="Use 'python main.py <command> --help' for command-specific help."
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ========== LOGIFY COMMAND ==========
    logify_parser = subparsers.add_parser(
        'logify',
        help='Convert document to weighted propositional logic',
        description='Convert a document (PDF/DOCX/TXT) to a weighted logified JSON structure.'
    )

    logify_parser.add_argument(
        '--fpath',
        required=True,
        help='Path to input document (PDF, DOCX, or TXT)'
    )
    logify_parser.add_argument(
        '--opath',
        default=None,
        help='Output directory for JSON files (default: same directory as input)'
    )
    logify_parser.add_argument(
        '--key',
        default=None,
        help='API key (default: OPENAI_API_KEY or OPENROUTER_API_KEY env var)'
    )
    logify_parser.add_argument(
        '--model',
        default='gpt-5.2',
        help='Model for logic conversion (default: gpt-5.2)'
    )
    logify_parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Sampling temperature (default: 0.1, ignored for reasoning models)'
    )
    logify_parser.add_argument(
        '--reasoning-effort',
        default='medium',
        choices=['none', 'low', 'medium', 'high', 'xhigh'],
        help='Reasoning effort for gpt-5.2/o1/o3 models (default: medium)'
    )
    logify_parser.add_argument(
        '--max-tokens',
        type=int,
        default=128000,
        help='Maximum tokens in LLM response (default: 128000)'
    )
    logify_parser.add_argument(
        '--weights-model',
        default='gpt-4o',
        help='Model for weight assignment (must support logprobs, default: gpt-4o)'
    )
    logify_parser.add_argument(
        '--k',
        type=int,
        default=10,
        help='Number of chunks to retrieve for weight assignment (default: 10)'
    )
    logify_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    # ========== QUERY COMMAND ==========
    query_parser = subparsers.add_parser(
        'query',
        help='Query a logified document',
        description='Ask natural language questions about a logified document.'
    )

    query_parser.add_argument(
        '--fpath',
        required=True,
        help='Path to original document (used to find weighted JSON if --jpath not provided)'
    )
    query_parser.add_argument(
        '--jpath',
        default=None,
        help='Path to weighted JSON file (default: {fpath_stem}_weighted.json)'
    )
    query_parser.add_argument(
        '--query',
        required=True,
        help='Natural language query'
    )
    query_parser.add_argument(
        '--key',
        default=None,
        help='API key (default: OPENAI_API_KEY or OPENROUTER_API_KEY env var)'
    )
    query_parser.add_argument(
        '--model',
        default='gpt-5.2',
        help='Model for query translation (default: gpt-5.2)'
    )
    query_parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Sampling temperature (default: 0.1, ignored for reasoning models)'
    )
    query_parser.add_argument(
        '--reasoning-effort',
        default='medium',
        choices=['none', 'low', 'medium', 'high', 'xhigh'],
        help='Reasoning effort for gpt-5.2/o1/o3 models (default: medium)'
    )
    query_parser.add_argument(
        '--max-tokens',
        type=int,
        default=64000,
        help='Maximum tokens in LLM response (default: 64000)'
    )
    query_parser.add_argument(
        '--k',
        type=int,
        default=20,
        help='Number of propositions to retrieve for query translation (default: 20)'
    )
    query_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages (only output JSON)'
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Route to appropriate function
    if args.command == 'logify':
        return run_logify(args)
    elif args.command == 'query':
        return run_query(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
