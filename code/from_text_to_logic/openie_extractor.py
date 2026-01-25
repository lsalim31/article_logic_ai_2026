#!/usr/bin/env python3
"""
openie_extractor.py - OpenIE Relation Triple Extractor

This module handles Stage 1 of the text-to-logic pipeline:
extracting relation triples from natural language text using Stanford CoreNLP OpenIE.

Uses native Stanza library (latest version) for coreference resolution and
Stanza's CoreNLPClient for OpenIE extraction.

Key features:
- Native Python coreference resolution using Stanza 1.7.0+ coref models
- Stanza Universal Dependencies for enhanced syntactic analysis
- Dependency-parse fallback using Stanza's native pipeline
- No confidence scoring (removed for cleaner output)
"""

import os
from typing import List, Dict, Any, Optional, Set

import stanza
from stanza.server import CoreNLPClient


class OpenIEExtractor:
    """
    Extracts relation triples from text using native Stanza and CoreNLP OpenIE.

    Architecture:
    1. Native Stanza coref resolution (Python-based, fast)
    2. Text resolution using coref chains
    3. CoreNLP OpenIE extraction on resolved text
    4. Stanza dependency parse fallback with Universal Dependencies
    """

    def __init__(
        self,
        memory: str = '8G',
        timeout: int = 60000,
        enable_coref: bool = True,
        use_depparse_fallback: bool = True,
        port: int = 9000,
        language: str = 'en',
        download_models: bool = False
    ):
        """
        Initialize Stanza pipelines and CoreNLP client for OpenIE extraction.

        Args:
            memory: JVM memory allocation for CoreNLP (default: '8G')
            timeout: Server timeout in milliseconds (default: 60000)
            enable_coref: Whether to enable native Stanza coreference resolution (default: True)
            use_depparse_fallback: Use Stanza dependency parse fallback for missing triples (default: True)
            port: Port for CoreNLP server (default: 9000)
            language: Language code for Stanza models (default: 'en')
            download_models: Whether to download Stanza models if not present (default: False)
        """
        print("Initializing OpenIE Extractor with native Stanza...")

        self.coref_enabled = enable_coref
        self.use_depparse_fallback = use_depparse_fallback
        self.memory = memory
        self.timeout = timeout
        self.port = port
        self.language = language

        # Initialize native Stanza pipelines
        self.coref_pipeline: Optional[stanza.Pipeline] = None
        self.depparse_pipeline: Optional[stanza.Pipeline] = None
        self.client: Optional[CoreNLPClient] = None

        # Download models if requested
        if download_models:
            print(f"Downloading Stanza models for '{language}'...")
            if enable_coref:
                stanza.download(language, processors='tokenize,coref')
            if use_depparse_fallback:
                stanza.download(language, processors='tokenize,pos,lemma,depparse')

        # Initialize native Stanza coreference resolution pipeline
        if enable_coref:
            print("Initializing native Stanza coreference pipeline...")
            try:
                # Allow downloading HuggingFace models needed by coref
                # Use default download_method to enable transformer model downloads
                self.coref_pipeline = stanza.Pipeline(
                    language,
                    processors='tokenize,coref',
                    verbose=False
                )
                print("  ✓ Native Stanza coref initialized")
            except Exception as e:
                print(f"  ✗ Warning: Stanza coref initialization failed: {e}")
                print(f"    Run with download_models=True or manually: stanza.download('{language}', processors='tokenize,coref')")
                self.coref_enabled = False

        # Initialize Stanza dependency parse pipeline for fallback
        if use_depparse_fallback:
            print("Initializing Stanza dependency parse pipeline...")
            try:
                self.depparse_pipeline = stanza.Pipeline(
                    language,
                    processors='tokenize,pos,lemma,depparse',
                    download_method=None,
                    verbose=False
                )
                print("  ✓ Stanza depparse initialized")
            except Exception as e:
                print(f"  ✗ Warning: Stanza depparse initialization failed: {e}")
                self.use_depparse_fallback = False

        # Initialize CoreNLP client for OpenIE (no coref needed, using native Stanza)
        print("Initializing CoreNLP client for OpenIE...")
        self.openie_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'depparse', 'natlog', 'openie']
        self.openie_properties = {
            'openie.triple.strict': 'true',
            'openie.triple.all_nominals': 'true',
            'openie.max_entailments_per_clause': '3',
            'openie.affinity_probability_cap': '0.33',
        }

        try:
            self._start_client()
            print("  ✓ CoreNLP OpenIE client initialized")
            print(f"\nInitialization complete:")
            print(f"  - Native Stanza coref: {self.coref_enabled}")
            print(f"  - Stanza depparse fallback: {self.use_depparse_fallback}")
            print(f"  - CoreNLP port: {self.port}")
        except Exception as e:
            print(f"Error initializing CoreNLP OpenIE client: {e}")
            raise RuntimeError(f"Failed to initialize CoreNLP: {e}")

    def _start_client(self):
        """Start the CoreNLP client for OpenIE."""
        self.client = CoreNLPClient(
            annotators=self.openie_annotators,
            timeout=self.timeout,
            memory=self.memory,
            properties=self.openie_properties,
            be_quiet=True,
            endpoint=f'http://localhost:{self.port}'
        )
        # Enter the context to start the server
        self.client.__enter__()

    def _resolve_coreferences(self, text: str) -> tuple[str, List[Dict[str, Any]]]:
        """
        Resolve coreferences in text using native Stanza coref model.

        Args:
            text: Input text with pronouns

        Returns:
            Tuple of (resolved_text, coref_chains)
            - resolved_text: Text with pronouns replaced by their antecedents
            - coref_chains: List of coreference chain information
        """
        if not self.coref_enabled or self.coref_pipeline is None:
            return text, []

        # Run Stanza coref
        doc = self.coref_pipeline(text)

        # Extract coref chains
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

        # Build resolved text by replacing pronouns with representatives
        resolved_text = text
        if coref_chains:
            # Process replacements from end to start to maintain character positions
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

            # Sort by position (reverse order to maintain positions)
            replacements.sort(key=lambda x: x['start'], reverse=True)

            # Apply replacements
            for repl in replacements:
                resolved_text = (
                    resolved_text[:repl['start']] +
                    repl['replacement'] +
                    resolved_text[repl['end']:]
                )

        return resolved_text, coref_chains

    def _extract_stanza_depparse_triples(
        self,
        sentence_text: str,
        sentence_idx: int,
        existing_subjects: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract triples from Stanza dependency parse for sentences where OpenIE fails.

        Uses Stanza's Universal Dependencies representation for better syntactic analysis.
        Handles:
        - Intransitive verbs with adverbs (e.g., "studies hard")
        - Verb/noun ambiguity using Stanza's UPOS tags
        - Complex dependency patterns with enhanced UD

        Args:
            sentence_text: Text of the sentence
            sentence_idx: Index of the sentence
            existing_subjects: Set of subjects already extracted by OpenIE

        Returns:
            List of extracted triples
        """
        if not self.use_depparse_fallback or self.depparse_pipeline is None:
            return []

        triples = []

        try:
            # Parse with Stanza
            doc = self.depparse_pipeline(sentence_text)

            for sent in doc.sentences:
                # Build word lookup by id (1-based in Stanza)
                words_by_id = {word.id: word for word in sent.words}

                # Build dependency graph: head_id -> [(dependent_id, deprel)]
                deps_from_head = {}
                for word in sent.words:
                    head_id = word.head
                    if head_id not in deps_from_head:
                        deps_from_head[head_id] = []
                    deps_from_head[head_id].append({
                        'dependent_id': word.id,
                        'deprel': word.deprel
                    })

                # Find root (head == 0 in UD)
                root_word = None
                for word in sent.words:
                    if word.head == 0:
                        root_word = word
                        break

                if root_word is None:
                    continue

                # Check if root is a verb using Universal POS (UPOS)
                is_verb = root_word.upos == 'VERB'

                # Handle verb/noun ambiguity: check if lemma differs from text
                # and if UPOS could be misclassified
                is_potential_verb = (
                    root_word.upos in ['NOUN', 'PROPN'] and
                    root_word.lemma.lower() != root_word.text.lower()
                )

                # Extract arguments from dependencies
                subject = None
                obj = None
                advmod = None

                for dep_info in deps_from_head.get(root_word.id, []):
                    deprel = dep_info['deprel']
                    dependent_word = words_by_id.get(dep_info['dependent_id'])

                    if dependent_word is None:
                        continue

                    # Universal Dependencies relations
                    if deprel in ['nsubj', 'nsubj:pass', 'csubj']:
                        subject = dependent_word.text
                    elif deprel in ['obj', 'iobj', 'dobj']:
                        obj = dependent_word.text
                    elif deprel == 'advmod':
                        advmod = dependent_word.text

                # Decide whether to extract
                should_extract = False
                predicate = root_word.lemma  # Use lemma for normalized form

                if is_verb and subject:
                    should_extract = True
                elif is_potential_verb and subject and advmod:
                    # Potential misclassification
                    should_extract = True
                elif subject and advmod and root_word.upos in ['NOUN', 'VERB', 'PROPN']:
                    # Permissive: subject + advmod pattern
                    should_extract = True

                if not should_extract:
                    continue

                # Skip duplicates
                if subject and subject.lower() in {s.lower() for s in existing_subjects}:
                    continue

                # Create triples (no confidence scores)
                if subject:
                    if obj:
                        triples.append({
                            'subject': subject,
                            'predicate': predicate,
                            'object': obj,
                            'sentence_index': sentence_idx,
                            'source': 'stanza_depparse',
                            'pos': root_word.upos
                        })
                    elif advmod:
                        triples.append({
                            'subject': subject,
                            'predicate': predicate,
                            'object': advmod,
                            'sentence_index': sentence_idx,
                            'source': 'stanza_depparse_advmod',
                            'pos': root_word.upos
                        })

        except Exception as e:
            print(f"Warning: Stanza depparse fallback failed for sentence {sentence_idx}: {e}")

        return triples

    def extract_triples(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract OpenIE relation triples from input text.

        Pipeline:
        1. Native Stanza coreference resolution (replace pronouns with antecedents)
        2. CoreNLP OpenIE extraction on resolved text
        3. Stanza dependency parse fallback for missed relations

        Args:
            text: Input text to extract relations from

        Returns:
            List of relation triples (no confidence scores)
            Each triple contains: subject, predicate, object, sentence_index, source
        """
        print("Extracting relation triples with native Stanza...")

        if self.client is None:
            raise RuntimeError("CoreNLP client not initialized.")

        try:
            # Step 1: Resolve coreferences with native Stanza
            resolved_text, coref_chains = self._resolve_coreferences(text)

            if self.coref_enabled and coref_chains:
                print(f"  ✓ Resolved {len(coref_chains)} coreference chains")

            # Step 2: Extract OpenIE triples from resolved text
            annotation = self.client.annotate(resolved_text)

            triples = []
            sentence_texts = []

            # Extract sentence texts for fallback
            for sentence in annotation.sentence:
                tokens = [token.word for token in sentence.token]
                sentence_texts.append(' '.join(tokens))

            # Extract OpenIE triples from each sentence
            for sent_idx, sentence in enumerate(annotation.sentence):
                sentence_triples = []
                existing_subjects = set()

                if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                    for triple in sentence.openieTriple:
                        subject = triple.subject.strip()
                        predicate = triple.relation.strip()
                        obj = triple.object.strip()

                        # Filter out empty components
                        if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                            sentence_triples.append({
                                'subject': subject,
                                'predicate': predicate,
                                'object': obj,
                                'sentence_index': sent_idx,
                                'source': 'openie'
                            })
                            existing_subjects.add(subject)

                triples.extend(sentence_triples)

                # Step 3: Use Stanza dependency parse fallback if no triples extracted
                if self.use_depparse_fallback and not sentence_triples:
                    fallback_triples = self._extract_stanza_depparse_triples(
                        sentence_texts[sent_idx], sent_idx, existing_subjects
                    )
                    triples.extend(fallback_triples)

            print(f"  ✓ Extracted {len(triples)} relation triples")
            print(f"    - OpenIE: {sum(1 for t in triples if t.get('source') == 'openie')}")
            print(f"    - Stanza fallback: {sum(1 for t in triples if 'stanza' in t.get('source', ''))}")

            # Log sample triples
            if triples:
                print("\n  Sample triples:")
                for i, triple in enumerate(triples[:5]):
                    src = f"[{triple.get('source', 'unknown')}]"
                    print(f"    {i+1}. ({triple['subject']} ; {triple['predicate']} ; {triple['object']}) {src}")

            return triples

        except Exception as e:
            print(f"Error: Triple extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_triples_with_coref_info(self, text: str) -> Dict[str, Any]:
        """
        Extract OpenIE triples along with native Stanza coreference chain information.

        Provides detailed information about coreference resolution for debugging
        and analysis.

        Args:
            text: Input text to extract relations from

        Returns:
            Dict containing:
                - 'triples': List of relation triples (no confidence scores)
                - 'coref_chains': List of coreference chains from native Stanza
                - 'resolved_text': Text with pronouns replaced
                - 'original_text': Original input text
        """
        print("Extracting triples with native Stanza coref information...")

        if self.client is None:
            raise RuntimeError("CoreNLP client not initialized.")

        try:
            # Step 1: Resolve coreferences with native Stanza
            resolved_text, coref_chains = self._resolve_coreferences(text)

            # Step 2: Extract triples using standard method
            triples = self.extract_triples(text)

            return {
                'triples': triples,
                'coref_chains': coref_chains,
                'resolved_text': resolved_text,
                'original_text': text
            }

        except Exception as e:
            print(f"Error extracting triples with coref info: {e}")
            import traceback
            traceback.print_exc()
            return {
                'triples': [],
                'coref_chains': [],
                'resolved_text': text,
                'original_text': text
            }

    def format_triples(self, triples: List[Dict[str, Any]]) -> str:
        """
        Format OpenIE triples as tab-separated values for downstream processing.

        Args:
            triples: List of relation triples

        Returns:
            Formatted string of triples (one per line, tab-separated)
            Format: subject\tpredicate\tobject
        """
        if not triples:
            return "No OpenIE triples extracted."

        formatted_lines = []
        for triple in triples:
            line = f"{triple['subject']}\t{triple['predicate']}\t{triple['object']}"
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def format_triples_verbose(self, triples: List[Dict[str, Any]]) -> str:
        """
        Format OpenIE triples in a human-readable verbose format.

        Args:
            triples: List of relation triples

        Returns:
            Formatted string with numbered triples and source information
        """
        if not triples:
            return "No OpenIE triples extracted."

        lines = []
        for i, triple in enumerate(triples, 1):
            source = triple.get('source', 'unknown')
            line = f"{i}. ({triple['subject']}) --[{triple['predicate']}]--> ({triple['object']})"
            line += f"  [src: {source}]"

            # Add POS tag if from Stanza depparse
            if 'pos' in triple:
                line += f" [pos: {triple['pos']}]"

            lines.append(line)

        return "\n".join(lines)

    def format_triples_json(self, triples: List[Dict[str, Any]], indent: int = 2) -> str:
        """
        Format OpenIE triples as JSON without source metadata.

        Args:
            triples: List of relation triples
            indent: JSON indentation (0 for compact, 2 for readable)

        Returns:
            JSON string of triples with subject, predicate, object, and sentence_index only
        """
        import json

        if not triples:
            return "[]"

        # Remove 'source' and 'pos' fields, keep only core triple data
        clean_triples = []
        for triple in triples:
            clean_triple = {
                'subject': triple['subject'],
                'predicate': triple['predicate'],
                'object': triple['object'],
                'sentence_index': triple['sentence_index']
            }
            clean_triples.append(clean_triple)

        return json.dumps(clean_triples, indent=indent, ensure_ascii=False)

    def close(self):
        """Clean up Stanza pipelines and CoreNLP resources."""
        # Close CoreNLP client
        if self.client is not None:
            try:
                self.client.__exit__(None, None, None)
                self.client = None
                print("CoreNLP client closed.")
            except Exception as e:
                print(f"Warning: Error closing CoreNLP client: {e}")

        # Clear Stanza pipelines (they don't need explicit cleanup, but clear references)
        self.coref_pipeline = None
        self.depparse_pipeline = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.close()
        except:
            pass
