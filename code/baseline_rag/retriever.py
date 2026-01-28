"""
SBERT-based retrieval module for RAG baseline.

This module implements semantic retrieval using Sentence-BERT embeddings.
Documents are pre-encoded into dense vectors, and queries are encoded at
runtime. Retrieval is performed via cosine similarity in the embedding space.

The retrieval is deterministic given fixed embeddings and query, ensuring
reproducibility across runs.
"""

from sentence_transformers import SentenceTransformer
import numpy as np


def load_sbert_model(model_name):
    """
    Load pre-trained SBERT model.

    Args:
        model_name: Name of the SBERT model (e.g., "all-MiniLM-L6-v2")

    Returns:
        Loaded SBERT model object
    """
    return SentenceTransformer(model_name)


def encode_chunks(chunks, model):
    """
    Encode document chunks into dense embeddings using SBERT.

    Args:
        chunks: List of chunk dictionaries from chunker.py
        model: Loaded SBERT model

    Returns:
        Numpy array of shape (num_chunks, embedding_dim) containing embeddings
    """
    texts = [chunk['text'] for chunk in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings


def encode_query(query, model):
    """
    Encode a single query into a dense embedding using SBERT.

    Args:
        query: Query string
        model: Loaded SBERT model

    Returns:
        Numpy array of shape (embedding_dim,) containing query embedding
    """
    embedding = model.encode(query, convert_to_numpy=True)
    return embedding


def retrieve(query_embedding, chunk_embeddings, chunks, k=5):
    """
    Retrieve top-k most similar chunks to the query.

    Args:
        query_embedding: Query embedding vector
        chunk_embeddings: Matrix of chunk embeddings (num_chunks x embedding_dim)
        chunks: Original list of chunk dictionaries
        k: Number of chunks to retrieve

    Returns:
        List of k chunk dictionaries, ordered by decreasing similarity
    """
    similarities = compute_cosine_similarity(query_embedding, chunk_embeddings)

    top_k_indices = np.argsort(similarities)[::-1][:k]

    retrieved_chunks = [chunks[i] for i in top_k_indices]

    return retrieved_chunks


def compute_cosine_similarity(query_embedding, chunk_embeddings):
    """
    Compute cosine similarity between query and all chunks.

    Args:
        query_embedding: Query vector (embedding_dim,)
        chunk_embeddings: Chunk matrix (num_chunks, embedding_dim)

    Returns:
        Numpy array of shape (num_chunks,) containing similarity scores
    """
    query_norm = np.linalg.norm(query_embedding)
    chunk_norms = np.linalg.norm(chunk_embeddings, axis=1)

    dot_products = np.dot(chunk_embeddings, query_embedding)
    similarities = dot_products / (chunk_norms * query_norm + 1e-9)

    return similarities
