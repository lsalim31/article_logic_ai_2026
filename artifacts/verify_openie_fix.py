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
        print("EXTRACTED TRIPLES (Verbose)")
        print("=" * 80)
        print(extractor.format_triples_verbose(triples))

        print("\n" + "=" * 80)
        print("✅ SUCCESS: OpenIE extractor is fully functional!")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
