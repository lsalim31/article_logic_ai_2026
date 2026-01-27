# Logic Solver Test and Demo Files

This directory now contains all testing and demo files related to the logic solver module.

## Test Files

### Core Tests
- **test_logic_solver.py** - Basic test script for the logic solver module
- **comprehensive_test.py** - Comprehensive test suite covering all components (encoding, parsing, SAT solving, edge cases)

### Debug Scripts
- **debug_solver.py** - Debugging script for the solver encoding and clause generation
- **debug_consistency.py** - Script for debugging consistency checking

### Demo Files
- **demo_complete_system.py** - Complete end-to-end demo of the logic solver system
- **try_it_yourself.py** - Interactive demo for testing queries

## Running the Tests

All test and demo scripts have been updated with proper import paths. To run them:

```bash
cd /workspace/repo/code/logic_solver
python3 test_logic_solver.py
python3 comprehensive_test.py
python3 demo_complete_system.py
python3 try_it_yourself.py
```

## Import Path Fix

All files have been updated to add the parent directory to the Python path, allowing them to import the `logic_solver` package correctly:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic_solver import LogicSolver
```

## Dependencies

These scripts require:
- pysat (PySAT library for SAT/MaxSAT solving)
- The logified data file at `/workspace/repo/artifacts/code/logify2_full_demo.json`
