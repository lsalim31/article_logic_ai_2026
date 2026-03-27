"""
Logic Solver Module

This module provides SAT/MaxSAT-based reasoning over logified structures.
"""

from .encoding import LogicEncoder, FormulaParser, encode_logified_structure
from .maxsat import LogicSolver, SolverResult, solve_query

__all__ = [
    'LogicEncoder',
    'FormulaParser',
    'encode_logified_structure',
    'LogicSolver',
    'SolverResult',
    'solve_query'
]
