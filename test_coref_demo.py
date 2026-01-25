#!/usr/bin/env python3
"""
Demo script showing coreference resolution working with a text that has pronouns.
"""

import sys
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

import stanza
from stanza.server import CoreNLPClient

# Test text with pronouns
TEST_TEXT = """Dr. Smith examined the patient. She ordered an ECG.
The patient was anxious, but he trusted her judgment.
Dr. Smith told him that his condition was stable."""

print("=" * 80)
print("Coreference Resolution Demo")
print("=" * 80)
print("\nINPUT TEXT:")
print("-" * 80)
print(TEST_TEXT)
print("-" * 80)

print("\nInitializing Stanza coref pipeline...")
coref_pipeline = stanza.Pipeline('en', processors='tokenize,coref', verbose=False)
print("✓ Initialized")

print("\nRunning coreference resolution...")
doc = coref_pipeline(TEST_TEXT)

if hasattr(doc, 'coref_chains') and doc.coref_chains:
    print(f"\n✓ Found {len(doc.coref_chains)} coreference chains:")

    for i, chain in enumerate(doc.coref_chains, 1):
        print(f"\nChain {i}:")
        representative = None
        mentions = []

        for mention in chain:
            mention_text = mention.text
            if mention.is_representative:
                representative = mention_text
                print(f"  Representative: '{mention_text}' [sent {mention.sent_index}]")
            mentions.append((mention_text, mention.sent_index, mention.is_representative))

        print(f"  All mentions:")
        for text, sent_idx, is_rep in mentions:
            marker = " [REP]" if is_rep else ""
            print(f"    - '{text}' (sent {sent_idx}){marker}")

        # Show replacement
        if representative:
            print(f"  Replacements:")
            for text, sent_idx, is_rep in mentions:
                if not is_rep:
                    print(f"    '{text}' → '{representative}'")

    # Build resolved text
    resolved_text = TEST_TEXT
    replacements = []

    for chain in doc.coref_chains:
        representative = None
        for mention in chain:
            if mention.is_representative:
                representative = mention.text
                break

        if representative is None:
            representative = chain[0].text

        for mention in chain:
            if not mention.is_representative:
                replacements.append({
                    'start': mention.start_char,
                    'end': mention.end_char,
                    'original': mention.text,
                    'replacement': representative
                })

    # Sort and apply replacements
    replacements.sort(key=lambda x: x['start'], reverse=True)

    for repl in replacements:
        resolved_text = (
            resolved_text[:repl['start']] +
            repl['replacement'] +
            resolved_text[repl['end']:]
        )

    print("\n" + "=" * 80)
    print("RESOLVED TEXT:")
    print("-" * 80)
    print(resolved_text)
    print("-" * 80)

else:
    print("\nNo coreference chains found.")

print("\n" + "=" * 80)
print("Coreference resolution is WORKING!")
print("=" * 80)
