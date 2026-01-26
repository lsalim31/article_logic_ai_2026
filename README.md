# Neuro-Symbolic Reasoning with Logify

This repository implements a neuro-symbolic reasoning framework that translates natural language documents into propositional logic with hard and soft constraints, enabling efficient "logify once, query many" reasoning via symbolic solvers.

## Repository Structure

```
repo/
│
├── README.md
├── article/                    # Paper manuscript and appendix
│   ├── appendix.tex
│   └── main_tex.tex (if exists)
│
├── code/                       # Implementation and baselines
│   ├── main.py                # Main entry point for Logify system
│   │
│   ├── from_text_to_logic/    # Text → Logified Structure (Stage 1)
│   │   ├── openie_extractor.py     # Stanford CoreNLP OpenIE extraction
│   │   ├── logic_converter.py      # LLM-based NL → propositional logic
│   │   ├── propositions.py         # Atomic proposition management
│   │   ├── constraints.py          # Hard/soft constraint handling
│   │   ├── weights.py              # SBERT + NLI weight assignment
│   │   ├── schema.py               # Proposition-text mapping
│   │   └── update.py               # Incremental knowledge updates
│   │
│   ├── logic_solver/          # Symbolic Reasoning (Stage 2)
│   │   ├── encoding.py             # Propositional logic → Max-SAT encoding
│   │   └── maxsat.py               # Max-SAT solver interface
│   │
│   ├── interface_with_user/   # Query Processing (Stage 3)
│   │   ├── translate.py            # NL query → formal query
│   │   ├── interpret.py            # Solver output → NL answer
│   │   └── refine.py               # Self-refinement loops
│   │
│   ├── baseline_rag/          # Baseline: Reasoning LLM + RAG
│   │   ├── main.py                 # RAG pipeline orchestration
│   │   ├── chunker.py              # Document chunking (512 tokens, 50 overlap)
│   │   ├── retriever.py            # SBERT-based semantic retrieval
│   │   ├── reasoner.py             # Chain-of-Thought LLM reasoning
│   │   ├── evaluator.py            # Metrics computation
│   │   ├── config.py               # Fixed hyperparameters + improved CoT prompt
│   │   └── USAGE_GUIDE.md          # Detailed usage instructions
│   │
│   ├── baseline_logiclm_plus/ # Baseline: Logic-LM++ (ACL 2024)
│   │   ├── main.py                 # Logic-LM++ pipeline
│   │   ├── formalizer.py           # NL → FOL formalization
│   │   ├── refiner.py              # Multi-step refinement + backtracking
│   │   ├── solver_interface.py     # Prover9/Z3 theorem proving
│   │   ├── evaluator.py            # Execution rate (Er) + accuracy (Ea)
│   │   └── config.py               # Refinement hyperparameters + prompts
│   │
│   ├── experiments/           # Experimental runs and outputs
│   ├── outputs/               # Logified structures and results
│   └── prompts/               # Prompt templates
│
├── artifacts/                 # Generated artifacts (if any)
└── important_references/      # Key papers and citations
```

## Quick Start

### 1. Logify System (Main Contribution)

**Logify once, query many:**

```bash
cd code
python main.py from_text_to_logic --text "document.txt"
python main.py query --query "Is X true?"
```

See `code/QUICK_START.md` for detailed instructions.

### 2. Baseline: RAG + Reasoning LLM

**Retrieve and reason with Chain-of-Thought:**

```bash
cd code/baseline_rag
export OPENAI_API_KEY="your-key"
python main.py --dataset folio --output results.json
```

See `code/baseline_rag/USAGE_GUIDE.md` for full documentation.

### 3. Baseline: Logic-LM++

**Iterative symbolic refinement with backtracking:**

```bash
cd code/baseline_logiclm_plus
python main.py --dataset folio --output results.json
```

See `code/baseline_logiclm_plus/README.md` for configuration details.

## Key Features

### Logify Framework
- **OpenIE + LLM extraction**: Stanford CoreNLP triples + GPT-4 logic conversion
- **Propositional logic**: Atomic propositions, hard constraints, soft constraints (with weights)
- **Algebraic reasoning**: Boolean ring formulation for consequence testing
- **Max-SAT solving**: Weighted constraint satisfaction for optimal readings
- **Evidence-based weighting**: SBERT retrieval + NLI reranking for soft constraint confidence

### RAG Baseline
- **SBERT retrieval**: Semantic chunk retrieval (top-k=5, 512 tokens/chunk)
- **Improved CoT prompt**: Emphasizes logical relationships, constraint identification, and gap acknowledgment
- **Multi-dataset support**: FOLIO, ProofWriter, ContractNLI
- **Structured output**: `**Reasoning:** ... **Answer:** True/False/Unknown`

### Logic-LM++ Baseline
- **FOL formalization**: First-order logic via LLM translation
- **Self-refinement**: Context-rich prompts with problem statement
- **Backtracking agent**: Semantic comparison prevents degradation
- **Theorem proving**: Prover9/Z3 symbolic solvers

## Datasets

| Dataset | Task | Labels | Source |
|---------|------|--------|--------|
| **FOLIO** | FOL reasoning | True/False/Uncertain | `yale-nlp/FOLIO` |
| **ProofWriter** | Proof generation | Proved/Disproved/Unknown | `allenai/proofwriter` |
| **ContractNLI** | Contract entailment | Entailed/Contradicted/NotMentioned | `koreeda/contractnli` |

## Requirements

### Core System
```bash
pip install stanza sentence-transformers openai z3-solver
```

### Baselines
```bash
pip install sentence-transformers openai datasets numpy
```

See `code/requirements.txt` and baseline-specific requirements for complete lists.

## Documentation

- **Paper**: `article/appendix.tex` (detailed methodology, prompts, algorithms)
- **Logify System**: `code/QUICK_START.md`, `code/HOW_TO_TEST.md`
- **RAG Baseline**: `code/baseline_rag/USAGE_GUIDE.md`
- **Logic-LM++ Baseline**: `code/baseline_logiclm_plus/README.md`
- **Implementation Status**: `code/INTEGRATION_STATUS.md`

## Citation

If you use this code, please cite the accompanying paper (details in `article/`).

## License

See LICENSE file for details.
