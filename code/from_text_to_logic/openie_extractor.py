#!/usr/bin/env python3
"""
openie_extractor.py - OpenIE Relation Triple Extractor

This module handles Stage 1 of the text-to-logic pipeline:
extracting relation triples from natural language text using Stanford CoreNLP OpenIE.

Uses Stanza's CoreNLPClient (the official, actively maintained library) for proper
coreference resolution and OpenIE support.

Key features:
- Coreference resolution to replace pronouns with their antecedents
- Dependency-parse fallback for sentences where OpenIE fails to extract triples
- Configurable extraction modes
"""

import os
from typing import List, Dict, Any, Optional, Set, Tuple

# Set CORENLP_HOME before importing
CORENLP_HOME = os.environ.get('CORENLP_HOME', '/workspace/.stanfordnlp_resources/stanford-corenlp-4.5.3')
os.environ['CORENLP_HOME'] = CORENLP_HOME

from stanza.server import CoreNLPClient


class OpenIEExtractor:
    """
    Extracts relation triples from text using Stanford CoreNLP OpenIE with coreference resolution.

    Uses Stanza's CoreNLPClient (official Stanford NLP Python library) for reliable access
    to CoreNLP's OpenIE and coreference resolution capabilities.
    """

    def __init__(
        self,
        memory: str = '8G',
        timeout: int = 60000,
        enable_coref: bool = True,
        use_depparse_fallback: bool = True,
        port: int = 9000
    ):
        """
        Initialize the Stanford CoreNLP client with OpenIE and coreference resolution.

        Args:
            memory: JVM memory allocation (default: '8G')
            timeout: Server timeout in milliseconds (default: 60000)
            enable_coref: Whether to enable coreference resolution (default: True)
            use_depparse_fallback: Extract triples from dependency parse for sentences
                                   where OpenIE fails (default: True)
            port: Port for CoreNLP server (default: 9000)
        """
        print("Initializing Stanford CoreNLP with OpenIE via Stanza...")

        self.coref_enabled = enable_coref
        self.use_depparse_fallback = use_depparse_fallback
        self.memory = memory
        self.timeout = timeout
        self.port = port
        self.client: Optional[CoreNLPClient] = None

        # Define annotators - include coref if enabled
        # Required for OpenIE: tokenize, ssplit, pos, lemma, depparse, natlog, openie
        # Required for coref: ner, coref
        base_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'depparse', 'natlog', 'openie']

        if enable_coref:
            # Insert coref before openie
            self.annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'depparse', 'coref', 'natlog', 'openie']
            self.properties = {
                'openie.resolve_coref': 'true',
                'openie.triple.strict': 'false',  # Extract more triples
                'openie.triple.all_nominals': 'true',  # Include nominal relations
            }
        else:
            self.annotators = base_annotators
            self.properties = {
                'openie.triple.strict': 'false',
                'openie.triple.all_nominals': 'true',
            }

        try:
            self._start_client()
            print(f"Stanford CoreNLP initialization complete.")
            print(f"  - Coref enabled: {self.coref_enabled}")
            print(f"  - Depparse fallback: {self.use_depparse_fallback}")
            print(f"  - Port: {self.port}")
        except Exception as e:
            print(f"Error initializing Stanford CoreNLP: {e}")
            raise RuntimeError(f"Failed to initialize Stanford CoreNLP: {e}")

    def _start_client(self):
        """Start the CoreNLP client using Stanza."""
        self.client = CoreNLPClient(
            annotators=self.annotators,
            timeout=self.timeout,
            memory=self.memory,
            properties=self.properties,
            be_quiet=True,
            endpoint=f'http://localhost:{self.port}'
        )
        # Enter the context to start the server
        self.client.__enter__()

    def _extract_depparse_triples(
        self,
        sentence,
        sentence_idx: int,
        existing_subjects: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract triples from dependency parse for sentences where OpenIE fails.

        This is a fallback mechanism to capture relations that OpenIE misses,
        particularly for:
        - Intransitive verbs with adverbs (e.g., "studies hard")
        - Sentences where POS tagger misclassifies verbs as nouns
        - Certain sentence structures that OpenIE doesn't handle

        Args:
            sentence: CoreNLP sentence object
            sentence_idx: Index of the sentence
            existing_subjects: Set of subjects already extracted by OpenIE (to avoid duplicates)

        Returns:
            List of extracted triples
        """
        triples = []

        # Build token lookup by index
        tokens = {token.tokenEndIndex: token for token in sentence.token}

        # Build dependency graph
        # In CoreNLP, edges go from HEAD (source) to DEPENDENT (target)
        # e.g., "reads" --[nsubj]--> "Bob" means "reads" is head, "Bob" is dependent
        deps_from_head = {}  # head_idx -> list of (dependent_idx, dep_type)
        for edge in sentence.basicDependencies.edge:
            head_idx = edge.source
            dependent_idx = edge.target

            if head_idx not in deps_from_head:
                deps_from_head[head_idx] = []
            deps_from_head[head_idx].append({
                'dependent': dependent_idx,
                'dep': edge.dep
            })

        # Find the root
        root_idx = sentence.basicDependencies.root[0] if sentence.basicDependencies.root else None
        if root_idx is None:
            return triples

        root_token = tokens.get(root_idx)
        if root_token is None:
            return triples

        # Determine if root is a verb or verb-like
        root_pos = root_token.pos
        root_lemma = root_token.lemma if hasattr(root_token, 'lemma') else root_token.word

        is_verb = root_pos.startswith('VB')
        # Handle cases where POS tagger misclassifies verbs as nouns (e.g., "studies" as NNS)
        # If lemma differs from word, it might be a verb form
        is_potential_verb = root_pos in ['NNS', 'NN'] and root_lemma != root_token.word.lower()

        # Check dependencies from root to find subject, object, advmod
        has_subject = False
        has_advmod = False
        subject = None
        obj = None
        advmod = None
        compound_subject = None

        for dep_info in deps_from_head.get(root_idx, []):
            dep_type = dep_info['dep']
            dependent_token = tokens.get(dep_info['dependent'])
            if dependent_token is None:
                continue

            if dep_type in ['nsubj', 'nsubj:pass']:
                subject = dependent_token.word
                has_subject = True
            elif dep_type in ['obj', 'dobj', 'iobj']:
                obj = dependent_token.word
            elif dep_type == 'advmod':
                advmod = dependent_token.word
                has_advmod = True
            elif dep_type == 'compound':
                # "Alice" in "Alice studies" might be tagged as compound if "studies" is NNS
                compound_subject = dependent_token.word

        # If we have a compound and advmod but no subject, the compound might be the subject
        # This handles "Alice studies hard" where "studies"(NNS) --[compound]--> "Alice"
        if compound_subject and not subject and has_advmod:
            subject = compound_subject
            has_subject = True

        # Decide if we should extract a triple
        should_extract = False
        predicate = root_token.word

        if is_verb and has_subject:
            should_extract = True
        elif is_potential_verb and has_subject and has_advmod:
            # Likely a misclassified verb like "studies" tagged as NNS
            should_extract = True
        elif has_subject and has_advmod and root_pos in ['NNS', 'NN', 'VB', 'VBZ', 'VBP', 'VBD', 'VBG', 'VBN']:
            # Be more permissive - if we have subject + advmod, likely a verb
            should_extract = True

        if not should_extract:
            return triples

        # Skip if we already have this subject from OpenIE
        if subject and subject.lower() in {s.lower() for s in existing_subjects}:
            return triples

        # Create triple
        if subject:
            if obj:
                triples.append({
                    'subject': subject,
                    'predicate': predicate,
                    'object': obj,
                    'confidence': 0.8,
                    'sentence_index': sentence_idx,
                    'source': 'depparse_fallback'
                })
            elif advmod:
                # For intransitive verbs with adverbs like "studies hard"
                triples.append({
                    'subject': subject,
                    'predicate': predicate,
                    'object': advmod,
                    'confidence': 0.7,
                    'sentence_index': sentence_idx,
                    'source': 'depparse_fallback_advmod'
                })

        return triples

    def extract_triples(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract OpenIE relation triples from the input text using Stanford CoreNLP.

        Performs coreference resolution to replace pronouns with their antecedents,
        then extracts relation triples using OpenIE. Uses dependency parse fallback
        for sentences where OpenIE fails to extract triples.

        Args:
            text (str): Input text to extract relations from

        Returns:
            List[Dict[str, Any]]: List of relation triples with confidence scores
                Each triple contains: subject, predicate, object, confidence, sentence_index, source
        """
        print("Extracting relation triples using Stanford CoreNLP OpenIE...")

        if self.client is None:
            raise RuntimeError("CoreNLP client not initialized. Call _start_client() first.")

        try:
            # Annotate the text
            annotation = self.client.annotate(text)

            triples = []
            sentences_with_triples = set()

            # Extract OpenIE triples from each sentence
            for sent_idx, sentence in enumerate(annotation.sentence):
                sentence_triples = []
                existing_subjects = set()

                if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                    for triple in sentence.openieTriple:
                        subject = triple.subject.strip()
                        predicate = triple.relation.strip()
                        obj = triple.object.strip()
                        confidence = triple.confidence if hasattr(triple, 'confidence') else 1.0

                        # Filter out empty components
                        if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                            sentence_triples.append({
                                'subject': subject,
                                'predicate': predicate,
                                'object': obj,
                                'confidence': float(confidence),
                                'sentence_index': sent_idx,
                                'source': 'openie'
                            })
                            existing_subjects.add(subject)
                            sentences_with_triples.add(sent_idx)

                triples.extend(sentence_triples)

                # Use dependency parse fallback if no triples were extracted
                if self.use_depparse_fallback and not sentence_triples:
                    fallback_triples = self._extract_depparse_triples(
                        sentence, sent_idx, existing_subjects
                    )
                    triples.extend(fallback_triples)
                    if fallback_triples:
                        sentences_with_triples.add(sent_idx)

            print(f"Extracted {len(triples)} relation triples")
            print(f"  - From OpenIE: {sum(1 for t in triples if t.get('source') == 'openie')}")
            print(f"  - From fallback: {sum(1 for t in triples if 'fallback' in t.get('source', ''))}")

            # Log some examples for debugging
            if triples:
                print("Sample triples:")
                for i, triple in enumerate(triples[:5]):
                    src = f"[{triple.get('source', 'unknown')}]"
                    print(f"  {i+1}. ({triple['subject']}; {triple['predicate']}; {triple['object']}) {src}")

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

            # Extract triples (reuse the main method to include fallback)
            triples = []
            for sent_idx, sentence in enumerate(annotation.sentence):
                sentence_triples = []
                existing_subjects = set()

                if hasattr(sentence, 'openieTriple') and sentence.openieTriple:
                    for triple in sentence.openieTriple:
                        subject = triple.subject.strip()
                        predicate = triple.relation.strip()
                        obj = triple.object.strip()
                        confidence = triple.confidence if hasattr(triple, 'confidence') else 1.0

                        if len(subject) > 0 and len(predicate) > 0 and len(obj) > 0:
                            sentence_triples.append({
                                'subject': subject,
                                'predicate': predicate,
                                'object': obj,
                                'confidence': float(confidence),
                                'sentence_index': sent_idx,
                                'source': 'openie'
                            })
                            existing_subjects.add(subject)

                triples.extend(sentence_triples)

                # Use fallback if enabled and no triples extracted
                if self.use_depparse_fallback and not sentence_triples:
                    fallback_triples = self._extract_depparse_triples(
                        sentence, sent_idx, existing_subjects
                    )
                    triples.extend(fallback_triples)

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
            source = triple.get('source', 'unknown')
            line = f"{i}. ({triple['subject']}) --[{triple['predicate']}]--> ({triple['object']})"
            line += f"  [conf: {triple['confidence']:.2f}, src: {source}]"
            lines.append(line)

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
        try:
            self.close()
        except:
            pass
