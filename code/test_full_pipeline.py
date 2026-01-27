#!/usr/bin/env python3
"""
Full Pipeline Integration Test
Tests: Text → Logify → Logic Solver → Query Results

This script tests the complete neuro-symbolic pipeline without modifying any code.
"""

import json
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_full_pipeline():
    """Test the complete pipeline: text → logify → solver → queries"""

    print("=" * 80)
    print("FULL PIPELINE INTEGRATION TEST")
    print("=" * 80)
    print()

    # Check if API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print()
        print("To run this test, you need to:")
        print("  1. Set your OpenAI API key:")
        print("     export OPENAI_API_KEY='your-api-key-here'")
        print("  2. Re-run this script")
        print()
        return False

    print("✓ API key found")
    print()

    # ============================================================================
    # STAGE 1: Read input text
    # ============================================================================
    print("STAGE 1: Reading input text...")
    print("-" * 80)

    input_file = "/workspace/repo/code/test_input.txt"

    try:
        with open(input_file, 'r') as f:
            text = f.read()

        print(f"✓ Loaded text from: {input_file}")
        print(f"  Text length: {len(text)} characters")
        print()
        print("Text content:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        print()
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found: {input_file}")
        return False

    # ============================================================================
    # STAGE 2: Logify the text (Text → Logic)
    # ============================================================================
    print("STAGE 2: Logifying text (extracting propositions and constraints)...")
    print("-" * 80)

    try:
        # Import logify module
        from from_text_to_logic.logify import LogifyConverter

        print("✓ Imported LogifyConverter")
        print()

        # Initialize converter
        print("Initializing converter with gpt-4o (cheaper for testing)...")
        converter = LogifyConverter(
            api_key=api_key,
            model="gpt-4o",  # Using cheaper model for testing
            temperature=0.1,
            reasoning_effort="low",
            max_tokens=4000
        )
        print("✓ Converter initialized")
        print()

        # Convert text to logic
        print("Converting text to logic structure (this may take 30-60 seconds)...")
        logified_structure = converter.convert_text_to_logic(text)
        print("✓ Text successfully logified!")
        print()

        # Save the logified structure
        output_file = "/workspace/repo/code/test_logified_output.json"
        converter.save_output(logified_structure, output_file)
        print(f"✓ Logified structure saved to: {output_file}")
        print()

        # Display summary
        print("Logified Structure Summary:")
        print(f"  - Primitive propositions: {len(logified_structure.get('primitive_props', []))}")
        print(f"  - Hard constraints: {len(logified_structure.get('hard_constraints', []))}")
        print(f"  - Soft constraints: {len(logified_structure.get('soft_constraints', []))}")
        print()

        # Show some examples
        if logified_structure.get('primitive_props'):
            print("Sample propositions:")
            for prop in logified_structure['primitive_props'][:3]:
                print(f"  {prop['id']}: {prop.get('translation', 'N/A')}")
            print()

        if logified_structure.get('hard_constraints'):
            print("Hard constraints (must hold):")
            for constraint in logified_structure['hard_constraints']:
                print(f"  {constraint['id']}: {constraint.get('formula', 'N/A')}")
                print(f"    → {constraint.get('translation', 'N/A')}")
            print()

        if logified_structure.get('soft_constraints'):
            print("Soft constraints (defeasible):")
            for constraint in logified_structure['soft_constraints']:
                print(f"  {constraint['id']}: {constraint.get('formula', 'N/A')}")
                print(f"    → {constraint.get('translation', 'N/A')}")
            print()

        # Clean up
        converter.close()

    except ImportError as e:
        print(f"❌ ERROR: Failed to import required modules: {e}")
        print()
        print("Make sure you have installed the required dependencies:")
        print("  pip install openai stanford-openie")
        return False
    except Exception as e:
        print(f"❌ ERROR during logification: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ============================================================================
    # STAGE 3: Load logified structure into Logic Solver
    # ============================================================================
    print()
    print("STAGE 3: Loading logified structure into Logic Solver...")
    print("-" * 80)

    try:
        # Check if pysat is installed
        try:
            import pysat
            print("✓ PySAT library available")
        except ImportError:
            print("❌ ERROR: PySAT library not installed")
            print()
            print("To install PySAT:")
            print("  pip install python-sat")
            print()
            return False

        # Import logic solver
        from logic_solver import LogicSolver

        print("✓ Imported LogicSolver")
        print()

        # Initialize solver with the logified structure
        print("Initializing Logic Solver with logified structure...")
        solver = LogicSolver(logified_structure)
        print("✓ Solver initialized successfully!")
        print()

    except Exception as e:
        print(f"❌ ERROR: Failed to initialize solver: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ============================================================================
    # STAGE 4: Query the solver with propositional formulas
    # ============================================================================
    print("STAGE 4: Querying the solver with propositional logic formulas...")
    print("-" * 80)
    print()

    # Define test queries
    # Note: These queries use the proposition IDs from the logified structure
    # We'll try to infer reasonable queries based on common patterns

    queries = []

    # Try to construct queries based on the extracted structure
    prop_ids = [p['id'] for p in logified_structure.get('primitive_props', [])]

    if len(prop_ids) >= 2:
        queries.append({
            "description": f"Query the first proposition ({prop_ids[0]})",
            "formula": prop_ids[0],
            "expected": "Checks if this proposition is necessarily true"
        })

        queries.append({
            "description": f"Query conjunction of first two propositions",
            "formula": f"{prop_ids[0]} & {prop_ids[1]}",
            "expected": "Checks if both can be true together"
        })

    # Add queries for hard constraints if they exist
    if logified_structure.get('hard_constraints'):
        for constraint in logified_structure['hard_constraints'][:2]:
            queries.append({
                "description": f"Verify hard constraint {constraint['id']}",
                "formula": constraint.get('formula', ''),
                "expected": "Should be TRUE (entailed by hard constraints)"
            })

    # Execute queries
    if not queries:
        print("⚠ WARNING: Could not construct queries from the logified structure")
        print("This might mean the logification didn't extract propositions properly.")
        print()
        return False

    print(f"Running {len(queries)} test queries...")
    print()

    success_count = 0
    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query['description']}")
        print(f"  Formula: {query['formula']}")
        print(f"  Expected: {query['expected']}")

        try:
            result = solver.query(query['formula'])
            print(f"  ✓ Result: {result.answer}")
            print(f"    Confidence: {result.confidence:.3f}")
            print(f"    Explanation: {result.explanation[:100]}..." if len(result.explanation) > 100 else f"    Explanation: {result.explanation}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

        print()

    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    print("=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print()
    print("✓ Stage 1: Text input loaded successfully")
    print("✓ Stage 2: Text logified (propositions + constraints extracted)")
    print("✓ Stage 3: Logic solver initialized")
    print(f"✓ Stage 4: Executed {success_count}/{len(queries)} queries successfully")
    print()

    if success_count == len(queries):
        print("🎉 FULL PIPELINE TEST PASSED! 🎉")
        print()
        print("The neuro-symbolic reasoning system is working:")
        print("  1. ✓ Text → Logic conversion (LLM-based extraction)")
        print("  2. ✓ Logic encoding (CNF + WCNF)")
        print("  3. ✓ SAT-based reasoning (query answering)")
        print()
        return True
    else:
        print("⚠ PARTIAL SUCCESS")
        print(f"  {success_count}/{len(queries)} queries executed successfully")
        print()
        return False


if __name__ == "__main__":
    print()
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
