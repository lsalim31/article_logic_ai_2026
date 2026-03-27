#!/usr/bin/env python3
"""
Native Stanza OpenIE Extractor Demo
Demonstrates the modernized OpenIE extractor with native Stanza coref
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

from openie_extractor import OpenIEExtractor


def main():
    """Run demonstration of native Stanza OpenIE extraction."""

    # Example text with pronouns and complex relations
    alice_text = """Alice is a student who loves mathematics. If Alice studies hard, she will pass the exam. Alice usually studies hard, but sometimes she gets distracted by social media. When Alice is focused, she always completes her homework. Alice's professor recommends that students attend office hours if they want to excel. Alice prefers studying in the library because it is quiet there."""

    print("=" * 80)
    print("NATIVE STANZA OPENIE EXTRACTOR DEMO")
    print("=" * 80)
    print("\nINPUT TEXT:")
    print(alice_text)
    print("\n" + "=" * 80)
    print()

    try:
        # Initialize extractor with native Stanza coref
        # Note: Set download_models=True on first run to download models
        print("Initializing OpenIE Extractor...")
        extractor = OpenIEExtractor(
            enable_coref=True,
            use_depparse_fallback=True,
            download_models=False,  # Set to True on first run
            language='en'
        )
        print()

        # Extract triples with detailed coref info
        print("=" * 80)
        print("EXTRACTION WITH COREFERENCE RESOLUTION")
        print("=" * 80)
        print()

        result = extractor.extract_triples_with_coref_info(alice_text)

        # Display coreference chains
        print("\n" + "=" * 80)
        print("COREFERENCE CHAINS (Native Stanza)")
        print("=" * 80)

        if result['coref_chains']:
            for i, chain in enumerate(result['coref_chains'], 1):
                print(f"\nChain {i}: '{chain['representative']}'")
                print("  Mentions:")
                for mention in chain['mentions']:
                    rep_marker = " ⭐" if mention['is_representative'] else ""
                    print(f"    - '{mention['text']}' (sent {mention['sentence_index']}){rep_marker}")
        else:
            print("No coreference chains detected.")

        # Display resolved text
        print("\n" + "=" * 80)
        print("RESOLVED TEXT")
        print("=" * 80)
        print(result['resolved_text'])

        # Display extracted triples
        print("\n" + "=" * 80)
        print("EXTRACTED TRIPLES")
        print("=" * 80)
        print(f"Total: {len(result['triples'])} triples\n")

        # Group by source
        openie_triples = [t for t in result['triples'] if t['source'] == 'openie']
        stanza_triples = [t for t in result['triples'] if 'stanza' in t['source']]

        print(f"From OpenIE: {len(openie_triples)}")
        print(f"From Stanza fallback: {len(stanza_triples)}\n")

        # Display triples grouped by subject
        subject_groups = {}
        for triple in result['triples']:
            subj = triple['subject']
            if subj not in subject_groups:
                subject_groups[subj] = []
            subject_groups[subj].append(triple)

        for subject in sorted(subject_groups.keys()):
            print(f"\nSubject: {subject}")
            for triple in subject_groups[subject]:
                src = triple['source']
                pos = f" [{triple['pos']}]" if 'pos' in triple else ""
                print(f"  → {triple['predicate']} → {triple['object']}  [{src}]{pos}")

        # Display verbose format
        print("\n" + "=" * 80)
        print("VERBOSE FORMAT")
        print("=" * 80)
        print(extractor.format_triples_verbose(result['triples']))

        # Display tab-separated format
        print("\n" + "=" * 80)
        print("TAB-SEPARATED FORMAT (for downstream processing)")
        print("=" * 80)
        print(extractor.format_triples(result['triples']))

        # Save results
        output_path = '/workspace/repo/artifacts/code/stanza_openie_demo_output.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print(f"✓ Demo complete! Results saved to: {output_path}")
        print("=" * 80)

        # Clean up
        extractor.close()

    except Exception as e:
        print(f"\n✗ Error in demo: {e}")
        import traceback
        traceback.print_exc()

        print("\n" + "=" * 80)
        print("TROUBLESHOOTING")
        print("=" * 80)
        print("\nIf you see 'FileNotFoundError' for Stanza models:")
        print("  1. Run with download_models=True:")
        print("     extractor = OpenIEExtractor(download_models=True)")
        print("\n  2. Or manually download:")
        print("     import stanza")
        print("     stanza.download('en', processors='tokenize,coref')")
        print("     stanza.download('en', processors='tokenize,pos,lemma,depparse')")
        print("\nIf you see CoreNLP errors:")
        print("  - Ensure Java is installed: java -version")
        print("  - CoreNLP will auto-download on first use")
        print("=" * 80)


if __name__ == "__main__":
    main()
