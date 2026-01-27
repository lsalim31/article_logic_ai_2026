#!/usr/bin/env python3
"""
weights.py - Soft Constraint Weight Assignment

Implements Appendix A.1.1: SBERT Retrieval + NLI Reranking for assigning
evidence-based weights to soft constraints.

Algorithm (Appendix A.1.1):
1. Segment document into overlapping chunks (reuses baseline_rag.chunker)
2. For each soft constraint:
   a. Retrieve top-K relevant chunks using SBERT (reuses baseline_rag.retriever)
   b. Score with NLI cross-encoder (entailment vs contradiction)
   c. Aggregate evidence with log-sum-exp pooling (Appendix formula)
   d. Transform to weight via sigmoid
3. Add 'weight' field to each soft_constraint

NOTE: For testing purposes, this also assigns weights to hard constraints.
      In production, only soft constraints need weights.

Input:
    - logified_structure: dict from logify.py (constraints without weights)
    - document_text: str (original document for evidence retrieval)

Output:
    - Same structure with 'weight' field added to each constraint

Usage (CLI):
    python weights.py <document_path> <logified_json_path>

    # Example:
    python weights.py ../experiments/SINTEC.pdf ../experiments/SINTEC-output.json
    # Output: ../experiments/SINTEC-output_weighted.json

Usage (Python):
    from from_text_to_logic.weights import assign_weights

    weighted_structure = assign_weights(logified_structure, document_text)
"""

import sys
import os
from pathlib import Path

# Add code directory to Python path (for imports to work from anywhere)
script_dir = Path(__file__).resolve().parent
code_dir = script_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import json
import argparse
import numpy as np
from typing import Dict, List, Any

# Reuse existing RAG infrastructure
from baseline_rag.chunker import chunk_document
from baseline_rag.retriever import (
    load_sbert_model,
    encode_chunks,
    encode_query,
    compute_cosine_similarity
)

# NLI cross-encoder (new dependency)
try:
    from sentence_transformers import CrossEncoder
except ImportError:
    raise ImportError(
        "sentence-transformers is required for weight assignment. "
        "Install with: pip install sentence-transformers"
    )


class WeightAssigner:
    """
    Assigns evidence-based weights to constraints using Appendix A.1.1.

    Reuses existing infrastructure:
    - baseline_rag.chunker: Document segmentation with overlap
    - baseline_rag.retriever: SBERT encoding and cosine similarity

    Adds new functionality:
    - Multi-hypothesis retrieval (extends single-query retrieval)
    - NLI cross-encoder scoring
    - Log-sum-exp evidence pooling (EXACT appendix formula)
    - Sigmoid weight transformation
    """

    def __init__(self,
                 sbert_model_name: str = "all-MiniLM-L6-v2",
                 nli_model_name: str = "cross-encoder/nli-deberta-v3-base",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 k_per_hypothesis: int = 20,
                 k_total: int = 50,
                 temperature: float = 2.0,
                 num_hypotheses: int = 1):
        """
        Initialize weight assigner with Appendix A.1.1 defaults.

        Args:
            sbert_model_name: SBERT model for retrieval (default: all-MiniLM-L6-v2)
            nli_model_name: NLI cross-encoder model (default: nli-deberta-v3-base)
            chunk_size: Tokens per chunk (default: 512, ~150 words)
            chunk_overlap: Overlapping tokens between chunks (default: 50)
            k_per_hypothesis: Top-K chunks per hypothesis (default: 20, per appendix)
            k_total: Max total chunks after union (default: 50, per appendix)
            temperature: Log-sum-exp temperature τ (default: 2, per appendix)
            num_hypotheses: Number of paraphrases r (default: 1, will use translation field)
        """
        # Load models
        print("Loading SBERT model for retrieval...")
        self.sbert_model = load_sbert_model(sbert_model_name)

        print("Loading NLI cross-encoder for evidence scoring...")
        self.nli_model = CrossEncoder(nli_model_name)

        # Chunking parameters
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Retrieval parameters (Appendix defaults)
        self.K = k_per_hypothesis
        self.K_total = k_total

        # Pooling parameters (Appendix defaults)
        self.tau = temperature

        # Hypothesis generation
        self.r = num_hypotheses

        print("✓ Weight assigner initialized")

    def assign_weights_to_structure(self,
                                   logified_structure: Dict[str, Any],
                                   document_text: str,
                                   verbose: bool = True) -> Dict[str, Any]:
        """
        Main entry point: Assign weights to all constraints.

        NOTE: For testing purposes, assigns weights to BOTH hard and soft constraints.
              In production, you may only need soft constraints.

        Args:
            logified_structure: Output from logify.py
            document_text: Original document text
            verbose: Print progress messages

        Returns:
            Same structure with 'weight' field added to all constraints
        """
        # Get constraints
        hard_constraints = logified_structure.get('hard_constraints', [])
        soft_constraints = logified_structure.get('soft_constraints', [])
        total_constraints = len(hard_constraints) + len(soft_constraints)

        if total_constraints == 0:
            if verbose:
                print("No constraints found. Returning structure unchanged.")
            return logified_structure

        if verbose:
            print(f"\nAssigning weights to {total_constraints} constraints...")
            print(f"  Hard constraints: {len(hard_constraints)}")
            print(f"  Soft constraints: {len(soft_constraints)}")

        # Step 1: Preprocess document (once for all constraints)
        if verbose:
            print("\n  Step 1: Segmenting document and computing embeddings...")

        chunks, chunk_embeddings = self._preprocess_document(document_text)

        if verbose:
            print(f"    ✓ Created {len(chunks)} overlapping chunks")

        # Step 2: Process hard constraints
        if len(hard_constraints) > 0 and verbose:
            print("\n  Step 2a: Processing hard constraints...")

        for i, constraint in enumerate(hard_constraints, 1):
            if verbose:
                print(f"    [{i}/{len(hard_constraints)}] {constraint['id']}: {constraint['translation'][:60]}...")

            weight = self._assign_weight_to_constraint(
                constraint, chunks, chunk_embeddings
            )

            constraint['weight'] = float(weight)

            if verbose:
                print(f"      → weight = {weight:.3f}")

        # Step 3: Process soft constraints
        if len(soft_constraints) > 0 and verbose:
            print("\n  Step 2b: Processing soft constraints...")

        for i, constraint in enumerate(soft_constraints, 1):
            if verbose:
                print(f"    [{i}/{len(soft_constraints)}] {constraint['id']}: {constraint['translation'][:60]}...")

            weight = self._assign_weight_to_constraint(
                constraint, chunks, chunk_embeddings
            )

            constraint['weight'] = float(weight)

            if verbose:
                print(f"      → weight = {weight:.3f}")

        if verbose:
            print("\n  ✓ Weight assignment complete!\n")
            if len(hard_constraints) > 0:
                print("  Hard Constraint Weights:")
                self._print_weight_summary(hard_constraints)
            if len(soft_constraints) > 0:
                print("\n  Soft Constraint Weights:")
                self._print_weight_summary(soft_constraints)

        return logified_structure

    def _assign_weight_to_constraint(self,
                                     constraint: Dict[str, Any],
                                     chunks: List[Dict],
                                     chunk_embeddings: np.ndarray) -> float:
        """
        Assign weight to a single constraint following Appendix A.1.1.

        Steps:
        1. Generate hypotheses
        2. Retrieve relevant chunks
        3. NLI scoring
        4. Log-sum-exp pooling (EXACT appendix formula)
        5. Sigmoid transform
        """
        # Generate hypotheses (Step 2.1)
        hypotheses = self._generate_hypotheses(constraint)

        # Retrieve relevant chunks (Step 2.2-2.3)
        retrieved_chunks = self._retrieve_for_constraint(
            hypotheses, chunks, chunk_embeddings
        )

        # NLI scoring (Step 2.4-2.5)
        evidence_scores = self._score_with_nli(retrieved_chunks, hypotheses)

        # Log-sum-exp pooling (Step 2.6) - EXACT APPENDIX FORMULA
        D = self._log_sum_exp_pooling(evidence_scores)

        # Sigmoid transform (Step 2.7)
        weight = self._sigmoid(D)

        return weight

    def _preprocess_document(self, text: str):
        """
        Appendix Step 1: Segment document and compute SBERT embeddings.

        REUSES:
        - baseline_rag.chunker.chunk_document()
        - baseline_rag.retriever.encode_chunks()
        """
        # Segment document using existing chunker
        chunks = chunk_document(
            text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap
        )

        # Encode chunks using existing SBERT encoder
        chunk_embeddings = encode_chunks(chunks, self.sbert_model)

        return chunks, chunk_embeddings

    def _generate_hypotheses(self, constraint: Dict[str, Any]) -> List[str]:
        """
        Appendix Step 2.1: Generate hypothesis set H(Q).

        For now: r=1 (use translation field only)
        Future: r=5 (add paraphrases)
        """
        # Use the translation field from the constraint
        hypothesis = constraint['translation']

        return [hypothesis]

    def _retrieve_for_constraint(self,
                                 hypotheses: List[str],
                                 chunks: List[Dict],
                                 chunk_embeddings: np.ndarray) -> List[Dict]:
        """
        Appendix Step 2.2-2.3: Retrieve top-K chunks per hypothesis,
        then union and cap to K_total.

        EXTENDS: baseline_rag.retriever to handle multiple hypotheses
        REUSES: encode_query(), compute_cosine_similarity()
        """
        # Encode all hypotheses
        hypothesis_embeddings = []
        for h in hypotheses:
            h_emb = encode_query(h, self.sbert_model)
            hypothesis_embeddings.append(h_emb)
        hypothesis_embeddings = np.array(hypothesis_embeddings)

        # Retrieve using multi-hypothesis logic
        retrieved_indices = self._retrieve_multi_hypothesis(
            hypothesis_embeddings,
            chunk_embeddings
        )

        # Return retrieved chunks
        return [chunks[i] for i in retrieved_indices]

    def _retrieve_multi_hypothesis(self,
                                   hypothesis_embeddings: np.ndarray,
                                   chunk_embeddings: np.ndarray) -> List[int]:
        """
        Appendix algorithm for multi-hypothesis retrieval:
        1. For each hypothesis h_j, retrieve top-K chunks by cosine similarity
        2. Form union E = ∪_j E_j
        3. Deduplicate and cap to K_total

        REUSES: compute_cosine_similarity() from baseline_rag.retriever
        """
        retrieved_indices = set()
        max_similarity = {}

        # For each hypothesis
        for h_emb in hypothesis_embeddings:
            # Compute similarities using existing function
            similarities = compute_cosine_similarity(h_emb, chunk_embeddings)

            # Get top-K indices for this hypothesis
            # NO threshold - take all K (as appendix specifies)
            top_k = np.argsort(similarities)[::-1][:self.K]

            for idx in top_k:
                retrieved_indices.add(idx)
                score = similarities[idx]
                # Track max similarity for this chunk across all hypotheses
                max_similarity[idx] = max(max_similarity.get(idx, -1), score)

        # Deduplicate and cap to K_total
        result = list(retrieved_indices)

        if len(result) > self.K_total:
            # Sort by max similarity and keep top K_total
            result.sort(key=lambda i: max_similarity[i], reverse=True)
            result = result[:self.K_total]

        return result

    def _score_with_nli(self,
                       chunks: List[Dict],
                       hypotheses: List[str]) -> np.ndarray:
        """
        Appendix Step 2.4-2.5: Score with NLI and compute evidence scores.

        For each (premise, hypothesis) pair:
        1. Get NLI logits: (z_ent, z_con, z_neu)
        2. Compute evidence difference: d(p, h_j) = z_ent - z_con
        3. For each premise, take max over hypotheses: d(p) = max_j d(p, h_j)

        Returns: Array of evidence scores d(p) for each premise
        """
        premises = [chunk['text'] for chunk in chunks]

        if len(premises) == 0:
            return np.array([])

        # Create all (premise, hypothesis) pairs
        pairs = []
        for p in premises:
            for h in hypotheses:
                pairs.append((p, h))

        # NLI inference (batch processing)
        nli_scores = self.nli_model.predict(pairs)  # Shape: [len(pairs), 3]
        # DeBERTa NLI label order: [contradiction, neutral, entailment]
        # nli_scores[:, 0] = contradiction
        # nli_scores[:, 1] = neutral
        # nli_scores[:, 2] = entailment

        # Reshape to [num_premises, num_hypotheses, 3]
        nli_scores = nli_scores.reshape(len(premises), len(hypotheses), 3)

        # Compute evidence difference: d(p, h_j) = z_ent - z_con
        z_con = nli_scores[:, :, 0]  # [premises, hypotheses] - contradiction
        z_ent = nli_scores[:, :, 2]  # [premises, hypotheses] - entailment
        d_matrix = z_ent - z_con     # [premises, hypotheses]

        # Take max over hypotheses: d(p) = max_j d(p, h_j)
        d_values = np.max(d_matrix, axis=1)  # [premises]

        # Numerical stability: clip extreme values
        # (Prevents overflow in log-sum-exp)
        d_values = np.clip(d_values, -10.0, 10.0)

        return d_values

    def _log_sum_exp_pooling(self, evidence_scores: np.ndarray) -> float:
        """
        Appendix Step 2.6: Log-sum-exp pooling.

        EXACT FORMULA from Appendix A.1.1:
        D(Q;T) = (1/τ) * log((1/K) * Σ_{i=1}^K exp(τ * d(p_i)))

        Where:
        - τ (tau): temperature parameter (default: 2)
        - K: number of retrieved premises (evidence scores)
        - d(p_i): evidence score for premise i

        This is a smooth approximation of max:
        - τ small → closer to average
        - τ large → closer to max
        - τ = 2 (default from appendix)

        Implementation uses numerical stability trick:
        Subtract max before exp, then add it back after log.
        This is mathematically equivalent but prevents overflow.
        """
        if len(evidence_scores) == 0:
            return 0.0

        tau = self.tau
        K = len(evidence_scores)

        # Numerical stability: subtract max before exp
        max_score = np.max(evidence_scores)

        # exp(τ * d_i) with stability: exp(τ * (d_i - max_d))
        exp_scores = np.exp(tau * (evidence_scores - max_score))

        # EXACT APPENDIX FORMULA (with stability trick):
        # D = (1/τ) * log((1/K) * Σ exp(τ * d_i))
        # = (1/τ) * log((1/K) * Σ exp(τ * (d_i - max_d)) * exp(τ * max_d))
        # = (1/τ) * log((1/K) * exp(τ * max_d) * Σ exp(τ * (d_i - max_d)))
        # = (1/τ) * [log((1/K) * Σ exp(τ * (d_i - max_d))) + τ * max_d]
        D = (1/tau) * (np.log((1/K) * np.sum(exp_scores)) + tau * max_score)

        return D

    def _sigmoid(self, x: float) -> float:
        """
        Appendix Step 2.7: Sigmoid transformation.

        EXACT FORMULA from Appendix A.1.1:
        w(Q) = σ(D(Q;T)) = 1 / (1 + exp(-D(Q;T)))

        Maps evidence score to probability-like weight in (0, 1):
        - D >> 0 (strong support) → w ≈ 1
        - D << 0 (strong contradiction) → w ≈ 0
        - D ≈ 0 (neutral) → w ≈ 0.5
        """
        return 1.0 / (1.0 + np.exp(-x))

    def _print_weight_summary(self, constraints: List[Dict]):
        """Print summary statistics of assigned weights."""
        weights = [c['weight'] for c in constraints]

        print(f"    Mean: {np.mean(weights):.3f} ± {np.std(weights):.3f}")
        print(f"    Range: [{np.min(weights):.3f}, {np.max(weights):.3f}]")
        print(f"    Median: {np.median(weights):.3f}")


# ============================================================================
# Convenience function for easy integration
# ============================================================================

def assign_weights(logified_structure: Dict[str, Any],
                  document_text: str,
                  verbose: bool = True,
                  **kwargs) -> Dict[str, Any]:
    """
    Convenience function: Assign weights to constraints.

    This is the main function to call from other modules.

    Args:
        logified_structure: Output from logify.py
        document_text: Original document text
        verbose: Print progress messages
        **kwargs: Additional parameters for WeightAssigner

    Returns:
        Same structure with 'weight' field added to all constraints

    Example:
        from from_text_to_logic.weights import assign_weights

        # After logification
        logified = converter.convert_text_to_logic(text)

        # Assign weights
        logified_with_weights = assign_weights(logified, text)

        # Now both hard_constraints[i]['weight'] and
        # soft_constraints[i]['weight'] exist!
    """
    assigner = WeightAssigner(**kwargs)
    return assigner.assign_weights_to_structure(
        logified_structure,
        document_text,
        verbose=verbose
    )


# ============================================================================
# Document text extraction (reused from logify.py)
# ============================================================================

def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from various document formats.

    Args:
        file_path: Path to document file (PDF, DOCX, TXT)

    Returns:
        Extracted text content
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    # Plain text file
    if suffix in ['.txt', '.text']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    # PDF file
    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF support. "
                "Install with: pip install PyMuPDF"
            )

        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)

    # DOCX file
    elif suffix in ['.docx', '.doc']:
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install with: pip install python-docx"
            )

        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs]
        return "\n".join(text_parts)

    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: .txt, .pdf, .docx"
        )


# ============================================================================
# Command-line interface
# ============================================================================

def main():
    """Command-line interface for weight assignment."""
    parser = argparse.ArgumentParser(
        description="Assign evidence-based weights to constraints (Appendix A.1.1)",
        epilog="Example: python weights.py document.pdf logified.json"
    )
    parser.add_argument(
        "document",
        help="Path to document file (PDF, DOCX, or TXT)"
    )
    parser.add_argument(
        "logified",
        help="Path to logified JSON file (from logify.py)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    # Validate paths
    doc_path = Path(args.document)
    json_path = Path(args.logified)

    if not doc_path.exists():
        print(f"Error: Document not found: {args.document}")
        return 1

    if not json_path.exists():
        print(f"Error: JSON file not found: {args.logified}")
        return 1

    # Extract text from document
    print(f"Reading document: {args.document}")
    text = extract_text_from_document(args.document)
    print(f"  ✓ Extracted {len(text)} characters")

    # Load logified structure
    print(f"Loading logified structure from {args.logified}...")
    with open(args.logified, 'r') as f:
        logified = json.load(f)

    # Assign weights
    logified_with_weights = assign_weights(
        logified,
        text,
        verbose=not args.quiet
    )

    # Generate output path: same folder as JSON, with _weighted.json suffix
    output_path = json_path.parent / (json_path.stem + "_weighted.json")

    with open(output_path, 'w') as f:
        json.dump(logified_with_weights, f, indent=2)

    print(f"\n✓ Weights assigned! Output saved to: {output_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
