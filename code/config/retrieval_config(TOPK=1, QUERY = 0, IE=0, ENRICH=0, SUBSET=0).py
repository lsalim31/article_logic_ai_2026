#!/usr/bin/env python3
"""
retrieval_config.py 
Centralizes all tunable parameters.
"""
############################################
#
# ALL MODELS AND THEIR PARAMETERS
#
############################################
SBERT_MODEL = "all-MiniLM-L6-v2"
NLI_MODEL = "cross-encoder/nli-deberta-v3-large"

MAX_COMPLETION_TOKENS = 42000
MAX_TOKENS = 42000

REASONING_MODEL = "gpt-5.2"
REASONING_EFFORT = "medium"
TEMPERATURE_LOGIC_CONVERTER = 0.1


TRANSLATE_MODEL = "openai/gpt-5-nano"
REASONING_EFFORT_TRANSLATE = "medium"
TEMPERATURE_TRANSLATE = 0.3

#"openai/gpt-4.1-nano" #"openai/gpt-5-nano"
#anthropic/claude-1

############################################
#
# USED IN TRANSLATE
#
############################################

PROMPT_TRANSLATION = "prompt_translate"

# For the multi-sentence unit
PROMPT_PASS_1 = "prompt_pass_1"
PROMPT_PASS_2 = "prompt_pass_2"

SBERT_TOP_K = 150  # Increased from 20 for broader recall
SBERT_MIN_SIMILARITY = 0.85  # Minimum cosine similarity threshold

# NLI cross-encoder settings (Stage 2: Semantic filtering)
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

#Enrich query
ON_EXPAND_QUERY_SYN = False
MAX_SYNONYMS = 3

#Adaptative voting
TRIGGER_QUERY = 0.8      # NLI confidence threshold to trigger voting
ADDITIONAL_LLM_QUERY = 4  # Number of extra LLM calls when triggered

SUBSET_TOP_K_RETRIEVAL = 20
SUBSET_NUM_CLUSTERS = 3
SUBSET_TOP_PER_CLUSTER = 2
SUBSET_ENTAILMENT_THRESHOLD = 0.5

MAX_VARIANTS = SUBSET_NUM_CLUSTERS*SUBSET_TOP_PER_CLUSTER

############################################
#
# USED IN LOGIGY
#
############################################
USE_OPENIE = False

HARDNESS_CONSTANT = 0.9
PROMPT_EXTRACTION = "prompt_current_micro_notOpenIE"

USE_ENRICHMENT = False
USE_SUBSET = False
DIRECT_RETRIEVAL_MULTIPLIER = 2
DEFAULT_MIN_WORDS = 100
DEFAULT_MAX_WORDS = 400

