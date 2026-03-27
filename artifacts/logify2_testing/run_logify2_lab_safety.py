#!/usr/bin/env python3
"""
Runner script for logify2.py with lab safety input.
This script demonstrates the OpenIE extraction phase and shows what would be sent to the LLM.

To run the full pipeline with LLM conversion, you need an OpenAI API key:
    python logify2.py --api-key YOUR_API_KEY --file lab_safety_input.txt --output lab_safety_output.json

For this demo, we'll show the OpenIE extraction and formatted prompt.
"""

import sys
import os
import json

# Add the code directory to the path
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor


def main():
    """Run OpenIE extraction and show the formatted input for LLM."""

    # Read the input text
    input_file = '/workspace/repo/artifacts/lab_safety_input.txt'
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print("=" * 80)
    print("LOGIFY2 PIPELINE - LAB SAFETY RULES")
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
        triples_output = '/workspace/repo/artifacts/lab_safety_triples.json'
        with open(triples_output, 'w', encoding='utf-8') as f:
            json.dump(openie_triples, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Triples saved to: {triples_output}")

        # Stage 2: Show what would be sent to LLM
        print("\n" + "=" * 80)
        print("STAGE 2: LLM Input (Preview)")
        print("=" * 80)

        combined_input = f"""ORIGINAL TEXT:
<<<
{text}
>>>

OPENIE TRIPLES:
<<<
{formatted_triples}
>>>"""

        print("\nThis is what would be sent to the LLM for logic conversion:")
        print("-" * 80)
        print(combined_input)
        print("-" * 80)

        # Save the formatted input
        input_preview = '/workspace/repo/artifacts/lab_safety_llm_input.txt'
        with open(input_preview, 'w', encoding='utf-8') as f:
            f.write(combined_input)
        print(f"\n✓ LLM input preview saved to: {input_preview}")

        # Show next steps
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("\nTo complete the full pipeline with LLM conversion:")
        print("\n1. Obtain an OpenAI API key from https://platform.openai.com/api-keys")
        print("\n2. Run the full pipeline:")
        print("   cd /workspace/repo/code/from_text_to_logic")
        print("   python logify2.py \\")
        print("       --api-key YOUR_API_KEY \\")
        print("       --file /workspace/repo/artifacts/lab_safety_input.txt \\")
        print("       --output /workspace/repo/artifacts/lab_safety_output.json \\")
        print("       --model gpt-5.2 \\")
        print("       --reasoning-effort high")
        print("\n3. Or set the API key as an environment variable:")
        print("   export OPENAI_API_KEY=your_key_here")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\n✓ Input text processed: {len(text)} characters")
        print(f"✓ OpenIE triples extracted: {len(openie_triples)} triples")
        print(f"✓ Files created:")
        print(f"  - {triples_output}")
        print(f"  - {input_preview}")
        print("\nStage 1 (OpenIE extraction) completed successfully!")
        print("Stage 2 (LLM conversion) requires OpenAI API key.")

        extractor.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
