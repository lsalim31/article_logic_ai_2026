"""
Document chunking module for RAG baseline.

This module handles the segmentation of long documents into overlapping chunks
of fixed token size. Chunking is necessary to handle documents that exceed
LLM context limits and to enable fine-grained retrieval.

The chunking strategy uses overlapping windows to ensure that context spanning
chunk boundaries is not lost during retrieval.
"""


def chunk_document(text, chunk_size=512, overlap=50):
    """
    Split a document into overlapping chunks of fixed token size.

    Args:
        text: Input document as string
        chunk_size: Maximum number of tokens per chunk
        overlap: Number of overlapping tokens between consecutive chunks

    Returns:
        List of dictionaries, each containing:
            - 'text': chunk text content
            - 'start_pos': starting character position in original document
            - 'end_pos': ending character position in original document
            - 'chunk_id': sequential chunk identifier
    """
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    tokens = tokenize(text)
    chunks = []
    chunk_id = 0

    start_idx = 0
    while start_idx < len(tokens):
        end_idx = min(start_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = detokenize(chunk_tokens)

        if start_idx == 0:
            char_start = 0
        else:
            char_start = len(detokenize(tokens[:start_idx])) + 1
        char_end = char_start + len(chunk_text)

        chunks.append({
            'text': chunk_text,
            'start_pos': char_start,
            'end_pos': char_end,
            'chunk_id': chunk_id
        })

        chunk_id += 1
        start_idx += chunk_size - overlap

    return chunks


def tokenize(text):
    """
    Tokenize text for chunk size computation.

    Args:
        text: Input text string

    Returns:
        List of tokens
    """
    return text.split()


def detokenize(tokens):
    """
    Convert tokens back to text string.

    Args:
        tokens: List of token strings

    Returns:
        Reconstructed text string
    """
    return ' '.join(tokens)
