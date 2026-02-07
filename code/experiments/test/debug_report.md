# Experiment Debug Report
## Summary
- Total: 30
- Correct: 17
- Incorrect: 0
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
- Latency (sec): 6.343

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
- Latency (sec): 7.838

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
- Formula: P_5 ⟹ P_6
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 9.089

**Raw Fields**
- hypothesis_key: test-3
- formula: P_5 ⟹ P_6
- query_mode: entailment
- error: None

---
### test-4
- Hypothesis: Alice typically studies hard before exams.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_8
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 10.424

**Raw Fields**
- hypothesis_key: test-4
- formula: P_8
- query_mode: entailment
- error: None

---
### test-5
- Hypothesis: When Alice is focused, she completes her assignments on time.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_9 ⟹ P_11
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 7.592

**Raw Fields**
- hypothesis_key: test-5
- formula: P_9 ⟹ P_11
- query_mode: entailment
- error: None

---
### test-6
- Hypothesis: Alice sometimes gets distracted by social media.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_14
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 6.435

**Raw Fields**
- hypothesis_key: test-6
- formula: P_14
- query_mode: entailment
- error: None

---
### test-7
- Hypothesis: Alice works part-time at the campus library.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_15
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 10.506

**Raw Fields**
- hypothesis_key: test-7
- formula: P_15
- query_mode: entailment
- error: None

---
### test-8
- Hypothesis: Her assignments are due every Friday.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_20
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 10.471

**Raw Fields**
- hypothesis_key: test-8
- formula: P_20
- query_mode: entailment
- error: None

---
### test-9
- Hypothesis: Alice rarely studies late at night.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_22
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 9.394

**Raw Fields**
- hypothesis_key: test-9
- formula: P_22
- query_mode: entailment
- error: None

---
### test-10
- Hypothesis: Alice is a student who studies hard before exams.
- Ground Truth: TRUE
- Prediction: TRUE
- Confidence: 1
- Formula: P_2 ∧ P_7
- Query Mode: entailment
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Latency (sec): 15.425

**Raw Fields**
- hypothesis_key: test-10
- formula: P_2 ∧ P_7
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
- Latency (sec): 29.486

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
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 13.696

**Raw Fields**
- hypothesis_key: test-12
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-13
- Hypothesis: Alice fails her exams even when she studies hard.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: P_5 ⟹ ¬P_6
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 48.075

**Raw Fields**
- hypothesis_key: test-13
- formula: P_5 ⟹ ¬P_6
- query_mode: entailment
- error: None

---
### test-14
- Hypothesis: Alice never studies hard before exams.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_7
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 40.861

**Raw Fields**
- hypothesis_key: test-14
- formula: ¬P_7
- query_mode: entailment
- error: None

---
### test-15
- Hypothesis: When Alice is focused, she misses assignments.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 28.603

**Raw Fields**
- hypothesis_key: test-15
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-16
- Hypothesis: Alice never gets distracted by social media.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_13
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 37.489

**Raw Fields**
- hypothesis_key: test-16
- formula: ¬P_13
- query_mode: entailment
- error: None

---
### test-17
- Hypothesis: Alice does not work part-time at the campus library.
- Ground Truth: FALSE
- Prediction: FALSE
- Confidence: 0
- Formula: ¬P_15
- Query Mode: entailment
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Latency (sec): 29.013

**Raw Fields**
- hypothesis_key: test-17
- formula: ¬P_15
- query_mode: entailment
- error: None

---
### test-18
- Hypothesis: Her assignments are due every Monday.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 7.480

**Raw Fields**
- hypothesis_key: test-18
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-19
- Hypothesis: Alice often studies late at night.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 22.504

**Raw Fields**
- hypothesis_key: test-19
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-20
- Hypothesis: Alice is a high school student.
- Ground Truth: FALSE
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 13.559

**Raw Fields**
- hypothesis_key: test-20
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-21
- Hypothesis: Alice lives in New York.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 11.234

**Raw Fields**
- hypothesis_key: test-21
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-22
- Hypothesis: Alice's major is mathematics.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 11.569

**Raw Fields**
- hypothesis_key: test-22
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-23
- Hypothesis: Alice always completes assignments early.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_11
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 25.313

**Raw Fields**
- hypothesis_key: test-23
- formula: P_11
- query_mode: entailment
- error: None

---
### test-24
- Hypothesis: Alice is focused during every exam.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Confidence: 0.5
- Formula: P_9
- Query Mode: entailment
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Latency (sec): 24.905

**Raw Fields**
- hypothesis_key: test-24
- formula: P_9
- query_mode: entailment
- error: None

---
### test-25
- Hypothesis: Alice works full-time.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 19.526

**Raw Fields**
- hypothesis_key: test-25
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-26
- Hypothesis: Alice uses social media only on weekends.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 12.838

**Raw Fields**
- hypothesis_key: test-26
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-27
- Hypothesis: Alice's library job is unpaid.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 8.830

**Raw Fields**
- hypothesis_key: test-27
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-28
- Hypothesis: Alice's exams are oral.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 18.378

**Raw Fields**
- hypothesis_key: test-28
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-29
- Hypothesis: Alice studies in the library every day.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 20.471

**Raw Fields**
- hypothesis_key: test-29
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
### test-30
- Hypothesis: Alice has a scholarship.
- Ground Truth: UNCERTAIN
- Prediction: None
- Confidence: None
- Formula: ERROR
- Query Mode: entailment
- Explanation: None
- Error: LLM failed to generate a valid formula
- Latency (sec): 12.769

**Raw Fields**
- hypothesis_key: test-30
- formula: ERROR
- query_mode: entailment
- error: LLM failed to generate a valid formula

---
