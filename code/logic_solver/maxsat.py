#!/usr/bin/env python3
"""
maxsat.py - Interface to PySAT RC2 MaxSAT solver

This module provides the interface for checking entailment and consistency
using the RC2 MaxSAT solver from PySAT.
"""

from typing import Dict, List, Tuple, Any, Optional
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from pysat.solvers import Solver

from .encoding import LogicEncoder, encode_logified_structure


class SolverResult:
    """Result of a solver query."""

    def __init__(self, answer: str, confidence: float, model: Optional[List[int]] = None,
                 explanation: Optional[str] = None):
        """
        Initialize solver result.

        Args:
            answer: "TRUE", "FALSE", or "UNCERTAIN"
            confidence: Confidence score in [0, 1]
            model: Satisfying assignment (if SAT)
            explanation: Human-readable explanation
        """
        self.answer = answer
        self.confidence = confidence
        self.model = model
        self.explanation = explanation

    def __repr__(self):
        return f"SolverResult(answer={self.answer}, confidence={self.confidence:.3f})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "explanation": self.explanation
        }


class LogicSolver:
    """MaxSAT-based logic solver for entailment and consistency checking."""

    # Confidence thresholds for categorical answers
    HIGH_CONFIDENCE_THRESHOLD = 0.80  # Above this, UNCERTAIN becomes TRUE
    LOW_CONFIDENCE_THRESHOLD = 0.20   # Below this, UNCERTAIN becomes FALSE

    def __init__(self, logified_structure: Dict[str, Any],
                 use_confidence_thresholds: bool = True):
        """
        Initialize solver with logified structure.

        Args:
            logified_structure: JSON structure with propositions and constraints
            use_confidence_thresholds: Whether to apply confidence thresholds to
                                       convert high/low confidence UNCERTAIN to TRUE/FALSE
        """
        self.structure = logified_structure
        self.encoder = LogicEncoder(logified_structure)
        self.base_wcnf = self.encoder.encode()
        self.prop_to_var, self.var_to_prop = self.encoder.get_prop_mapping()
        self.use_confidence_thresholds = use_confidence_thresholds

    def check_entailment(self, query_formula: str) -> SolverResult:
        """
        Check if query is entailed by the knowledge base.

        Entailment check: KB ⊨ Q iff KB ∧ ¬Q is UNSAT

        Args:
            query_formula: Propositional formula (e.g., "P_1", "P_3 => P_4")

        Returns:
            SolverResult with answer TRUE/FALSE/UNCERTAIN and confidence
        """
        try:
            # Create a copy of the base WCNF
            wcnf = self._copy_wcnf(self.base_wcnf)

            # Add ¬Q as hard clauses
            negated_query_clauses = self.encoder.encode_query(query_formula, negate=True)
            for clause in negated_query_clauses:
                wcnf.append(clause)  # Hard clause

            # Check satisfiability of KB ∧ ¬Q
            # If UNSAT, then KB ⊨ Q (query is entailed)
            # If SAT, then KB ⊭ Q (query is not entailed)

            # First check if it's SAT/UNSAT with hard constraints only
            hard_only = self._extract_hard_clauses(wcnf)
            is_sat, model = self._check_sat(hard_only)

            if not is_sat:
                # UNSAT: Query is entailed by hard constraints alone
                # Compute how strongly soft constraints support Q being true
                soft_confidence = self._compute_confidence_for_entailment(query_formula)
                return SolverResult(
                    answer="TRUE",
                    confidence=soft_confidence,
                    model=None,
                    explanation="Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)"
                )


            # SAT with hard constraints: Check soft constraints
            # Use RC2 to find optimal model considering soft constraints
            optimal_cost = self._solve_maxsat(wcnf)

            if optimal_cost is None:
                # UNSAT even with soft constraints
                return SolverResult(
                    answer="TRUE",
                    confidence=1.0,
                    model=None,
                    explanation="Query is entailed (KB ∧ ¬Q is unsatisfiable)"
                )

            # SAT: Query is not necessarily entailed
            # Now check if Q itself is consistent
            consistency_result = self.check_consistency(query_formula)

            if consistency_result.answer == "FALSE":
                # Q is inconsistent with KB, so ¬Q is entailed
                # Compute how strongly soft constraints support Q being true
                soft_confidence = self._compute_confidence_for_entailment(query_formula)
                return SolverResult(
                    answer="FALSE",
                    confidence=soft_confidence,
                    model=model,
                    explanation="Query is contradicted by the knowledge base"
                )


            # Query is neither entailed nor contradicted
            # Compute confidence based on soft constraints
            confidence = self._compute_confidence_for_entailment(query_formula)

            return SolverResult(
                answer="UNCERTAIN",
                confidence=confidence,
                model=model,
                explanation="Query is neither entailed nor contradicted by the knowledge base"
            )

        except Exception as e:
            return SolverResult(
                answer="UNCERTAIN",
                confidence=0.5,
                explanation=f"Error during solving: {str(e)}"
            )

    def check_consistency(self, query_formula: str) -> SolverResult:
        """
        Check if query is consistent with the knowledge base.

        Consistency check: KB ∧ Q is SAT

        Args:
            query_formula: Propositional formula

        Returns:
            SolverResult with answer TRUE (consistent) / FALSE (inconsistent) / UNCERTAIN
        """
        try:
            # Create a copy of the base WCNF
            wcnf = self._copy_wcnf(self.base_wcnf)

            # Add Q as hard clauses
            query_clauses = self.encoder.encode_query(query_formula, negate=False)
            for clause in query_clauses:
                wcnf.append(clause)  # Hard clause

            # Check satisfiability of KB ∧ Q
            hard_only = self._extract_hard_clauses(wcnf)
            is_sat, model = self._check_sat(hard_only)

            if is_sat:
                # SAT: Query is consistent
                # Compute confidence based on soft constraints
                confidence = self._compute_confidence_for_consistency(query_formula, model)

                return SolverResult(
                    answer="TRUE",
                    confidence=confidence,
                    model=model,
                    explanation="Query is consistent with the knowledge base"
                )
            else:
                # UNSAT: Query is inconsistent
                return SolverResult(
                    answer="FALSE",
                    confidence=0.0,  # Q cannot be true
                    model=None,
                    explanation="Query is inconsistent with the knowledge base (KB ∧ Q is unsatisfiable)"
                )

        except Exception as e:
            return SolverResult(
                answer="UNCERTAIN",
                confidence=0.5,
                explanation=f"Error during solving: {str(e)}"
            )

    def query(self, query_formula: str) -> SolverResult:
        """
        Main query interface: check if query follows from the knowledge base.

        This combines entailment and consistency checking to provide a comprehensive answer.
        When use_confidence_thresholds is True, high/low confidence UNCERTAIN results
        are converted to TRUE/FALSE respectively.

        Args:
            query_formula: Propositional formula

        Returns:
            SolverResult with TRUE (entailed) / FALSE (contradicted) / UNCERTAIN
        """
        # First check entailment
        entailment_result = self.check_entailment(query_formula)

        if entailment_result.answer == "TRUE":
            # Query is entailed
            return entailment_result
        elif entailment_result.answer == "FALSE":
            # Query is contradicted
            return entailment_result
        else:
            # UNCERTAIN: Query is neither entailed nor contradicted
            # But first check if there was an error
            if "Error" in entailment_result.explanation:
                # Propagate the error
                return entailment_result

            # Check consistency to refine the answer
            consistency_result = self.check_consistency(query_formula)

            if consistency_result.answer == "FALSE":
                # Query is inconsistent (contradicted)
                # Compute how strongly soft constraints support Q being true
                soft_confidence = self._compute_confidence_for_entailment(query_formula)
                return SolverResult(
                    answer="FALSE",
                    confidence=soft_confidence,
                    explanation="Query is contradicted by the knowledge base"
                )

            else:
                # Check if consistency had an error
                if "Error" in consistency_result.explanation:
                    return consistency_result

                # Query is consistent but not entailed
                # Return uncertainty with confidence from soft constraints
                avg_confidence = (entailment_result.confidence + consistency_result.confidence) / 2

                # Apply confidence thresholds to convert high/low confidence UNCERTAIN
                if self.use_confidence_thresholds:
                    if avg_confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                        return SolverResult(
                            answer="TRUE",
                            confidence=avg_confidence,
                            explanation="Query is likely true based on soft constraint confidence (threshold-based)"
                        )
                    elif avg_confidence <= self.LOW_CONFIDENCE_THRESHOLD:
                        return SolverResult(
                            answer="FALSE",
                            confidence=1.0 - avg_confidence,
                            explanation="Query is likely false based on soft constraint confidence (threshold-based)"
                        )

                return SolverResult(
                    answer="UNCERTAIN",
                    confidence=avg_confidence,
                    explanation="Query is consistent but not entailed by the knowledge base"
                )

    def _copy_wcnf(self, wcnf: WCNF) -> WCNF:
        """Create a copy of a WCNF formula."""
        new_wcnf = WCNF()

        # Copy hard clauses
        for clause in wcnf.hard:
            new_wcnf.append(clause)

        # Copy soft clauses with weights
        for clause, weight in zip(wcnf.soft, wcnf.wght):
            if weight > 0:  # Only copy if weight is set
                new_wcnf.append(clause, weight=weight)

        return new_wcnf

    def _extract_hard_clauses(self, wcnf: WCNF) -> List[List[int]]:
        """Extract only hard clauses from WCNF."""
        hard_clauses = []
        for clause in wcnf.hard:
            hard_clauses.append(clause)
        return hard_clauses

    def _check_sat(self, clauses: List[List[int]]) -> Tuple[bool, Optional[List[int]]]:
        """
        Check satisfiability of CNF clauses.

        Args:
            clauses: List of CNF clauses

        Returns:
            Tuple of (is_satisfiable, model)
        """
        if not clauses:
            # Empty clause set is SAT
            return True, []

        # Use a SAT solver (Glucose or MiniSat)
        solver = Solver(name='g3', bootstrap_with=clauses)

        is_sat = solver.solve()
        model = solver.get_model() if is_sat else None

        solver.delete()

        return is_sat, model

    def _solve_maxsat(self, wcnf: WCNF) -> Optional[int]:
        """
        Solve MaxSAT problem and return optimal cost.

        Args:
            wcnf: Weighted CNF formula

        Returns:
            Optimal cost (sum of unsatisfied soft clause weights), or None if UNSAT
        """
        try:
            # Use RC2 solver
            with RC2(wcnf) as solver:
                # Compute optimal model
                model = solver.compute()

                if model is None:
                    # UNSAT
                    return None

                # Get the cost (sum of weights of unsatisfied soft clauses)
                cost = solver.cost

                return cost

        except Exception:
            # If RC2 fails, fall back to basic SAT check
            hard_clauses = self._extract_hard_clauses(wcnf)
            is_sat, _ = self._check_sat(hard_clauses)
            return 0 if is_sat else None

    def _compute_confidence_for_entailment(self, query_formula: str) -> float:
        """
        Compute confidence score for entailment based on soft constraints.

        Higher confidence means the query is more likely to be true.

        Args:
            query_formula: Query formula

        Returns:
            Confidence score in [0, 1]
        """
        try:
            # Solve MaxSAT with Q
            wcnf_with_q = self._copy_wcnf(self.base_wcnf)
            query_clauses = self.encoder.encode_query(query_formula, negate=False)
            for clause in query_clauses:
                wcnf_with_q.append(clause)

            cost_with_q = self._solve_maxsat(wcnf_with_q)

            # Solve MaxSAT with ¬Q
            wcnf_with_not_q = self._copy_wcnf(self.base_wcnf)
            negated_query_clauses = self.encoder.encode_query(query_formula, negate=True)
            for clause in negated_query_clauses:
                wcnf_with_not_q.append(clause)

            cost_with_not_q = self._solve_maxsat(wcnf_with_not_q)

            if cost_with_q is None and cost_with_not_q is None:
                return 0.5  # Both unsatisfiable, uncertain

            if cost_with_q is None:
                return 0.0  # Q is unsatisfiable, ¬Q is likely true

            if cost_with_not_q is None:
                return 1.0  # ¬Q is unsatisfiable, Q is likely true

            # Both satisfiable: compare costs
            # Lower cost = better fit with soft constraints
            total_cost = cost_with_q + cost_with_not_q
            if total_cost == 0:
                return 0.5  # No soft constraints violated either way

            # Confidence that Q is true: ¬Q has higher cost
            confidence = cost_with_not_q / total_cost

            return confidence

        except Exception:
            return 0.5  # Default to uncertain

    def _compute_confidence_for_consistency(self, query_formula: str, model: List[int]) -> float:
        """
        Compute confidence score for consistency based on soft constraints.

        Args:
            query_formula: Query formula
            model: Satisfying assignment

        Returns:
            Confidence score in [0, 1]
        """
        # Count how many soft constraints are satisfied by the model
        total_weight = 0.0
        satisfied_weight = 0.0

        for constraint in self.structure.get('soft_constraints', []):
            weight = constraint.get('weight', 0.5)
            formula = constraint['formula']

            try:
                # Check if this soft constraint is satisfied by the model
                clauses = self.encoder.encode_query(formula, negate=False)
                is_satisfied = self._model_satisfies_clauses(model, clauses)

                total_weight += weight
                if is_satisfied:
                    satisfied_weight += weight

            except Exception:
                continue

        if total_weight == 0:
            return 0.5  # No soft constraints

        confidence = satisfied_weight / total_weight
        return confidence

    def _model_satisfies_clauses(self, model: List[int], clauses: List[List[int]]) -> bool:
        """
        Check if a model satisfies all clauses.

        Args:
            model: Satisfying assignment (list of signed literals)
            clauses: List of CNF clauses

        Returns:
            True if model satisfies all clauses
        """
        model_set = set(model)

        for clause in clauses:
            # A clause is satisfied if at least one literal is in the model
            satisfied = any(lit in model_set for lit in clause)
            if not satisfied:
                return False

        return True


def solve_query(logified_structure: Dict[str, Any], query_formula: str,
                use_confidence_thresholds: bool = True) -> SolverResult:
    """
    Convenience function to solve a query against a logified structure.

    Args:
        logified_structure: JSON structure with propositions and constraints
        query_formula: Propositional formula to check
        use_confidence_thresholds: Whether to apply confidence thresholds to
                                   convert high/low confidence UNCERTAIN to TRUE/FALSE

    Returns:
        SolverResult with answer and confidence
    """
    solver = LogicSolver(logified_structure, use_confidence_thresholds=use_confidence_thresholds)
    return solver.query(query_formula)
