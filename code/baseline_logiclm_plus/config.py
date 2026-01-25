"""
Configuration module for LOGIC-LM++ baseline.

This module contains:
- Model configuration (model name, temperature, max tokens)
- Refinement hyperparameters (max iterations, num candidates)
- Solver configuration (timeout, solver choice)
- Prompt templates for formalization, refinement, and pairwise comparison

Design decisions:
- SAT formalization only (matches propositional system)
- JSON-structured LLM outputs for reliable parsing
- Fixed 3 refinement iterations (faithful to paper)
- No early stopping (as-published methodology)
"""

# Model configuration
MODEL_NAME = "openai/gpt-4"
TEMPERATURE = 0
MAX_TOKENS = 2048

# Refinement parameters
MAX_REFINEMENT_ITERATIONS = 3
NUM_REFINEMENT_CANDIDATES = 2
SOLVER_TIMEOUT = 30  # seconds

# Formalization target
SYMBOLIC_TARGET = "SAT"  # Only SAT supported

# Prompt templates
FORMALIZATION_PROMPT = """You are a formal logician. Convert the following natural language text and query into a propositional logic (SAT) formulation.

TEXT:
{text}

QUERY:
{query}

Instructions:
1. Extract atomic propositions (assign each a unique variable like P1, P2, etc.)
2. Express all constraints as CNF clauses in DIMACS format
3. Identify which variable/literal represents the query
4. Use positive integers for variables (e.g., 1 for P1, 2 for P2)
5. Use negative integers for negations (e.g., -1 for NOT P1)

Output format (JSON):
{{
    "variables": {{"P1": "description of P1", "P2": "description of P2", ...}},
    "clauses": [[1, -2], [2, 3], ...],
    "query_literal": 5
}}

Be precise and complete. Include ALL constraints from the text."""

REFINEMENT_PROMPT = """You previously formalized a logical reasoning problem. The current formulation may have issues.

ORIGINAL TEXT:
{text}

ORIGINAL QUERY:
{query}

CURRENT FORMULATION:
{current_formulation}

FEEDBACK:
{error_feedback}

Generate {num_candidates} improved alternative formulations that address potential issues. Each should be complete and valid.

Output {num_candidates} JSON objects, one per line, in the same format as the original formalization."""

PAIRWISE_COMPARISON_PROMPT = """Compare two candidate logical formulations of the same problem.

ORIGINAL TEXT:
{text}

ORIGINAL QUERY:
{query}

FORMULATION A:
{formulation_a}

FORMULATION B:
{formulation_b}

Which formulation (A or B) more faithfully represents the original text and query?

Consider:
- Completeness (all constraints captured)
- Correctness (no spurious constraints)
- Precision (variables well-defined)

Output ONLY: A or B"""
