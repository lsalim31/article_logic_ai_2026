#!/usr/bin/env python3
"""
Setup script for the Logify Neuro-Symbolic Reasoning System.

Installation (development mode, from code/ directory):
    pip install -e .

This makes all subpackages importable from anywhere:
    from from_text_to_logic.logify import LogifyConverter
    from logic_solver import LogicSolver
    from interface_with_user.translate import translate_query

Console scripts installed:
    logify-cli    - Main CLI (python main.py equivalent)
    logify        - Direct logify command
    weights       - Direct weights command
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

# Read long description from README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='logify-neuro-symbolic',
    version='0.2.0',
    description='Neuro-Symbolic AI: Text to Propositional Logic with MaxSAT Reasoning',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Logify Research Team',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=requirements,
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
            # Main CLI entry point
            'logify-cli=main:main',
            # Direct module entry points
            'logify=from_text_to_logic.logify:main',
            'weights=from_text_to_logic.weights:main',
            'translate=interface_with_user.translate:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Text Processing :: Linguistic',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords='neuro-symbolic, propositional-logic, maxsat, nlp, reasoning, llm',
    project_urls={
        'Documentation': 'https://github.com/your-org/logify#readme',
        'Source': 'https://github.com/your-org/logify',
    },
)
