# Bibliography Analysis Report: Logify Project
**Date:** January 21, 2026
**Analysis of:** Key references from the neuro-symbolic reasoning project

## Executive Summary

This report analyzes the key references cited in the Logify project - a neuro-symbolic AI framework that combines Large Language Models (LLMs) with symbolic solvers for faithful logical reasoning over natural language text. The analysis focuses on identifying overlaps with our project and extracting relevant results that can improve our implementation.

---

## Paper-by-Paper Analysis

### 1. Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning
**Authors:** Pan, Liangming et al. (EMNLP 2023)
**Citation:** `pan2023logiclm`

#### (i) Overlaps with Our Project
- **Direct overlap:** Logic-LM is the most closely related work to our Logify system
- **Same goal:** Combining LLMs with symbolic solvers for faithful logical reasoning
- **Translation approach:** Both systems translate natural language problems into symbolic formulations
- **Solver integration:** Both use deterministic solvers (logic programs, FOL, CSP, SAT)
- **Self-refinement:** Both implement error correction loops for query translation

#### (ii) Relevant Results for Our Project
- **Performance benchmark:** Logic-LM achieves significant gains over chain-of-thought prompting
- **Per-query formalization:** Logic-LM formalizes problems per query (contrast: our approach logifies once, queries many)
- **Hard constraints only:** Logic-LM treats all constraints as hard (improvement opportunity: our soft constraints)
- **Execution rates:** Logic-LM shows 85.8% on FOLIO, 99% on ProofWriter - our system achieves 93.2% and 99.6% respectively
- **Self-refinement value:** Demonstrated importance of error correction in symbolic translation

---

### 2. LINC: A Neurosymbolic Approach for Logical Reasoning by Combining Language Models with First-Order Logic Provers
**Authors:** Olausson, Theo X. et al. (EMNLP 2023)
**Citation:** `olausson2023linc`

#### (i) Overlaps with Our Project
- **Neuro-symbolic architecture:** Both combine neural and symbolic components
- **FOL integration:** LINC focuses on first-order logic with Prover9
- **Error analysis:** Both systems analyze failure modes in translation/reasoning
- **Per-query approach:** Like Logic-LM, LINC formalizes per query

#### (ii) Relevant Results for Our Project
- **FOL complexity issues:** LINC's error analysis shows most failures due to FOL representation choices
- **Reliability trade-off:** Confirms our decision to use propositional logic for better reliability
- **Execution rate drops:** FOL-based approaches show degraded performance (86% vs 99% for propositional)
- **Error mode insights:** Detailed failure analysis can inform our refinement strategies
- **Prover9 integration patterns:** Technical approaches for theorem prover interfaces

---

### 3. FOLIO: Natural Language Reasoning with First-Order Logic
**Authors:** Han, Simeng et al. (EMNLP 2024)
**Citation:** `han2024folio`

#### (i) Overlaps with Our Project
- **Evaluation dataset:** FOLIO is one of our benchmark datasets (1,430 examples)
- **Logical reasoning focus:** Tests natural language to logic translation and reasoning
- **FOL representation:** Dataset provides FOL formulations for comparison

#### (ii) Relevant Results for Our Project
- **Benchmark performance:** Our system achieves 85.2% on FOLIO vs Logic-LM's 78.9%
- **FOL vs propositional trade-offs:** Dataset shows where FOL is necessary vs where propositional suffices
- **Human annotation quality:** Provides gold standard for evaluation
- **Error patterns:** Analysis of common mistakes in NL-to-logic translation
- **Reasoning depth evaluation:** Tests multi-step inference capabilities

---

### 4. ProofWriter: Generating Implications, Proofs, and Abductive Statements over Natural Language
**Authors:** Tafjord, Oyvind et al. (ACL 2021)
**Citation:** `tafjord2021proofwriter`

#### (i) Overlaps with Our Project
- **Synthetic reasoning dataset:** ProofWriter is our benchmark for deductive reasoning
- **Depth-5 subset:** We use 600 examples testing reasoning chains
- **Propositional-like structure:** Aligns with our propositional logic approach

#### (ii) Relevant Results for Our Project
- **Execution rate:** 99% execution rate shows propositional approaches are more reliable
- **Reasoning depth:** Tests systematic degradation of performance with reasoning complexity
- **Our performance:** 87.4% accuracy vs Logic-LM's 79.7% (+7.7% improvement)
- **Depth analysis:** Our system maintains better performance across all reasoning depths
- **Synthetic data generation:** Techniques for creating training/evaluation data

---

### 5. PAL: Program-aided Language Models
**Authors:** Gao, Luyu et al. (ICML 2023)
**Citation:** `gao2023pal`

#### (i) Overlaps with Our Project
- **Tool-augmented LLMs:** Both systems augment LLMs with external tools
- **Faithful computation:** Both ensure correctness through external symbolic systems
- **Separation of concerns:** LLM for interface, external tool for computation

#### (ii) Relevant Results for Our Project
- **Code execution paradigm:** Use code/symbolic execution for reliable computation
- **Interface design patterns:** How to structure LLM-tool interactions
- **Arithmetic reasoning success:** Demonstrates value of offloading computation
- **Error handling:** Strategies for managing execution failures
- **Performance improvements:** Significant gains over pure LLM approaches

---

### 6. SatLM: Satisfiability-Aided Language Models Using Declarative Prompting
**Authors:** Ye, Xi et al. (NeurIPS 2023)
**Citation:** `ye2023satlm`

#### (i) Overlaps with Our Project
- **SAT solver integration:** Both use SAT/Max-SAT solvers
- **Declarative approach:** Both translate problems to declarative formulations
- **LLM-solver combination:** Similar architectural pattern

#### (ii) Relevant Results for Our Project
- **SAT encoding techniques:** Methods for translating problems to SAT
- **Solver interface patterns:** How to structure LLM-SAT solver interactions
- **Declarative prompting:** Techniques for getting LLMs to produce logical formulations
- **Performance on satisfiability:** Specialized techniques for SAT problems
- **Error handling in SAT context:** Managing unsatisfiable formulas

---

### 7. ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts
**Authors:** Koreeda, Yuta and Manning, Christopher (EMNLP 2021)
**Citation:** `koreeda2021contractnli`

#### (i) Overlaps with Our Project
- **Document-level inference:** Our system is designed for reasoning over long documents
- **Legal document analysis:** Contracts are a key application domain
- **Scattered evidence:** Tests reasoning when constraints are distributed across text

#### (ii) Relevant Results for Our Project
- **Long document challenges:** Shows performance degradation on longer documents
- **Our performance:** 79.8% vs Logic-LM's 67.3% (+12.5% improvement)
- **Document length analysis:** Our system remains stable across document lengths (-4.2% degradation vs -16.4% for baselines)
- **Legal reasoning patterns:** Domain-specific constraints and reasoning patterns
- **Evaluation methodology:** How to assess document-level reasoning

---

### 8. Weighted Max-SAT References (MiniMaxSat)
**Authors:** Heras, Federico et al. (SAT 2007, JAIR 2008)
**Citations:** `heras2007minimaxsat`, `heras2008minimaxsat`

#### (i) Overlaps with Our Project
- **Weighted Max-SAT solver:** Our system uses weighted Max-SAT as the core reasoning engine
- **Soft constraints:** Both handle weighted/soft constraints
- **Optimization framework:** Both solve optimization problems over logical formulas

#### (ii) Relevant Results for Our Project
- **Solver performance:** Efficiency benchmarks for weighted Max-SAT
- **Algorithm techniques:** Specific algorithmic improvements for weighted problems
- **Implementation details:** How to structure weighted Max-SAT problems
- **Complexity analysis:** Theoretical bounds and practical performance
- **Integration patterns:** How to use Max-SAT solvers in larger systems

---

### 9. Algebraic Model Counting
**Authors:** Kimmig, Angelika et al. (JAL 2017)
**Citation:** `KimmigVanDenBroeckDeRaedt2017`

#### (i) Overlaps with Our Project
- **Model counting:** Our system uses weighted model counting for probability computation
- **Algebraic approach:** Both use algebraic structures for reasoning
- **Semiring framework:** Generalizes weighted reasoning approaches

#### (ii) Relevant Results for Our Project
- **Theoretical foundations:** Algebraic structures for probabilistic reasoning
- **Weighted model counting:** Algorithms for computing probabilities over models
- **Semiring generalization:** Framework for different types of weights/confidences
- **Complexity results:** Computational complexity of model counting problems
- **Practical algorithms:** Efficient methods for approximate model counting

---

### 10. Assumption-based Truth Maintenance System (ATMS)
**Authors:** de Kleer, Johan (AI 1986)
**Citation:** `deKleer1986`

#### (i) Overlaps with Our Project
- **Multiple consistent contexts:** ATMS represents multiple consistent interpretations
- **Constraint-based reasoning:** Both handle evolving constraints
- **Consistency maintenance:** Both ensure logical consistency

#### (ii) Relevant Results for Our Project
- **Compact representation:** Techniques for representing multiple consistent interpretations
- **Incremental updates:** How to efficiently update representations as constraints change
- **Assumption management:** Handling contradictory or uncertain assumptions
- **Algorithmic foundations:** Classical algorithms for consistency maintenance
- **Conceptual parallel:** Our ring homomorphisms are similar to ATMS environments

---

## Key Findings and Recommendations

### 1. Competitive Advantages Identified
- **Logify-once approach:** Our pre-processing strategy significantly outperforms per-query formalization
- **Soft constraints:** Our weighted constraint approach provides better calibrated confidence
- **Document-level reasoning:** Superior performance on long documents with scattered evidence
- **Propositional reliability:** Strategic choice of propositional logic improves execution rates

### 2. Technical Improvements from Literature
- **Self-refinement loops:** Critical for improving query translation (Logic-LM, LINC)
- **Schema-based translation:** Structured vocabulary significantly aids LLM translation (+10.4%)
- **Incremental solver updates:** Max-SAT solvers can handle incremental clause addition
- **Error analysis patterns:** Common failure modes from LINC and Logic-LM inform our refinement

### 3. Missing Capabilities to Address
- **Learned weight assignment:** Current heuristic weights could benefit from data-driven approaches
- **Human-in-the-loop correction:** ATMS-style assumption management for interactive refinement
- **Richer constraint types:** Beyond Boolean constraints, modal or temporal constraints
- **Cross-document reasoning:** Extending to multiple related documents

### 4. Benchmarking Gaps
- **Calibration evaluation:** Need systematic evaluation of confidence calibration
- **Ablation studies:** More comprehensive component analysis (following our Table 6)
- **Scalability analysis:** Performance on very long documents (>10K tokens)
- **Domain adaptation:** Performance across different text types beyond legal/medical

---

## Conclusion

The analyzed literature strongly validates our Logify approach while identifying specific areas for improvement. Our system demonstrates clear advantages in the "logify once, query many" paradigm, soft constraint handling, and document-level reasoning. The key technical insights from related work - particularly around self-refinement, schema-based translation, and weighted reasoning - provide concrete directions for enhancing our system's performance and reliability.

---

**Report prepared for:** Logify Project Team
**Next steps:** Implementation of identified improvements and extended benchmarking