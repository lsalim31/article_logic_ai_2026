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
CHUNK_SIZE = 400
OVERLAP = 80

# LLM Configuration
DEFAULT_MODEL = "openai/gpt-5-nano"
TEMPERATURE = 0

# Chain-of-Thought Prompt Template (Fixed)
COT_PROMPT_TEMPLATE = """You are a precise reasoning assistant. Given a set of context passages and a query, determine whether the query is supported by the context through careful logical analysis.

Context:
{retrieved_chunks}

Query: {query}

Instructions:
1. Extract all relevant facts from the context that relate to the query
2. Identify any logical relationships, implications, or constraints between facts
3. Reason step-by-step from the extracted facts to evaluate the query
4. If facts are missing or insufficient, acknowledge the gap explicitly
5. Provide your final answer based solely on what the context supports

Format your response as:
**Reasoning:** [Your step-by-step analysis]
**Answer:** [True/False/Unknown OR Entailed/Contradicted/NotMentioned]

Begin your analysis:
"""
