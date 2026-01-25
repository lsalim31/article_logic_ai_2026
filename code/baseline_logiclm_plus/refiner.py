"""
Multi-step refinement module with pairwise comparison and backtracking.

This module implements the core LOGIC-LM++ innovations from the ACL 2024 paper:
1. Self-refinement with context-rich prompts (no few-shots, include problem statement)
2. Pairwise comparison for selecting best candidate
3. **Backtracking agent** to prevent semantic degradation (key innovation)

The backtracking agent (Section 3.3 of paper) compares refined formulations against
previous versions and reverts if no semantic improvement is detected. This prevents
the refinement loop from accepting syntactically correct but semantically wrong formulations.

Core responsibilities:
1. Generate N alternative refinements of current formulation
2. Perform pairwise comparisons to select best candidate
3. **Apply backtracking: compare selected vs. previous, revert if no improvement**
4. Run refinement loop with early stopping (consecutive backtracks)
5. Track refinement history and backtracking decisions

Key functions:
- generate_refinements(current_formulation, error_feedback, original_text,
                      original_query, num_candidates=2) -> List[dict]
  Generate N candidate refinements using LLM with context-rich prompt

- pairwise_compare(formulation_a, formulation_b, original_text,
                   original_query) -> str
  LLM-based semantic comparison, returns 'A' or 'B'

- backtracking_decision(previous_formulation, refined_formulation,
                        original_text, original_query) -> str
  **Backtracking agent**: returns 'IMPROVED' or 'REVERT'

- select_best_formulation(candidates, original_text, original_query) -> dict
  Tournament-style selection from N candidates using pairwise comparisons

- refine_loop(initial_formulation, original_text, original_query,
              max_iterations=4) -> dict
  Main refinement loop with backtracking and early stopping

Refinement loop logic (Logic-LM++ paper, Section 3):
1. Start with initial formalization
2. For each iteration (up to max_iterations):
   a. Validate current formulation with solver (Prover9/Z3)
   b. If solver succeeds, terminate early (no refinement needed)
   c. Generate N candidate refinements with solver error feedback
   d. Select best candidate via pairwise comparison
   e. **BACKTRACKING**: Compare selected vs. previous formulation
      - If IMPROVED: accept selected, reset consecutive_backtrack counter
      - If REVERT: keep previous, increment consecutive_backtrack counter
   f. If consecutive_backtrack >= threshold: early stop (no improvement possible)
3. Return final formulation + history + backtracking statistics

Error handling:
- Solver errors passed as feedback to refinement generation
- Malformed refinements counted as failures, skipped
- If all refinements fail, keep previous formulation (implicit backtrack)

Output format from refine_loop():
{
    'final_formulation': dict,              # Best formulation after refinement
    'num_iterations': int,                  # Actual iterations run (may be < max if early stop)
    'refinement_history': List[dict],       # History of all formulations tried
    'backtracking_history': List[str],      # ['IMPROVED', 'REVERT', 'IMPROVED', ...]
    'total_llm_calls': int,                 # Track API usage
    'num_backtracks': int,                  # Number of times backtracking occurred
    'refinement_successful': bool,          # Whether final formulation differs from initial
    'early_stop_reason': str | None         # Reason for early stopping if applicable
}

Design decisions (from Logic-LM++ paper):
- Variable iterations (0-4 tested in paper, Figure 3)
- Early stopping via consecutive backtracks (prevents wasted iterations)
- Pairwise comparison for semantic evaluation (not just syntax)
- Context-rich refinement prompts (include problem statement, self-reflection instructions)
- Backtracking prevents semantic degradation (paper's key innovation, Figure 2 & 4)
"""
