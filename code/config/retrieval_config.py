#!/usr/bin/env python3
"""
retrieval_config.py 
Centralizes all tunable parameters.
Loads configuration from YAML profiles for experiment flexibility.
"""

import os
import yaml
from pathlib import Path

# Determine config directory and default profile
_config_dir = Path(__file__).resolve().parent
_profiles_dir = _config_dir / "profiles"

# Allow override via environment variable or default to 'default.yaml'
_profile_name = os.environ.get("CONFIG_PROFILE", "default_openAI.yaml")
_profile_path = _profiles_dir / _profile_name

# Global config storage
_active_config = None


def load_config(profile_path=None):
    """
    Load configuration from a YAML profile.
    
    Args:
        profile_path: Path to YAML file. If None, uses CONFIG_PROFILE env var or default.yaml
    
    Returns:
        dict: The loaded configuration
    """
    global _active_config
    
    if profile_path is None:
        profile_path = _profile_path
    else:
        profile_path = Path(profile_path)
    
    if not profile_path.exists():
        raise FileNotFoundError(f"Config profile not found: {profile_path}")
    
    with open(profile_path, 'r') as f:
        _active_config = yaml.safe_load(f)
    
    # Handle inheritance
    if "_inherit" in _active_config:
        parent_path = _profiles_dir / _active_config["_inherit"]
        with open(parent_path, 'r') as f:
            parent_config = yaml.safe_load(f)
        # Merge: parent values, overwritten by child values
        _active_config = _deep_merge(parent_config, _active_config)
        del _active_config["_inherit"]
    
    _update_module_variables()
    return _active_config


def _deep_merge(base, override):
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _update_module_variables():
    """Update module-level variables from active config for backward compatibility."""
    global _active_config
    global SBERT_MODEL, NLI_MODEL
    global MAX_COMPLETION_TOKENS, MAX_TOKENS
    global REASONING_MODEL, REASONING_EFFORT, TEMPERATURE_LOGIC_CONVERTER
    global TRANSLATE_MODEL, REASONING_EFFORT_TRANSLATE, TEMPERATURE_TRANSLATE
    global PROMPT_TRANSLATION, PROMPT_PASS_1, PROMPT_PASS_2, PROMPT_EXTRACTION
    global SBERT_TOP_K, SBERT_MIN_SIMILARITY, HARDNESS_CONSTANT, DIRECT_RETRIEVAL_MULTIPLIER
    global NLI_ENTAILMENT_THRESHOLD, NLI_CONTRADICTION_THRESHOLD, NLI_BATCH_SIZE
    global ENABLE_NLI_FILTERING, ENABLE_HYBRID_EMBEDDING
    global ENABLE_AUTO_NEGATION_CORRECTION, ENABLE_NEGATION_WARNINGS
    global CONFIDENCE_THRESHOLD_TRUE, MIN_PROPOSITION_WEIGHT
    global ON_EXPAND_QUERY_SYN, MAX_SYNONYMS
    global TRIGGER_QUERY, ADDITIONAL_LLM_QUERY
    global SUBSET_TOP_K_RETRIEVAL, SUBSET_NUM_CLUSTERS, SUBSET_TOP_PER_CLUSTER, SUBSET_ENTAILMENT_THRESHOLD
    global MAX_VARIANTS
    global USE_OPENIE, USE_ENRICHMENT, USE_SUBSET
    global DEFAULT_MIN_WORDS, DEFAULT_MAX_WORDS
    
    cfg = _active_config
    
    # Models
    SBERT_MODEL = cfg["models"]["sbert"]
    NLI_MODEL = cfg["models"]["nli"]
    REASONING_MODEL = cfg["models"]["reasoning"]
    TRANSLATE_MODEL = cfg["models"]["translate"]
    
    # Tokens
    MAX_COMPLETION_TOKENS = cfg["tokens"]["max_completion_tokens"]
    MAX_TOKENS = cfg["tokens"]["max_tokens"]
    
    # Reasoning
    REASONING_EFFORT = cfg["reasoning"]["effort"]
    REASONING_EFFORT_TRANSLATE = cfg["reasoning"]["effort_translate"]
    TEMPERATURE_LOGIC_CONVERTER = cfg["reasoning"]["temperature_logic_converter"]
    TEMPERATURE_TRANSLATE = cfg["reasoning"]["temperature_translate"]
    
    # Prompts
    PROMPT_TRANSLATION = cfg["prompts"]["translation"]
    PROMPT_PASS_1 = cfg["prompts"]["pass_1"]
    PROMPT_PASS_2 = cfg["prompts"]["pass_2"]
    PROMPT_EXTRACTION = cfg["prompts"]["extraction"]
    
    # Retrieval
    SBERT_TOP_K = cfg["retrieval"]["sbert_top_k"]
    SBERT_MIN_SIMILARITY = cfg["retrieval"]["sbert_min_similarity"]
    HARDNESS_CONSTANT = cfg["retrieval"]["hardness_constant"]
    DIRECT_RETRIEVAL_MULTIPLIER = cfg["retrieval"]["direct_retrieval_multiplier"]
    
    # NLI
    NLI_ENTAILMENT_THRESHOLD = cfg["nli"]["entailment_threshold"]
    NLI_CONTRADICTION_THRESHOLD = cfg["nli"]["contradiction_threshold"]
    NLI_BATCH_SIZE = cfg["nli"]["batch_size"]
    
    # Feature flags
    USE_OPENIE = cfg["features"]["use_openie"]
    USE_ENRICHMENT = cfg["features"]["use_enrichment"]
    USE_SUBSET = cfg["features"]["use_subset"]
    ENABLE_NLI_FILTERING = cfg["features"]["enable_nli_filtering"]
    ENABLE_HYBRID_EMBEDDING = cfg["features"]["enable_hybrid_embedding"]
    ENABLE_AUTO_NEGATION_CORRECTION = cfg["features"]["enable_auto_negation_correction"]
    ENABLE_NEGATION_WARNINGS = cfg["features"]["enable_negation_warnings"]
    ON_EXPAND_QUERY_SYN = cfg["features"]["expand_query_synonyms"]
    
    # Synonyms
    MAX_SYNONYMS = cfg["synonyms"]["max_synonyms"]
    
    # Voting
    TRIGGER_QUERY = cfg["voting"]["trigger_query"]
    ADDITIONAL_LLM_QUERY = cfg["voting"]["additional_llm_query"]
    
    # Subset
    SUBSET_TOP_K_RETRIEVAL = cfg["subset"]["top_k_retrieval"]
    SUBSET_NUM_CLUSTERS = cfg["subset"]["num_clusters"]
    SUBSET_TOP_PER_CLUSTER = cfg["subset"]["top_per_cluster"]
    SUBSET_ENTAILMENT_THRESHOLD = cfg["subset"]["entailment_threshold"]
    
    # Computed value
    MAX_VARIANTS = SUBSET_NUM_CLUSTERS * SUBSET_TOP_PER_CLUSTER
    
    # Confidence
    CONFIDENCE_THRESHOLD_TRUE = cfg["confidence"]["threshold_true"]
    MIN_PROPOSITION_WEIGHT = cfg["confidence"]["min_proposition_weight"]
    
    # Document limits
    DEFAULT_MIN_WORDS = cfg["document"]["default_min_words"]
    DEFAULT_MAX_WORDS = cfg["document"]["default_max_words"]


# Load default config on module import
load_config()
