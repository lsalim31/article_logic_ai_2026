#!/usr/bin/env python3
"""
Setup script for article_logic_ai_2026 package.

Installation (development mode, from code/ directory):
    pip install -e .

This makes all subpackages importable from anywhere:
    from from_text_to_logic.logify import LogifyConverter
    from baseline_rag.chunker import chunk_document
    from logic_solver.encoding import encode_to_sat
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r') as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]
else:
    requirements = []

# Add additional dependencies not in requirements.txt
additional_requirements = [
    'sentence-transformers>=2.2.0',  # For SBERT in weights.py and retriever.py
    'PyMuPDF>=1.23.0',               # For PDF reading (fitz)
    'python-docx>=0.8.11',           # For DOCX reading
]

# Combine requirements, avoiding duplicates
all_requirements = list(set(requirements + additional_requirements))

setup(
    name='article_logic_ai_2026',
    version='0.1.0',
    description='Neuro-symbolic AI: Text to Logic Pipeline with MaxSAT Solving',
    author='Logic AI Research Team',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=all_requirements,
    extras_require={
        'experiments': [
            'datasets>=2.14.0',     # For LogicBench experiments
            'z3-solver>=4.12.0',    # For FOL experiments
        ],
        'dev': [
            'pytest>=7.4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'logify=from_text_to_logic.logify:main',
            'weights=from_text_to_logic.weights:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
