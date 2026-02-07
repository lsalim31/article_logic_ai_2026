# Experiment Debug Report
## Summary
- Total: 30
- Correct: 24
- Incorrect: 6
- Errors: 0

## Detailed Results
### test-1
- Hypothesis: Alice is a university student.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_1
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 10.212

**Raw Fields**
- hypothesis_key: test-1
- formula: P_1
- query_mode: entailment
- error: None

---
### test-2
- Hypothesis: Alice studies computer science.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_5
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 4.858

**Raw Fields**
- hypothesis_key: test-2
- formula: P_5
- query_mode: entailment
- error: None

---
### test-3
- Hypothesis: If Alice studies hard, she passes her exams.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_10 ⟹ P_11
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 12.243

**Raw Fields**
- hypothesis_key: test-3
- formula: P_10 ⟹ P_11
- query_mode: entailment
- error: None

---
### test-4
- Hypothesis: Alice typically studies hard before exams.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_12
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 7.733

**Raw Fields**
- hypothesis_key: test-4
- formula: P_12
- query_mode: entailment
- error: None

---
### test-5
- Hypothesis: When Alice is focused, she completes her assignments on time.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_14 ⟹ P_15
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 14.760

**Raw Fields**
- hypothesis_key: test-5
- formula: P_14 ⟹ P_15
- query_mode: entailment
- error: None

---
### test-6
- Hypothesis: Alice sometimes gets distracted by social media.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_16
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 8.605

**Raw Fields**
- hypothesis_key: test-6
- formula: P_16
- query_mode: entailment
- error: None

---
### test-7
- Hypothesis: Alice works part-time at the campus library.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_19
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 7.008

**Raw Fields**
- hypothesis_key: test-7
- formula: P_19
- query_mode: entailment
- error: None

---
### test-8
- Hypothesis: Her assignments are due every Friday.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_22
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 5.822

**Raw Fields**
- hypothesis_key: test-8
- formula: P_22
- query_mode: entailment
- error: None

---
### test-9
- Hypothesis: Alice rarely studies late at night.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_29
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 7.044

**Raw Fields**
- hypothesis_key: test-9
- formula: P_29
- query_mode: entailment
- error: None

---
### test-10
- Hypothesis: Alice is a student who studies hard before exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 19.591

**Raw Fields**
- hypothesis_key: test-10
- formula: NONE
- query_mode: entailment
- error: None

---
### test-11
- Hypothesis: Alice is not a university student.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_1
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 60.559

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
- Confidence: 0.0
- Formula: ¬P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 25.180

**Raw Fields**
- hypothesis_key: test-12
- formula: ¬P_6
- query_mode: entailment
- error: None

---
### test-13
- Hypothesis: Alice fails her exams even when she studies hard.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: P_10 ⟹ ¬P_11
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 57.089

**Raw Fields**
- hypothesis_key: test-13
- formula: P_10 ⟹ ¬P_11
- query_mode: entailment
- error: None

---
### test-14
- Hypothesis: Alice never studies hard before exams.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_13
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 33.833

**Raw Fields**
- hypothesis_key: test-14
- formula: ¬P_13
- query_mode: entailment
- error: None

---
### test-15
- Hypothesis: When Alice is focused, she misses assignments.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_14 ⟹ ¬P_15
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 16.600

**Raw Fields**
- hypothesis_key: test-15
- formula: P_14 ⟹ ¬P_15
- query_mode: entailment
- error: None

---
### test-16
- Hypothesis: Alice never gets distracted by social media.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_17
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 28.618

**Raw Fields**
- hypothesis_key: test-16
- formula: ¬P_17
- query_mode: entailment
- error: None

---
### test-17
- Hypothesis: Alice does not work part-time at the campus library.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_19
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 35.960

**Raw Fields**
- hypothesis_key: test-17
- formula: ¬P_19
- query_mode: entailment
- error: None

---
### test-18
- Hypothesis: Her assignments are due every Monday.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_23
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 47.521

**Raw Fields**
- hypothesis_key: test-18
- formula: ¬P_23
- query_mode: entailment
- error: None

---
### test-19
- Hypothesis: Alice often studies late at night.
- Ground Truth: FALSE
- Prediction: TRUE
- Confidence: 1
- Formula: P_30
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 48.646

**Raw Fields**
- hypothesis_key: test-19
- formula: P_30
- query_mode: entailment
- error: None

---
### test-20
- Hypothesis: Alice is a high school student.
- Ground Truth: FALSE
- Prediction: TRUE
- Confidence: 1
- Formula: P_3
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 55.452

**Raw Fields**
- hypothesis_key: test-20
- formula: P_3
- query_mode: entailment
- error: None

---
### test-21
- Hypothesis: Alice lives in New York.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 5.875

**Raw Fields**
- hypothesis_key: test-21
- formula: NONE
- query_mode: entailment
- error: None

---
### test-22
- Hypothesis: Alice's major is mathematics.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 1.0
- Formula: P_7
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 50.820

**Raw Fields**
- hypothesis_key: test-22
- formula: P_7
- query_mode: entailment
- error: None

---
### test-23
- Hypothesis: Alice always completes assignments early.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_15
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 25.404

**Raw Fields**
- hypothesis_key: test-23
- formula: P_15
- query_mode: entailment
- error: None

---
### test-24
- Hypothesis: Alice is focused during every exam.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.0
- Formula: P_31 ⟹ P_14
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 21.577

**Raw Fields**
- hypothesis_key: test-24
- formula: P_31 ⟹ P_14
- query_mode: entailment
- error: None

---
### test-25
- Hypothesis: Alice works full-time.
- Ground Truth: UNCERTAIN
- Prediction: TRUE
- Confidence: 1
- Formula: P_21
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 59.257

**Raw Fields**
- hypothesis_key: test-25
- formula: P_21
- query_mode: entailment
- error: None

---
### test-26
- Hypothesis: Alice uses social media only on weekends.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 8.466

**Raw Fields**
- hypothesis_key: test-26
- formula: NONE
- query_mode: entailment
- error: None

---
### test-27
- Hypothesis: Alice's library job is unpaid.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 6.196

**Raw Fields**
- hypothesis_key: test-27
- formula: NONE
- query_mode: entailment
- error: None

---
### test-28
- Hypothesis: Alice's exams are oral.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 8.190

**Raw Fields**
- hypothesis_key: test-28
- formula: NONE
- query_mode: entailment
- error: None

---
### test-29
- Hypothesis: Alice studies in the library every day.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 15.222

**Raw Fields**
- hypothesis_key: test-29
- formula: NONE
- query_mode: entailment
- error: None

---
### test-30
- Hypothesis: Alice has a scholarship.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: NONE
- Query Mode: entailment
- Explanation: No matching proposition for hypothesis
- Error: None
- Latency (sec): 5.656

**Raw Fields**
- hypothesis_key: test-30
- formula: NONE
- query_mode: entailment
- error: None

---
