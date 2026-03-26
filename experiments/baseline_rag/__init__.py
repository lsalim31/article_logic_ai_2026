"""
baseline_rag - RAG (Retrieval-Augmented Generation) baseline implementation.

This package provides chunking and retrieval utilities for document processing.

Modules:
    chunker: Document chunking with overlapping windows
    retriever: SBERT-based semantic retrieval
    config: Configuration settings
    evaluator: Evaluation metrics
    reasoner: LLM reasoning module

Usage:
    from baseline_rag.chunker import chunk_document
    from baseline_rag.retriever import load_sbert_model, encode_chunks
"""

# Lazy imports to avoid ImportError when dependencies aren't installed
# Use explicit imports in your code: from baseline_rag.chunker import chunk_document

__all__ = [
    'chunker',
    'retriever',
    'config',
    'evaluator',
    'reasoner',
]
