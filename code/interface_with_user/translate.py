from config.retrieval_config import (
    TEMPERATURE_LOGIC_CONVERTER, MAX_TOKENS, REASONING_EFFORT,
    SBERT_TOP_K, SBERT_MIN_SIMILARITY, ENABLE_HYBRID_EMBEDDING,
    REASONING_MODEL, TRANSLATE_MODEL, TEMPERATURE_TRANSLATE,
    REASONING_EFFORT_TRANSLATE, PROMPT_TRANSLATION,
    TRIGGER_QUERY, ADDITIONAL_LLM_QUERY, SBERT_MODEL, NLI_MODEL,
    SUBSET_TOP_K_RETRIEVAL, SUBSET_NUM_CLUSTERS,
    SUBSET_TOP_PER_CLUSTER, SUBSET_ENTAILMENT_THRESHOLD,
    MAX_VARIANTS, MAX_SYNONYMS, ON_EXPAND_QUERY_SYN,
    USE_SUBSET, DIRECT_RETRIEVAL_MULTIPLIER,
)


# 2) Add this new function alongside the other candidate-generation functions:
def generate_candidates_via_direct_retrieval(
    query: str,
    chunks: List[Dict],
    api_key: str,
    model: str,
    verbose: bool = True,
) -> List[Dict]:
    """
    Generate formula candidates directly from the top SBERT propositions.

    This is the non-subset mode controlled by USE_SUBSET=False.
    """
    direct_chunks = chunks
    k_direct = len(direct_chunks)

    if verbose:
        print("\n #FUNCTION: generate_candidates_via_direct_retrieval")
        print(f"  Using top-{k_direct} SBERT propositions (from {len(chunks)} retrieved)")

    props_text = "\n".join(
        f'  - {chunk["id"]}: "{chunk["translation"]}"' for chunk in direct_chunks
    )
    available_ids = ", ".join(chunk["id"] for chunk in direct_chunks)
    query_is_negative = negation_detection.detect_negation_in_hypothesis(query)

    prompt = build_prompt(
        query=query,
        props_text=props_text,
        available_ids=available_ids,
        query_is_negative=query_is_negative,
    )
    return generate_candidates_llm(prompt=prompt, api_key=api_key, model=model)


# 3) Replace translate_query_single with this version.
# It preserves version-1 behavior when USE_SUBSET=True,
# and uses TRANSLATE_MODEL for direct retrieval mode.
def translate_query_single(
    query: str,
    json_path: str,
    api_key: str,
    model: str = TRANSLATE_MODEL,
    model_reasonig: str = REASONING_MODEL,
    temperature: float = TEMPERATURE_TRANSLATE,
    reasoning_effort: str = REASONING_EFFORT_TRANSLATE,
    max_tokens: int = MAX_TOKENS,
    k: int = SBERT_TOP_K,
    sbert_model_name: str = SBERT_MODEL,
    verbose: bool = True
    ) -> Dict[str, Any]:
    """
    Single-sentence translation pipeline.

    Behavior:
    - If USE_SUBSET=True: preserve version-1 subset-entailment flow.
    - If USE_SUBSET=False: use direct top-K retrieval + prompt-based LLM translation.

    Important:
    - Direct retrieval mode uses `model` (TRANSLATE_MODEL by default),
      not `model_reasonig`.
    """
    print(f"""\n
          \n#FUNCTION: translate_query_single
          \nPARAMETERS: query = {query}, 
    json_path: {json_path},
    model: str = {model},
    temperature ={temperature} 
    k = {k}
    sbert_model_name = {sbert_model_name},
    verbose = {verbose}
          """)

    # 1. Pre-process (Yes/No Handling)
    original_query = query
    if is_yes_no_question(query):
        try:
            query = convert_yes_no_to_statement(query, api_key, model_reasonig)
            if verbose:
                print(f"  → Statement: {query}")
        except Exception:
            if verbose:
                print("  → Conversion failed, proceeding with original.")
    else:
        print("is_yes_no_question routine not used")

    # 2. Retrieval
    if verbose:
        print(f"\n \n Starting retrieval. Loading propositions from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        logified_structure = json.load(f)

    chunks = extract_proposition_chunks(logified_structure)
    sbert_model = load_sbert_model(sbert_model_name)
    retrieved = retrieve_with_expanded_query(query, chunks, sbert_model, k=k)

    if not retrieved:
        print("Nothing retrieved")
        return {
            "formula": "NONE",
            "translation": "No relevant props",
            "query": query,
            "original_query": original_query,
            "explanation": "No documents found.",
            "confidence": -1
        }

    print(f"Within translate_query_single, we finished retrieved with {len(chunks)} chunks")

    # 3. MODAL OPPOSITE DETECTION
    if verbose:
        print("\nChecking for modal opposites...")

    modal_opposite_result = detect_modal_opposite(query, retrieved, sbert_model, verbose=verbose)
    if modal_opposite_result:
        modal_opposite_result["query"] = query
        modal_opposite_result["original_query"] = original_query
        if verbose:
            print(f"  → Modal opposite detected! Returning: {modal_opposite_result['formula']}")
        return modal_opposite_result

    # 4. ANTONYM CONTRADICTION DETECTION
    if verbose:
        print("\nChecking for antonym contradictions...")

    antonym_result = detect_antonym_contradiction(query, retrieved, sbert_model, verbose=verbose)
    if antonym_result:
        antonym_result["query"] = query
        antonym_result["original_query"] = original_query
        if verbose:
            print(f"  → Antonym contradiction detected! Returning: {antonym_result['formula']}")
        return antonym_result

    # 4b. IMPLICATION CONTRADICTION DETECTION
    if verbose:
        print("\nChecking for implication contradictions...")

    impl_result = detect_implication_contradiction(query, logified_structure, sbert_model, verbose=verbose)
    if impl_result:
        impl_result["query"] = query
        impl_result["original_query"] = original_query
        if verbose:
            print(f"  → Implication contradiction detected! Returning: {impl_result['formula']}")
        return impl_result

    # 5-6. Generate candidates
    if USE_SUBSET:
        # Version-1 behavior preserved
        if verbose:
            print("\nGenerating candidates via subset entailment...")

        chunks_for_translation = retrieve_with_expanded_query(query, chunks, sbert_model, k)
        candidates = generate_candidates_via_subset_entailment(
            query, chunks_for_translation, sbert_model, api_key, model_reasonig, verbose=verbose
        )
    else:
        # Direct mode: retrieve a larger SBERT neighborhood and translate directly
        if verbose:
            print("\nGenerating candidates via direct top-K retrieval...")

        k_direct = max(k, k * DIRECT_RETRIEVAL_MULTIPLIER)
        chunks_for_translation = retrieve_with_expanded_query(query, chunks, sbert_model, k_direct)
        candidates = generate_candidates_via_direct_retrieval(
            query=query,
            chunks=chunks_for_translation,
            api_key=api_key,
            model=model,  # IMPORTANT: use TRANSLATE_MODEL path, not reasoning model
            verbose=verbose,
        )

    if not candidates:
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "LLM failed to generate valid candidates."
        }

    # If model abstained, return NONE
    if len(candidates) == 1 and candidates[0].get("formula") == "NONE":
        return {
            "formula": "NONE",
            "translation": candidates[0].get("translation", "Not matching proposition"),
            "query": query,
            "original_query": original_query,
            "explanation": "LLM abstained (no matching proposition).",
            "confidence": 0.5
        }

    # Build prop_map for verbalization
    prop_map = {p['id']: p['translation'].strip(".") for p in chunks_for_translation}

    # 7. Verbalize & Verify
    if verbose:
        print("Step B & C: Verbalizing and Verifying with NLI...")
    nli_model = load_nli_model_singleton()

    winner, winning_text, best_net_score = select_best_candidate(
        candidates, query, prop_map, nli_model, verbose=verbose
    )

    if winner is None:
        return {
            "formula": "ERROR",
            "translation": "",
            "query": query,
            "explanation": "All candidates failed syntax parsing."
        }

    # Compute SBERT confidence for voting trigger decision
    sbert_confidence = compute_sbert_confidence(query, winning_text)
    if verbose:
        print(f"  SBERT confidence: {sbert_confidence:.4f} (NLI score: {best_net_score:.4f})")

    # 8. ADAPTIVE VOTING
    if sbert_confidence < TRIGGER_QUERY and ADDITIONAL_LLM_QUERY > 0:
        if verbose:
            print(f"\n[Adaptive Voting] Confidence {best_net_score:.2f} < {TRIGGER_QUERY}, triggering voting...")
            print(f"[Adaptive Voting] Making {ADDITIONAL_LLM_QUERY} additional LLM calls...")

        all_formulas = [normalize_formula(winner['formula'])]
        all_results = [(winner, winning_text, best_net_score)]

        for i in range(ADDITIONAL_LLM_QUERY):
            if verbose:
                print(f"  [Voting] Additional call {i+1}/{ADDITIONAL_LLM_QUERY}...")

            if USE_SUBSET:
                # Version-1 behavior preserved
                additional_candidates = generate_candidates_via_subset_entailment(
                    query, chunks_for_translation, sbert_model, api_key, model_reasonig, verbose=True
                )
            else:
                additional_candidates = generate_candidates_via_direct_retrieval(
                    query=query,
                    chunks=chunks_for_translation,
                    api_key=api_key,
                    model=model,  # IMPORTANT: use TRANSLATE_MODEL path here too
                    verbose=True,
                )

            if additional_candidates and not (
                len(additional_candidates) == 1 and additional_candidates[0].get("formula") == "NONE"
            ):
                add_winner, add_text, add_score = select_best_candidate(
                    additional_candidates, query, prop_map, nli_model, verbose=True
                )
                if add_winner is not None:
                    all_formulas.append(normalize_formula(add_winner['formula']))
                    all_results.append((add_winner, add_text, add_score))
                    if verbose:
                        print(f"    → Got formula: {add_winner['formula']} (score: {add_score:.2f})")
            else:
                all_formulas.append("NONE")
                if verbose:
                    print("    → LLM abstained (NONE)")

        formula_counts = Counter(all_formulas)
        winning_formula, vote_count = formula_counts.most_common(1)[0]

        if verbose:
            print(f"\n[Adaptive Voting] Vote results: {dict(formula_counts)}")
            print(f"[Adaptive Voting] Winner: {winning_formula} ({vote_count}/{len(all_formulas)} votes)")

        if winning_formula == "NONE":
            voting_confidence = vote_count / len(all_formulas)
            return {
                "formula": "NONE",
                "translation": "",
                "query": query,
                "original_query": original_query,
                "explanation": f"Abstained via voting ({vote_count}/{len(all_formulas)} votes for NONE)",
                "confidence": 0.5,
                "sbert_confidence": sbert_confidence,
                "voting_triggered": True,
                "voting_confidence": voting_confidence,
                "vote_counts": dict(formula_counts)
            }

        matching_results = [
            (w, t, s) for (w, t, s) in all_results
            if normalize_formula(w['formula']) == winning_formula
        ]

        if matching_results:
            matching_results.sort(key=lambda x: x[2], reverse=True)
            winner, winning_text, best_net_score = matching_results[0]

        voting_confidence = vote_count / len(all_formulas)
        explanation = (
            f"Selected via voting ({vote_count}/{len(all_formulas)} votes, "
            f"NLI: {best_net_score:.2f}). LLM Reasoning: {winner.get('reasoning', '')}"
        )

        return {
            "formula": winner['formula'],
            "translation": winning_text,
            "query": query,
            "original_query": original_query,
            "explanation": explanation,
            "confidence": best_net_score,
            "sbert_confidence": sbert_confidence,
            "voting_triggered": True,
            "voting_confidence": voting_confidence,
            "vote_counts": dict(formula_counts)
        }

    # No voting needed
    return {
        "formula": winner['formula'],
        "translation": winning_text,
        "query": query,
        "original_query": original_query,
        "explanation": f"Selected via NLI (Confidence: {best_net_score:.2f}). LLM Reasoning: {winner.get('reasoning', '')}",
        "confidence": best_net_score,
        "sbert_confidence": sbert_confidence
    }
