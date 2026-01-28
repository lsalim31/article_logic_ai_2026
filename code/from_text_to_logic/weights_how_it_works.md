# Weights.py - How It Works

## Overview

`weights.py` verifies whether a document **endorses** a soft constraint as a general, necessary rule. It outputs calibrated probability scores derived from LLM logprobs.

---

## High-Level Algorithm

```
INPUT:  Document path + Soft constraint (natural language)
OUTPUT: Probability that the document endorses the constraint
```

**Pipeline:**

1. **Extract** text from document (PDF/DOCX/TXT)
2. **Chunk** the text into overlapping segments
3. **Retrieve** the top-k most relevant chunks using SBERT similarity
4. **Verify** via LLM with a YES/NO prompt
5. **Extract** logprobs for YES and NO tokens
6. **Return** logits and probabilities

---

## Detailed Steps

### Step 1: Document Text Extraction

The algorithm accepts documents in three formats:
- **PDF**: Extracted using PyMuPDF (`fitz`)
- **DOCX**: Extracted using `python-docx`
- **TXT**: Read directly

This produces the full document text `T`.

### Step 2: Chunking

The document text `T` is segmented into overlapping chunks using whitespace tokenization:

```
Parameters:
- chunk_size: 512 tokens (default)
- overlap: 50 tokens (default)
```

**Why chunking?**
- Documents may be very long
- Retrieval works better on focused segments
- Reduces noise from irrelevant sections

**Overlap rationale:**
- Ensures context spanning chunk boundaries is not lost
- A sentence split between chunks will appear (partially) in both

### Step 3: SBERT Retrieval

We use Sentence-BERT to find the most relevant chunks for the soft constraint.

**Process:**
1. Load SBERT model (`all-MiniLM-L6-v2`)
2. Encode all chunks → matrix of shape `(num_chunks, embedding_dim)`
3. Encode the soft constraint S → vector of shape `(embedding_dim,)`
4. Compute cosine similarity between S and each chunk
5. Select top-k chunks (k=10 by default)

**Why SBERT retrieval?**
- The soft constraint may only be relevant to a small portion of the document
- Passing the entire document to the LLM would exceed context limits and dilute signal
- Semantic similarity captures paraphrases and related concepts

### Step 4: LLM Verification

We construct a prompt that asks the LLM a binary YES/NO question:

```
You are a verifier that will answer with exactly one token: "YES" or "NO".
Do not produce any other text.

[TEXT]
<Top-k retrieved chunks, concatenated>

[CONSTRAINT]
<The soft constraint S>

[QUESTION]
Does the text endorse this constraint as a general, necessary rule?
Answer "YES" or "NO" with no other words.
```

**Key design choices:**
- **Single token output**: Forces the model to commit to YES or NO
- **"Endorse as a general, necessary rule"**: Distinguishes between:
  - The constraint being *mentioned* (not sufficient)
  - The constraint being *endorsed* (required for YES)
- **No reasoning allowed**: Prevents the model from hedging

### Step 5: Logprob Extraction

We call the OpenAI API with `logprobs=True` to get token-level log probabilities.

**API parameters:**
```python
logprobs=True,
top_logprobs=20  # Get top 20 candidates to ensure YES/NO are captured
```

**Extraction process:**
1. Access `response.choices[0].logprobs.content[0].top_logprobs`
2. Search for tokens matching "YES" or "NO" (case-insensitive)
3. Extract their logprob values

**Handling missing tokens:**
- If YES or NO is not in the top logprobs, it means the model assigns very low probability to that token
- We return `-inf` (or a large negative number like -100) in this case

### Step 6: Output Computation

**Logits** (raw log probabilities from the model):
```
logit_yes = log P(YES | prompt)
logit_no  = log P(NO | prompt)
```

**Probabilities** (exponentiated logits):
```
prob_yes = exp(logit_yes) = P(YES | prompt)
prob_no  = exp(logit_no)  = P(NO | prompt)
```

**Note:** `prob_yes + prob_no` may not equal 1.0 because:
- There are other possible tokens (e.g., "Maybe", "Possibly", punctuation)
- We only extract probabilities for YES and NO specifically

### Step 7: Negation Verification

For calibration, we also verify the **negated** version of each constraint:

```
Negated constraint: "It is not the case that {original constraint}"
```

This produces a second set of probabilities (`prob_yes_negated`, `prob_no_negated`).

### Step 8: Binary Softmax Confidence

We compute a final confidence score using the standard NLI approach:

```
confidence = P(YES|original) / (P(YES|original) + P(YES|negated))
```

This is equivalent to applying softmax over the entailment (original) and contradiction (negated) probabilities, dropping the "neutral" case.

**Interpretation:**
- `confidence > 0.6`: Document supports the constraint
- `confidence ≈ 0.5`: Ambiguous/uncertain
- `confidence < 0.4`: Document likely contradicts the constraint

**Why this works:**
- If both P(YES|original) and P(YES|negated) are high, confidence ≈ 0.5 (ambiguous)
- If P(YES|original) >> P(YES|negated), confidence → 1.0 (strong support)
- If P(YES|original) << P(YES|negated), confidence → 0.0 (contradiction)

---

## Mathematical Details

### Cosine Similarity (Step 3)

For query embedding `q` and chunk embedding `c`:

```
similarity(q, c) = (q · c) / (||q|| × ||c||)
```

Range: [-1, 1], where 1 = identical direction, 0 = orthogonal, -1 = opposite.

### Log Probability to Probability (Step 6)

The model outputs log probabilities (base e):

```
logit = log(prob)
prob  = exp(logit)
```

Examples:
| logit | prob |
|-------|------|
| 0.0   | 1.0  |
| -0.69 | 0.5  |
| -2.30 | 0.1  |
| -4.61 | 0.01 |
| -inf  | 0.0  |

---

## Usage Examples

### Python API

```python
from from_text_to_logic.weights import verify_constraint

result = verify_constraint(
    pathfile="document.pdf",
    text_s="Employees must wear safety goggles in the lab",
    api_key="sk-...",
    model="gpt-4o",
    temperature=0.0,
    k=10
)

print(f"P(YES) = {result['prob_yes']:.4f}")
print(f"P(NO)  = {result['prob_no']:.4f}")
```

### Command Line

```bash
python weights.py document.pdf \
    --constraint "Employees must wear safety goggles in the lab" \
    --api-key sk-... \
    --model gpt-4o \
    --k 10
```

---

## Output Format

Each soft constraint in the output JSON receives a `weight` array with 3 values:

```python
"weight": [
    0.9998,   # P(YES|original) - probability document supports original constraint
    0.8176,   # P(YES|negated) - probability document supports negated constraint
    0.5501    # confidence - binary softmax: P(orig) / (P(orig) + P(neg))
]
```

**Interpretation:**
- `weight[0]`: Raw probability the document supports the constraint
- `weight[1]`: Raw probability the document supports the negation
- `weight[2]`: Calibrated confidence score (use this for downstream analysis)

---

## Limitations

1. **Token variations**: We handle "YES"/"Yes"/"yes" and "NO"/"No"/"no", but other phrasings (e.g., "Yeah", "Nope") are not captured.

2. **Context window**: If top-k chunks exceed the model's context, truncation may occur.

3. **Retrieval quality**: If SBERT fails to retrieve relevant chunks, the LLM may answer based on incomplete information.

4. **Reasoning models**: Models like GPT-5.x, o1, o3 may not support logprobs. Use GPT-4o or similar for this task.

---

## Dependencies

- `sentence-transformers`: SBERT embeddings
- `openai`: LLM API calls
- `numpy`: Numerical operations
- `PyMuPDF` (optional): PDF extraction
- `python-docx` (optional): DOCX extraction
