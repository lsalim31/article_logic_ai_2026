#!/usr/bin/env python3
"""
Test the new array format for OpenIE triples
"""

import sys
sys.path.insert(0, '/__modal/volumes/vo-ganFuMvAI7iQpFsGPQS0zl/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor

INPUT_TEXT = """The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented."""

def main():
    print("=" * 80)
    print("TESTING NEW ARRAY FORMAT FOR OPENIE TRIPLES")
    print("=" * 80)

    print("\nINPUT TEXT:")
    print("-" * 80)
    print(INPUT_TEXT)
    print("-" * 80)

    print("\nInitializing OpenIE Extractor...")
    print("(This may take a moment to start the CoreNLP server)")

    try:
        # Initialize with coref and depparse enabled
        with OpenIEExtractor(
            enable_coref=True,
            use_depparse_fallback=True,
            download_models=False,
            memory='4G'
        ) as extractor:

            print("\n" + "=" * 80)
            print("EXTRACTING TRIPLES...")
            print("=" * 80)

            # Extract triples
            triples = extractor.extract_triples(INPUT_TEXT)

            print("\n" + "=" * 80)
            print("OLD FORMAT (dict with field names):")
            print("=" * 80)
            print("\nSample triple (internal representation):")
            if triples:
                print(triples[0])

            print("\n" + "=" * 80)
            print("NEW FORMAT (array without field names):")
            print("=" * 80)

            # Format as JSON with new array format
            json_output = extractor.format_triples_json(triples, indent=2)
            print(json_output)

            print("\n" + "=" * 80)
            print("COMPACT FORMAT (no indentation):")
            print("=" * 80)

            # Compact format (saves even more tokens)
            compact_output = extractor.format_triples_json(triples, indent=0)
            print(compact_output)

            print("\n" + "=" * 80)
            print("TOKEN SAVINGS ANALYSIS:")
            print("=" * 80)

            # Compare token counts (rough estimate)
            old_style_example = '{"subject": "X", "predicate": "Y", "object": "Z", "sentence_index": 0}'
            new_style_example = '["X", "Y", "Z", 0]'

            print(f"\nOld format length per triple: ~{len(old_style_example)} chars")
            print(f"New format length per triple: ~{len(new_style_example)} chars")
            print(f"Savings per triple: ~{len(old_style_example) - len(new_style_example)} chars")
            print(f"\nTotal triples extracted: {len(triples)}")
            print(f"Estimated savings: ~{(len(old_style_example) - len(new_style_example)) * len(triples)} chars")
            print(f"                  ≈{((len(old_style_example) - len(new_style_example)) * len(triples)) // 4} tokens")

            print("\n" + "=" * 80)
            print("VERBOSE OUTPUT (for human readability):")
            print("=" * 80)
            print(extractor.format_triples_verbose(triples))

            print("\n" + "=" * 80)
            print("✓ TEST COMPLETE")
            print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
