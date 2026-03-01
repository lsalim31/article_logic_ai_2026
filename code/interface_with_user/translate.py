# translate.py - New Implementation (Corrected with Debugging)

import numpy as np
import logging
from itertools import combinations
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Tuple, Optional
from openai import OpenAI

from typing import List, Tuple, Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config.py (additions)

top_k_retrieval = 50
num_clusters = 5
top_per_cluster = 2
entailment_threshold = 0.8
sbert_model_name = "all-MiniLM-L6-v2"
nli_model_name = "cross-encoder/nli-deberta-v3-base"
llm_model_name = "anthropic/claude-3-haiku"  # or your preferred model
openrouter_api_key = "your-api-key"  # or load from env



class TranslateQuery:
    def __init__(self, config, kb_propositions: List[str], kb_embeddings: np.ndarray = None):
        self.config = config
        self.kb_propositions = kb_propositions
        
        logger.info(f"Initializing TranslateQuery with {len(kb_propositions)} KB propositions")
        
        # Load SBERT model
        logger.info(f"Loading SBERT model: {config.sbert_model_name}")
        self.sbert_model = SentenceTransformer(config.sbert_model_name)
        
        # Pre-compute KB embeddings if not provided, and normalize
        if kb_embeddings is None:
            logger.info("Computing KB embeddings...")
            kb_embeddings = self.sbert_model.encode(kb_propositions, normalize_embeddings=True)
        else:
            logger.info("Normalizing provided KB embeddings...")
            norms = np.linalg.norm(kb_embeddings, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-10)  # Avoid division by zero
            kb_embeddings = kb_embeddings / norms
        self.kb_embeddings = kb_embeddings
        
        # Load NLI model (CrossEncoder for NLI)
        logger.info(f"Loading NLI model: {config.nli_model_name}")
        self.nli_model = CrossEncoder(config.nli_model_name)
        
        # Load LLM client
        logger.info("Initializing LLM client")
        self.llm_client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.llm_model = config.llm_model_name
        
        # Config parameters (not hardcoded)
        self.top_k_retrieval = config.top_k_retrieval  # 50
        self.num_clusters = config.num_clusters  # 5
        self.top_per_cluster = config.top_per_cluster  # 2
        self.entailment_threshold = config.entailment_threshold  # e.g., 0.8
        
        logger.info(f"Config: top_k={self.top_k_retrieval}, clusters={self.num_clusters}, "
                    f"per_cluster={self.top_per_cluster}, threshold={self.entailment_threshold}")

    def translate(self, hypothesis: str) -> Optional[str]:
        logger.info(f"Translating hypothesis: '{hypothesis[:100]}...' " if len(hypothesis) > 100 
                    else f"Translating hypothesis: '{hypothesis}'")
        
        # Edge case: empty KB
        if len(self.kb_propositions) == 0:
            logger.warning("KB is empty, returning None")
            return None
        
        # Step 1: SBERT Retrieval - Top k (up to 50)
        logger.info("Step 1: SBERT Retrieval")
        top_indices, top_scores = self._retrieve_top_k(hypothesis, self.top_k_retrieval)
        top_propositions = [self.kb_propositions[i] for i in top_indices]
        top_embeddings = self.kb_embeddings[top_indices]
        
        logger.info(f"  Retrieved {len(top_indices)} propositions")
        logger.debug(f"  Top scores: {top_scores[:5]}...")
        
        # Step 2: K-means Clustering (cosine distance via normalized vectors)
        logger.info("Step 2: K-means Clustering")
        cluster_labels = self._cluster_propositions(top_embeddings)
        n_clusters_found = len(np.unique(cluster_labels))
        logger.info(f"  Formed {n_clusters_found} clusters")
        
        # Step 3: Select Top-2 from Each Cluster
        logger.info("Step 3: Select from Clusters")
        diverse_props, diverse_indices = self._select_from_clusters(
            top_propositions, top_indices, top_scores, cluster_labels
        )
        logger.info(f"  Selected {len(diverse_props)} diverse propositions")
        for i, (prop, idx) in enumerate(zip(diverse_props, diverse_indices)):
            logger.debug(f"    P_{idx}: '{prop[:80]}...' " if len(prop) > 80 else f"    P_{idx}: '{prop}'")
        
        # Step 4: Brute Force Subsets + NLI/SBERT Scoring
        logger.info("Step 4: Finding Entailing Subsets")
        total_subsets = 2 ** len(diverse_props) - 1
        logger.info(f"  Checking {total_subsets} subsets...")
        qualifying_subsets = self._find_entailing_subsets(hypothesis, diverse_props, diverse_indices)
        
        logger.info(f"  Found {len(qualifying_subsets)} qualifying subsets (threshold={self.entailment_threshold})")
        for indices, props, score in qualifying_subsets[:5]:  # Show first 5
            logger.debug(f"    {{{', '.join([f'P_{i}' for i in indices])}}}: score={score:.3f}")
        
        if not qualifying_subsets:
            logger.warning("No qualifying subsets found, returning None")
            return None
        
        # Step 5: LLM Formula Writing
        logger.info("Step 5: LLM Formula Writing")
        formula = self._llm_write_formula(hypothesis, qualifying_subsets)
        logger.info(f"  Generated formula: {formula}")
        
        return formula

    def _retrieve_top_k(self, hypothesis: str, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Retrieve top-k propositions by SBERT cosine similarity"""
        hyp_embedding = self.sbert_model.encode(hypothesis, normalize_embeddings=True)
        
        # Cosine similarity (embeddings are normalized)
        similarities = np.dot(self.kb_embeddings, hyp_embedding)
        
        # Handle case where KB has fewer than k propositions
        k = min(k, len(self.kb_propositions))
        
        top_indices = np.argsort(similarities)[-k:][::-1]
        top_scores = similarities[top_indices]
        
        return top_indices, top_scores

    def _cluster_propositions(self, embeddings: np.ndarray) -> np.ndarray:
        """K-means clustering with cosine distance (normalize then euclidean = cosine)"""
        # Handle case where we have fewer embeddings than clusters
        n_clusters = min(self.num_clusters, len(embeddings))
        
        if n_clusters <= 1:
            logger.debug("  Only 1 cluster needed (few embeddings)")
            return np.zeros(len(embeddings), dtype=int)
        
        # Normalize embeddings for cosine distance
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)  # Avoid division by zero
        normalized = embeddings / norms
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(normalized)
        
        # Log cluster sizes
        unique, counts = np.unique(cluster_labels, return_counts=True)
        for cluster_id, count in zip(unique, counts):
            logger.debug(f"    Cluster {cluster_id}: {count} propositions")
        
        return cluster_labels

    def _select_from_clusters(
        self, 
        propositions: List[str], 
        indices: np.ndarray,
        scores: np.ndarray, 
        cluster_labels: np.ndarray
    ) -> Tuple[List[str], List[int]]:
        """Select top-N from each cluster by similarity score"""
        selected_props = []
        selected_indices = []
        
        unique_clusters = np.unique(cluster_labels)
        
        for cluster_id in unique_clusters:
            # Get propositions in this cluster
            mask = cluster_labels == cluster_id
            cluster_positions = np.where(mask)[0]
            
            if len(cluster_positions) == 0:
                continue
            
            # Sort by similarity score (already computed)
            cluster_scores = scores[cluster_positions]
            sorted_positions = cluster_positions[np.argsort(cluster_scores)[::-1]]
            
            # Take top N from this cluster
            for pos in sorted_positions[:self.top_per_cluster]:
                selected_props.append(propositions[pos])
                selected_indices.append(int(indices[pos]))
        
        return selected_props, selected_indices

    def _find_entailing_subsets(
        self, 
        hypothesis: str, 
        propositions: List[str],
        indices: List[int]
    ) -> List[Tuple[List[int], List[str], float]]:
        """Find all subsets that entail hypothesis above threshold"""
        qualifying = []
        
        # Pre-compute hypothesis embedding (avoid redundant computation)
        hyp_emb = self.sbert_model.encode(hypothesis, normalize_embeddings=True)
        
        checked = 0
        for size in range(1, len(propositions) + 1):
            for idx_combo in combinations(range(len(propositions)), size):
                subset_props = [propositions[i] for i in idx_combo]
                subset_indices = [indices[i] for i in idx_combo]
                
                # Combine propositions
                combined_premise = " ".join(subset_props)
                
                # Score: max of NLI entailment and SBERT similarity
                score = self._compute_entailment_score(combined_premise, hyp_emb)
                
                checked += 1
                if checked % 100 == 0:
                    logger.debug(f"    Checked {checked} subsets...")
                
                if score >= self.entailment_threshold:
                    qualifying.append((subset_indices, subset_props, score))
                    logger.debug(f"    Found qualifying subset: {subset_indices} (score={score:.3f})")
        
        logger.debug(f"    Total subsets checked: {checked}")
        return qualifying

    def _compute_entailment_score(self, premise: str, hyp_emb: np.ndarray) -> float:
        """Compute entailment score using NLI and SBERT
        
        Args:
            premise: Combined premise text
            hyp_emb: Pre-computed hypothesis embedding (normalized)
        """
        # NLI score using CrossEncoder
        # Note: cross-encoder/nli-deberta-v3-base uses [contradiction, entailment, neutral]
        # Check your specific model's label order!
        nli_scores = self.nli_model.predict([(premise, self._current_hypothesis)])[0]
        
        # Handle different output formats
        if isinstance(nli_scores, np.ndarray) and len(nli_scores) == 3:
            # Softmax to get probabilities
            exp_scores = np.exp(nli_scores - np.max(nli_scores))
            probs = exp_scores / exp_scores.sum()
            # For cross-encoder/nli-deberta-v3-base: [contradiction, entailment, neutral]
            nli_entailment = probs[1]  # entailment is index 1
        elif isinstance(nli_scores, (int, float)):
            # Single score (some models output this)
            nli_entailment = float(nli_scores)
        else:
            logger.warning(f"Unexpected NLI output format: {type(nli_scores)}")
            nli_entailment = 0.0
        
        # SBERT similarity (handles identity case)
        premise_emb = self.sbert_model.encode(premise, normalize_embeddings=True)
        sbert_sim = float(np.dot(premise_emb, hyp_emb))
        
        return max(nli_entailment, sbert_sim)

    def _find_entailing_subsets(
        self, 
        hypothesis: str, 
        propositions: List[str],
        indices: List[int]
    ) -> List[Tuple[List[int], List[str], float]]:
        """Find all subsets that entail hypothesis above threshold"""
        qualifying = []
        
        # Pre-compute hypothesis embedding (avoid redundant computation)
        hyp_emb = self.sbert_model.encode(hypothesis, normalize_embeddings=True)
        
        # Store hypothesis for NLI (needed in _compute_entailment_score)
        self._current_hypothesis = hypothesis
        
        checked = 0
        for size in range(1, len(propositions) + 1):
            for idx_combo in combinations(range(len(propositions)), size):
                subset_props = [propositions[i] for i in idx_combo]
                subset_indices = [indices[i] for i in idx_combo]
                
                # Combine propositions
                combined_premise = " ".join(subset_props)
                
                # Score: max of NLI entailment and SBERT similarity
                score = self._compute_entailment_score(combined_premise, hyp_emb)
                
                checked += 1
                if checked % 100 == 0:
                    logger.debug(f"    Checked {checked} subsets...")
                
                if score >= self.entailment_threshold:
                    qualifying.append((subset_indices, subset_props, score))
                    logger.debug(f"    Found qualifying subset: {subset_indices} (score={score:.3f})")
        
        logger.debug(f"    Total subsets checked: {checked}")
        return qualifying

    def _llm_write_formula(
        self, 
        hypothesis: str, 
        qualifying_subsets: List[Tuple[List[int], List[str], float]]
    ) -> str:
        """Ask LLM to write formula from qualifying subsets"""
        
        # Format subsets for prompt
        subsets_text = ""
        for indices, props, score in qualifying_subsets:
            prop_ids = ", ".join([f"P_{i}" for i in indices])
            props_text = " AND ".join(props)
            subsets_text += f"  - {{{prop_ids}}}: \"{props_text}\" (score: {score:.2f})\n"
        
        prompt = f"""The following proposition subsets entail the hypothesis:

{subsets_text}

Hypothesis: "{hypothesis}"

Write a propositional logic formula using these proposition IDs (P_0, P_1, etc.) that captures when the hypothesis is entailed.

Rules:
- Use & for AND, | for OR, ~ for NOT
- Prefer simpler formulas
- If one subset is sufficient, use just that one
- Output ONLY the formula, nothing else

Formula:"""

        logger.debug(f"LLM Prompt:\n{prompt}")
        
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        formula = response.choices[0].message.content.strip()
        
        logger.debug(f"LLM Response: {formula}")
        
        return formula


# Utility function to set log level
def set_log_level(level: str):
    """Set logging level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'"""
    logger.setLevel(getattr(logging, level.upper()))

# Backward compatibility wrapper
_translator_instance = None

# Backward compatibility wrapper to match old interface
_translator_instance = None
_current_json_path = None

def translate_query(
    query: str,
    json_path: str,
    api_key: str,
    model: str = "anthropic/claude-3-haiku",
    temperature: float = 0.1,
    reasoning_effort: str = "medium",
    max_tokens: int = 64000,
    k: int = 50,
    sbert_model_name: str = "all-MiniLM-L6-v2",
    verbose: bool = True,
    enable_decomposition: bool = True,
) -> Dict[str, Any]:
    """Wrapper function for backward compatibility with old interface"""
    global _translator_instance, _current_json_path
    
    # Load KB from json_path
    import json
    with open(json_path, 'r') as f:
        kb_data = json.load(f)
    
    # Extract propositions from KB (adjust key based on your JSON structure)
    if 'propositions' in kb_data:
        kb_propositions = [p['text'] if isinstance(p, dict) else p for p in kb_data['propositions']]
    elif 'atoms' in kb_data:
        kb_propositions = [p['text'] if isinstance(p, dict) else p for p in kb_data['atoms']]
    else:
        # Fallback: try to find proposition-like data
        kb_propositions = []
        logger.warning(f"Could not find 'propositions' or 'atoms' in {json_path}")
    
    # Create config object
    class Config:
        pass
    
    config = Config()
    config.sbert_model_name = sbert_model_name
    config.nli_model_name = "cross-encoder/nli-deberta-v3-base"
    config.openrouter_api_key = api_key
    config.llm_model_name = model
    config.top_k_retrieval = k
    config.num_clusters = 5
    config.top_per_cluster = 2
    config.entailment_threshold = 0.8
    
    # Re-initialize if json_path changed
    if _translator_instance is None or _current_json_path != json_path:
        if verbose:
            logger.info(f"Initializing TranslateQuery with KB from {json_path}")
        _translator_instance = TranslateQuery(config, kb_propositions)
        _current_json_path = json_path
    
    # Translate
    formula = _translator_instance.translate(query)
    
    # Return in expected format (Dict)
    return {
        "formula": formula,
        "query": query,
        "success": formula is not None,
    }

