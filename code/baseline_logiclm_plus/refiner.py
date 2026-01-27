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

import json
import os
from openai import OpenAI
from config import (
    REFINEMENT_PROMPT,
    PAIRWISE_COMPARISON_PROMPT,
    BACKTRACKING_PROMPT,
    MAX_CONSECUTIVE_BACKTRACKS,
    NUM_REFINEMENT_CANDIDATES,
    TEMPERATURE,
    MAX_TOKENS
)
from solver_interface import solve_fol


def _get_openai_client():
    """
    Get OpenAI client with auto-detection of OpenRouter or OpenAI.

    Returns:
        OpenAI client configured for OpenRouter or OpenAI
    """
    api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
    base_url = None

    if os.environ.get('OPENROUTER_API_KEY'):
        base_url = "https://openrouter.ai/api/v1"
    elif os.environ.get('OPENAI_BASE_URL'):
        base_url = os.environ.get('OPENAI_BASE_URL')

    return OpenAI(api_key=api_key, base_url=base_url)


def generate_refinements(current_formulation, error_feedback, original_text,
                        original_query, num_candidates=2, model_name="gpt-4",
                        temperature=0):
    """
    Generate N candidate refinements using LLM with context-rich prompt.

    Args:
        current_formulation: dict with 'predicates', 'premises', 'conclusion'
        error_feedback: str, solver error message
        original_text: str, original problem statement
        original_query: str, original question
        num_candidates: int, number of refinement candidates to generate
        model_name: str, LLM model name
        temperature: float, sampling temperature

    Returns:
        List[dict], list of candidate formulations (may be < num_candidates if parsing fails)
    """
    # Format current formulation as string
    formulation_str = json.dumps(current_formulation, indent=2)

    # Build refinement prompt
    prompt = REFINEMENT_PROMPT.format(
        text=original_text,
        query=original_query,
        current_formulation=formulation_str,
        error_feedback=error_feedback,
        num_candidates=num_candidates
    )

    # Call LLM
    client = _get_openai_client()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=MAX_TOKENS
        )
        raw_response = response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM for refinement: {e}")
        return []

    # Parse response - expect N JSON objects, one per line
    candidates = []
    lines = raw_response.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            candidate = json.loads(line)
            # Validate structure
            if 'predicates' in candidate and 'premises' in candidate and 'conclusion' in candidate:
                candidates.append(candidate)
        except json.JSONDecodeError:
            # Try to extract JSON from line if surrounded by other text
            try:
                start_idx = line.find('{')
                end_idx = line.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = line[start_idx:end_idx+1]
                    candidate = json.loads(json_str)
                    if 'predicates' in candidate and 'premises' in candidate and 'conclusion' in candidate:
                        candidates.append(candidate)
            except:
                continue

    return candidates[:num_candidates]


def pairwise_compare(formulation_a, formulation_b, original_text, original_query,
                    model_name="gpt-4", temperature=0):
    """
    LLM-based semantic comparison between two formulations.

    Args:
        formulation_a: dict, first formulation
        formulation_b: dict, second formulation
        original_text: str, original problem statement
        original_query: str, original question
        model_name: str, LLM model name
        temperature: float, sampling temperature

    Returns:
        str, 'A' or 'B' indicating which formulation is better
    """
    # Format formulations
    formulation_a_str = json.dumps(formulation_a, indent=2)
    formulation_b_str = json.dumps(formulation_b, indent=2)

    # Build comparison prompt
    prompt = PAIRWISE_COMPARISON_PROMPT.format(
        text=original_text,
        query=original_query,
        formulation_a=formulation_a_str,
        formulation_b=formulation_b_str
    )

    # Call LLM
    client = _get_openai_client()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=10
        )
        raw_response = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling LLM for pairwise comparison: {e}")
        return 'A'  # Default to first option on error

    # Parse response - should be just 'A' or 'B'
    if 'B' in raw_response.upper():
        return 'B'
    else:
        return 'A'


def backtracking_decision(previous_formulation, refined_formulation, original_text,
                         original_query, model_name="gpt-4", temperature=0):
    """
    Backtracking agent: determine if refined formulation improves over previous.

    This is the key innovation of Logic-LM++. It prevents semantic degradation
    by comparing refined formulations against the previous version.

    Args:
        previous_formulation: dict, previous formulation
        refined_formulation: dict, newly refined formulation
        original_text: str, original problem statement
        original_query: str, original question
        model_name: str, LLM model name
        temperature: float, sampling temperature

    Returns:
        str, 'IMPROVED' or 'REVERT'
    """
    # Format formulations
    previous_str = json.dumps(previous_formulation, indent=2)
    refined_str = json.dumps(refined_formulation, indent=2)

    # Build backtracking prompt
    prompt = BACKTRACKING_PROMPT.format(
        text=original_text,
        query=original_query,
        previous_formulation=previous_str,
        refined_formulation=refined_str
    )

    # Call LLM
    client = _get_openai_client()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=10
        )
        raw_response = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling LLM for backtracking decision: {e}")
        return 'REVERT'  # Default to safe option on error

    # Parse response - should be 'IMPROVED' or 'REVERT'
    if 'IMPROVED' in raw_response.upper():
        return 'IMPROVED'
    else:
        return 'REVERT'


def select_best_formulation(candidates, original_text, original_query,
                           model_name="gpt-4", temperature=0):
    """
    Select best formulation from N candidates using pairwise comparisons.

    Uses tournament-style selection: compare pairs until one winner remains.
    For N=2, this is a single comparison.

    Args:
        candidates: List[dict], list of candidate formulations
        original_text: str, original problem statement
        original_query: str, original question
        model_name: str, LLM model name
        temperature: float, sampling temperature

    Returns:
        dict, best formulation
    """
    if len(candidates) == 0:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # For N=2 (default), just do single pairwise comparison
    if len(candidates) == 2:
        winner = pairwise_compare(candidates[0], candidates[1], original_text,
                                 original_query, model_name, temperature)
        if winner == 'A':
            return candidates[0]
        else:
            return candidates[1]

    # For N>2, do tournament
    current_pool = candidates[:]
    while len(current_pool) > 1:
        next_pool = []
        for i in range(0, len(current_pool), 2):
            if i + 1 < len(current_pool):
                winner = pairwise_compare(current_pool[i], current_pool[i+1],
                                        original_text, original_query, model_name, temperature)
                if winner == 'A':
                    next_pool.append(current_pool[i])
                else:
                    next_pool.append(current_pool[i+1])
            else:
                # Odd one out advances automatically
                next_pool.append(current_pool[i])
        current_pool = next_pool

    return current_pool[0]


def refine_loop(initial_formulation, original_text, original_query,
                max_iterations=4, solver='prover9', solver_timeout=30,
                model_name="gpt-4", temperature=0, num_candidates=2,
                max_consecutive_backtracks=2):
    """
    Main refinement loop with backtracking and early stopping.

    This is the core Logic-LM++ pipeline:
    1. Validate current formulation with solver
    2. If solver succeeds, terminate early
    3. Generate N candidate refinements with error feedback
    4. Select best candidate via pairwise comparison
    5. Apply backtracking: compare selected vs. previous
    6. If too many consecutive backtracks, early stop

    Args:
        initial_formulation: dict, initial formalization
        original_text: str, original problem statement
        original_query: str, original question
        max_iterations: int, maximum refinement iterations
        solver: str, 'prover9' or 'z3'
        solver_timeout: int, solver timeout in seconds
        model_name: str, LLM model name
        temperature: float, sampling temperature
        num_candidates: int, number of refinement candidates per iteration
        max_consecutive_backtracks: int, early stop threshold

    Returns:
        dict with fields:
            - final_formulation: best formulation after refinement
            - num_iterations: actual iterations run
            - refinement_history: history of all formulations
            - backtracking_history: list of 'IMPROVED'/'REVERT' decisions
            - total_llm_calls: total LLM API calls
            - num_backtracks: total REVERT decisions
            - refinement_successful: whether final differs from initial
            - early_stop_reason: reason for early stopping if applicable
    """
    # Initialize tracking
    current_formulation = initial_formulation
    refinement_history = [initial_formulation]
    backtracking_history = []
    total_llm_calls = 0
    consecutive_backtracks = 0
    early_stop_reason = None

    for iteration in range(max_iterations):
        # Step a: Validate current formulation with solver
        solver_result = solve_fol(
            premises=current_formulation.get('premises', []),
            conclusion=current_formulation.get('conclusion', ''),
            solver=solver,
            timeout=solver_timeout
        )

        # Step b: If solver succeeds, terminate early
        if solver_result['answer'] in ['Proved', 'Disproved', 'Unknown']:
            early_stop_reason = 'solver_success'
            break

        # Get error feedback for refinement
        error_feedback = solver_result.get('error', 'Solver failed to validate formulation')

        # Step c: Generate N candidate refinements
        candidates = generate_refinements(
            current_formulation=current_formulation,
            error_feedback=error_feedback,
            original_text=original_text,
            original_query=original_query,
            num_candidates=num_candidates,
            model_name=model_name,
            temperature=temperature
        )
        total_llm_calls += 1  # One call generates all candidates

        # If no valid candidates generated, keep previous formulation (implicit backtrack)
        if len(candidates) == 0:
            backtracking_history.append('REVERT')
            consecutive_backtracks += 1
            if consecutive_backtracks >= max_consecutive_backtracks:
                early_stop_reason = 'max_consecutive_backtracks'
                break
            continue

        # Step d: Select best candidate via pairwise comparison
        selected = select_best_formulation(
            candidates=candidates,
            original_text=original_text,
            original_query=original_query,
            model_name=model_name,
            temperature=temperature
        )
        # LLM calls: for N=2, this is 1 call
        total_llm_calls += 1

        if selected is None:
            backtracking_history.append('REVERT')
            consecutive_backtracks += 1
            if consecutive_backtracks >= max_consecutive_backtracks:
                early_stop_reason = 'max_consecutive_backtracks'
                break
            continue

        # Step e: BACKTRACKING - compare selected vs. previous
        decision = backtracking_decision(
            previous_formulation=current_formulation,
            refined_formulation=selected,
            original_text=original_text,
            original_query=original_query,
            model_name=model_name,
            temperature=temperature
        )
        total_llm_calls += 1
        backtracking_history.append(decision)

        if decision == 'IMPROVED':
            # Accept selected, reset consecutive backtrack counter
            current_formulation = selected
            refinement_history.append(selected)
            consecutive_backtracks = 0
        else:
            # REVERT: keep previous, increment counter
            consecutive_backtracks += 1

        # Step f: Check early stopping condition
        if consecutive_backtracks >= max_consecutive_backtracks:
            early_stop_reason = 'max_consecutive_backtracks'
            break

    # Compute final statistics
    num_backtracks = backtracking_history.count('REVERT')
    refinement_successful = (current_formulation != initial_formulation)

    return {
        'final_formulation': current_formulation,
        'num_iterations': len(backtracking_history),
        'refinement_history': refinement_history,
        'backtracking_history': backtracking_history,
        'total_llm_calls': total_llm_calls,
        'num_backtracks': num_backtracks,
        'refinement_successful': refinement_successful,
        'early_stop_reason': early_stop_reason
    }
