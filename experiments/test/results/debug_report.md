# Experiment Debug Report

## Summary
- Total: 20
- Correct: 16
- Incorrect: 4
- Errors: 0
- Avg latency (sec): 11.433

## Detailed Results

### Doc 1 / test-31
- Hypothesis: Alice attends a university.
- Ground Truth: TRUE
- Prediction: TRUE
- Correct: True
- Confidence: 1
- Formula: P_1
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Error Type: None
- Latency (sec): 12.440

---

### Doc 1 / test-32
- Hypothesis: Alice's field of study is computer science.
- Ground Truth: TRUE
- Prediction: TRUE
- Correct: True
- Confidence: 1
- Formula: P_2
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Error Type: None
- Latency (sec): 7.168

---

### Doc 1 / test-33
- Hypothesis: Alice has a part-time job.
- Ground Truth: TRUE
- Prediction: TRUE
- Correct: True
- Confidence: 1
- Formula: ¬P_27
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Error Type: None
- Latency (sec): 1.340

---

### Doc 1 / test-34
- Hypothesis: Alice studies a subject other than computer science.
- Ground Truth: FALSE
- Prediction: FALSE
- Correct: True
- Confidence: 0
- Formula: (P_24 ∨ P_23 ∨ P_25 ∨ P_22) ∧ ¬P_2
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 16.982

---

### Doc 1 / test-35
- Hypothesis: Alice is never distracted while studying.
- Ground Truth: NOT MENTIONED
- Prediction: NOT MENTIONED
- Correct: True
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 16.609

---

### Doc 1 / test-36
- Hypothesis: Alice frequently studies late at night.
- Ground Truth: FALSE
- Prediction: FALSE
- Correct: True
- Confidence: 0
- Formula: ¬P_13
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 1.132

---

### Doc 1 / test-37
- Hypothesis: Alice enjoys working at the library.
- Ground Truth: NOT MENTIONED
- Prediction: NOT MENTIONED
- Correct: True
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 0
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 10.715

---

### Doc 1 / test-38
- Hypothesis: Alice plans to graduate next year.
- Ground Truth: NOT MENTIONED
- Prediction: NOT MENTIONED
- Correct: True
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 0
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 4.955

---

### Doc 1 / test-39
- Hypothesis: Alice passes all of her exams.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Correct: True
- Confidence: 0.5
- Formula: P_4
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 10.356

---

### Doc 1 / test-40
- Hypothesis: Alice completes her assignments on time.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Correct: True
- Confidence: 0.5
- Formula: P_8
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 9.862

---

### Doc 1 / test-41
- Hypothesis: Alice likes to play volleybal in her free time.
- Ground Truth: TRUE
- Prediction: TRUE
- Correct: True
- Confidence: 1
- Formula: P_15
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Error Type: None
- Latency (sec): 9.645

---

### Doc 1 / test-42
- Hypothesis: Alice's volleyball league happens on Sundays.
- Ground Truth: TRUE
- Prediction: UNCERTAIN
- Correct: False
- Confidence: 0.5
- Formula: P_19
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 10.460

---

### Doc 1 / test-43
- Hypothesis: There may be times where Alice plays board games.
- Ground Truth: TRUE
- Prediction: TRUE
- Correct: True
- Confidence: 1
- Formula: P_16
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is entailed by the hard constraints (KB ∧ ¬Q is unsatisfiable)
- Error: None
- Error Type: None
- Latency (sec): 9.671

---

### Doc 1 / test-44
- Hypothesis: Alice can be on her free time but not enjoying playing board games.
- Ground Truth: FALSE
- Prediction: FALSE
- Correct: True
- Confidence: 0
- Formula: ¬P_16
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 21.982

---

### Doc 1 / test-45
- Hypothesis: Alice hates playing volleyball on her free time.
- Ground Truth: FALSE
- Prediction: NOT MENTIONED
- Correct: False
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 21.228

---

### Doc 1 / test-46
- Hypothesis: Alice is usually competitive.
- Ground Truth: UNCERTAIN
- Prediction: NOT MENTIONED
- Correct: False
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 20.604

---

### Doc 1 / test-47
- Hypothesis: Alice does not have free time.
- Ground Truth: NOT MENTIONED
- Prediction: NOT MENTIONED
- Correct: True
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 0
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 16.797

---

### Doc 1 / test-48
- Hypothesis: Alice has a dog.
- Ground Truth: NOT MENTIONED
- Prediction: NOT MENTIONED
- Correct: True
- Confidence: 1
- Formula: NONE
- Query Mode: entailment
- Evidence Spans Count: 0
- Explanation: No matching proposition for hypothesis
- Error: None
- Error Type: None
- Latency (sec): 10.022

---

### Doc 1 / test-49
- Hypothesis: Alice is not competitive.
- Ground Truth: UNCERTAIN
- Prediction: UNCERTAIN
- Correct: True
- Confidence: 1.0
- Formula: P_18
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is consistent but not entailed by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 15.523

---

### Doc 1 / test-50
- Hypothesis: Alice usually studies late at night.
- Ground Truth: UNCERTAIN
- Prediction: FALSE
- Correct: False
- Confidence: 0
- Formula: ¬P_13
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 1.162

---
