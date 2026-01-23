#!/usr/bin/env python3
"""
openie_extractor.py - OpenIE Relation Triple Extractor

This module handles Stage 1 of the text-to-logic pipeline:
extracting relation triples from natural language text using Stanford CoreNLP OpenIE.

Uses CoreNLPClient directly for proper coreference resolution support.
"""

import os
from typing import List, Dict, Any, Optional

# Set CORENLP_HOME before importing CoreNLPClient
CORENLP_HOME = os.environ.get('CORENLP_HOME', '/workspace/.stanfordnlp_resources/stanford-corenlp-4.5.3')
os.environ['CORENLP_HOME'] = CORENLP_HOME

from stanfordnlp.server import CoreNLPClient


class OpenIEExtractor:
    """Extracts relation triples from text using Stanford CoreNLP OpenIE with coreference resolution."""

    def __init__(self, memory: str = '8G', timeout: int = 60000, enable_coref: bool = True):
        """
        Initialize the Stanford CoreNLP client with OpenIE and coreference resolution.

        Args:
            memory: JVM memory allocation (default: '8G')
            timeout: Server timeout in milliseconds (default: 60000)
            enable_coref: Whether to enable coreference resolution (default: True)
        """
        print("Initializing Stanford CoreNLP with OpenIE and coreference resolution...")

        self.coref_enabled = enable_coref
        self.memory = memory
        self.timeout = timeout
        self.client: Optional[CoreNLPClient] = None

        # Define annotators - include coref if enabled
        if enable_coref:
            self.annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'depparse', 'coref', 'openie']
            self.properties = {'openie.resolve_coref': 'true'}
        else:
            self.annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'depparse', 'openie']
            self.properties = {}

        try:
            self._start_client()
            print(f"Stanford CoreNLP initialization complete. Coref enabled: {self.coref_enabled}")
        except Exception as e:
            print(f"Error initializing Stanford CoreNLP: {e}")
            raise RuntimeError(f"Failed to initialize Stanford CoreNLP: {e}")

    def _start_client(self):
        """Start the CoreNLP client."""
        self.client = CoreNLPClient(
            annotators=self.annotators,
            timeout=self.timeout,
            memory=self.memory,
            properties=self.properties,
            be_quiet=True
        )
        # Enter the context to start the server
        self.client.__enter__()

    def extract_triples(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract OpenIE relation triples from the input text using Stanford CoreNLP.

        Performs coreference resolution to replace pronouns with their antecedents,
        then extracts relation triples using OpenIE.

        Args:
            text (str): Input text to extract relations from

        Returns:
            List[Dict[str, Any]]: List of relation triples with confidence scores
                Each triple contains: subject, predicate, object, confidence, sentence_index
        """
        print("Extracting relation triples using Stanford CoreNLP OpenIE...")

        if self.client is None:
            raise RuntimeError("CoreNLP client not initialized. Call _start_client() first.")

        try:
            # Annotate the text
            annotation = self.client.annotate(text)

            triples = []

            # Extract OpenIE triples from each sentence
            for sent_idx, sentence in enumerate(annotation.sentence):
                if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                    for triple in sentence.openieTriple:
                        subject = triple.subject.strip()
                        predicate = triple.relation.strip()
                        obj = triple.object.strip()
                        confidence = triple.confidence if hasattr(triple, 'confidence') else 1.0

                        # Filter out empty or very short components
                        if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                            triples.append({
                                'subject': subject,
                                'predicate': predicate,
                                'object': obj,
                                'confidence': float(confidence),
                                'sentence_index': sent_idx
                            })

            print(f"Extracted {len(triples)} relation triples from Stanford CoreNLP OpenIE")

            # Log some examples for debugging
            if triples:
                print("Sample triples:")
                for i, triple in enumerate(triples[:5]):
                    print(f"  {i+1}. ({triple['subject']}; {triple['predicate']}; {triple['object']}) [conf: {triple['confidence']:.3f}]")

            return triples

        except Exception as e:
            print(f"Warning: Stanford CoreNLP OpenIE extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_triples_with_coref_info(self, text: str) -> Dict[str, Any]:
        """
        Extract OpenIE triples along with coreference chain information.

        This method provides additional context about which pronouns were resolved
        to which entities, useful for debugging and analysis.

        Args:
            text (str): Input text to extract relations from

        Returns:
            Dict containing:
                - 'triples': List of relation triples
                - 'coref_chains': List of coreference chains with resolved mentions
                - 'sentences': List of original sentences
        """
        print("Extracting triples with coreference information...")

        if self.client is None:
            raise RuntimeError("CoreNLP client not initialized.")

        try:
            annotation = self.client.annotate(text)

            # Extract sentences and their tokens
            sentences = []
            sentences_tokens = []
            for sentence in annotation.sentence:
                tokens = [token.word for token in sentence.token]
                sentences_tokens.append(tokens)
                sentences.append(' '.join(tokens))

            # Extract coreference chains
            coref_chains = []
            if hasattr(annotation, 'corefChain') and annotation.corefChain:
                for chain in annotation.corefChain:
                    chain_mentions = []
                    representative = None
                    for mention in chain.mention:
                        sent_idx = mention.sentenceIndex
                        begin_idx = mention.beginIndex
                        end_idx = mention.endIndex
                        mention_text = ' '.join(sentences_tokens[sent_idx][begin_idx:end_idx])
                        mention_info = {
                            'text': mention_text,
                            'sentence_index': sent_idx,
                            'begin_index': begin_idx,
                            'end_index': end_idx,
                            'type': str(mention.mentionType)
                        }
                        chain_mentions.append(mention_info)
                        # The first PROPER or NOMINAL mention is typically the representative
                        if representative is None and mention.mentionType in [0, 1]:  # PROPER=0, NOMINAL=1
                            representative = mention_text

                    if representative is None and chain_mentions:
                        representative = chain_mentions[0]['text']

                    coref_chains.append({
                        'representative': representative,
                        'mentions': chain_mentions
                    })

            # Extract triples
            triples = self.extract_triples(text)

            return {
                'triples': triples,
                'coref_chains': coref_chains,
                'sentences': sentences
            }

        except Exception as e:
            print(f"Error extracting triples with coref info: {e}")
            import traceback
            traceback.print_exc()
            return {'triples': [], 'coref_chains': [], 'sentences': []}

    def format_triples(self, triples: List[Dict[str, Any]]) -> str:
        """
        Format OpenIE triples as tab-separated values for downstream processing.

        Args:
            triples (List[Dict[str, Any]]): List of relation triples

        Returns:
            str: Formatted string of triples (one per line, tab-separated)
        """
        if not triples:
            return "No OpenIE triples extracted."

        formatted_lines = []
        for triple in triples:
            line = f"{triple['subject']}\t{triple['predicate']}\t{triple['object']}\t{triple['confidence']:.4f}"
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def format_triples_verbose(self, triples: List[Dict[str, Any]]) -> str:
        """
        Format OpenIE triples in a human-readable verbose format.

        Args:
            triples (List[Dict[str, Any]]): List of relation triples

        Returns:
            str: Formatted string with numbered triples
        """
        if not triples:
            return "No OpenIE triples extracted."

        lines = []
        for i, triple in enumerate(triples, 1):
            lines.append(f"{i}. ({triple['subject']}) --[{triple['predicate']}]--> ({triple['object']})")
            if 'confidence' in triple:
                lines[-1] += f"  [conf: {triple['confidence']:.3f}]"

        return "\n".join(lines)

    def close(self):
        """Clean up Stanford CoreNLP resources."""
        if self.client is not None:
            try:
                self.client.__exit__(None, None, None)
                self.client = None
                print("Stanford CoreNLP client closed.")
            except Exception as e:
                print(f"Warning: Error closing CoreNLP client: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
