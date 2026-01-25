"""
Multi-step refinement module with pairwise comparison.

This module implements the core LOGIC-LM++ innovation: iterative refinement
of symbolic formulations through LLM-based self-correction and comparison.

Core responsibilities:
1. Generate N alternative refinements of current formulation
2. Perform pairwise comparisons to select best candidate
3. Run refinement loop for fixed iterations (no early stopping)
4. Track refinement history for analysis

Key functions:
- generate_refinements(current_formulation, error_feedback, original_text,
                      original_query, num_candidates=2) -> List[dict]
  Generate N candidate refinements using LLM

- pairwise_compare(formulation_a, formulation_b, original_text,
                   original_query) -> str
  LLM-based comparison, returns 'A' or 'B'

- select_best_formulation(candidates, original_text, original_query) -> dict
  Tournament-style selection from N candidates using pairwise comparisons

- refine_loop(initial_formulation, original_text, original_query,
              max_iterations=3) -> dict
  Main refinement loop: fixed iterations, no early stopping

Refinement loop logic:
1. Start with initial formalization
2. For each iteration (fixed, no early stopping per Q3):
   a. Validate current formulation with solver
   b. Generate N candidate refinements
   c. Select best via pairwise comparison
   d. Update current formulation
3. Return final formulation + history

Error handling:
- Solver errors passed as feedback to refinement generation
- Malformed refinements counted as failures, skipped
- If all refinements fail, keep previous formulation

Output format from refine_loop():
{
    'final_formulation': dict,              # Best formulation after all iterations
    'num_iterations': int,                  # Always equals max_iterations
    'refinement_history': List[dict],       # History of all formulations tried
    'total_llm_calls': int,                 # Track API usage
    'refinement_successful': bool           # Whether any improvement occurred
}

Design decisions:
- Fixed iterations (no early stopping, faithful to paper)
- Pairwise comparison (as in LOGIC-LM++ paper)
- Malformed outputs → formalization failure, no retry (per Q2)
- Solver validation during refinement (catch errors early)
"""
