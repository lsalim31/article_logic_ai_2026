# Experiment Debug Report
## Summary
- Total: 30
- Correct: 9
- Incorrect: 21
- Errors: 0

## Detailed Results
### test-1
- Hypothesis: Alice is a university student.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_1
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 8.242

**Raw Fields**
- hypothesis_key: test-1
- formula: P_1
- query_mode: entailment
- error: None

---
### test-2
- Hypothesis: Alice studies computer science.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_3
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 4.762

**Raw Fields**
- hypothesis_key: test-2
- formula: P_3
- query_mode: entailment
- error: None

---
### test-3
- Hypothesis: If Alice studies hard, she passes her exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_5 ⟹ P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 6.692

**Raw Fields**
- hypothesis_key: test-3
- formula: P_5 ⟹ P_6
- query_mode: entailment
- error: None

---
### test-4
- Hypothesis: Alice typically studies hard before exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_7
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 5.215

**Raw Fields**
- hypothesis_key: test-4
- formula: P_7
- query_mode: entailment
- error: None

---
### test-5
- Hypothesis: When Alice is focused, she completes her assignments on time.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_8 ⟹ P_9
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 21.208

**Raw Fields**
- hypothesis_key: test-5
- formula: P_8 ⟹ P_9
- query_mode: entailment
- error: None

---
### test-6
- Hypothesis: Alice sometimes gets distracted by social media.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 17.900

**Raw Fields**
- hypothesis_key: test-6
- formula: P_11
- query_mode: entailment
- error: None

---
### test-7
- Hypothesis: Alice works part-time at the campus library.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_12 ∧ P_13
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 9.502

**Raw Fields**
- hypothesis_key: test-7
- formula: P_12 ∧ P_13
- query_mode: entailment
- error: None

---
### test-8
- Hypothesis: Her assignments are due every Friday.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_15
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 5.118

**Raw Fields**
- hypothesis_key: test-8
- formula: P_15
- query_mode: entailment
- error: None

---
### test-9
- Hypothesis: Alice rarely studies late at night.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: P_16
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 24.617

**Raw Fields**
- hypothesis_key: test-9
- formula: P_16
- query_mode: entailment
- error: None

---
### test-10
- Hypothesis: Alice is a student who studies hard before exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_2 ∧ P_7
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 19.574

**Raw Fields**
- hypothesis_key: test-10
- formula: P_2 ∧ P_7
- query_mode: entailment
- error: None

---
### test-11
- Hypothesis: Alice is not a university student.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: ¬P_1
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 33.797

**Raw Fields**
- hypothesis_key: test-11
- formula: ¬P_1
- query_mode: entailment
- error: None

---
### test-12
- Hypothesis: Alice studies biology.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_4
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 30.539

**Raw Fields**
- hypothesis_key: test-12
- formula: P_4
- query_mode: entailment
- error: None

---
### test-13
- Hypothesis: Alice fails her exams even when she studies hard.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: ¬P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 42.945

**Raw Fields**
- hypothesis_key: test-13
- formula: ¬P_6
- query_mode: entailment
- error: None

---
### test-14
- Hypothesis: Alice never studies hard before exams.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: ¬P_7
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 34.179

**Raw Fields**
- hypothesis_key: test-14
- formula: ¬P_7
- query_mode: entailment
- error: None

---
### test-15
- Hypothesis: When Alice is focused, she misses assignments.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_8 ⟹ ¬P_10
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 33.777

**Raw Fields**
- hypothesis_key: test-15
- formula: P_8 ⟹ ¬P_10
- query_mode: entailment
- error: None

---
### test-16
- Hypothesis: Alice never gets distracted by social media.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: ¬P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 22.338

**Raw Fields**
- hypothesis_key: test-16
- formula: ¬P_11
- query_mode: entailment
- error: None

---
### test-17
- Hypothesis: Alice does not work part-time at the campus library.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: ¬(P_12 ∧ P_13)
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 32.337

**Raw Fields**
- hypothesis_key: test-17
- formula: ¬(P_12 ∧ P_13)
- query_mode: entailment
- error: None

---
### test-18
- Hypothesis: Her assignments are due every Monday.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_15
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 35.255

**Raw Fields**
- hypothesis_key: test-18
- formula: P_15
- query_mode: entailment
- error: None

---
### test-19
- Hypothesis: Alice often studies late at night.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: P_16
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 33.110

**Raw Fields**
- hypothesis_key: test-19
- formula: P_16
- query_mode: entailment
- error: None

---
### test-20
- Hypothesis: Alice is a high school student.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_1
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 33.534

**Raw Fields**
- hypothesis_key: test-20
- formula: P_1
- query_mode: entailment
- error: None

---
### test-21
- Hypothesis: Alice lives in New York.
- Ground Truth: UNCERTAIN
- Prediction: TRUE
- Confidence: nan
- Formula: P_1 ∨ ¬P_1
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 31.875

**Raw Fields**
- hypothesis_key: test-21
- formula: P_1 ∨ ¬P_1
- query_mode: entailment
- error: None

---
### test-22
- Hypothesis: Alice's major is mathematics.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_3 ∨ P_4 ∨ P_7 ∨ P_5 ∨ P_12 ∨ P_14 ∨ P_16 ∨ P_8 ∨ P_1 ∨ P_2 ∨ P_13 ∨ P_6 ∨ P_9 ∨ P_10 ∨ P_15 ∨ P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 51.557

**Raw Fields**
- hypothesis_key: test-22
- formula: P_3 ∨ P_4 ∨ P_7 ∨ P_5 ∨ P_12 ∨ P_14 ∨ P_16 ∨ P_8 ∨ P_1 ∨ P_2 ∨ P_13 ∨ P_6 ∨ P_9 ∨ P_10 ∨ P_15 ∨ P_11
- query_mode: entailment
- error: None

---
### test-23
- Hypothesis: Alice always completes assignments early.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_9
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 35.336

**Raw Fields**
- hypothesis_key: test-23
- formula: P_9
- query_mode: entailment
- error: None

---
### test-24
- Hypothesis: Alice is focused during every exam.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: P_8
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 16.653

**Raw Fields**
- hypothesis_key: test-24
- formula: P_8
- query_mode: entailment
- error: None

---
### test-25
- Hypothesis: Alice works full-time.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_14
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 54.882

**Raw Fields**
- hypothesis_key: test-25
- formula: P_14
- query_mode: entailment
- error: None

---
### test-26
- Hypothesis: Alice uses social media only on weekends.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 25.361

**Raw Fields**
- hypothesis_key: test-26
- formula: P_11
- query_mode: entailment
- error: None

---
### test-27
- Hypothesis: Alice's library job is unpaid.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_13
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 36.262

**Raw Fields**
- hypothesis_key: test-27
- formula: P_13
- query_mode: entailment
- error: None

---
### test-28
- Hypothesis: Alice's exams are oral.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 39.804

**Raw Fields**
- hypothesis_key: test-28
- formula: P_6
- query_mode: entailment
- error: None

---
### test-29
- Hypothesis: Alice studies in the library every day.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_4
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 32.700

**Raw Fields**
- hypothesis_key: test-29
- formula: P_4
- query_mode: entailment
- error: None

---
### test-30
- Hypothesis: Alice has a scholarship.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_12 ∨ P_13 ∨ P_14 ∨ P_4 ∨ P_1 ∨ P_3 ∨ P_2 ∨ P_5 ∨ P_7 ∨ P_16 ∨ P_6 ∨ P_9 ∨ P_10 ∨ P_8 ∨ P_15 ∨ P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 29.386

**Raw Fields**
- hypothesis_key: test-30
- formula: P_12 ∨ P_13 ∨ P_14 ∨ P_4 ∨ P_1 ∨ P_3 ∨ P_2 ∨ P_5 ∨ P_7 ∨ P_16 ∨ P_6 ∨ P_9 ∨ P_10 ∨ P_8 ∨ P_15 ∨ P_11
- query_mode: entailment
- error: None

---
