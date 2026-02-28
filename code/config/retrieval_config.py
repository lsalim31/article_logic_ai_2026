#!/usr/bin/env python3
"""
retrieval_config.py 
Centralizes all tunable parameters.
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

MAX_COMPLETION_TOKENS = 42000
MAX_TOKENS = 42000
TEMPERATURE_LOGIC_CONVERTER = 0.1
TEMPERATURE_TRANSLATE = 0.3

REASONING_EFFORT = "medium"
REASONING_EFFORT_TRANSLATE = "medium"

REASONING_MODEL = "gpt-5.2"
TRANSLATE_MODEL = "openai/gpt-oss-20b"
#"openai/gpt-4.1-nano" #"openai/gpt-5-nano"

HARDNESS_CONSTANT = 0.9
USE_OPENIE = False
PROMPT_EXTRACTION = "prompt_current_micro_notOpenIE"
PROMPT_TRANSLATION = "prompt_translate"
PROMPT_PASS_1 = "prompt_pass_1"
PROMPT_PASS_2 = "prompt_pass_2"

TRIGGER_QUERY = 0.8      # NLI confidence threshold to trigger voting
ADDITIONAL_LLM_QUERY = 4  # Number of extra LLM calls when triggered

USE_ENRICHMENT = False
