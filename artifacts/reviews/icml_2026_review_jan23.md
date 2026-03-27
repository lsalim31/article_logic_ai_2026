# ICML 2026 Review: Logify — Faithful Logical Reasoning via Text Logification

**Review Date:** January 23, 2026
**Manuscript Stage:** Mid-to-Late Stage Draft
**Reviewer Confidence:** 4/5

---

## Summary

This paper proposes **Logify**, a neuro-symbolic framework for faithful logical reasoning over natural language text. The core idea is to "logify" a document once—extracting atomic propositions, hard constraints (must hold), and soft constraints (defeasible tendencies)—then answer queries via weighted Max-SAT solvers. The pipeline consists of two stages: (1) OpenIE triple extraction using Stanford CoreNLP/Stanza with coreference resolution, and (2) LLM-based logic conversion with few-shot prompting. Crucially, soft constraint weights are assigned separately via an SBERT+NLI evidence retrieval pipeline rather than by the LLM. The algebraic framework represents the text as a Boolean ring quotiented by hard constraints, with soft constraints inducing a probability distribution over consistent "readings." Experiments on FOLIO, ProofWriter, ContractNLI, and a new MedGuide dataset show improvements over Logic-LM and chain-of-thought baselines.

---

## Strengths

1. **Novel "logify once, query many" paradigm**: Unlike Logic-LM and LINC which formalize per-query, this approach amortizes extraction cost across multiple queries—a practical advantage for document-level reasoning (contracts, guidelines). The 6× speedup for incremental updates (Table 7) demonstrates practical value.

2. **Principled hard/soft constraint distinction**: The separation of hard constraints (Boolean ring ideal) from soft constraints (weighted distribution over readings) is theoretically motivated and empirically beneficial (+8.3% on MedGuide when adding soft constraints, Table 5). This addresses a real limitation of prior work that treats all constraints as hard.

3. **Decoupled weight assignment**: The SBERT+NLI pipeline for weight assignment (Appendix A.1) is methodologically sound—separating "what is defeasible" (LLM) from "how strongly supported" (retrieval+NLI) avoids unreliable LLM confidence estimation. The log-sum-exp pooling is a sensible choice over brittle max-pooling.

4. **Strong experimental results**: Consistent improvements across datasets (+6.3% FOLIO, +7.7% ProofWriter, +12.5% ContractNLI over Logic-LM). The document-length analysis (Table 4) showing stability on long documents (−4.2% vs. −16.4% for baselines) validates the core thesis.

5. **Excellent reproducibility potential**: The appendix provides the complete prompt (A.5), a worked exemplar (A.6), OpenIE configuration (A.4), and default hyperparameters. This level of detail exceeds typical ICML submissions.

6. **Clean two-stage pipeline design**: The OpenIE → LLM architecture leverages classical NLP (coreference resolution, dependency parsing) as scaffolding for LLM-based semantic analysis—a sensible hybrid that addresses known LLM weaknesses in entity tracking.

---

## Weaknesses

### Major Issues

1. **Incomplete experimental results (Critical)**: Line 57 states "[TBD: main results]" in the contributions. Several key details are missing:
   - No standard deviation or confidence intervals reported
   - No statistical significance tests
   - MedGuide dataset is created by the authors but not described sufficiently (50 examples is small; how were ground truth labels determined? What is the inter-annotator agreement?)

2. **Questionable baseline fairness**: The paper compares Logify (GPT-4) against Logic-LM but doesn't specify:
   - Which LLM version Logic-LM uses (the original paper used text-davinci-003 and GPT-4)
   - Whether prompts are identical where possible
   - Whether Logic-LM's self-refinement is enabled

   Without these details, the +6.3% to +12.5% gains are difficult to interpret.

3. **Missing error analysis**: LINC's error taxonomy (L1-L3, C1-C3) was highly influential. This paper lacks:
   - Categorization of failure modes
   - Analysis of where logification fails (proposition extraction errors vs. constraint extraction errors vs. weight assignment errors)
   - Examples of incorrect outputs

4. **OpenIE contribution unclear**: The paper positions OpenIE as "Stage 1" but doesn't ablate its contribution. Does OpenIE actually help, or is it redundant given GPT-4's capabilities? An ablation removing OpenIE triples would strengthen the paper significantly.

5. **Soft constraint weight calibration not evaluated**: The paper claims weights produce "well-calibrated confidence scores (0.78 correlation)" but:
   - Calibration methodology is not explained (ECE? Reliability diagrams?)
   - 0.78 correlation is reported without context (what would random be? What does Logic-LM achieve?)
   - The claim that weights are "evidence scores, not statistically calibrated probabilities" (Appendix A.1 line 14) seems to contradict the calibration claim

### Minor Issues

6. **Figure placeholders**: Figure 1 caption is "Caption" (line 103), Figure 2 has "TODO: Insert architecture diagram" (line 283). These must be completed.

7. **Algebraic machinery underutilized**: The Boolean ring formulation (Section 2.2) is elegant but the paper never shows it provides advantages over standard CNF encoding. Is Gröbner basis computation actually used? The connection to PolyBoRi (line 85) is mentioned but never exploited.

8. **Limited solver discussion**: The paper mentions RC2, MaxHS, Open-WBO (line 384) but doesn't specify which is used or compare them. For weighted model counting, c2d and D4 are mentioned but actual usage is unclear.

9. **Propositional logic limitation acknowledged but not addressed**: The paper argues propositional logic is more reliable (valid), but doesn't discuss when this limitation matters. ContractNLI likely benefits from FOL (e.g., "all parties" quantification).

---

## Detailed Comments

### Claims and Evidence

| Claim | Evidence | Assessment |
|-------|----------|------------|
| "Logify outperforms Logic-LM by +6.3% on FOLIO" | Table 1 | Numbers present but no significance test; baseline setup unclear |
| "Soft constraints yield better-calibrated confidence" | Table 5, 0.78 correlation | Calibration metric undefined; needs ECE or reliability diagram |
| "Incremental updates are 6× faster" | Table 7 | Convincing, but n=1 scenario (addenda) |
| "Two-stage pipeline improves extraction" | No direct evidence | OpenIE ablation missing |
| "Schema-based translation improves execution rate" | Table 6 | +7.4% to +19.4% gains shown; convincing |

### Relation to Prior Work

**Coverage is good** for:
- Logic-LM, LINC (main baselines)
- Weighted Max-SAT, algebraic model counting
- ATMS (de Kleer)

**Missing citations**:
- [Survey on Open Information Extraction](https://aclanthology.org/2024.findings-emnlp.560/) (EMNLP 2024) — directly relevant to Stage 1
- LLM-Modulo Frameworks (ICML 2024) — tighter neuro-symbolic integration
- [Logically Consistent LMs via Neuro-Symbolic Integration](https://openreview.net/forum?id=7PGluppo4k) — related approach to consistency
- Recent work on [NuWLS](https://ojs.aaai.org/index.php/AAAI/article/view/25505) for weighted partial Max-SAT solving

### Comparison to Reference Papers

**vs. Logic-LM:**

| Aspect | Logic-LM | Logify | Assessment |
|--------|----------|--------|------------|
| Formalization | Per-query | Per-document (once) | ✓ Novel contribution |
| Constraints | All hard | Hard + soft | ✓ Novel contribution |
| Formalisms | Multiple (Pyke, Prover9, Z3) | Propositional only | Mixed—less flexible |
| Self-refinement | Solver errors → LLM | Similar | Incremental improvement |
| Execution rate | 85.8% (FOLIO) | 93.2% (FOLIO) | +7.4% improvement |

**vs. LINC:**

| Aspect | LINC | Logify | Assessment |
|--------|------|--------|------------|
| Logic | FOL | Propositional | Trade-off (less expressive, more reliable) |
| Error analysis | L1-L3 taxonomy | None | Weakness |
| Solver | Prover9 | Max-SAT | Different capabilities |
| Uncertainty | None | Soft constraints | ✓ Novel contribution |

### Neuro-Symbolic Specific Criteria

**Symbolic formulation quality**: Good. The prompt (Appendix A.5) clearly specifies grammar, the exemplar (A.6) demonstrates flattening of FOL-like expressions to propositional logic. The "atomicity" and "independence" principles are well-motivated.

**Solver selection**: Adequate but underspecified. Max-SAT is appropriate for optimization with soft constraints. However, weighted model counting tools (c2d, D4) are mentioned but usage is unclear.

**Integration approach**: Principled. The two-stage pipeline (OpenIE → LLM) is motivated, and the separation of weight assignment from extraction is methodologically sound.

**Faithfulness guarantees**: Conditional. The paper correctly states "if the logification is correct, the answers are provably correct" (line 48-49). The key assumption is extraction fidelity, which is not empirically verified.

---

## Questions for Authors

1. **Q1 (Critical)**: What is the performance when OpenIE triples are removed from Stage 2 input? This ablation would clarify whether OpenIE provides value or is redundant given GPT-4's capabilities. If OpenIE contributes <1% improvement, the two-stage claim is weakened.

2. **Q2 (Critical)**: How was the MedGuide dataset constructed? What are the annotation guidelines, inter-annotator agreement, and can it be released? A 50-example dataset with no provenance details weakens the soft constraints evaluation.

3. **Q3**: What calibration metric is used for the 0.78 correlation claim? Please provide Expected Calibration Error (ECE) and/or reliability diagrams for Logify vs. baselines.

4. **Q4**: Which specific Max-SAT solver is used in experiments? Are results sensitive to solver choice?

5. **Q5**: Can you provide failure examples categorized by error source (proposition extraction, constraint extraction, weight assignment, query translation)? This would significantly strengthen the paper.

6. **Q6**: For ContractNLI, propositional logic cannot express "all parties agree"—how are such quantified statements handled? Are they flattened to finite conjunctions?

---

## Missing Related Work

1. **Jiang et al. (EMNLP 2024)**: "A Survey on Open Information Extraction from Rule-based Model to Large Language Model" — comprehensive survey directly relevant to Stage 1.

2. **Kambhampati et al. (ICML 2024)**: LLM-Modulo Frameworks — argues for tighter bi-directional LLM-verifier integration; relevant to the self-refinement discussion.

3. **LogiCity (NeurIPS 2024)**: Benchmark for neuro-symbolic reasoning in urban simulation; relevant for discussion of evaluation.

4. **Marcondes et al. (2024)**: Neuro-symbolic reasoning with multiple LLMs via FOL — related approach combining multiple LLMs with logical inference.

---

## Minor Issues

1. **Typo (line 406)**: "eveyone" → "everyone"
2. **Incomplete caption** (line 103): Figure 1 caption is "Caption"
3. **TODO comment** (line 283): Architecture diagram missing
4. **Inconsistent notation**: $\Pi_{\mathrm{form}}$ in Definition 1 vs. grounding map terminology elsewhere
5. **Appendix A.1 typo** (line 4): "constrains" → "constraints"
6. **Table 1 missing column**: Header has 4 columns but only 3 data columns

---

## Ethical Concerns

No significant ethical concerns identified. The MedGuide dataset involves medical guidelines but appears to use publicly available excerpts. The paper appropriately notes limitations regarding extraction errors propagating to downstream reasoning.

---

## Scores

| Criterion | Score | Notes |
|-----------|-------|-------|
| **Soundness** | 3/4 | Theoretical framework sound; experimental methodology has gaps |
| **Presentation** | 3/4 | Well-written with excellent appendix; missing figures detract |
| **Contribution** | 3/4 | Genuine contributions but incremental over Logic-LM |

---

## Overall Recommendation

**Overall Score: 5/10 (Borderline Reject → Weak Accept)**

**Confidence: 4/5** — I am familiar with Logic-LM, LINC, and the neuro-symbolic reasoning literature. I checked the theoretical claims and experimental setup carefully.

---

## Justification

This paper presents a well-motivated framework with genuine contributions: the amortized "logify once" approach, the principled hard/soft constraint distinction, and the decoupled weight assignment pipeline. The algebraic formulation is elegant, and the experimental improvements are promising.

However, the paper has significant gaps that prevent a clear accept:
1. **Missing ablations** (especially OpenIE contribution)
2. **Incomplete experimental reporting** (no significance tests, TBD in contributions)
3. **Unfinished figures** (placeholders unacceptable for submission)
4. **Missing error analysis** (critical for neuro-symbolic work)
5. **Questionable baseline fairness** (Logic-LM configuration unclear)

If the authors address these issues—particularly completing the figures, adding the OpenIE ablation, providing statistical significance, and including error analysis—this paper would be a solid accept. The core ideas are strong enough to merit publication with revisions.

---

## Suggestions for Improvement (Prioritized)

### Must Fix Before Submission
1. Complete Figure 1 and Figure 2 with actual diagrams
2. Remove "[TBD: main results]" and finalize contribution statement
3. Add statistical significance tests (bootstrap CI or paired t-test)
4. Specify exact Logic-LM configuration used for comparison
5. Add OpenIE ablation (with/without triples in Stage 2)

### Strongly Recommended
6. Add error analysis with categorized failure examples
7. Define and properly evaluate calibration (ECE, reliability diagram)
8. Expand MedGuide description (annotation process, release plans)
9. Add missing citations (EMNLP 2024 OpenIE survey, LLM-Modulo)
10. Clarify which Max-SAT solver is used and whether results are solver-sensitive

### Nice to Have
11. Show a case where Boolean ring algebra provides advantages over CNF
12. Discuss computational cost (API calls, solver time) vs. baselines
13. Include a human evaluation of logification quality on a sample

---

## Sources Consulted

- [Neuro-Symbolic AI Survey 2024](https://arxiv.org/html/2501.05435v1)
- [LogiCity NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/8196be81e68289d7a9ece21ed7f5750a-Paper-Datasets_and_Benchmarks_Track.pdf)
- [OpenIE Survey EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.560/)
- [Logically Consistent LMs](https://openreview.net/forum?id=7PGluppo4k)
- [NuWLS Max-SAT Solver](https://ojs.aaai.org/index.php/AAAI/article/view/25505)
