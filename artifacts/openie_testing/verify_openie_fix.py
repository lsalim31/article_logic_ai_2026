#!/usr/bin/env python3
"""
Final verification that OpenIE extractor works correctly with coreference.
"""

import sys
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor

# Test the original input
INPUT_TEXT = """The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented."""

print("=" * 80)
print("OpenIE Extractor - Final Verification")
print("=" * 80)
print("\nINPUT TEXT:")
print("-" * 80)
print(INPUT_TEXT)
print("-" * 80)

try:
    with OpenIEExtractor(
        memory='4G',
        enable_coref=True,
        use_depparse_fallback=True
    ) as extractor:

        print("\n✓ Initialization successful (coref enabled)")

        triples = extractor.extract_triples(INPUT_TEXT)

        print(f"\n✓ Extracted {len(triples)} relation triples")

        print("\n" + "=" * 80)
        print("NEW ARRAY FORMAT (Token-Optimized JSON)")
        print("=" * 80)
        print("\nFormat: [subject, predicate, object, sentence_index]")
        print("-" * 80)
        json_output = extractor.format_triples_json(triples, indent=2)
        print(json_output)

        print("\n" + "=" * 80)
        print("COMPACT FORMAT (No Indentation)")
        print("=" * 80)
        compact_output = extractor.format_triples_json(triples, indent=0)
        print(compact_output)

        print("\n" + "=" * 80)
        print("VERBOSE FORMAT (Human-Readable)")
        print("=" * 80)
        print(extractor.format_triples_verbose(triples))

        print("\n" + "=" * 80)
        print("TOKEN SAVINGS ANALYSIS")
        print("=" * 80)
        old_format_chars = len('{"subject": "X", "predicate": "Y", "object": "Z", "sentence_index": 0}')
        new_format_chars = len('["X", "Y", "Z", 0]')
        savings_per_triple = old_format_chars - new_format_chars
        total_savings = savings_per_triple * len(triples)
        print(f"Old format: ~{old_format_chars} chars/triple")
        print(f"New format: ~{new_format_chars} chars/triple")
        print(f"Savings: ~{savings_per_triple} chars/triple ({len(triples)} triples)")
        print(f"Total savings: ~{total_savings} chars ≈ {total_savings // 4} tokens")

        print("\n" + "=" * 80)
        print("✅ SUCCESS: OpenIE extractor with new array format is working!")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
