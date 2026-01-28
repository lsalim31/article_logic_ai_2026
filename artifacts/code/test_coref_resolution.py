#!/usr/bin/env python3
"""
Test script to verify Stanford OpenIE coreference resolution is working.
Tests with text containing pronouns and coreferences.
"""

import sys
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor

def test_coref_resolution():
    """Test coreference resolution with sample text."""

    # Test text with clear coreference cases
    test_cases = [
        {
            "name": "Simple pronoun resolution",
            "text": "Alice is a student. She studies hard."
        },
        {
            "name": "Company reference",
            "text": "TechCorp was founded in 2020. It became profitable by 2023."
        },
        {
            "name": "Multiple pronouns",
            "text": "Bob met Sarah at the library. He was studying math. She was reading a novel."
        }
    ]

    print("=" * 80)
    print("TESTING STANFORD OPENIE COREFERENCE RESOLUTION")
    print("=" * 80)
    print()

    try:
        # Initialize extractor
        extractor = OpenIEExtractor()
        print(f"Coreference resolution enabled: {extractor.coref_enabled}")
        print()

        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"TEST CASE {i}: {test_case['name']}")
            print(f"{'=' * 80}")
            print(f"INPUT TEXT:")
            print(f"  {test_case['text']}")
            print()

            # Extract triples
            triples = extractor.extract_triples(test_case['text'])

            print(f"EXTRACTED TRIPLES ({len(triples)} total):")
            if triples:
                for j, triple in enumerate(triples, 1):
                    print(f"  {j}. ({triple['subject']}) -> [{triple['predicate']}] -> ({triple['object']})")
                    print(f"     Confidence: {triple['confidence']:.4f}")
            else:
                print("  No triples extracted.")

            # Analysis
            print(f"\nANALYSIS:")
            pronouns_found = []
            entities_found = []

            for triple in triples:
                # Check for pronouns in subjects
                pronoun_list = ['she', 'he', 'it', 'they', 'him', 'her', 'them']
                if triple['subject'].lower() in pronoun_list:
                    pronouns_found.append(triple['subject'])
                else:
                    entities_found.append(triple['subject'])

            if pronouns_found:
                print(f"  ⚠️  Found unresolved pronouns: {set(pronouns_found)}")
                print(f"  → Coreference resolution may not be working")
            else:
                print(f"  ✓ No pronouns found in subjects")
                if entities_found:
                    print(f"  ✓ Found entities: {set(entities_found)}")
                    print(f"  → Coreference resolution appears to be working!")

        print(f"\n{'=' * 80}")
        print("TEST COMPLETE")
        print(f"{'=' * 80}\n")

        # Cleanup
        extractor.close()

    except Exception as e:
        print(f"\n❌ ERROR during testing:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_coref_resolution()
    sys.exit(0 if success else 1)
