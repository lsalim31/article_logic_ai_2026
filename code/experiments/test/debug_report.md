# Experiment Debug Report
## Summary
- Total: 30
- Correct: 9
- Incorrect: 8
- Errors: 13

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
- Latency (sec): 12.353

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
- Formula: P_3
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 8.049

**Raw Fields**
- hypothesis_key: test-2
- formula: P_3
- query_mode: entailment
- error: None

---
### test-3
- Hypothesis: If Alice studies hard, she passes her exams.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_4 ⟹ P_5
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 12.561

**Raw Fields**
- hypothesis_key: test-3
- formula: P_4 ⟹ P_5
- query_mode: entailment
- error: None

---
### test-4
- Hypothesis: Alice typically studies hard before exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 0.6002004008016032
- Formula: P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 18.450

**Raw Fields**
- hypothesis_key: test-4
- formula: P_6
- query_mode: entailment
- error: None

---
### test-5
- Hypothesis: When Alice is focused, she completes her assignments on time.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_7 ⟹ P_8
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 11.103

**Raw Fields**
- hypothesis_key: test-5
- formula: P_7 ⟹ P_8
- query_mode: entailment
- error: None

---
### test-6
- Hypothesis: Alice sometimes gets distracted by social media.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_10
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 9.471

**Raw Fields**
- hypothesis_key: test-6
- formula: P_10
- query_mode: entailment
- error: None

---
### test-7
- Hypothesis: Alice works part-time at the campus library.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_11 ∧ P_12
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 13.968

**Raw Fields**
- hypothesis_key: test-7
- formula: P_11 ∧ P_12
- query_mode: entailment
- error: None

---
### test-8
- Hypothesis: Her assignments are due every Friday.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_13
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 12.268

**Raw Fields**
- hypothesis_key: test-8
- formula: P_13
- query_mode: entailment
- error: None

---
### test-9
- Hypothesis: Alice rarely studies late at night.
- Ground Truth: TRUE
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 12.006

**Raw Fields**
- hypothesis_key: test-9
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-10
- Hypothesis: Alice is a student who studies hard before exams.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Confidence: 0.6002004008016032
- Formula: P_2 ∧ P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 27.355

**Raw Fields**
- hypothesis_key: test-10
- formula: P_2 ∧ P_6
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
- Latency (sec): 37.566

**Raw Fields**
- hypothesis_key: test-11
- formula: ¬P_1
- query_mode: entailment
- error: None

---
### test-12
- Hypothesis: Alice studies biology.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 8.798

**Raw Fields**
- hypothesis_key: test-12
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-13
- Hypothesis: Alice fails her exams even when she studies hard.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.3997995991983968
- Formula: P_4 ⟹ ¬P_5
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 55.362

**Raw Fields**
- hypothesis_key: test-13
- formula: P_4 ⟹ ¬P_5
- query_mode: entailment
- error: None

---
### test-14
- Hypothesis: Alice never studies hard before exams.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.3997995991983968
- Formula: ¬P_6
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 34.933

**Raw Fields**
- hypothesis_key: test-14
- formula: ¬P_6
- query_mode: entailment
- error: None

---
### test-15
- Hypothesis: When Alice is focused, she misses assignments.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_7 ⟹ ¬P_9
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 46.543

**Raw Fields**
- hypothesis_key: test-15
- formula: P_7 ⟹ ¬P_9
- query_mode: entailment
- error: None

---
### test-16
- Hypothesis: Alice never gets distracted by social media.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: ¬P_10
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 63.712

**Raw Fields**
- hypothesis_key: test-16
- formula: ¬P_10
- query_mode: entailment
- error: None

---
### test-17
- Hypothesis: Alice does not work part-time at the campus library.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬(P_11 ∧ P_12)
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 66.595

**Raw Fields**
- hypothesis_key: test-17
- formula: ¬(P_11 ∧ P_12)
- query_mode: entailment
- error: None

---
### test-18
- Hypothesis: Her assignments are due every Monday.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 12.354

**Raw Fields**
- hypothesis_key: test-18
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-19
- Hypothesis: Alice often studies late at night.
- Ground Truth: FALSE
- Prediction: UNCERTAIN
- Confidence: 0.35
- Formula: P_14
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 35.600

**Raw Fields**
- hypothesis_key: test-19
- formula: P_14
- query_mode: entailment
- error: None

---
### test-20
- Hypothesis: Alice is a high school student.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 17.002

**Raw Fields**
- hypothesis_key: test-20
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-21
- Hypothesis: Alice lives in New York.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 18.737

**Raw Fields**
- hypothesis_key: test-21
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-22
- Hypothesis: Alice's major is mathematics.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 9.450

**Raw Fields**
- hypothesis_key: test-22
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-23
- Hypothesis: Alice always completes assignments early.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_8
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 34.040

**Raw Fields**
- hypothesis_key: test-23
- formula: P_8
- query_mode: entailment
- error: None

---
### test-24
- Hypothesis: Alice is focused during every exam.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 27.146

**Raw Fields**
- hypothesis_key: test-24
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-25
- Hypothesis: Alice works full-time.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 18.360

**Raw Fields**
- hypothesis_key: test-25
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-26
- Hypothesis: Alice uses social media only on weekends.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 23.312

**Raw Fields**
- hypothesis_key: test-26
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-27
- Hypothesis: Alice's library job is unpaid.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 11.259

**Raw Fields**
- hypothesis_key: test-27
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-28
- Hypothesis: Alice's exams are oral.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 11.719

**Raw Fields**
- hypothesis_key: test-28
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-29
- Hypothesis: Alice studies in the library every day.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 23.777

**Raw Fields**
- hypothesis_key: test-29
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
### test-30
- Hypothesis: Alice has a scholarship.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: None
- Query Mode: entailment
- Explanation: None
- Error: Not formular, error or none from query translation. Failed to translate hypothesis to formula
- Latency (sec): 10.737

**Raw Fields**
- hypothesis_key: test-30
- formula: None
- query_mode: entailment
- error: Not formular, error or none from query translation. Failed to translate hypothesis to formula

---
