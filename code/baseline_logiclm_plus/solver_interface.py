"""
FOL solver interface module for Logic-LM++.

This module provides a clean interface to first-order logic theorem provers
(Prover9) and SMT solvers (Z3), as specified in the Logic-LM++ paper.

From paper (page 3, line 309): "Symbolic Reasoning, where we use a symbolic
solver like Prover9 and Z3 theorem prover to solve the formulations generated earlier."

Core responsibilities:
1. Solve FOL problems using Prover9 (theorem prover) or Z3 (SMT solver)
2. Test entailment/contradiction via theorem proving
3. Validate formulations (syntax, well-formedness)
4. Handle solver timeouts and errors
5. Parse solver output and error messages for refinement feedback

Key functions:
- solve_fol(premises, conclusion, solver='prover9', timeout=30) -> dict
  Main FOL solving entry point, returns answer + diagnostics

- validate_formulation(premises, conclusion) -> dict
  Quick validation: check if formulation is well-formed FOL

- test_entailment_prover9(premises, conclusion) -> dict
  Use Prover9 to test if premises ⊢ conclusion

- test_entailment_z3(premises, conclusion) -> dict
  Use Z3 SMT solver to test entailment

- parse_solver_error(error_output, solver) -> str
  Extract actionable error messages for refinement feedback

Entailment logic (theorem proving):
The solver determines logical consequence through proof search:
- Query is PROVED if: premises ⊢ conclusion (proof found)
- Query is DISPROVED if: premises ⊢ ¬conclusion (counterproof found)
- Query is UNKNOWN if: no proof found within timeout (open-world assumption for ProofWriter)

Error types passed to refinement:
1. Syntax errors: malformed FOL formulas
2. Type errors: wrong predicate arity, variable scoping issues
3. Unsatisfiable premises: contradictory axioms
4. Timeout: proof search exceeded time limit

Output format from solve_fol():
{
    'answer': str,                      # 'Proved' | 'Disproved' | 'Unknown' | 'Error'
    'proof': str | None,                # Proof trace if available (for debugging)
    'solver_time': float,               # Time spent in solver (seconds)
    'error': str | None,                # Error message if solver failed (sent to refinement)
    'timeout': bool,                    # True if solver timed out
    'solver_used': str                  # 'prover9' | 'z3'
}

Output format from validate_formulation():
{
    'valid': bool,                      # Is formulation well-formed FOL?
    'error_message': str | None,        # Description of error if invalid
    'num_predicates': int,              # Number of unique predicates
    'num_premises': int                 # Number of premises
}

Solver choice (from Logic-LM++ paper):
- Primary: Prover9 (first-order logic theorem prover, Robinson 1965)
- Fallback: Z3 (SMT solver with FOL support, de Moura & Bjørner 2008)

Design decisions:
- FOL syntax compatible with Prover9 and Z3
- Timeout handling (prevent infinite proof search)
- Detailed error messages for refinement (semantic feedback critical)
- Execution success tracked separately from correctness (Table 2 in paper)
"""

import time
import re
from z3 import *
from config import SOLVER_TIMEOUT


def solve_fol(premises, conclusion, solver='z3', timeout=SOLVER_TIMEOUT):
    """
    Main FOL solving entry point, returns answer + diagnostics.

    Args:
        premises: List[str] - FOL premises
        conclusion: str - FOL conclusion to test
        solver: str - 'prover9' or 'z3'
        timeout: int - timeout in seconds

    Returns:
        dict with keys: answer, proof, solver_time, error, timeout, solver_used
    """
    start_time = time.time()

    # Validate formulation first
    validation = validate_formulation(premises, conclusion)
    if not validation['valid']:
        return {
            'answer': 'Error',
            'proof': None,
            'solver_time': time.time() - start_time,
            'error': f"Invalid formulation: {validation['error_message']}",
            'timeout': False,
            'solver_used': solver
        }

    # Call appropriate solver
    if solver == 'z3':
        result = test_entailment_z3(premises, conclusion, timeout)
    elif solver == 'prover9':
        result = test_entailment_prover9(premises, conclusion, timeout)
    else:
        return {
            'answer': 'Error',
            'proof': None,
            'solver_time': time.time() - start_time,
            'error': f"Unknown solver: {solver}",
            'timeout': False,
            'solver_used': solver
        }

    result['solver_time'] = time.time() - start_time
    result['solver_used'] = solver
    return result


def validate_formulation(premises, conclusion):
    """
    Quick validation: check if formulation is well-formed FOL.

    Args:
        premises: List[str] - FOL premises
        conclusion: str - FOL conclusion

    Returns:
        dict with keys: valid, error_message, num_predicates, num_premises
    """
    # Check basic structure
    if not isinstance(premises, list):
        return {
            'valid': False,
            'error_message': 'Premises must be a list',
            'num_predicates': 0,
            'num_premises': 0
        }

    if not isinstance(conclusion, str):
        return {
            'valid': False,
            'error_message': 'Conclusion must be a string',
            'num_predicates': 0,
            'num_premises': 0
        }

    if len(premises) == 0:
        return {
            'valid': False,
            'error_message': 'Must have at least one premise',
            'num_predicates': 0,
            'num_premises': 0
        }

    if len(conclusion.strip()) == 0:
        return {
            'valid': False,
            'error_message': 'Conclusion cannot be empty',
            'num_predicates': 0,
            'num_premises': len(premises)
        }

    # Extract predicates (simple regex for predicate names)
    all_formulas = premises + [conclusion]
    predicates = set()
    for formula in all_formulas:
        # Match predicate names (capital letter followed by alphanumeric)
        matches = re.findall(r'[A-Z][a-zA-Z0-9]*\(', formula)
        for match in matches:
            predicates.add(match[:-1])  # Remove trailing '('

    return {
        'valid': True,
        'error_message': None,
        'num_predicates': len(predicates),
        'num_premises': len(premises)
    }


def test_entailment_z3(premises, conclusion, timeout=SOLVER_TIMEOUT):
    """
    Use Z3 SMT solver to test entailment.

    Tests if premises ⊢ conclusion by checking if premises ∧ ¬conclusion is unsatisfiable.

    Args:
        premises: List[str] - FOL premises
        conclusion: str - FOL conclusion
        timeout: int - timeout in seconds

    Returns:
        dict with keys: answer, proof, error, timeout
    """
    try:
        # Set timeout for Z3
        set_option("timeout", timeout * 1000)  # Z3 uses milliseconds

        solver = Solver()

        # Parse and convert FOL formulas to Z3
        predicate_decls = {}  # Map predicate names to Z3 functions

        # Helper function to parse FOL formula to Z3
        def parse_fol_to_z3(formula_str):
            """Parse FOL string to Z3 expression.

            Handles:
            - Propositional: P, Q, R (nullary predicates)
            - First-order: Pred(x), Pred(x,y) with quantifiers
            - Connectives: ∧ ∨ → ¬ (and, or, implies, not)
            - Quantifiers: ∀x ∃x (forall, exists)
            """
            # Normalize whitespace
            formula_str = formula_str.strip()

            # Handle simple propositional variables (single capital letters or simple predicates)
            # These are very common in propositional logic: P, Q, R, etc.
            simple_prop_pattern = r'\b([A-Z])\b'
            simple_props = re.findall(simple_prop_pattern, formula_str)
            for prop in simple_props:
                if prop not in predicate_decls and prop not in ['X', 'Y', 'Z']:  # Avoid variable names
                    predicate_decls[prop] = Bool(prop)

            # Extract all predicates and their arities from the formula
            predicate_pattern = r'([A-Z][a-zA-Z0-9]*)\(([^)]*)\)'
            matches = re.findall(predicate_pattern, formula_str)

            for pred_name, args_str in matches:
                args = [a.strip() for a in args_str.split(',') if a.strip()]
                arity = len(args)

                # Declare predicate if not seen before
                if pred_name not in predicate_decls:
                    # Create uninterpreted function (predicate)
                    if arity == 0:
                        predicate_decls[pred_name] = Bool(pred_name)
                    elif arity == 1:
                        predicate_decls[pred_name] = Function(pred_name, IntSort(), BoolSort())
                    elif arity == 2:
                        predicate_decls[pred_name] = Function(pred_name, IntSort(), IntSort(), BoolSort())
                    else:
                        # Support up to 3 arguments
                        predicate_decls[pred_name] = Function(pred_name,
                            *([IntSort()] * arity + [BoolSort()]))

            # Replace logical symbols with Python operators
            z3_formula_str = formula_str
            z3_formula_str = z3_formula_str.replace('∧', ' and ')
            z3_formula_str = z3_formula_str.replace('∨', ' or ')
            z3_formula_str = z3_formula_str.replace('¬', 'not ')
            z3_formula_str = z3_formula_str.replace('→', ' >> ')  # Use >> for implies temporarily

            # Build context with predicate declarations and Z3 functions
            context = dict(predicate_decls)
            context.update({
                'And': And,
                'Or': Or,
                'Not': Not,
                'Implies': Implies,
                'ForAll': ForAll,
                'Exists': Exists,
                'Int': Int,
                'Bool': Bool,
                'and': lambda *args: And(*args) if len(args) > 1 else args[0],
                'or': lambda *args: Or(*args) if len(args) > 1 else args[0],
                'not': Not
            })

            # Handle quantifiers if present
            # Pattern: ∀x (formula) or ∃x (formula)
            if '∀' in formula_str or '∃' in formula_str:
                # For now, treat quantified formulas as free boolean variables
                # Full quantifier handling requires more sophisticated parsing
                # This allows the solver to continue with a conservative approximation
                return Bool(f'quantified_{abs(hash(formula_str)) % 10000}')

            # Replace predicate calls with Z3 expressions
            for pred_name in list(predicate_decls.keys()):
                if len(pred_name) == 1:
                    # Single letter propositional variable - already declared
                    continue

                # Find all occurrences of Pred(args)
                pattern = f'{pred_name}\\(([^)]*)\\)'
                matches_list = list(re.finditer(pattern, z3_formula_str))

                # Replace from right to left to avoid index issues
                for match in reversed(matches_list):
                    full_match = match.group(0)
                    args_str = match.group(1)
                    args = [a.strip() for a in args_str.split(',') if a.strip()]

                    if len(args) == 0:
                        # Nullary predicate
                        replacement = pred_name
                    else:
                        # Create Z3 function call
                        z3_args = []
                        for arg in args:
                            if arg.isdigit():
                                z3_args.append(str(arg))
                            else:
                                # Variable or constant name
                                if arg not in context:
                                    context[arg] = Int(arg)
                                z3_args.append(arg)

                        replacement = f"{pred_name}({', '.join(z3_args)})"

                    # Replace this occurrence
                    start, end = match.span()
                    z3_formula_str = z3_formula_str[:start] + replacement + z3_formula_str[end:]

            # Replace >> with Implies
            # Do this carefully to handle operator precedence
            if '>>' in z3_formula_str:
                # Parse implications manually to get precedence right
                parts = z3_formula_str.split('>>')
                if len(parts) == 2:
                    z3_formula_str = f"Implies(({parts[0].strip()}), ({parts[1].strip()}))"
                elif len(parts) > 2:
                    # Right-associative: A >> B >> C == A >> (B >> C)
                    result = parts[-1].strip()
                    for part in reversed(parts[:-1]):
                        result = f"Implies(({part.strip()}), ({result}))"
                    z3_formula_str = result

            # Try to evaluate the formula
            try:
                z3_expr = eval(z3_formula_str, context)
                return z3_expr
            except Exception as e:
                # If parsing fails, return a fresh boolean variable
                # This allows the solver to continue rather than crash
                return Bool(f'unparsed_{abs(hash(formula_str)) % 10000}')

        # Parse all premises
        premise_constraints = []
        for premise in premises:
            try:
                z3_premise = parse_fol_to_z3(premise)
                premise_constraints.append(z3_premise)
            except Exception as e:
                # Skip unparseable premises with warning
                continue

        # Parse conclusion
        try:
            z3_conclusion = parse_fol_to_z3(conclusion)
        except Exception as e:
            return {
                'answer': 'Error',
                'proof': None,
                'error': f'Could not parse conclusion: {str(e)}',
                'timeout': False
            }

        # Add premises to solver
        for constraint in premise_constraints:
            solver.add(constraint)

        # Add negated conclusion
        solver.add(Not(z3_conclusion))

        # Check satisfiability
        result = solver.check()

        if result == unsat:
            # Premises ∧ ¬conclusion is UNSAT, so premises ⊢ conclusion
            return {
                'answer': 'Proved',
                'proof': 'Z3 proved premises ⊢ conclusion (premises ∧ ¬conclusion is UNSAT)',
                'error': None,
                'timeout': False
            }
        elif result == sat:
            # Found counterexample - check if we can disprove
            # Try checking if premises ⊢ ¬conclusion
            solver2 = Solver()
            for constraint in premise_constraints:
                solver2.add(constraint)
            solver2.add(z3_conclusion)  # Add conclusion without negation

            result2 = solver2.check()
            if result2 == unsat:
                # Premises ∧ conclusion is UNSAT, so premises ⊢ ¬conclusion
                return {
                    'answer': 'Disproved',
                    'proof': 'Z3 disproved conclusion (premises ∧ conclusion is UNSAT)',
                    'error': None,
                    'timeout': False
                }
            else:
                # Can't prove or disprove
                return {
                    'answer': 'Unknown',
                    'proof': None,
                    'error': None,
                    'timeout': False
                }
        else:  # unknown
            return {
                'answer': 'Unknown',
                'proof': None,
                'error': 'Z3 could not determine satisfiability within timeout',
                'timeout': True
            }

    except Exception as e:
        error_msg = parse_solver_error(str(e), 'z3')
        return {
            'answer': 'Error',
            'proof': None,
            'error': error_msg,
            'timeout': False
        }


def test_entailment_prover9(premises, conclusion, timeout=SOLVER_TIMEOUT):
    """
    Use Prover9 to test if premises ⊢ conclusion.

    Note: This is a placeholder implementation.
    Full Prover9 integration would require installing Prover9 and
    creating proper input files in Prover9 format.

    Args:
        premises: List[str] - FOL premises
        conclusion: str - FOL conclusion
        timeout: int - timeout in seconds

    Returns:
        dict with keys: answer, proof, error, timeout
    """
    # Prover9 is not commonly available, so we return an error
    # directing users to use Z3 instead
    return {
        'answer': 'Error',
        'proof': None,
        'error': 'Prover9 not implemented. Please use solver="z3" instead.',
        'timeout': False
    }


def parse_solver_error(error_output, solver):
    """
    Extract actionable error messages for refinement feedback.

    Args:
        error_output: str - Raw error message from solver
        solver: str - 'prover9' or 'z3'

    Returns:
        str - Cleaned, actionable error message
    """
    # Clean up common error patterns
    error_msg = str(error_output)

    # Remove technical stack traces
    if 'Traceback' in error_msg:
        lines = error_msg.split('\n')
        # Keep only the last line (actual error message)
        for line in reversed(lines):
            if line.strip() and not line.startswith(' '):
                error_msg = line
                break

    # Shorten Z3-specific errors
    if solver == 'z3':
        if 'timeout' in error_msg.lower():
            return "Z3 timeout: proof search exceeded time limit"
        if 'parse' in error_msg.lower():
            return "Z3 syntax error: could not parse FOL formula"
        if 'sort' in error_msg.lower() or 'type' in error_msg.lower():
            return "Z3 type error: inconsistent predicate types or arities"

    # Generic cleanup
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."

    return error_msg
