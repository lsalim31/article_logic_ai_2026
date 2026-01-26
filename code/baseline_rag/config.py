"""
Configuration module for Reasoning LLM + RAG baseline.

This module stores all hyperparameters and configuration settings for the
RAG baseline experiment. All parameters are fixed to ensure reproducibility
and fair comparison with the Logify system.

Key Parameters:
- SBERT model for retrieval
- Chunk size and overlap for document segmentation
- Number of retrieved chunks (k)
- LLM model name (configurable)
- Temperature for deterministic generation
- Fixed Chain-of-Thought prompt template
"""


# SBERT Configuration
SBERT_MODEL = "all-MiniLM-L6-v2"

# Retrieval Configuration
TOP_K = 5

# Chunking Configuration
CHUNK_SIZE = 512
OVERLAP = 50

# LLM Configuration
DEFAULT_MODEL = "openai/gpt-5-nano"
TEMPERATURE = 0

# Chain-of-Thought Prompt Template (Fixed)
COT_PROMPT_TEMPLATE = """Given the following context, answer the question using step-by-step reasoning.

Context:
{retrieved_chunks}

Question: {query}

Instructions:
1. Identify relevant facts from the context
2. Apply logical reasoning step-by-step
3. State your conclusion clearly

Answer (True/False/Unknown):
"""
