# Dependency Management and Bug Fixes

## Date: 2026-01-25

## Issues Identified and Fixed

### 1. **Format Mismatch Bug in logify2.py** ❌ → ✅

**Problem:**
- `logify2.py` was calling `format_triples()` which outputs tab-separated format
- The prompt (`prompt_logify2`) expects JSON array format: `[["subject", "predicate", "object", sentence_index]]`
- This mismatch caused the LLM to receive incorrectly formatted data

**Root Cause:**
- The codebase has TWO formatting methods:
  - `format_triples()` → tab-separated: `subject\tpredicate\tobject`
  - `format_triples_json()` → JSON array: `[["subject", "predicate", "object", sentence_index]]`
- The wrong one was being used

**Fix Applied:**
```python
# File: /workspace/repo/code/from_text_to_logic/logify2.py
# Changed line 49 from:
formatted_triples = self.extractor.format_triples(openie_triples)
# To:
formatted_triples = self.extractor.format_triples_json(openie_triples, indent=0)
```

**Additional Fixes:**
- Updated `logic_converter.py` to use "RELATION TRIPLES" label (matching prompt) instead of "OPENIE TRIPLES"
- Updated `run_logify2_student_assessment.py` to use correct format

### 2. **Missing Dependencies**

**Problems Encountered:**
1. **Stanza models not downloaded**
   - Error: `Cannot load model from /workspace/stanza_resources/en/pos/combined_charlm.pt`

2. **CoreNLP not installed**
   - Error: `Please install CoreNLP by running stanza.install_corenlp()`

3. **Java not installed**
   - Error: `FileNotFoundError: [Errno 2] No such file or directory: 'java'`

**Solutions Applied:**
```bash
# 1. Download Stanza models
python3 -c "import stanza; stanza.download('en', processors='tokenize,pos,lemma,depparse')"

# 2. Install CoreNLP
python3 -c "import stanza; stanza.install_corenlp()"

# 3. Install Java
apt-get update && apt-get install -y default-jdk
```

## Long-Term Dependency Management Strategy

### Approach 1: Docker Container with Pre-installed Dependencies ⭐ RECOMMENDED

**Benefits:**
- One-time setup
- Consistent environment
- No manual dependency installation

**Implementation:**
Create `/workspace/repo/Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    default-jdk \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY code/from_text_to_logic/requirements_openie.txt .
RUN pip install --no-cache-dir -r requirements_openie.txt

# Download Stanza models and CoreNLP
RUN python3 -c "import stanza; stanza.download('en', processors='tokenize,pos,lemma,depparse')" && \\
    python3 -c "import stanza; stanza.install_corenlp()"

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy code
COPY . /app

CMD ["/bin/bash"]
```

**Usage:**
```bash
docker build -t logify2 .
docker run -it -v $(pwd):/app logify2
python code/from_text_to_logic/logify2.py --api-key YOUR_KEY --file input.txt
```

### Approach 2: Setup Script

**Implementation:**
Create `/workspace/repo/setup_dependencies.sh`:
```bash
#!/bin/bash
set -e

echo "Installing system dependencies..."
apt-get update
apt-get install -y default-jdk

echo "Installing Python dependencies..."
pip install -r code/from_text_to_logic/requirements_openie.txt

echo "Downloading Stanza models..."
python3 -c "import stanza; stanza.download('en', processors='tokenize,pos,lemma,depparse')"

echo "Installing CoreNLP..."
python3 -c "import stanza; stanza.install_corenlp()"

echo "✓ All dependencies installed successfully!"
```

**Usage:**
```bash
chmod +x setup_dependencies.sh
./setup_dependencies.sh
```

### Approach 3: Conda Environment (Alternative)

**Implementation:**
Create `/workspace/repo/environment.yml`:
```yaml
name: logify2
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - openjdk=17
  - pip
  - pip:
    - stanza
    - openai
    - torch
    - torchvision
    - torchaudio
```

**Usage:**
```bash
conda env create -f environment.yml
conda activate logify2
python3 -c "import stanza; stanza.download('en')"
python3 -c "import stanza; stanza.install_corenlp()"
```

### Approach 4: Requirements with Post-Install Script

**Implementation:**
Create `/workspace/repo/code/from_text_to_logic/setup.py`:
```python
#!/usr/bin/env python3
import subprocess
import sys

def setup_nlp_resources():
    """Download required NLP models and CoreNLP"""
    print("Downloading Stanza models...")
    import stanza
    stanza.download('en', processors='tokenize,pos,lemma,depparse')

    print("Installing CoreNLP...")
    stanza.install_corenlp()

    print("✓ Setup complete!")

if __name__ == "__main__":
    setup_nlp_resources()
```

**Usage:**
```bash
pip install -r requirements_openie.txt
python code/from_text_to_logic/setup.py
```

## Recommended Workflow for Future Use

### For Development:
1. Use **Docker** (Approach 1) for consistent environment
2. Mount code directory as volume for live editing
3. Pre-build image with all dependencies

### For Production:
1. Use Docker with multi-stage build
2. Cache models in Docker layer
3. Use environment variables for API keys

### For Quick Testing:
1. Use **setup script** (Approach 2)
2. Cache dependencies in persistent volume
3. Document Java requirement in README

## Environment Variables to Set

```bash
# Required for OpenAI API
export OPENAI_API_KEY=your_key_here

# Optional: Specify CoreNLP location
export CORENLP_HOME=/workspace/stanza_corenlp

# Optional: Specify Stanza resources
export STANZA_RESOURCES_DIR=/workspace/stanza_resources
```

## Files Modified

1. **`/workspace/repo/code/from_text_to_logic/logify2.py`**
   - Fixed: Changed `format_triples()` to `format_triples_json()`

2. **`/workspace/repo/code/from_text_to_logic/logic_converter.py`**
   - Fixed: Changed "OPENIE TRIPLES" to "RELATION TRIPLES" label

3. **`/workspace/repo/artifacts/few_shot_examples/run_logify2_student_assessment.py`**
   - Fixed: Changed to use `format_triples_json()`

## Testing the Fix

```bash
# Test OpenIE extraction (Stage 1)
cd /workspace/repo/artifacts/few_shot_examples
python run_logify2_student_assessment.py

# Test full pipeline (Stages 1 + 2) - requires API key
export OPENAI_API_KEY=your_key_here
python run_logify2_student_assessment.py
```

## Next Steps

1. **Create Dockerfile** for reproducible environment
2. **Update README** with dependency installation instructions
3. **Add CI/CD** to test dependency installation
4. **Document** the two formatting methods in openie_extractor.py
5. **Consider** deprecating `format_triples()` or renaming for clarity

## Why This Matters

Without proper dependency management:
- ❌ New users can't run the code
- ❌ Inconsistent environments cause bugs
- ❌ Manual setup is error-prone
- ❌ Difficult to reproduce results

With proper dependency management:
- ✅ One-command setup
- ✅ Consistent environments
- ✅ Reproducible results
- ✅ Easy onboarding for new users
