#!/usr/bin/env python3
"""
retrieval_config.py - Configuration for retrieval and NLI filtering

Centralizes all tunable parameters for the query translation pipeline.
"""

# SBERT bi-encoder settings (Stage 1: Candidate retrieval)
SBERT_MODEL = "all-MiniLM-L6-v2"
SBERT_TOP_K = 50  # Increased from 20 for broader recall
SBERT_MIN_SIMILARITY = 0.3  # Minimum cosine similarity threshold

# NLI cross-encoder settings (Stage 2: Semantic filtering)
NLI_MODEL = "cross-encoder/nli-deberta-v3-large"
NLI_ENTAILMENT_THRESHOLD = 0.5  # Min P(entailment) to keep proposition
NLI_CONTRADICTION_THRESHOLD = 0.5  # Min P(contradiction) to keep proposition
NLI_BATCH_SIZE = 32  # Batch size for efficient inference

# Feature flags
ENABLE_NLI_FILTERING = True  # Set False to disable NLI filtering
ENABLE_HYBRID_EMBEDDING = True  # Embed translation + evidence together

# Negation handling (Fix 1 from negation_fix_proposal.md)
ENABLE_AUTO_NEGATION_CORRECTION = True  # Auto-correct polarity mismatches
ENABLE_NEGATION_WARNINGS = True  # Log warnings for polarity issues

# Confidence thresholds (for future use in experiments)
CONFIDENCE_THRESHOLD_TRUE = 0.55  # TRUE → UNCERTAIN if confidence below this
MIN_PROPOSIT3ION_WEIGHT = 0.4  # Low weight → low confidence adjustment


MAX_COMPLETION_TOKENS = 32000
MAX_TOKENS = 32000
TEMPERATURE_LOGIC_CONVERTER = 0.1
TEMPERATURE_TRANSLATE = 0.3

REASONING_EFFORT = "medium"
REASONING_EFFORT_TRANSLATE = "medium"

REASONING_MODEL = "gpt-5.2"
TRANSLATE_MODEL = "openai/gpt-5-nano"

HARDNESS_CONSTANT = 0.9

PROMPT_EXTRACTION = "prompt_current"
PROMPT_TRANSLATION = "prompt_translate_feb21_90percentage"


TRIGGER_QUERY = 0.8      # NLI confidence threshold to trigger voting
ADDITIONAL_LLM_QUERY = 4  # Number of extra LLM calls when triggered
