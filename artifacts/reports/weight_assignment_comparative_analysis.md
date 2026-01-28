# Comparative Analysis: Weight Assignment Methods for Soft Constraints

## Executive Summary

After careful analysis of the provided documents (`text_main_v2.tex` and `appendix_v1.tex`), I must report a **critical finding**: The referenced weight assignment sections (`\ref{sec:weights_SBERT}` and `\ref{sec:weights_LLM}`) **do not exist** in the current repository. This report documents the current state of weight assignment methodology and provides a comparative analysis based on what can be inferred from the main paper and existing literature.

## Current Implementation Status

### What Exists: Heuristic-Based Weight Assignment

The main paper (`text_main_v2.tex`, lines 310-317) describes only **one implemented method**:

**Method: Linguistic Heuristics**
```
- "almost always" → w ≈ 0.9
- "typically" → w ≈ 0.7
- "sometimes" → w ≈ 0.5
- "rarely" → w ≈ 0.2
```

**Implementation Details:**
- **Location**: Section 3.2.3 "Weight Assignment" in main paper
- **Approach**: Static mapping from hedge words to confidence scores
- **Theoretical Foundation**: Based on "strength of linguistic hedging"
- **Code Status**: Referenced in `main.py` but `weights.py` is essentially empty

### What's Missing: SBERT and LLM Methods

The repository references two additional methods that are **not implemented**:
1. `\ref{sec:weights_SBERT}` - SBERT-based weight assignment
2. `\ref{sec:weights_LLM}` - LLM-based weight assignment

## Comparative Analysis Framework

Based on the existing heuristic method and anticipated characteristics of the missing methods, here's a comprehensive comparison:

### Method 1: Heuristic-Based Assignment (Currently Implemented)

**Methodology:**
- **Input**: Linguistic hedge tokens ("typically", "rarely", etc.)
- **Process**: Static lookup table mapping hedge strength to weights
- **Output**: Fixed confidence weights w ∈ (0,1)

**Strengths:**
- ✅ **Computational Efficiency**: O(1) lookup time
- ✅ **Reproducibility**: Deterministic mapping
- ✅ **Interpretability**: Clear hedge → weight correspondence
- ✅ **Implementation Simplicity**: Requires no external models
- ✅ **Domain Independence**: Works across all text types

**Limitations:**
- ❌ **Context Blindness**: Ignores surrounding context
- ❌ **Coarse Granularity**: Only ~4-5 confidence levels
- ❌ **No Learning**: Cannot adapt from data
- ❌ **Linguistic Oversimplification**: Treats all "typically" as identical
- ❌ **Domain Insensitivity**: Medical "typically" vs. legal "typically"

**Mathematical Framework:**
```
w_heuristic(constraint) = lookup_table[extract_hedge(constraint)]
```

### Method 2: SBERT-Based Assignment (Referenced but Missing)

**Anticipated Methodology:**
- **Input**: Full constraint sentence + reference certainty corpus
- **Process**: Sentence-BERT embeddings → similarity to calibrated examples
- **Output**: Confidence weights based on semantic similarity

**Expected Strengths:**
- ✅ **Semantic Awareness**: Captures meaning beyond surface tokens
- ✅ **Context Sensitivity**: Considers full sentence context
- ✅ **Continuous Scale**: Can produce any weight in (0,1)
- ✅ **Linguistic Robustness**: Handles paraphrases and variations
- ✅ **Pre-trained Knowledge**: Leverages large-scale language understanding

**Expected Limitations:**
- ❌ **Computational Cost**: Requires neural network inference
- ❌ **Reference Corpus Dependency**: Needs calibrated certainty examples
- ❌ **Limited Domain Adaptation**: Pre-trained on general text
- ❌ **Embedding Space Issues**: Semantic similarity ≠ certainty similarity
- ❌ **Calibration Challenges**: SBERT similarities may not map well to probabilities

**Expected Mathematical Framework:**
```
w_sbert(constraint) = f(similarity(SBERT(constraint), reference_examples))
```

### Method 3: LLM-Based Assignment (Referenced but Missing)

**Anticipated Methodology:**
- **Input**: Full document context + constraint + confidence estimation prompt
- **Process**: LLM reasoning over context and linguistic cues
- **Output**: Reasoned confidence scores with explanations

**Expected Strengths:**
- ✅ **Full Context Awareness**: Considers entire document context
- ✅ **Complex Reasoning**: Can handle multi-step certainty inference
- ✅ **Domain Adaptability**: Can be prompted for specific domains
- ✅ **Explainability**: Can provide reasoning for confidence scores
- ✅ **Linguistic Sophistication**: Understands complex hedging patterns
- ✅ **Dynamic Adaptation**: Can adjust based on document characteristics

**Expected Limitations:**
- ❌ **High Computational Cost**: Requires LLM inference per constraint
- ❌ **Calibration Issues**: LLM confidence often poorly calibrated
- ❌ **Hallucination Risk**: May generate overconfident or inconsistent scores
- ❌ **Prompt Sensitivity**: Results depend heavily on prompt engineering
- ❌ **Non-deterministic**: May produce different scores for identical inputs
- ❌ **API Dependency**: Requires external LLM access

**Expected Mathematical Framework:**
```
w_llm(constraint, context) = LLM("Rate certainty of: " + constraint + " in context: " + context)
```

## Theoretical Comparison

### Complexity Analysis

| Method | Time Complexity | Space Complexity | Model Size |
|--------|----------------|------------------|------------|
| Heuristic | O(1) | O(k) hedge words | ~1KB |
| SBERT | O(n) tokens | O(d) embedding dim | ~110MB |
| LLM | O(m) context length | O(m) context | ~7GB+ |

### Accuracy Expectations (Hypothetical)

Based on typical performance patterns:

| Method | Expected Accuracy | Calibration | Context Sensitivity |
|--------|------------------|-------------|-------------------|
| Heuristic | Baseline | Poor | None |
| SBERT | +5-15% | Moderate | Sentence-level |
| LLM | +10-25% | Poor→Good* | Full document |

*Depends heavily on calibration techniques

## Critical Gaps and Recommendations

### 1. Implementation Gap
**Issue**: Two of three claimed methods are not implemented
**Impact**: Undermines reproducibility and experimental validity
**Recommendation**: Implement both SBERT and LLM methods before publication

### 2. Experimental Validation Gap
**Issue**: No comparative evaluation of weight assignment methods
**Impact**: Cannot determine which method works best for which use cases
**Recommendation**: Conduct systematic comparison on benchmark datasets

### 3. Calibration Analysis Gap
**Issue**: No analysis of whether assigned weights reflect true confidence
**Impact**: Poor weight assignment could undermine soft constraint utility
**Recommendation**: Evaluate weight calibration using reliability diagrams

## Proposed Evaluation Framework

### Metrics for Comparison
1. **Downstream Task Performance**: Accuracy on final reasoning tasks
2. **Weight Calibration**: Correlation between assigned weights and actual certainty
3. **Computational Efficiency**: Runtime and memory requirements
4. **Consistency**: Agreement across similar constraints
5. **Domain Robustness**: Performance across legal, medical, technical texts

### Experimental Design
```
For each method M in {Heuristic, SBERT, LLM}:
  For each dataset D in {MedGuide, ContractNLI, Technical docs}:
    1. Extract soft constraints from D
    2. Assign weights using method M
    3. Evaluate on downstream reasoning tasks
    4. Measure calibration via reliability plots
    5. Record computational costs
```

## Conclusions

### Current State
- **Only 1 of 3** claimed weight assignment methods is implemented
- The implemented heuristic method is simple but limited
- **Critical reproducibility issue**: Methods referenced in paper don't exist

### Research Implications
- Weight assignment is a crucial component affecting soft constraint utility
- Different methods likely have complementary strengths (speed vs. accuracy vs. context)
- Proper evaluation requires all three methods to be implemented and compared

### Priority Recommendations
1. **Immediate**: Implement missing SBERT and LLM weight assignment methods
2. **High**: Conduct comparative evaluation on multiple datasets
3. **Medium**: Develop hybrid approaches combining multiple methods
4. **Future**: Explore learned weight assignment from labeled data

This analysis reveals that while the theoretical framework for soft constraints is solid, the practical implementation of weight assignment methods is incomplete, requiring significant additional work to fulfill the paper's claims.