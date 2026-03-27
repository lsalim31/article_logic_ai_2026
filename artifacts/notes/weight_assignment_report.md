# Weight Assignment Methods Report - Current Status

## Executive Summary

**Key Finding**: The referenced weight assignment sections (`\ref{sec:weights_SBERT}` and `\ref{sec:weights_LLM}`) do not currently exist in the repository. This report documents the current state of weight assignment methodology and identifies this as a critical gap.

## Current Weight Assignment Approach

### Existing Method: Heuristic-Based Assignment

Based on the main paper (`text_main_v2.tex`, Section 3.2.3), the current system uses **linguistic heuristics**:

```
- "almost always" → w ≈ 0.9
- "typically" → w ≈ 0.7
- "sometimes" → w ≈ 0.5
- "rarely" → w ≈ 0.2
```

**Characteristics:**
- **Approach**: Rule-based mapping from hedge words to confidence scores
- **Input**: Linguistic hedge strength in natural language
- **Output**: Fixed confidence weights w ∈ (0,1)
- **Advantages**: Simple, interpretable, fast
- **Limitations**:
  - No context sensitivity
  - Domain-agnostic (ignores medical vs legal differences)
  - No learning from data
  - Crude discretization of confidence space

## Missing Weight Assignment Methods

### Expected Method 1: SBERT-Based Assignment
**Status**: Referenced but not implemented

**Anticipated Characteristics** (based on SBERT literature):
- **Approach**: Sentence-BERT embeddings for semantic similarity
- **Input**: Constraint text and reference certainty examples
- **Output**: Learned confidence weights based on semantic similarity
- **Advantages**:
  - Context-aware semantic understanding
  - Captures nuanced linguistic variations
  - Pre-trained on large corpora
- **Potential Limitations**:
  - Computationally more expensive
  - Requires reference certainty corpus
  - May not capture domain-specific hedging patterns

### Expected Method 2: LLM-Based Assignment
**Status**: Referenced but not implemented

**Anticipated Characteristics** (based on LLM capabilities):
- **Approach**: Large language model direct confidence estimation
- **Input**: Full context + constraint text
- **Output**: LLM-generated confidence scores with reasoning
- **Advantages**:
  - Full context awareness
  - Can handle complex linguistic patterns
  - Explanable through chain-of-thought
  - Domain-adaptable through prompting
- **Potential Limitations**:
  - Computationally expensive
  - Potential hallucination/calibration issues
  - Requires careful prompt engineering
  - Less reproducible than deterministic methods

## Critical Gaps in Current Implementation

### 1. Missing Sections in Appendix
- No `\ref{sec:weights_SBERT}` section exists
- No `\ref{sec:weights_LLM}` section exists
- Current appendix only contains FOL comparison and usage modes

### 2. Incomplete Code Implementation
- `weights.py` file is empty (only contains comment)
- No SBERT integration code
- No LLM-based weight assignment implementation
- Main paper claims these methods exist but they are not implemented

### 3. Experimental Validation Gap
- Paper reports results with "soft constraints" but doesn't specify which weight assignment method was used
- No comparative evaluation of the three weight assignment approaches
- Missing ablation study on weight assignment methods

## Recommendations for Repository Update

### Immediate Actions Required
1. **Implement Missing Sections**: Add `sec:weights_SBERT` and `sec:weights_LLM` to appendix
2. **Code Implementation**: Develop the three weight assignment methods in `weights.py`
3. **Experimental Validation**: Compare all three approaches on benchmark datasets
4. **Documentation**: Update main paper to specify which method was used for reported results

### Proposed Comparison Framework
```
Method          | Accuracy | Speed | Context-Aware | Reproducible | Domain-Adaptive
----------------|----------|-------|---------------|--------------|----------------
Heuristic       | Baseline | Fast  | No            | Yes          | No
SBERT-based     | +X%      | Med   | Partial       | Yes          | Limited
LLM-based       | +Y%      | Slow  | Full          | Moderate     | Yes
```

## Impact on Project Status

**Current Status**: The paper makes claims about weight assignment methods that are not implemented or evaluated. This represents a significant gap between reported methodology and actual implementation.

**Priority**: **High** - This affects the reproducibility and validity of the soft constraint results reported in the main paper.

**Next Steps**: Implement both missing weight assignment methods and conduct comparative evaluation before finalizing the paper submission.