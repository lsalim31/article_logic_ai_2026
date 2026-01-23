```
logic-aware-extraction/
│
├── README.md
├── requirements.txt
├── setup.py
│
├── logify/                     # Text → Logified Structure
│   ├── init.py
│   ├── openIE_extractor.py     # Given text, extracts a list of linguistic structured triples
│   ├── logic_converter.py      # Given text and structured triples, extract primitive propositions, their translations, and (hard/soft) constraints
│   ├── weights.py              # Assign weights
│   ├── schema.py               # A dictionary from P_i to the actual sentences from the text.
│   └── update.py               # Add new text/propositions/constraints (not  a priority)
│
├── logic_solver/               # All logic calculations
│   ├── init.py
│   ├── encoding.py             # Propositions → Logic software (e.g., Max-SAT)
│   └── maxsat.py               # Solver interface
│
├── interface/                  # User-LLM interactions
│   ├── init.py
│   ├── translate.py            # NL query → formal
│   ├── interpret.py            # Solver output → NL
│   └── refine.py               # Self-refinement
│
├── outputs/
│   ├── logified/
│   └── results/
│
└── experiments/
```
