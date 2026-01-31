# Negation Handling Fix for Logify

## Problem Summary

**Error Pattern 1**: Complete failure on contradictions (100% error rate on FALSE predictions)

The system fails to detect contradictions in ContractNLI. Analysis reveals:

* 0 of 7 FALSE cases predicted correctly

* Only 8.4% of query formulas contain negation operators (`¬`)

* Same proposition maps to contradictory ground truths (e.g., P_15 → {TRUE, FALSE, FALSE, UNCERTAIN})

## Root Cause Analysis

### Issue 1: Ambiguous Negation Semantics in Query Translation

**Current behavior** (translate.py lines 418-421):

```text
1. "Shall"/"Must" obligations → Use proposition directly: P_i (mode: entailment) 2. "Shall not" prohibitions → The proposition already captures the negation, use: P_i (mode: entailment)
```

**The problem**: When translating "shall not X", the system assumes the extracted proposition P_i already captures the prohibition. However:

1. **Extraction ambiguity**: During logification (logic_converter.py), the LLM may extract either:

   * Affirmative: P_9 = "Receiving Party reverses engineering objects"

   * Negative: P_9 = "Receiving Party shall not reverse engineer objects"

2. **Query translation mismatch**: When translating hypothesis "Receiving Party shall not reverse engineer...", the system:

   * Retrieves P_9 using SBERT semantic similarity

   * Maps to formula "P_9" (no negation operator)

   * If P_9 was extracted as affirmative, this is **semantically incorrect**

3. **No polarity validation**: There's no check to ensure the retrieved proposition's polarity matches the query's intent

### Issue 2: Entailment Logic Doesn't Distinguish Absence from Contradiction

**Current behavior** (maxsat.py lines 63-149):

* Entailment check: KB ⊨ Q iff KB ∧ ¬Q is UNSAT

* If KB ∧ ¬Q is SAT (satisfiable), returns "UNCERTAIN"

* **Never returns "FALSE" for contradiction**

**Example failure case** (from results):

* Hypothesis: "Confidential Information shall only include technical information"

* Ground truth: FALSE (contract includes non-technical info)

* Logify prediction: UNCERTAIN (confidence 0.5)

* Formula: "P_1"

The system likely found P_1 = "Confidential Information includes technical and non-technical information", but the entailment check can't distinguish between:

* **Absence**: KB doesn't mention this proposition → UNCERTAIN

* **Contradiction**: KB contains ¬P_1 (opposite is true) → FALSE

## Proposed Fix

### Fix 1: Explicit Negation Detection in Query Translation

**File**: `code/interface_with_user/translate.py`

**Add negation detection helper** (insert after line 433):

```python
def detect_negation_in_hypothesis(hypothesis: str) -> bool: """ Detect if hypothesis expresses a prohibition or negation. Returns: True if hypothesis is negative/prohibition, False otherwise """ negation_patterns = [ r'\bshall not\b', r'\bmust not\b', r'\bcannot\b', r'\bcan not\b', r'\bwill not\b', r'\bmay not\b', r'\bshould not\b', r'\bprohibit(ed|s)?\b', r'\bforbid(den|s)?\b', r'\bno\s+\w+\s+(shall|must|will|may)', # "no party shall..." r'\bneither\b.*\bnor\b', ] for pattern in negation_patterns: if re.search(pattern, hypothesis, re.IGNORECASE): return True return False def detect_negation_in_proposition(translation: str) -> bool: """ Detect if a proposition translation already encodes negation. Args: translation: Natural language translation of proposition Returns: True if proposition is negative, False if affirmative """ negation_indicators = [ r'\bnot\b', r'\bno\b', r'\bnever\b', r'\bcannot\b', r'\bwithout\b', r'\bexclude(s|d)?\b', r'\bprohibit(s|ed)?\b', r'\bforbid(s|den)?\b', ] for pattern in negation_indicators: if re.search(pattern, translation, re.IGNORECASE): return True return False
```

**Modify formula construction** (update the `build_query_translation_prompt` function around line 419-421):

```python
=== TRANSLATION GUIDELINES === 1. "Shall"/"Must" obligations → Use proposition directly: P_i (mode: entailment) 2. "Shall not"/"Must not" prohibitions: - If the proposition translation is affirmative (e.g., "Party discloses information"), use negation: ¬P_i - If the proposition translation already includes negation (e.g., "Party does not disclose"), use: P_i - Mode: entailment 3. "May"/"Can" permissions → Use proposition for the permitted action: P_i (mode: consistency) 4. Contradictions "X shall only include Y" (when KB shows X includes Z≠Y): - Check if retrieved propositions contradict the hypothesis - If contradiction exists, formulate as: ¬(retrieved_formula) 5. Conditionals "If A then B" / "in case" / "when" → Use implication: P_a ⟹ P_b (mode: entailment) 6. "Some"/"Any" (existential) → Use disjunction: P_1 ∨ P_2 7. "All"/"Every" (universal) → Use conjunction: P_1 ∧ P_2 IMPORTANT: - Choose the SIMPLEST formula that preserves semantic intent - ALWAYS check if hypothesis polarity (affirmative/negative) matches retrieved proposition polarity - When polarities mismatch, apply negation operator (¬) to correct the formula
```

**Add polarity check in translation code** (modify `translate_hypothesis` function around line 200):

```python
def translate_hypothesis( hypothesis: str, logified: Dict, model: str = "gpt-4o", temperature: float = 0.1, k: int = 20, debug: bool = False ) -> TranslationResult: """ Translate natural language hypothesis to propositional formula. NEW: Includes negation detection and polarity correction. """ # ... existing retrieval code ... # Detect negation in hypothesis hypothesis_is_negative = detect_negation_in_hypothesis(hypothesis) # Check polarity of retrieved propositions retrieved_props_metadata = [] for prop_id in retrieved_prop_ids: prop_data = next((p for p in logified['primitive_props'] if p['id'] == prop_id), None) if prop_data: prop_is_negative = detect_negation_in_proposition(prop_data['translation']) retrieved_props_metadata.append({ 'id': prop_id, 'translation': prop_data['translation'], 'is_negative': prop_is_negative }) # Build prompt with polarity information prompt = build_query_translation_prompt( hypothesis=hypothesis, retrieved_props=retrieved_props_metadata, hypothesis_is_negative=hypothesis_is_negative ) # ... rest of translation ... # Post-processing: validate formula polarity formula_result = response['formula'] # If hypothesis is negative but formula has no negation, flag for review if hypothesis_is_negative and '¬' not in formula_result and '~' not in formula_result: if debug: print(f"WARNING: Negative hypothesis '{hypothesis}' mapped to formula without negation: {formula_result}") print(f"Retrieved propositions: {retrieved_props_metadata}") return TranslationResult( formula=formula_result, query_mode=response['query_mode'], translation=response['translation'], reasoning=response['reasoning'], hypothesis_is_negative=hypothesis_is_negative, polarity_mismatch_warning=hypothesis_is_negative and '¬' not in formula_result )
```

### Fix 2: Contradiction Detection in Solver

**File**: `code/logic_solver/maxsat.py`

**Add contradiction detection** (insert new method after line 149):

```python
def check_contradiction(self, query_formula: str) -> SolverResult: """ Check if query is explicitly contradicted by the knowledge base. A query Q is contradicted if: 1. KB ⊭ Q (query is not entailed) 2. KB ⊨ ¬Q (negation of query is entailed) Args: query_formula: Propositional formula (e.g., "P_1", "P_3 => P_4") Returns: SolverResult with answer FALSE if contradicted, UNCERTAIN otherwise """ try: # Step 1: Check if KB ⊨ Q entailment_result = self.check_entailment(query_formula) if entailment_result.answer == "TRUE": # Query is entailed, not contradicted return SolverResult( answer="UNCERTAIN", confidence=0.0, model=None, explanation="Query is entailed, not contradicted" ) # Step 2: Check if KB ⊨ ¬Q (negation is entailed) negated_formula = f"¬({query_formula})" negation_entailment = self.check_entailment(negated_formula) if negation_entailment.answer == "TRUE": # KB entails ¬Q, so Q is contradicted return SolverResult( answer="FALSE", confidence=negation_entailment.confidence, model=None, explanation=f"Knowledge base entails ¬({query_formula}), contradicting the query" ) # Neither Q nor ¬Q is entailed return SolverResult( answer="UNCERTAIN", confidence=0.5, model=None, explanation="Neither query nor its negation is entailed by KB" ) except Exception as e: return SolverResult( answer="ERROR", confidence=0.0, model=None, explanation=f"Contradiction check failed: {str(e)}" )
```

**Modify the main query method** (update `query` method around line 203):

```python
def query(self, query_formula: str) -> SolverResult: """ Main query interface: checks entailment, contradiction, and consistency. Returns: - "TRUE" if KB ⊨ Q (entailed) - "FALSE" if KB ⊨ ¬Q (contradicted) - "UNCERTAIN" if neither entailed nor contradicted """ try: # Step 1: Check entailment entailment_result = self.check_entailment(query_formula) if entailment_result.answer == "TRUE": return entailment_result # Step 2: Check contradiction (NEW) contradiction_result = self.check_contradiction(query_formula) if contradiction_result.answer == "FALSE": return contradiction_result # Step 3: Neither entailed nor contradicted return SolverResult( answer="UNCERTAIN", confidence=0.5, model=None, explanation="Query is neither entailed nor contradicted by the knowledge base" ) except Exception as e: return SolverResult( answer="ERROR", confidence=0.0, model=None, explanation=f"Query processing failed: {str(e)}" )
```

### Fix 3: Improve Proposition Extraction Granularity

**File**: `code/prompts/prompt_logify`

**Add explicit negation handling guidance** (insert after line 66, in GUIDELINES section):

```text
NEGATION HANDLING GUIDELINES: - Extract propositions in AFFIRMATIVE form when possible Example: Instead of P_1 = "Party shall not disclose", use P_1 = "Party discloses" Then express prohibitions as hard constraints: H_1: ¬P_1 - Use NEGATIVE propositions only when negation is intrinsic to the concept Example: P_2 = "Information is not clearly musculoskeletal" (negation is part of the description) - For prohibitions "shall not X" or "must not X": Create affirmative proposition P_i = "X occurs" Add hard constraint: H_j: ¬P_i (prohibition on X) - This separation enables queries to check both presence and absence: Query "Can X occur?" → Check if KB ⊨ P_i (yes) or KB ⊨ ¬P_i (no)
```

**Add negation example to EXEMPLAR 2** (modify line 478, H_3):

```json
{ "id": "H_3", "formula": "P_7 ⟹ ¬P_8", "translation": "If the fume hood is running, the ventilation system cannot be turned off", "evidence": "Sentence 2: 'While the fume hood is running, the ventilation system cannot be turned off'", "reasoning": "P_8 is extracted as affirmative ('ventilation system is turned off'). The prohibition is expressed as ¬P_8 in the constraint. This allows queries to check both 'Can ventilation be turned off?' (¬P_8 in formula) and 'Is ventilation on?' (check ¬P_8 is entailed)." }
```

### Fix 4: Add Validation Layer

**New file**: `code/from_text_to_logic/validate_propositions.py`

```python
""" Validation utilities for proposition extraction and query translation. """ from typing import Dict, List, Tuple import re def validate_proposition_granularity(logified: Dict) -> List[str]: """ Check if propositions are overly coarse (mapping to contradictory labels). Returns: List of warning messages for propositions that may be too coarse """ warnings = [] # Check for propositions that are too generic for prop in logified['primitive_props']: translation = prop['translation'].lower() # Warning: propositions with multiple verbs may need decomposition verbs = re.findall(r'\b(and|or)\b', translation) if len(verbs) >= 2: warnings.append( f"{prop['id']}: Translation contains multiple connectives ({len(verbs)}). " f"Consider breaking into atomic propositions: '{prop['translation']}'" ) # Warning: propositions with hedge words should be in soft constraints hedge_words = ['usually', 'typically', 'sometimes', 'generally', 'often', 'mostly'] for hedge in hedge_words: if hedge in translation: warnings.append( f"{prop['id']}: Contains hedge word '{hedge}'. " f"Proposition should be definitive; uncertainty should be in soft constraints." ) return warnings def validate_negation_consistency( hypothesis: str, formula: str, retrieved_props: List[Dict] ) -> Tuple[bool, str]: """ Validate that negation polarity is consistent between hypothesis and formula. Args: hypothesis: Natural language hypothesis formula: Translated propositional formula retrieved_props: List of propositions used in formula with metadata Returns: (is_valid, explanation) tuple """ # Detect if hypothesis is negative negation_patterns = [ r'\bshall not\b', r'\bmust not\b', r'\bcannot\b', r'\bno\s+\w+\s+(shall|must)', r'\bonly\s+include\b' ] hypothesis_is_negative = any( re.search(pattern, hypothesis, re.IGNORECASE) for pattern in negation_patterns ) # Check if formula contains negation operators formula_has_negation = bool(re.search(r'[¬~]', formula)) # Check if retrieved propositions are negative props_are_negative = any( re.search(r'\bnot\b|\bno\b|\bnever\b|\bcannot\b', prop['translation'], re.IGNORECASE) for prop in retrieved_props ) # Validation logic if hypothesis_is_negative: if not formula_has_negation and not props_are_negative: return False, ( f"POLARITY MISMATCH: Negative hypothesis '{hypothesis}' " f"mapped to formula without negation: '{formula}'. " f"Retrieved props: {[p['translation'] for p in retrieved_props]}" ) return True, "Negation polarity is consistent" def validate_formula_semantics( formula: str, prop_translations: Dict[str, str] ) -> Tuple[bool, str]: """ Check if formula semantics are consistent with proposition meanings. Args: formula: Propositional formula (e.g., "P_1 ∧ ¬P_2") prop_translations: Mapping from prop_id to natural language meaning Returns: (is_valid, explanation) tuple """ # Extract proposition IDs used in formula prop_ids = re.findall(r'P_\d+', formula) if len(prop_ids) == 0: return False, f"Formula '{formula}' contains no propositions" # Check for semantic contradictions (same prop used with opposite polarities) # Example: "P_1 ∧ ¬P_1" is always false prop_polarities = {} for prop_id in prop_ids: # Check if prop appears negated negated_pattern = rf'[¬~]\s*{prop_id}\b' is_negated = bool(re.search(negated_pattern, formula)) if prop_id in prop_polarities: if prop_polarities[prop_id] != is_negated: return False, ( f"SEMANTIC CONTRADICTION: {prop_id} appears both negated and non-negated " f"in formula '{formula}'" ) else: prop_polarities[prop_id] = is_negated return True, "Formula semantics are consistent"
```

## Implementation Priority

### High Priority (Addresses 100% FALSE error rate)

1. **Fix 1**: Add negation detection in query translation (translate.py)

   * Expected impact: +20-30% on FALSE case recall

2. **Fix 2**: Add contradiction detection in solver (maxsat.py)

   * Expected impact: Enable FALSE predictions (currently 0%)

### Medium Priority (Addresses 75% false positive rate)

1. **Fix 3**: Improve proposition extraction guidance (prompt_logify)

   * Expected impact: +10-15% on UNCERTAIN case precision

### Low Priority (Quality assurance)

1. **Fix 4**: Add validation layer (validate_propositions.py)

   * Expected impact: Early detection of errors, better debugging

## Testing Strategy

### Unit Tests

```python
# Test negation detection def test_negation_detection(): assert detect_negation_in_hypothesis("Party shall not disclose") == True assert detect_negation_in_hypothesis("Party shall disclose") == False assert detect_negation_in_hypothesis("Information includes only technical data") == True # Test polarity matching def test_polarity_matching(): props = [{'id': 'P_1', 'translation': 'Party discloses information'}] # Negative hypothesis + affirmative prop → should add negation hypothesis = "Party shall not disclose information" # Expected formula: ¬P_1 # Test contradiction detection def test_contradiction_detection(): # KB: P_1 ∧ (H: ¬P_1) # Query: P_1 # Expected: FALSE (contradicted)
```

### Integration Tests

```python
def test_contractnli_false_cases(): """ Test on the 7 FALSE cases from ContractNLI that Logify currently fails. """ test_cases = [ { 'hypothesis': 'Confidential Information shall only include technical information', 'ground_truth': 'FALSE', 'expected_formula': '¬P_1', # if P_1 = "CI includes technical and non-technical" }, { 'hypothesis': 'Receiving Party may create copies of Confidential Information', 'ground_truth': 'FALSE', 'expected_formula': '¬P_x', # if P_x = "RP creates copies" } ] for case in test_cases: result = logify_system.query(case['hypothesis']) assert result.prediction == case['ground_truth'], \ f"Expected {case['ground_truth']}, got {result.prediction}"
```

## Expected Outcomes

### Quantitative Improvements

* **FALSE case recall**: 0% → 70-80% (comparable to RAG's 79%)

* **UNCERTAIN false positive rate**: 75% → 30-40%

* **Overall accuracy on ContractNLI 7-doc subset**: 40% → 55-60%

### Qualitative Improvements

* Explicit distinction between "not mentioned" (UNCERTAIN) and "contradicted" (FALSE)

* Consistent polarity handling across extraction and query translation

* Better formula transparency (negation operators visible in output)

* Validation warnings for common errors

## Migration Path

1. **Phase 1**: Implement Fix 1 and Fix 2 (negation detection + contradiction checking)

2. **Phase 2**: Test on ContractNLI FALSE cases, measure recall improvement

3. **Phase 3**: Implement Fix 3 (update prompt_logify for better extraction)

4. **Phase 4**: Re-run full ContractNLI evaluation, measure overall accuracy

5. **Phase 5**: Implement Fix 4 (validation layer) for ongoing quality assurance

6. **Phase 6**: Cross-dataset validation on DocNLI (after fixing cache path bugs)

## Open Questions

1. **Hard vs Soft Constraints**: Should prohibitions be hard constraints (H: ¬P_i) or soft constraints?

   * Current approach: Hard constraints for "shall not", soft for "typically not"

2. **Negation Normal Form**: Should all formulas be converted to NNF before solving?

   * Current: Encoding layer handles this (encoding.py lines 181-224)

3. **Proposition reuse**: How to handle when same proposition maps to contradictory ground truths?

   * Proposed: Validation layer warns about this, prompting finer granularity

## References

* Paper (agent/paper.tex): Sections 4.2.2, 4.2.3, 5.1

* Code locations:

  * translate.py (lines 418-426): Query translation guidelines

  * maxsat.py (lines 63-149): Entailment checking logic

  * prompt_logify: Proposition extraction prompt

  * encoding.py (lines 181-224): NNF conversion and negation handling
