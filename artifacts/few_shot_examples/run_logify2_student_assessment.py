#!/usr/bin/env python3
"""
Runner script for logify2.py with student assessment input.
This script runs the full OpenIE + LLM pipeline.
"""

import sys
import os
import json

# Add the code directory to the path
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor
from logic_converter import LogicConverter


def main():
    """Run the full logify2 pipeline on student assessment text."""

    # Read the input text
    input_file = '/workspace/repo/artifacts/few_shot_examples/inputs/example_03_student_assessment.txt'
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print("=" * 80)
    print("LOGIFY2 PIPELINE - STUDENT ASSESSMENT RULES")
    print("=" * 80)
    print("\nINPUT TEXT:")
    print("-" * 80)
    print(text)
    print("-" * 80)

    # Stage 1: Extract OpenIE triples
    print("\n" + "=" * 80)
    print("STAGE 1: OpenIE Extraction")
    print("=" * 80)

    try:
        extractor = OpenIEExtractor()
        print("\nExtracting relation triples...")
        openie_triples = extractor.extract_triples(text)

        print(f"\nExtracted {len(openie_triples)} triples:")
        print("-" * 80)
        for i, triple in enumerate(openie_triples, 1):
            print(f"\n{i}. {triple['subject']} | {triple['predicate']} | {triple['object']}")
            source = triple.get('source', 'unknown')
            print(f"   Source: {source}")

        # Format triples for LLM
        formatted_triples = extractor.format_triples(openie_triples)

        # Save triples to file
        triples_output = '/workspace/repo/artifacts/few_shot_examples/outputs/example_03_student_assessment_triples.json'
        with open(triples_output, 'w', encoding='utf-8') as f:
            json.dump(openie_triples, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Triples saved to: {triples_output}")

        # Stage 2: Show the LLM input format
        print("\n" + "=" * 80)
        print("STAGE 2: LLM Input Format")
        print("=" * 80)

        combined_input = f"""ORIGINAL TEXT:
<<<
{text}
>>>

RELATION TRIPLES:
<<<
{formatted_triples}
>>>"""

        print("\nFormatted input for LLM:")
        print("-" * 80)
        print(combined_input)
        print("-" * 80)

        # Save the formatted input
        input_file_llm = '/workspace/repo/artifacts/few_shot_examples/outputs/example_03_student_assessment_llm_input.txt'
        with open(input_file_llm, 'w', encoding='utf-8') as f:
            f.write(combined_input)
        print(f"\n✓ LLM input saved to: {input_file_llm}")

        # Stage 3: Run LLM conversion if API key available
        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key and api_key != "":
            print("\n" + "=" * 80)
            print("STAGE 2: LLM Logic Conversion")
            print("=" * 80)

            converter = LogicConverter(api_key=api_key, model="gpt-5.2", reasoning_effort="high")
            print("\nConverting to logic using GPT-5.2 (high reasoning)...")

            logic_structure = converter.convert(text, formatted_triples)

            # Save output
            output_file = '/workspace/repo/artifacts/few_shot_examples/outputs/example_03_student_assessment_output.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(logic_structure, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Logic structure saved to: {output_file}")
            print(f"  - Primitive propositions: {len(logic_structure.get('primitive_props', []))}")
            print(f"  - Hard constraints: {len(logic_structure.get('hard_constraints', []))}")
            print(f"  - Soft constraints: {len(logic_structure.get('soft_constraints', []))}")

            print("\n" + "=" * 80)
            print("FULL PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("API KEY NOT FOUND")
            print("=" * 80)
            print("\nStage 1 (OpenIE extraction) completed successfully!")
            print("Stage 2 (LLM conversion) skipped - no OPENAI_API_KEY found.")
            print("\nTo run the full pipeline:")
            print("  export OPENAI_API_KEY=your_key_here")
            print("  python run_logify2_student_assessment.py")

        extractor.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
