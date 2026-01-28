#!/usr/bin/env python3
"""
encoding.py - Convert logified structure to SAT encoding

This module converts the logified JSON structure (propositions, hard/soft constraints)
into a format suitable for PySAT's RC2 MaxSAT solver.
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from pysat.formula import CNF, WCNF
from pysat.card import CardEnc


class FormulaParser:
    """Parse propositional logic formulas and convert to CNF."""

    def __init__(self, prop_to_var: Dict[str, int]):
        """
        Initialize parser with proposition-to-variable mapping.

        Args:
            prop_to_var: Dictionary mapping proposition IDs (e.g., "P_1") to SAT variables (integers)
        """
        self.prop_to_var = prop_to_var

    def parse(self, formula: str) -> List[List[int]]:
        """
        Parse a propositional formula and convert to CNF clauses.

        Supports operators: ∧ (AND), ∨ (OR), ¬ (NOT), ⇒ (IMPLIES), ⟹ (IMPLIES), → (IMPLIES),
                           ⇔ (IFF), ⟺ (IFF), ↔ (IFF)

        Args:
            formula: String formula like "P_1 ∧ P_2" or "P_3 ⇒ P_4"

        Returns:
            List of clauses (each clause is a list of literals)
        """
        # Normalize the formula
        formula = formula.strip()

        # Replace various arrow symbols with standard ones
        formula = formula.replace('⇒', '=>')
        formula = formula.replace('⟹', '=>')
        formula = formula.replace('→', '=>')
        formula = formula.replace('⟺', '<=>')
        formula = formula.replace('⇔', '<=>')
        formula = formula.replace('↔', '<=>')
        formula = formula.replace('∧', '&')
        formula = formula.replace('∨', '|')
        formula = formula.replace('¬', '~')
        formula = formula.replace('⟸', '<=')  # Reverse implication
        formula = formula.replace('⇐', '<=')

        # Parse and convert to CNF
        return self._parse_and_convert_to_cnf(formula)

    def _parse_and_convert_to_cnf(self, formula: str) -> List[List[int]]:
        """
        Parse formula and convert to CNF.

        Grammar:
          formula := iff_expr
          iff_expr := implies_expr ('<=>' implies_expr)*
          implies_expr := or_expr ('=>' or_expr)*
          or_expr := and_expr ('|' and_expr)*
          and_expr := not_expr ('&' not_expr)*
          not_expr := '~' not_expr | atom
          atom := '(' formula ')' | prop_id
        """
        tokens = self._tokenize(formula)
        expr, remaining = self._parse_iff(tokens)

        if remaining:
            raise ValueError(f"Unexpected tokens after parsing: {remaining}")

        # Convert expression tree to CNF
        return self._to_cnf(expr)

    def _tokenize(self, formula: str) -> List[str]:
        """Tokenize the formula into operators, parentheses, and proposition IDs."""
        # Pattern: proposition IDs (P_\d+), operators, parentheses
        pattern = r'(P_\d+|<=>|=>|[&|~()])'
        tokens = re.findall(pattern, formula)
        return [t.strip() for t in tokens if t.strip()]

    def _parse_iff(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse IFF (biconditional) expressions."""
        left, tokens = self._parse_implies(tokens)

        while tokens and tokens[0] == '<=>':
            tokens = tokens[1:]  # consume '<='
            right, tokens = self._parse_implies(tokens)
            # A <=> B is (A => B) & (B => A)
            left = ('&', ('=>', left, right), ('=>', right, left))

        return left, tokens

    def _parse_implies(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse implication expressions."""
        left, tokens = self._parse_or(tokens)

        while tokens and tokens[0] == '=>':
            tokens = tokens[1:]  # consume '=>'
            right, tokens = self._parse_or(tokens)
            # A => B is ~A | B
            left = ('=>', left, right)

        return left, tokens

    def _parse_or(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse OR expressions."""
        left, tokens = self._parse_and(tokens)

        while tokens and tokens[0] == '|':
            tokens = tokens[1:]  # consume '|'
            right, tokens = self._parse_and(tokens)
            left = ('|', left, right)

        return left, tokens

    def _parse_and(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse AND expressions."""
        left, tokens = self._parse_not(tokens)

        while tokens and tokens[0] == '&':
            tokens = tokens[1:]  # consume '&'
            right, tokens = self._parse_not(tokens)
            left = ('&', left, right)

        return left, tokens

    def _parse_not(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse NOT expressions."""
        if not tokens:
            raise ValueError("Unexpected end of formula")

        if tokens[0] == '~':
            tokens = tokens[1:]  # consume '~'
            expr, tokens = self._parse_not(tokens)
            return ('~', expr), tokens
        else:
            return self._parse_atom(tokens)

    def _parse_atom(self, tokens: List[str]) -> Tuple[Any, List[str]]:
        """Parse atomic propositions or parenthesized expressions."""
        if not tokens:
            raise ValueError("Unexpected end of formula")

        if tokens[0] == '(':
            tokens = tokens[1:]  # consume '('
            expr, tokens = self._parse_iff(tokens)
            if not tokens or tokens[0] != ')':
                raise ValueError("Missing closing parenthesis")
            tokens = tokens[1:]  # consume ')'
            return expr, tokens

        # Must be a proposition ID
        prop_id = tokens[0]
        if not prop_id.startswith('P_'):
            raise ValueError(f"Invalid proposition ID: {prop_id}")

        if prop_id not in self.prop_to_var:
            raise ValueError(f"Unknown proposition: {prop_id}")

        return prop_id, tokens[1:]

    def _to_cnf(self, expr) -> List[List[int]]:
        """
        Convert expression tree to CNF clauses.

        Returns list of clauses, where each clause is a list of literals.
        """
        # First, convert to NNF (Negation Normal Form)
        nnf = self._to_nnf(expr, positive=True)

        # Then convert NNF to CNF
        return self._nnf_to_cnf(nnf)

    def _to_nnf(self, expr, positive: bool = True):
        """
        Convert to Negation Normal Form (negations only on atoms).

        Args:
            expr: Expression tree
            positive: Whether we're in positive context (False means negated)
        """
        if isinstance(expr, str):  # Atomic proposition
            var = self.prop_to_var[expr]
            return var if positive else -var

        op = expr[0]

        if op == '~':
            # Push negation down
            return self._to_nnf(expr[1], positive=not positive)

        elif op == '&':
            if positive:
                # (A & B) stays as AND
                return ('&', self._to_nnf(expr[1], True), self._to_nnf(expr[2], True))
            else:
                # ~(A & B) = ~A | ~B (De Morgan's)
                return ('|', self._to_nnf(expr[1], False), self._to_nnf(expr[2], False))

        elif op == '|':
            if positive:
                # (A | B) stays as OR
                return ('|', self._to_nnf(expr[1], True), self._to_nnf(expr[2], True))
            else:
                # ~(A | B) = ~A & ~B (De Morgan's)
                return ('&', self._to_nnf(expr[1], False), self._to_nnf(expr[2], False))

        elif op == '=>':
            # A => B = ~A | B
            if positive:
                return ('|', self._to_nnf(expr[1], False), self._to_nnf(expr[2], True))
            else:
                # ~(A => B) = A & ~B
                return ('&', self._to_nnf(expr[1], True), self._to_nnf(expr[2], False))

        else:
            raise ValueError(f"Unknown operator: {op}")

    def _nnf_to_cnf(self, nnf) -> List[List[int]]:
        """
        Convert NNF expression to CNF clauses.

        Returns list of clauses.
        """
        if isinstance(nnf, int):  # Literal
            return [[nnf]]

        op = nnf[0]

        if op == '&':
            # Conjunction: concatenate clauses
            left_cnf = self._nnf_to_cnf(nnf[1])
            right_cnf = self._nnf_to_cnf(nnf[2])
            return left_cnf + right_cnf

        elif op == '|':
            # Disjunction: distribute over conjunction
            left_cnf = self._nnf_to_cnf(nnf[1])
            right_cnf = self._nnf_to_cnf(nnf[2])

            # Distribute: (A1 & A2 & ...) | (B1 & B2 & ...) =
            # (A1 | B1) & (A1 | B2) & ... & (A2 | B1) & ...
            result = []
            for left_clause in left_cnf:
                for right_clause in right_cnf:
                    # Merge the two clauses (OR of literals)
                    merged = left_clause + right_clause
                    result.append(merged)
            return result

        else:
            raise ValueError(f"Unexpected operator in NNF: {op}")


class LogicEncoder:
    """Encode logified structure as Weighted CNF for MaxSAT solving."""

    def __init__(self, logified_structure: Dict[str, Any]):
        """
        Initialize encoder with logified structure.

        Args:
            logified_structure: JSON structure with primitive_props, hard_constraints, soft_constraints
        """
        self.structure = logified_structure
        self.prop_to_var: Dict[str, int] = {}  # P_1 -> 1, P_2 -> 2, etc.
        self.var_to_prop: Dict[int, str] = {}  # Reverse mapping
        self.wcnf = WCNF()

        # Build proposition mapping
        self._build_prop_mapping()

        # Initialize parser
        self.parser = FormulaParser(self.prop_to_var)

    def _build_prop_mapping(self):
        """Build mapping between proposition IDs and SAT variables."""
        for i, prop in enumerate(self.structure.get('primitive_props', []), start=1):
            prop_id = prop['id']
            self.prop_to_var[prop_id] = i
            self.var_to_prop[i] = prop_id

    def encode(self) -> WCNF:
        """
        Encode the logified structure as WCNF.

        Returns:
            WCNF object with hard and soft constraints
        """
        # Encode hard constraints (infinite weight)
        for constraint in self.structure.get('hard_constraints', []):
            formula = constraint['formula']
            clauses = self.parser.parse(formula)
            for clause in clauses:
                self.wcnf.append(clause)  # Hard clause (no weight = infinite)

        # Encode soft constraints (weighted)
        for constraint in self.structure.get('soft_constraints', []):
            formula = constraint['formula']
            weight_raw = constraint.get('weight', 0.5)  # Default weight if not provided

            # Handle weight array from weights.py: [prob_yes_orig, prob_yes_neg, confidence]
            # Extract the third element (confidence) if it's an array
            if isinstance(weight_raw, list):
                if len(weight_raw) >= 3:
                    weight = weight_raw[2]  # Use confidence (third element)
                else:
                    weight = 0.5  # Fallback if array is too short
            else:
                weight = weight_raw  # Use as-is if it's already a float

            # Convert weight to integer weight for MaxSAT
            # We use log-odds: w / (1-w) and scale by 1000
            if weight >= 1.0:
                int_weight = 10000  # Very high weight
            elif weight <= 0.0:
                int_weight = 1  # Very low weight
            else:
                # Log-odds ratio scaled to integer
                log_odds = weight / (1 - weight)
                int_weight = max(1, int(log_odds * 1000))

            clauses = self.parser.parse(formula)
            for clause in clauses:
                self.wcnf.append(clause, weight=int_weight)

        return self.wcnf

    def encode_query(self, query_formula: str, negate: bool = False) -> List[List[int]]:
        """
        Encode a query formula as CNF clauses.

        Args:
            query_formula: Propositional formula (e.g., "P_1 & P_2")
            negate: If True, encode ¬query (for entailment checking)

        Returns:
            List of CNF clauses
        """
        if negate:
            # Wrap in negation
            query_formula = f"~({query_formula})"

        return self.parser.parse(query_formula)

    def get_prop_mapping(self) -> Tuple[Dict[str, int], Dict[int, str]]:
        """
        Get proposition-to-variable mappings.

        Returns:
            Tuple of (prop_to_var, var_to_prop)
        """
        return self.prop_to_var, self.var_to_prop


def encode_logified_structure(logified_structure: Dict[str, Any]) -> Tuple[WCNF, LogicEncoder]:
    """
    Convenience function to encode a logified structure.

    Args:
        logified_structure: JSON structure with propositions and constraints

    Returns:
        Tuple of (WCNF formula, LogicEncoder instance)
    """
    encoder = LogicEncoder(logified_structure)
    wcnf = encoder.encode()
    return wcnf, encoder
