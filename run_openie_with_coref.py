#!/usr/bin/env python3
"""
Script to run OpenIE extractor with working coreference resolution.

This version modifies the initialization to allow downloading of HuggingFace models
needed by the coref processor.
"""

import sys
import os

# Add the code directory to the path
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

import stanza
from stanza.server import CoreNLPClient
from typing import List, Dict, Any, Optional, Set

# Input text
INPUT_TEXT = """The hospital's emergency triage protocol requires immediate attention for patients presenting with chest pain,
unless the pain is clearly musculoskeletal in origin and the patient is under 40 years old.
Dr. Martinez, who has been working double shifts this week, believes that patients over 65 should always receive an ECG regardless of symptoms, althought Dr. Yang only sometimes believes this.
The official guidelines only mandate this when cardiac history is documented."""

class OpenIEExtractorWithCoref:
    """
    Modified version of OpenIEExtractor that properly initializes coreference resolution.
    """

    def __init__(
        self,
        memory: str = '4G',
        timeout: int = 60000,
        port: int = 9000,
        language: str = 'en'
    ):
        print("Initializing OpenIE Extractor with working coreference...")

        self.memory = memory
        self.timeout = timeout
        self.port = port
        self.language = language

        # Initialize native Stanza coreference resolution pipeline
        print("Initializing native Stanza coreference pipeline...")
        try:
            # Remove download_method=None to allow HuggingFace model downloads
            self.coref_pipeline = stanza.Pipeline(
                language,
                processors='tokenize,coref',
                verbose=False
            )
            print("  ✓ Native Stanza coref initialized")
            self.coref_enabled = True
        except Exception as e:
            print(f"  ✗ Warning: Stanza coref initialization failed: {e}")
            self.coref_enabled = False
            self.coref_pipeline = None

        # Initialize Stanza dependency parse pipeline for fallback
        print("Initializing Stanza dependency parse pipeline...")
        try:
            self.depparse_pipeline = stanza.Pipeline(
                language,
                processors='tokenize,pos,lemma,depparse',
                download_method=None,
                verbose=False
            )
            print("  ✓ Stanza depparse initialized")
            self.use_depparse_fallback = True
        except Exception as e:
            print(f"  ✗ Warning: Stanza depparse initialization failed: {e}")
            self.use_depparse_fallback = False
            self.depparse_pipeline = None

        # Initialize CoreNLP client for OpenIE
        print("Initializing CoreNLP client for OpenIE...")
        self.openie_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'depparse', 'natlog', 'openie']
        self.openie_properties = {
            'openie.triple.strict': 'true',
            'openie.triple.all_nominals': 'true',
            'openie.max_entailments_per_clause': '3',
            'openie.affinity_probability_cap': '0.33',
        }

        try:
            self.client = CoreNLPClient(
                annotators=self.openie_annotators,
                timeout=self.timeout,
                memory=self.memory,
                properties=self.openie_properties,
                be_quiet=True,
                endpoint=f'http://localhost:{self.port}'
            )
            self.client.__enter__()
            print("  ✓ CoreNLP OpenIE client initialized")
            print(f"\nInitialization complete:")
            print(f"  - Native Stanza coref: {self.coref_enabled}")
            print(f"  - Stanza depparse fallback: {self.use_depparse_fallback}")
            print(f"  - CoreNLP port: {self.port}")
        except Exception as e:
            print(f"Error initializing CoreNLP OpenIE client: {e}")
            raise RuntimeError(f"Failed to initialize CoreNLP: {e}")

    def _resolve_coreferences(self, text: str) -> tuple:
        """Resolve coreferences in text using native Stanza coref model."""
        if not self.coref_enabled or self.coref_pipeline is None:
            return text, []

        doc = self.coref_pipeline(text)

        coref_chains = []
        if hasattr(doc, 'coref_chains') and doc.coref_chains:
            for chain in doc.coref_chains:
                mentions = []
                representative_text = None

                for mention in chain:
                    mention_text = mention.text
                    mention_info = {
                        'text': mention_text,
                        'sentence_index': mention.sent_index,
                        'start_char': mention.start_char,
                        'end_char': mention.end_char,
                        'is_representative': mention.is_representative
                    }
                    mentions.append(mention_info)

                    if mention.is_representative:
                        representative_text = mention_text

                if representative_text is None and mentions:
                    representative_text = mentions[0]['text']

                coref_chains.append({
                    'representative': representative_text,
                    'mentions': mentions
                })

        # Build resolved text
        resolved_text = text
        if coref_chains:
            replacements = []
            for chain in coref_chains:
                representative = chain['representative']
                for mention in chain['mentions']:
                    if not mention['is_representative']:
                        replacements.append({
                            'start': mention['start_char'],
                            'end': mention['end_char'],
                            'original': mention['text'],
                            'replacement': representative
                        })

            replacements.sort(key=lambda x: x['start'], reverse=True)

            for repl in replacements:
                resolved_text = (
                    resolved_text[:repl['start']] +
                    repl['replacement'] +
                    resolved_text[repl['end']:]
                )

        return resolved_text, coref_chains

    def extract_triples_with_coref_info(self, text: str) -> Dict[str, Any]:
        """Extract OpenIE triples with coreference information."""
        print("\nExtracting relation triples with coreference resolution...")

        # Step 1: Resolve coreferences
        resolved_text, coref_chains = self._resolve_coreferences(text)

        if self.coref_enabled and coref_chains:
            print(f"  ✓ Resolved {len(coref_chains)} coreference chains")
            print("\n  Coreference chains:")
            for i, chain in enumerate(coref_chains, 1):
                print(f"    {i}. Representative: '{chain['representative']}'")
                for mention in chain['mentions']:
                    if not mention['is_representative']:
                        print(f"       - '{mention['text']}' -> '{chain['representative']}'")
        else:
            print("  No coreferences found")

        print(f"\n  Original text:\n    {text}")
        print(f"\n  Resolved text:\n    {resolved_text}")

        # Step 2: Extract triples from resolved text
        annotation = self.client.annotate(resolved_text)

        triples = []
        for sent_idx, sentence in enumerate(annotation.sentence):
            if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                for triple in sentence.openieTriple:
                    subject = triple.subject.strip()
                    predicate = triple.relation.strip()
                    obj = triple.object.strip()

                    if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                        triples.append({
                            'subject': subject,
                            'predicate': predicate,
                            'object': obj,
                            'sentence_index': sent_idx,
                            'source': 'openie'
                        })

        print(f"\n  ✓ Extracted {len(triples)} relation triples")

        return {
            'triples': triples,
            'coref_chains': coref_chains,
            'resolved_text': resolved_text,
            'original_text': text
        }

    def format_triples_verbose(self, triples: List[Dict[str, Any]]) -> str:
        """Format OpenIE triples in verbose format."""
        if not triples:
            return "No OpenIE triples extracted."

        lines = []
        for i, triple in enumerate(triples, 1):
            source = triple.get('source', 'unknown')
            line = f"{i}. ({triple['subject']}) --[{triple['predicate']}]--> ({triple['object']})"
            line += f"  [src: {source}]"
            lines.append(line)

        return "\n".join(lines)

    def close(self):
        """Clean up resources."""
        if self.client is not None:
            try:
                self.client.__exit__(None, None, None)
                self.client = None
                print("\nCoreNLP client closed.")
            except Exception as e:
                print(f"Warning: Error closing CoreNLP client: {e}")

def main():
    print("=" * 80)
    print("OpenIE Extractor with Coreference Resolution")
    print("=" * 80)
    print("\nINPUT TEXT:")
    print("-" * 80)
    print(INPUT_TEXT)
    print("-" * 80)

    try:
        extractor = OpenIEExtractorWithCoref(
            memory='4G',
            timeout=60000,
            port=9000,
            language='en'
        )

        print("\n" + "=" * 80)
        print("EXTRACTION WITH COREFERENCE ANALYSIS")
        print("=" * 80)

        result = extractor.extract_triples_with_coref_info(INPUT_TEXT)

        print("\n" + "=" * 80)
        print("RESULTS - VERBOSE FORMAT")
        print("=" * 80)
        verbose_output = extractor.format_triples_verbose(result['triples'])
        print(verbose_output)

        print("\n" + "=" * 80)
        print("COREFERENCE SUMMARY")
        print("=" * 80)
        if result['coref_chains']:
            for i, chain in enumerate(result['coref_chains'], 1):
                print(f"\nChain {i}:")
                print(f"  Representative: {chain['representative']}")
                print(f"  Mentions ({len(chain['mentions'])}):")
                for mention in chain['mentions']:
                    rep_marker = " [REP]" if mention['is_representative'] else ""
                    print(f"    - '{mention['text']}' (sent {mention['sentence_index']}){rep_marker}")
        else:
            print("No coreference chains detected.")

        print("\n" + "=" * 80)
        print(f"SUMMARY: Extracted {len(result['triples'])} relation triples")
        print(f"         Resolved {len(result['coref_chains'])} coreference chains")
        print("=" * 80)

        extractor.close()

    except Exception as e:
        print(f"\n[ERROR] Failed to run OpenIE extractor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
