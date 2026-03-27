# Experiment Debug Report

## Summary
- Total: 20
- Correct: 17
- Incorrect: 3
- Errors: 0
- Avg latency (sec): 21.878

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
- Latency (sec): 15.552

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
- Latency (sec): 9.485

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
- Latency (sec): 1.255

---

### Doc 1 / test-34
- Hypothesis: Alice studies a subject other than computer science.
- Ground Truth: FALSE
- Prediction: FALSE
- Correct: True
- Confidence: 0
- Formula: P_24 ∨ P_23 ∨ P_25 ∨ P_22
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 103.634

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
- Latency (sec): 18.111

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
- Latency (sec): 1.112

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
- Latency (sec): 7.737

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
- Latency (sec): 9.162

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
- Latency (sec): 15.054

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
- Latency (sec): 7.452

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
- Latency (sec): 15.891

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
- Latency (sec): 16.053

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
- Latency (sec): 17.448

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
- Latency (sec): 13.670

---

### Doc 1 / test-45
- Hypothesis: Alice hates playing volleyball on her free time.
- Ground Truth: FALSE
- Prediction: FALSE
- Correct: True
- Confidence: 0
- Formula: ¬P_15
- Query Mode: entailment
- Evidence Spans Count: 1
- Explanation: Query is contradicted by the knowledge base
- Error: None
- Error Type: None
- Latency (sec): 28.654

---

### Doc 1 / test-46
- Hypothesis: Alice is usually competitive.
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
- Latency (sec): 25.825

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
- Latency (sec): 87.935

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
- Latency (sec): 9.542

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
- Latency (sec): 17.281

---

### Doc 1 / test-50
- Hypothesis: Alice is free on Sundays.
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
- Latency (sec): 16.717

---
