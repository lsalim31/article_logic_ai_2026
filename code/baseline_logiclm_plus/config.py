"""
Configuration module for LOGIC-LM++ baseline.

This module contains:
- Model configuration (model name, temperature, max tokens)
- Refinement hyperparameters (max iterations, num candidates)
- Solver configuration (timeout, solver choice)
- Prompt templates for formalization, refinement, and pairwise comparison

Design decisions (from Logic-LM++ paper, ACL 2024):
- First-order logic (FOL) formalization for FOLIO, AR-LSAT
- Propositional logic formalization for LogicBench propositional tasks
- JSON-structured LLM outputs for reliable parsing
- Variable iterations (tested 0-4 in paper, Figure 3)
- Early stopping via backtracking agent (prevents semantic degradation)
- Context-rich refinement prompts (no few-shots, include problem statement)

Note on logic types:
- Propositional logic uses ground atoms (P, Q, R) without quantifiers
- FOL uses predicates with arguments and quantifiers (∀x, ∃x)
- The choice affects both formalization prompts and solver behavior
"""

# Model configuration
# WARNING: DO NOT CHANGE THIS MODEL. EVER.
# The baseline results are calibrated to gpt-5-nano and changing this will invalidate all comparisons.
MODEL_NAME = "gpt-5-nano"
TEMPERATURE = 0
MAX_TOKENS = 2048

# Refinement parameters
# Paper tests 0-4 iterations (Figure 3, page 4). Default to 4 for comprehensive refinement.
MAX_REFINEMENT_ITERATIONS = 4
NUM_REFINEMENT_CANDIDATES = 2  # Paper uses N=2 for pairwise comparison
SOLVER_TIMEOUT = 30  # seconds

# Backtracking parameters
# If backtracking reverts this many consecutive times, stop early (no improvement possible)
MAX_CONSECUTIVE_BACKTRACKS = 2

# Formalization target
# Paper uses Prover9 (FOL theorem prover) and Z3 (SMT solver), not SAT
SYMBOLIC_TARGET = "FOL"  # First-order logic (Prover9/Z3)

# Prompt templates
FORMALIZATION_PROMPT = """You are a formal logician. Convert the following natural language text and query into first-order logic (FOL) formulation.

TEXT:
{text}

QUERY:
{query}

Instructions:
1. Define predicates for each relation (e.g., Student(x), Human(x), Teaches(x))
2. Formalize the text as FOL premises using quantifiers (∀, ∃) and connectives (∧, ∨, →, ¬)
3. Express the query as a FOL conclusion to be tested
4. Use standard FOL syntax compatible with Prover9/Z3

Output format (JSON):
{{
    "predicates": {{"Student(x)": "x is a student", "Human(x)": "x is a human", ...}},
    "premises": ["∀x (Student(x) → Human(x))", "∃x (Young(x) ∧ Student(x))", ...],
    "conclusion": "Human(rose) ∨ Manager(jerry)"
}}

Be precise and complete. Include ALL constraints from the text. Ensure semantic correctness, not just syntactic validity."""

REFINEMENT_PROMPT = """You previously formalized a logical reasoning problem. The current formulation has failed.

ORIGINAL PROBLEM STATEMENT:
{text}

ORIGINAL QUESTION:
{query}

YOUR CURRENT FORMULATION:
{current_formulation}

SOLVER FEEDBACK (error or failure reason):
{error_feedback}

INSTRUCTIONS:
Self-reflect on why your formulation failed. The issue is likely SEMANTIC (incorrect translation from natural language), not just syntactic.

Common semantic errors to check:
- Misinterpreting negations (e.g., "No young person teaches" ≠ "All young people teach")
- Incorrect quantifier scope
- Missing or spurious constraints
- Wrong predicate definitions

Generate {num_candidates} alternative formulations that fix the semantic errors. Each must be complete and valid FOL.

Output {num_candidates} JSON objects, one per line, in the same format as the original formalization.

CRITICAL: Re-read the original problem statement carefully. Ensure your translation preserves the intended meaning."""

PAIRWISE_COMPARISON_PROMPT = """Task: Evaluate which logical formulation more accurately represents the natural language intent.

ORIGINAL PROBLEM STATEMENT:
{text}

ORIGINAL QUESTION:
{query}

FORMULATION A:
{formulation_a}

FORMULATION B:
{formulation_b}

Which formulation (A or B) is MORE SEMANTICALLY CORRECT relative to the original problem statement?

Consider (in order of importance):
1. Semantic correctness (does the formulation preserve the intended meaning?)
2. Completeness (are all constraints from the text captured?)
3. Precision (are predicates and quantifiers correct?)
4. No spurious constraints (no added information not in the text)

Focus on MEANING, not just syntax. A syntactically correct formulation can be semantically wrong.

Output ONLY: A or B"""

# Backtracking comparison prompt (Logic-LM++ innovation)
# Compares selected refinement against previous formulation to decide whether to accept or revert
BACKTRACKING_PROMPT = """Task: Determine if a refined formulation is semantically better than the previous version.

ORIGINAL PROBLEM STATEMENT:
{text}

ORIGINAL QUESTION:
{query}

PREVIOUS FORMULATION:
{previous_formulation}

REFINED FORMULATION (after self-refinement):
{refined_formulation}

Does the refined formulation represent a SEMANTIC IMPROVEMENT over the previous formulation?

Consider:
- Does it fix semantic errors (e.g., negation misinterpretation)?
- Does it preserve correct aspects of the previous version?
- Is it more faithful to the original problem statement?

Answer: IMPROVED or REVERT

If REVERT, the system will backtrack to the previous formulation."""

# =============================================================================
# PROPOSITIONAL LOGIC PROMPTS (for LogicBench propositional_logic tasks)
# =============================================================================
# These prompts enforce ground propositional formulas WITHOUT quantifiers,
# which the Z3 solver can handle correctly. This aligns with the Logify paper's
# design choice to use propositional logic for reliability.

PROPOSITIONAL_FORMALIZATION_PROMPT = """You are a formal logician. Convert the following natural language text and query into PROPOSITIONAL LOGIC (not first-order logic).

TEXT:
{text}

QUERY:
{query}

CRITICAL INSTRUCTIONS:
1. Use ONLY ground propositional variables (e.g., P, Q, R, FinishedWorkEarly, OrderedPizza)
2. DO NOT use quantifiers (∀, ∃) or predicate arguments like P(x)
3. Each proposition must be a simple TRUE/FALSE statement about specific entities
4. Use logical connectives: ∧ (and), ∨ (or), → (implies), ¬ (not), ↔ (iff)

CORRECT EXAMPLE:
- Text: "If Liam finished work early, he orders pizza. Liam did not order pizza."
- Propositions: P = "Liam finished work early", Q = "Liam ordered pizza"
- Premises: ["P → Q", "¬Q"]
- Conclusion (for "Did Liam finish work early?"): "P" (test if P is true)
- Conclusion (for "Did Liam NOT finish work early?"): "¬P" (test if ¬P is true)

WRONG (DO NOT DO THIS):
- "∀x (FinishedWorkEarly(x) → OrdersPizza(x))" -- NO quantifiers!
- "OrdersPizza(Liam)" -- NO predicate arguments!

Output format (JSON):
{{
    "predicates": {{"P": "Liam finished work early", "Q": "Liam ordered pizza", ...}},
    "premises": ["P → Q", "¬Q", ...],
    "conclusion": "¬P"
}}

The conclusion should be the formula to TEST. If the query asks "Does X imply Y?", test whether Y follows from the premises."""

PROPOSITIONAL_REFINEMENT_PROMPT = """You previously formalized a propositional logic problem. The current formulation has issues.

ORIGINAL PROBLEM STATEMENT:
{text}

ORIGINAL QUESTION:
{query}

YOUR CURRENT FORMULATION:
{current_formulation}

SOLVER FEEDBACK:
{error_feedback}

INSTRUCTIONS:
1. Use ONLY ground propositional variables (P, Q, R, or descriptive names like FinishedWork)
2. DO NOT use quantifiers (∀, ∃) or predicate arguments
3. Check if the conclusion correctly captures what the query is asking
4. Ensure all relevant facts from the text are captured as premises

Common errors:
- Using FOL syntax (∀x, P(x)) instead of propositional (P, Q)
- Wrong conclusion (testing P when should test ¬P, or vice versa)
- Missing premises that connect the propositions

Generate {num_candidates} alternative formulations. Each must use ONLY propositional logic.

Output {num_candidates} JSON objects, one per line."""
