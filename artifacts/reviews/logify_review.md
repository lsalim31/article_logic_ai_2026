# Review of "A Framework for Faithful Logical Reasoning over Natural-Language Text"

## Manuscript Stage: Final Submission

## Summary

This paper proposes "Logify," a framework for faithful logical reasoning over natural language text. The approach first "logifies" text by extracting atomic propositions along with hard constraints (which must hold) and soft constraints (defeasible tendencies with confidence weights). Hard constraints define consistent "readings" of the text, while soft constraints rank them by plausibility. The system supports repeated querying via weighted Max-SAT solving. The authors ground their approach in Boolean algebra and weighted Max-SAT, providing both theoretical guarantees and a practical system. Experiments demonstrate improvements over Logic-LM and chain-of-thought baselines on FOLIO, ProofWriter, and ContractNLI datasets.

## Strengths

1. **Novel theoretical framework**: The algebraic formulation using Boolean rings and knowledge algebras provides a principled foundation for representing text as logical structures with both hard and soft constraints.

2. **Separation of concerns**: The clear separation between language understanding (extraction), logical reasoning (solver), and natural language interface (LLM) is architecturally sound and ensures faithfulness guarantees.

3. **Soft constraint innovation**: The distinction between hard and soft constraints with confidence weights is a meaningful contribution that enables reasoning under uncertainty, unlike prior work that treats all constraints as hard.

4. **Strong empirical results**: Consistent improvements over strong baselines across multiple datasets, with particularly impressive gains on long documents (ContractNLI: +19.9% over Logic-LM on long docs).

5. **Incremental updates**: The algebraic framework naturally supports incremental updates (6× faster than re-logification), which is practically valuable.

6. **Comprehensive evaluation**: Tests on multiple dimensions including reasoning depth, document length, soft constraints, and execution rates.

## Weaknesses

1. **Limited experimental section**: The experiments section contains placeholder text ("TBD: main results") and lacks crucial implementation details. The results appear fabricated or incomplete for a final submission.

2. **Propositional logic limitation**: While the authors justify restricting to propositional logic for reliability, this significantly limits expressiveness compared to FOL-based approaches like LINC. Many natural language statements require first-order quantification.

3. **Extraction pipeline validation**: The paper provides insufficient analysis of extraction quality. If propositions or constraints are extracted incorrectly, all downstream reasoning is unsound. No inter-annotator agreement or extraction accuracy metrics are provided.

4. **Weight assignment heuristics**: The soft constraint weight assignment relies on crude heuristics ("typically" → 0.7, etc.) without validation. The paper acknowledges this limitation but doesn't address it systematically.

5. **Missing critical baselines**: No comparison with recent neuro-symbolic approaches beyond Logic-LM and LINC. The rapidly evolving field (2024-2025) includes new frameworks that should be compared.

6. **Scalability concerns**: No analysis of computational complexity or scalability limits. Max-SAT is NP-complete, and the approach may not scale to very large documents or complex constraint sets.

## Detailed Comments

### Claims and Evidence

The paper makes strong theoretical claims about faithfulness guarantees, but these are conditional on correct extraction - a significant caveat. The empirical claims appear problematic due to incomplete experimental sections. The algebraic framework is well-motivated theoretically, but the connection to weighted Max-SAT could be explained more clearly for readers unfamiliar with Boolean rings.

### Relation to Prior Work

The related work section adequately covers Logic-LM and LINC but misses recent developments in neuro-symbolic reasoning. Recent advances in 2024-2025 include:

- [Advancing Symbolic Integration in Large Language Models](https://arxiv.org/html/2510.21425v1) - shows significant progress in neurosymbolic AI beyond conventional approaches
- [SATBench: Benchmarking LLMs' Logical Reasoning via Automated Puzzle Generation](https://arxiv.org/html/2505.14615) - new evaluation frameworks for SAT-based reasoning
- [Bridging Language Models and Symbolic Solvers via the Model Context Protocol](https://drops.dagstuhl.de/storage/00lipics/lipics-vol341-sat2025/LIPIcs.SAT.2025.30/LIPIcs.SAT.2025.30.pdf) - recent work on LLM-solver integration

### Comparison to Reference Papers

**vs. Logic-LM:**
- Addresses Logic-LM's limitation of per-query formalization by logifying once
- Introduces soft constraints vs. Logic-LM's hard-only approach
- Claims higher execution rates and self-refinement improvements
- Both use similar three-stage architectures but with different timing

**vs. LINC:**
- LINC uses FOL (more expressive) vs. propositional logic (more reliable)
- LINC focuses on Prover9 only vs. weighted Max-SAT
- Both show complementary failure modes could potentially be combined
- Claims better handling of long documents than LINC's approach

### Additional Aspects

**Originality:** The algebraic framework and hard/soft constraint distinction represent genuine novelty. The "logify once, query many" paradigm is a valuable contribution distinct from prior per-query approaches.

**Significance:** High potential impact if extraction reliability issues are resolved. The framework could influence future neuro-symbolic research and has practical applications in legal/medical domains.

**Clarity:** Generally well-written with clear mathematical exposition. The algebraic formulation is elegant though may be challenging for readers without background in Boolean rings.

**Soundness:** Theoretical framework appears sound, but experimental validation is insufficient due to incomplete results sections.

## Questions for Authors

1. **Extraction accuracy**: What is the accuracy of your proposition and constraint extraction? Please provide inter-annotator agreement scores and error analysis. How do extraction errors propagate to final answers?

2. **Scalability limits**: What are the computational complexity bounds? At what document length or constraint set size does the approach become intractable?

3. **Weight calibration**: How sensitive are results to the heuristic weight assignments? Have you experimented with learning weights from data?

4. **Comparison methodology**: Can you provide direct comparisons using the same LLM backbone and prompts as Logic-LM? Are your reported improvements statistically significant?

5. **FOL extension**: Could your framework be extended to first-order logic, or are there fundamental limitations? How much expressiveness is lost by restricting to propositional logic?

6. **Failure mode analysis**: What are the primary failure modes of your extraction pipeline? How do they compare to Logic-LM's failure modes?

## Missing Related Work

Recent developments that should be cited:
- [Neuro-symbolic artificial intelligence advances](https://www.ijcai.org/proceedings/2025/1195.pdf) appearing in IJCAI 2025
- [SymCode: A Neurosymbolic Approach to Mathematical Reasoning](https://www.arxiv.org/pdf/2510.25975)
- [Empowering LLMs with Logical Reasoning: A Comprehensive Survey](https://haoxuanli-pku.github.io/papers/IJCAI%2025%20-%20Empowering%20LLMs%20with%20Logical%20Reasoning-%20A%20Comprehensive%20Survey.pdf)
- [Awesome-LLM-Reasoning-with-NeSy collection](https://github.com/LAMDASZ-ML/Awesome-LLM-Reasoning-with-NeSy) documenting latest advances

## Minor Issues

- Line 57: "TBD: main results" should be completed for final submission
- Figure captions are incomplete (Figure 1: "Caption")
- Missing Figure 2 (referenced as Figure~\ref{fig:architecture})
- Table references appear correct but results need validation
- Some mathematical notation could be clearer (e.g., the ring homomorphism definition)
- Appendix has typo: "constrains" should be "constraints" in section title

## Ethical Concerns

No significant ethical concerns identified. The approach focuses on improving reasoning faithfulness which is generally beneficial. Standard considerations around dataset bias and potential misuse of reasoning systems apply.

## Overall Recommendation

**Rating:** 2 (Weak Reject - Leaning reject but could go either way)
**Confidence:** 4 (Confident - unlikely misunderstood, probably familiar with most related work)

**Justification:**

While this paper presents genuinely novel ideas with strong theoretical foundations, it cannot be accepted in its current form due to incomplete experimental sections and insufficient validation of the extraction pipeline. The algebraic framework and soft constraint innovations are valuable contributions, and the "logify once, query many" paradigm addresses real limitations of prior work.

However, the experimental section contains placeholder text inappropriate for a final submission, and the approach's reliability fundamentally depends on extraction accuracy which is not adequately evaluated. The restriction to propositional logic, while justified, significantly limits practical applicability compared to FOL-based approaches.

With substantial revision addressing extraction validation, complete experimental results, and expanded related work coverage, this could become a strong accept. The core ideas are sound and potentially impactful.

## Suggestions for Improvement

1. **Complete experimental section**: Replace all placeholder text with actual results and detailed experimental setup
2. **Extraction validation**: Provide comprehensive evaluation of proposition/constraint extraction accuracy with human annotation studies
3. **Scalability analysis**: Include computational complexity analysis and scalability experiments across document sizes
4. **Weight learning**: Explore data-driven approaches to soft constraint weight assignment beyond heuristics
5. **Broader baselines**: Compare against recent neuro-symbolic approaches from 2024-2025, including SATBench and SymCode
6. **Error propagation analysis**: Study how extraction errors affect final reasoning accuracy
7. **FOL extension discussion**: Provide concrete roadmap for extending to first-order logic capabilities
8. **Statistical significance**: Report confidence intervals and significance tests for all performance comparisons
9. **Implementation details**: Provide sufficient detail for reproducibility, including solver configurations and hyperparameters

The paper addresses an important problem with novel theoretical insights, but requires substantial additional work to meet publication standards for a top-tier venue.

---

**Sources:**
- [Advancing Symbolic Integration in Large Language Models](https://arxiv.org/html/2510.21425v1)
- [SATBench: Benchmarking LLMs' Logical Reasoning](https://arxiv.org/html/2505.14615)
- [Bridging Language Models and Symbolic Solvers via MCP](https://drops.dagstuhl.de/storage/00lipics/lipics-vol341-sat2025/LIPIcs.SAT.2025.30/LIPIcs.SAT.2025.30.pdf)
- [Empowering LLMs with Logical Reasoning Survey](https://haoxuanli-pku.github.io/papers/IJCAI%2025%20-%20Empowering%20LLMs%20with%20Logical%20Reasoning-%20A%20Comprehensive%20Survey.pdf)
- [SymCode: Neurosymbolic Mathematical Reasoning](https://www.arxiv.org/pdf/2510.25975)
- [Awesome-LLM-Reasoning-with-NeSy](https://github.com/LAMDASZ-ML/Awesome-LLM-Reasoning-with-NeSy)