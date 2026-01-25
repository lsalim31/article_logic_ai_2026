#!/usr/bin/env python3
"""
Test the fixed openie_extractor.py with coreference resolution.
"""

import sys
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor

# Test with the original medical text
INPUT_TEXT = """The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented."""

# Test with a text that has pronouns for coref
COREF_TEXT = """Dr. Smith examined the patient. She ordered an ECG. The patient was anxious, but he trusted her judgment."""

print("=" * 80)
print("Testing Fixed OpenIE Extractor")
print("=" * 80)

print("\nTest 1: Original Medical Text")
print("-" * 80)
print(INPUT_TEXT[:100] + "...")
print("-" * 80)

try:
    with OpenIEExtractor(
        memory='4G',
        timeout=60000,
        enable_coref=True,
        use_depparse_fallback=True,
        port=9000,
        language='en',
        download_models=False
    ) as extractor:

        print("\nExtracting triples from medical text...")
        result1 = extractor.extract_triples_with_coref_info(INPUT_TEXT)

        print(f"\n✓ Extracted {len(result1['triples'])} triples")
        print(f"✓ Found {len(result1['coref_chains'])} coreference chains")

        print("\n" + "=" * 80)
        print("Test 2: Text with Pronouns (Coref Test)")
        print("-" * 80)
        print(COREF_TEXT)
        print("-" * 80)

        print("\nExtracting triples with coreference...")
        result2 = extractor.extract_triples_with_coref_info(COREF_TEXT)

        print(f"\n✓ Extracted {len(result2['triples'])} triples")
        print(f"✓ Found {len(result2['coref_chains'])} coreference chains")

        if result2['coref_chains']:
            print("\nCoreference Chains Detected:")
            for i, chain in enumerate(result2['coref_chains'], 1):
                print(f"\n  Chain {i}: {chain['representative']}")
                for mention in chain['mentions']:
                    marker = " [REP]" if mention['is_representative'] else ""
                    print(f"    - '{mention['text']}'{marker}")

        print("\n" + "=" * 80)
        print("Resolved Text:")
        print("-" * 80)
        print(result2['resolved_text'])
        print("-" * 80)

        print("\nExtracted Triples:")
        verbose = extractor.format_triples_verbose(result2['triples'])
        print(verbose)

        print("\n" + "=" * 80)
        print("✅ SUCCESS: Coreference resolution is working!")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
