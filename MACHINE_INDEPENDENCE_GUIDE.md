# Machine Independence Guide

This document explains how the codebase has been designed for machine independence and what needs to be configured for deployment on different platforms (local, Google Cloud, AWS, etc.).

## Current Status: ✅ MACHINE INDEPENDENT

The codebase is already machine-independent. All critical components use dynamic path computation.

## Key Features

### 1. Dynamic Path Computation

All test and demo files compute paths relative to their location:

```python
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
REPO_DIR = CODE_DIR.parent
ARTIFACTS_DIR = REPO_DIR / "artifacts" / "code"
```

**Files using this pattern:**
- `code/logic_solver/comprehensive_test.py`
- `code/logic_solver/debug_consistency.py`
- `code/logic_solver/debug_solver.py`
- `code/logic_solver/demo_complete_system.py`
- `code/logic_solver/test_logic_solver.py`
- `code/logic_solver/try_it_yourself.py`
- `code/from_text_to_logic/weights.py`
- `code/interface_with_user/translate.py`

### 2. Cross-Platform Path Operations

- All file operations use `pathlib.Path` or `os.path.join()`
- Both are cross-platform compatible (Windows, Linux, Mac)
- Path separators are handled automatically

### 3. No Hardcoded Absolute Paths

- All `/workspace/repo/...` paths have been removed
- All paths are computed relative to script location
- Works regardless of installation directory

### 4. Package Structure

The code is organized as proper Python packages with `__init__.py` files:

```
code/
├── from_text_to_logic/
│   ├── __init__.py
│   ├── logify.py
│   └── weights.py
├── interface_with_user/
│   ├── __init__.py
│   └── translate.py
├── logic_solver/
│   ├── __init__.py
│   ├── encoding.py
│   └── ...
├── baseline_rag/
│   ├── __init__.py
│   └── ...
└── ...
```

## Required Setup for New Machines

### 1. Install Python 3.8+

```bash
# Check Python version
python3 --version

# If not installed, install Python 3.8 or higher
```

### 2. Clone Repository

```bash
git clone https://github.com/lsalim31/article_logic_ai_2026.git
cd article_logic_ai_2026
```

### 3. Install Dependencies

```bash
cd code
pip install -r requirements.txt
```

**Current dependencies in `requirements.txt`:**
```
python-sat>=0.1.8.dev0
stanza>=1.7.0
openai>=1.0.0
numpy>=1.24.0
```

**Additional dependencies needed (add these):**
```
sentence-transformers>=2.2.0  # For SBERT in translate.py and weights.py
PyMuPDF>=1.23.0  # For PDF reading (fitz)
python-docx>=0.8.11  # For DOCX reading
datasets>=2.14.0  # For experiments
```

### 4. Set Up API Keys

API keys can be provided in three ways:

**Option A: Command-line arguments (Recommended for security)**
```bash
python logify.py input.txt --api-key YOUR_KEY
```

**Option B: Environment variables**
```bash
export OPENAI_API_KEY=your_key_here
export OPENROUTER_API_KEY=your_openrouter_key_here
```

**Option C: .env file (Not implemented yet)**
```bash
cp .env.template .env
# Edit .env with your keys
```

## Google Cloud Deployment

### Option 1: Google Compute Engine (VM)

```bash
# Create VM instance
gcloud compute instances create logic-ai-vm \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud

# SSH into VM
gcloud compute ssh logic-ai-vm

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Clone and setup
git clone https://github.com/lsalim31/article_logic_ai_2026.git
cd article_logic_ai_2026/code
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add missing dependencies
pip install sentence-transformers PyMuPDF python-docx datasets
```

### Option 2: Google Cloud Run (Containerized)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy code
COPY code/ /app/code/
COPY artifacts/ /app/artifacts/

# Install dependencies
WORKDIR /app/code
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install sentence-transformers PyMuPDF python-docx

# Set entrypoint
CMD ["python", "logic_solver/demo_complete_system.py"]
```

Deploy:
```bash
gcloud run deploy logic-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## AWS Deployment

Similar to Google Cloud, works on:
- EC2 instances
- Lambda functions (with containerization)
- ECS/Fargate

## Platform-Specific Notes

### Windows
- Path separators: Automatically handled by `pathlib.Path`
- Virtual env activation: `venv\Scripts\activate`
- No changes needed to code

### Linux
- Path separators: Automatically handled
- Virtual env activation: `source venv/bin/activate`
- Recommended for production

### macOS
- Same as Linux
- M1/M2 compatibility: All dependencies support ARM64

## Verification Checklist

After setup on a new machine, verify:

```bash
# 1. Check Python version
python3 --version  # Should be 3.8+

# 2. Check imports work
cd code
python3 -c "import logic_solver; print('✓ logic_solver works')"
python3 -c "import from_text_to_logic; print('✓ from_text_to_logic works')"

# 3. Check paths are computed correctly
cd logic_solver
python3 -c "
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
print(f'Repo root: {SCRIPT_DIR.parent.parent}')
"

# 4. Run a simple test
python3 demo_complete_system.py
```

## Known Issues and Fixes

### Issue 1: ImportError for sentence_transformers
**Fix:** `pip install sentence-transformers`

### Issue 2: ImportError for fitz (PyMuPDF)
**Fix:** `pip install PyMuPDF`

### Issue 3: ImportError for docx
**Fix:** `pip install python-docx`

### Issue 4: Path not found errors
**Cause:** Running scripts from wrong directory
**Fix:** Always run from the code directory or use absolute imports

## Complete requirements.txt

Here's the complete list of dependencies needed:

```
# Core dependencies
python-sat>=0.1.8.dev0
stanza>=1.7.0
sentence-transformers>=2.2.0
openai>=1.0.0
numpy>=1.24.0

# Document processing
PyMuPDF>=1.23.0
python-docx>=0.8.11

# Experiments
datasets>=2.14.0

# Optional
# z3-solver>=4.12.0  # For FOL experiments
# pytest>=7.4.0  # For testing
```

## Summary

✅ **Code is machine-independent**
- All paths computed dynamically
- Cross-platform compatible
- No hardcoded absolute paths

⚠️ **Manual setup required**
- Install dependencies from requirements.txt
- Add missing dependencies (sentence-transformers, PyMuPDF, python-docx)
- Provide API keys via command-line or environment variables

📝 **Recommended improvements**
1. Update requirements.txt with all dependencies
2. Create setup.py for `pip install -e .`
3. Add .env.template for API key configuration
4. Create Dockerfile for containerized deployment

## Testing on New Machine

```bash
# Full test procedure
git clone https://github.com/lsalim31/article_logic_ai_2026.git
cd article_logic_ai_2026/code
pip install -r requirements.txt
pip install sentence-transformers PyMuPDF python-docx datasets

# Set API key
export OPENAI_API_KEY=your_key_here

# Test logic solver
cd logic_solver
python3 demo_complete_system.py

# Test translate
cd ../interface_with_user
python3 translate.py "test query" ../artifacts/code/logify2_full_demo.json --api-key $OPENAI_API_KEY --model gpt-4o
```

All tests should pass without modification to the code.
