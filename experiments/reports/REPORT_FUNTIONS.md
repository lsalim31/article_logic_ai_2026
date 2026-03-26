# REPORT_FUNTIONS

Scope: /code. Generated from current source tree.

## .
### main.py
- `from_text_to_logic(text_path)`
  Input: `(text_path)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `query(query_str, text_path = None)`
  Input: `(query_str, text_path = None)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `load_active_structure()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `save_active_structure(structure)`
  Input: `(structure)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `parse_args()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`

## Ignore_old
### Ignore_old/test_logic_solver.py
- `test_basic_queries()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_formula_parsing()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`

### Ignore_old/translate_mid.py
- `parse_formula(formula_str: str)`
  Input: `(formula_str: str)`
  Output: `Formula`
  Internal calls: `parse_formula, split_arguments`
  Config params: `None`
- `split_arguments(s: str)`
  Input: `(s: str)`
  Output: `list`
  Internal calls: `None`
  Config params: `None`
- `verbalize(formula: Formula, prop_map: Dict[str, str])`
  Input: `(formula: Formula, prop_map: Dict[str, str])`
  Output: `str`
  Internal calls: `verbalize`
  Config params: `None`
- `verbalize_from_string(formula_str: str, prop_map: Dict[str, str])`
  Input: `(formula_str: str, prop_map: Dict[str, str])`
  Output: `str`
  Internal calls: `parse_formula, verbalize`
  Config params: `None`
- `extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = True)`
  Input: `(logified_structure: Dict[str, Any], hybrid_embedding: bool = True)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: int = 20)`
  Input: `(query: str, chunks: List[Dict], sbert_model, k: int = 20)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `is_yes_no_question(query: str)`
  Input: `(query: str)`
  Output: `bool`
  Internal calls: `None`
  Config params: `None`
- `get_configured_client(api_key: str, model: str)`
  Input: `(api_key: str, model: str)`
  Output: `Tuple[OpenAI, str]`
  Internal calls: `None`
  Config params: `None`
- `convert_yes_no_to_statement(query: str, api_key: str, model: str = 'gpt-4o', **kwargs)`
  Input: `(query: str, api_key: str, model: str = 'gpt-4o', **kwargs)`
  Output: `str`
  Internal calls: `get_configured_client`
  Config params: `None`
- `load_nli_model_singleton()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `generate_candidates_llm(prompt: str, api_key: str, model: str, temperature: float = 0.7)`
  Input: `(prompt: str, api_key: str, model: str, temperature: float = 0.7)`
  Output: `List[Dict]`
  Internal calls: `get_configured_client`
  Config params: `None`
- `translate_query(query: str, json_path: str, api_key: str, model: str = 'gpt-4o', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, k: int = 20, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Input: `(query: str, json_path: str, api_key: str, model: str = 'gpt-4o', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, k: int = 20, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Output: `Dict[str, Any]`
  Internal calls: `convert_yes_no_to_statement, extract_proposition_chunks, generate_candidates_llm, is_yes_no_question, load_nli_model_singleton, retrieve_top_k_propositions, verbalize_from_string`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `translate_query`
  Config params: `None`

### Ignore_old/translate_old.py
- `extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = True)`
  Input: `(logified_structure: Dict[str, Any], hybrid_embedding: bool = True)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: int = 20, min_similarity: float = 0.3, nli_model = None, enable_nli_filtering: bool = True)`
  Input: `(query: str, chunks: List[Dict], sbert_model, k: int = 20, min_similarity: float = 0.3, nli_model = None, enable_nli_filtering: bool = True)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `is_yes_no_question(query: str)`
  Input: `(query: str)`
  Output: `bool`
  Internal calls: `None`
  Config params: `None`
- `convert_yes_no_to_statement(query: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 1000)`
  Input: `(query: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 1000)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `build_prompt(query: str, retrieved_chunks: List[Dict], logified_structure: Dict = None)`
  Input: `(query: str, retrieved_chunks: List[Dict], logified_structure: Dict = None)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `extract_formula_from_text(response_text: str, available_prop_ids: List[str] = None)`
  Input: `(response_text: str, available_prop_ids: List[str] = None)`
  Output: `Optional[str]`
  Internal calls: `None`
  Config params: `None`
- `call_llm(prompt: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, max_retries: int = 2, retry_delay: float = 1.0)`
  Input: `(prompt: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, max_retries: int = 2, retry_delay: float = 1.0)`
  Output: `Dict[str, Any]`
  Internal calls: `extract_formula_from_text`
  Config params: `None`
- `translate_query(query: str, json_path: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, k: int = 20, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Input: `(query: str, json_path: str, api_key: str, model: str = 'gpt-5.2', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 64000, k: int = 20, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Output: `Dict[str, Any]`
  Internal calls: `build_prompt, call_llm, convert_yes_no_to_statement, extract_proposition_chunks, is_yes_no_question, retrieve_top_k_propositions`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `translate_query`
  Config params: `None`

### Ignore_old/weights_old.py
- `extract_text_from_document(file_path: str)`
  Input: `(file_path: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `retrieve_top_k_chunks(constraint: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, k: int = 10)`
  Input: `(constraint: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, k: int = 10)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `build_verification_prompt(chunks: List[Dict], constraint: str)`
  Input: `(chunks: List[Dict], constraint: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `extract_logprobs_for_yes_no(response)`
  Input: `(response)`
  Output: `Dict[str, float]`
  Internal calls: `None`
  Config params: `None`
- `verify_single_constraint(constraint_text: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, client: OpenAI, model: str = 'gpt-4o', temperature: float = 0.0, max_tokens: int = 5, k: int = 10)`
  Input: `(constraint_text: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, client: OpenAI, model: str = 'gpt-4o', temperature: float = 0.0, max_tokens: int = 5, k: int = 10)`
  Output: `Dict[str, float]`
  Internal calls: `build_verification_prompt, extract_logprobs_for_yes_no, retrieve_top_k_chunks`
  Config params: `None`
- `assign_weights(pathfile: str, json_path: str, api_key: str, model: str = 'gpt-4o', temperature: float = 0.0, max_tokens: int = 5, reasoning_effort: str = 'low', k: int = 10, chunk_size: int = 512, chunk_overlap: int = 50, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True, weight_hard_constraints: bool = True)`
  Input: `(pathfile: str, json_path: str, api_key: str, model: str = 'gpt-4o', temperature: float = 0.0, max_tokens: int = 5, reasoning_effort: str = 'low', k: int = 10, chunk_size: int = 512, chunk_overlap: int = 50, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True, weight_hard_constraints: bool = True)`
  Output: `Dict[str, Any]`
  Internal calls: `extract_text_from_document, verify_single_constraint`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `assign_weights`
  Config params: `None`

## baseline_logiclm_plus
### baseline_logiclm_plus/evaluator.py
- `evaluate_predictions(predictions, ground_truth)`
  Input: `(predictions, ground_truth)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_logiclm_metrics(results)`
  Input: `(results)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_backtracking_stats(results)`
  Input: `(results)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_efficiency_metrics(results)`
  Input: `(results)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `generate_report(all_results, baseline_results = None)`
  Input: `(all_results, baseline_results = None)`
  Output: `value (type unknown)`
  Internal calls: `compute_backtracking_stats, compute_efficiency_metrics, compute_logiclm_metrics, evaluate_predictions`
  Config params: `None`

### baseline_logiclm_plus/formalizer.py
- `formalize(text, query, logic_type = 'propositional', model_name = MODEL_NAME, temperature = TEMPERATURE)`
  Input: `(text, query, logic_type = 'propositional', model_name = MODEL_NAME, temperature = TEMPERATURE)`
  Output: `value (type unknown)`
  Internal calls: `parse_formalization_response, validate_formalization`
  Config params: `None`
- `formalize_to_fol(text, query, model_name = MODEL_NAME, temperature = TEMPERATURE)`
  Input: `(text, query, model_name = MODEL_NAME, temperature = TEMPERATURE)`
  Output: `value (type unknown)`
  Internal calls: `parse_formalization_response, validate_formalization`
  Config params: `None`
- `parse_formalization_response(raw_response)`
  Input: `(raw_response)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `validate_formalization(formalization)`
  Input: `(formalization)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_logiclm_plus/main.py
- `run_logiclm_plus(text, query, model_name = MODEL_NAME, ground_truth = None, config = None, **kwargs)`
  Input: `(text, query, model_name = MODEL_NAME, ground_truth = None, config = None, **kwargs)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_batch(examples, model_name = MODEL_NAME, config = None, output_dir = None, save_interval = 10, **kwargs)`
  Input: `(examples, model_name = MODEL_NAME, config = None, output_dir = None, save_interval = 10, **kwargs)`
  Output: `value (type unknown)`
  Internal calls: `compute_aggregate_metrics, run_logiclm_plus, save_results`
  Config params: `None`
- `load_dataset(dataset_name, data_dir = 'data', use_huggingface = True)`
  Input: `(dataset_name, data_dir = 'data', use_huggingface = True)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `save_results(results, output_path)`
  Input: `(results, output_path)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `compute_aggregate_metrics(results)`
  Input: `(results)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_logiclm_plus/refiner.py
- `_get_openai_client()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `generate_refinements(current_formulation, error_feedback, original_text, original_query, num_candidates = 2, model_name = 'gpt-4', temperature = 0)`
  Input: `(current_formulation, error_feedback, original_text, original_query, num_candidates = 2, model_name = 'gpt-4', temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `_get_openai_client`
  Config params: `None`
- `pairwise_compare(formulation_a, formulation_b, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Input: `(formulation_a, formulation_b, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `_get_openai_client`
  Config params: `None`
- `backtracking_decision(previous_formulation, refined_formulation, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Input: `(previous_formulation, refined_formulation, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `_get_openai_client`
  Config params: `None`
- `select_best_formulation(candidates, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Input: `(candidates, original_text, original_query, model_name = 'gpt-4', temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `pairwise_compare`
  Config params: `None`
- `refine_loop(initial_formulation, original_text, original_query, max_iterations = 4, solver = 'prover9', solver_timeout = 30, model_name = 'gpt-4', temperature = 0, num_candidates = 2, max_consecutive_backtracks = 2)`
  Input: `(initial_formulation, original_text, original_query, max_iterations = 4, solver = 'prover9', solver_timeout = 30, model_name = 'gpt-4', temperature = 0, num_candidates = 2, max_consecutive_backtracks = 2)`
  Output: `value (type unknown)`
  Internal calls: `backtracking_decision, generate_refinements, select_best_formulation`
  Config params: `None`

### baseline_logiclm_plus/run_logicbench_with_refinement.py
- `load_logicbench_from_github(logic_type, task_type = 'BQA', max_examples = None)`
  Input: `(logic_type, task_type = 'BQA', max_examples = None)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `normalize_answer(answer)`
  Input: `(answer)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `convert_logiclm_answer_to_logicbench(logiclm_answer)`
  Input: `(logiclm_answer)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_with_forced_refinement(text, query, logic_type = 'propositional', model_name = MODEL_NAME, min_refinements = 1, max_iterations = 4, solver = 'z3', solver_timeout = 30)`
  Input: `(text, query, logic_type = 'propositional', model_name = MODEL_NAME, min_refinements = 1, max_iterations = 4, solver = 'z3', solver_timeout = 30)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(logic_type, task_type, output_path, max_samples = None, min_refinements = 1, max_iterations = 4, solver = 'z3', model_name = MODEL_NAME)`
  Input: `(logic_type, task_type, output_path, max_samples = None, min_refinements = 1, max_iterations = 4, solver = 'z3', model_name = MODEL_NAME)`
  Output: `value (type unknown)`
  Internal calls: `convert_logiclm_answer_to_logicbench, load_logicbench_from_github, normalize_answer, run_with_forced_refinement`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `run_experiment`
  Config params: `None`

### baseline_logiclm_plus/solver_interface.py
- `solve_fol(premises, conclusion, solver = 'z3', timeout = SOLVER_TIMEOUT)`
  Input: `(premises, conclusion, solver = 'z3', timeout = SOLVER_TIMEOUT)`
  Output: `value (type unknown)`
  Internal calls: `test_entailment_prover9, test_entailment_z3, validate_formulation`
  Config params: `None`
- `validate_formulation(premises, conclusion)`
  Input: `(premises, conclusion)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `test_entailment_z3(premises, conclusion, timeout = SOLVER_TIMEOUT)`
  Input: `(premises, conclusion, timeout = SOLVER_TIMEOUT)`
  Output: `value (type unknown)`
  Internal calls: `parse_solver_error`
  Config params: `None`
- `test_entailment_prover9(premises, conclusion, timeout = SOLVER_TIMEOUT)`
  Input: `(premises, conclusion, timeout = SOLVER_TIMEOUT)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `parse_solver_error(error_output, solver)`
  Input: `(error_output, solver)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_logiclm_plus/test_logiclm.py
- `test_z3_fallback()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_entailment_checking()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_solver_timeout()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_malformed_fol()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_error_message_parsing()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_prover9_basic()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_formalization_output_format()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_malformed_json_handling()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_predicate_extraction()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_quantifier_handling()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_fol_syntax_validation()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_formalization_failure_handling()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_solver_failure_handling()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_accuracy_metrics()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_execution_rate_Er()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_execution_accuracy_Ea()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_backtracking_stats()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_efficiency_metrics()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `run_all_tests()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `test_accuracy_metrics, test_backtracking_stats, test_efficiency_metrics, test_entailment_checking, test_error_message_parsing, test_execution_accuracy_Ea, test_execution_rate_Er, test_fol_syntax_validation, test_formalization_failure_handling, test_formalization_output_format, test_malformed_fol, test_malformed_json_handling, test_predicate_extraction, test_prover9_basic, test_quantifier_handling, test_solver_failure_handling, test_solver_timeout, test_z3_fallback`
  Config params: `None`

## baseline_rag
### baseline_rag/chunker.py
- `chunk_document(text, chunk_size = 512, overlap = 50)`
  Input: `(text, chunk_size = 512, overlap = 50)`
  Output: `value (type unknown)`
  Internal calls: `detokenize, tokenize`
  Config params: `None`
- `tokenize(text)`
  Input: `(text)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `detokenize(tokens)`
  Input: `(tokens)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_rag/evaluator.py
- `normalize_label(label)`
  Input: `(label)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `evaluate(predictions, ground_truth, label_set = None)`
  Input: `(predictions, ground_truth, label_set = None)`
  Output: `value (type unknown)`
  Internal calls: `compute_accuracy, compute_confusion_matrix, compute_macro_metrics, compute_per_class_metrics, normalize_label`
  Config params: `None`
- `compute_accuracy(predictions, ground_truth)`
  Input: `(predictions, ground_truth)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_confusion_matrix(predictions, ground_truth, labels)`
  Input: `(predictions, ground_truth, labels)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_per_class_metrics(predictions, ground_truth, labels)`
  Input: `(predictions, ground_truth, labels)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `compute_macro_metrics(per_class_metrics)`
  Input: `(per_class_metrics)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `format_results(metrics, dataset_name)`
  Input: `(metrics, dataset_name)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_rag/main.py
- `load_dataset(dataset_name, split = 'validation')`
  Input: `(dataset_name, split = 'validation')`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `preprocess_document(document)`
  Input: `(document)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_baseline_experiment(dataset_name, model_name = None)`
  Input: `(dataset_name, model_name = None)`
  Output: `value (type unknown)`
  Internal calls: `load_dataset, preprocess_document, process_single_example`
  Config params: `SBERT_MODEL`
- `process_single_example(example, chunk_embeddings, chunks, sbert_model, llm_model)`
  Input: `(example, chunk_embeddings, chunks, sbert_model, llm_model)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `save_results(results, output_path)`
  Input: `(results, output_path)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `run_baseline_experiment, save_results`
  Config params: `None`

### baseline_rag/nli_reranker.py
- `load_nli_model(model_name: str = None)`
  Input: `(model_name: str = None)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `NLI_MODEL`
- `score_nli_pairs(model, premise_hypothesis_pairs: List[Tuple[str, str]], batch_size: int = None)`
  Input: `(model, premise_hypothesis_pairs: List[Tuple[str, str]], batch_size: int = None)`
  Output: `np.ndarray`
  Internal calls: `None`
  Config params: `NLI_BATCH_SIZE`
- `filter_propositions_by_nli(propositions: List[Dict], query: str, model, entailment_threshold: float = None, contradiction_threshold: float = None)`
  Input: `(propositions: List[Dict], query: str, model, entailment_threshold: float = None, contradiction_threshold: float = None)`
  Output: `List[Dict]`
  Internal calls: `score_nli_pairs`
  Config params: `NLI_CONTRADICTION_THRESHOLD, NLI_ENTAILMENT_THRESHOLD`

### baseline_rag/reasoner.py
- `construct_prompt(query, retrieved_chunks, prompt_template)`
  Input: `(query, retrieved_chunks, prompt_template)`
  Output: `value (type unknown)`
  Internal calls: `format_chunks`
  Config params: `None`
- `format_chunks(retrieved_chunks)`
  Input: `(retrieved_chunks)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `call_llm(prompt, model_name, temperature = 0)`
  Input: `(prompt, model_name, temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `parse_response(response)`
  Input: `(response)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `reason_with_cot(query, retrieved_chunks, model_name, prompt_template, temperature = 0)`
  Input: `(query, retrieved_chunks, model_name, prompt_template, temperature = 0)`
  Output: `value (type unknown)`
  Internal calls: `call_llm, construct_prompt, parse_response`
  Config params: `None`

### baseline_rag/retriever.py
- `load_sbert_model(model_name)`
  Input: `(model_name)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `encode_chunks(chunks, model)`
  Input: `(chunks, model)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `encode_query(query, model)`
  Input: `(query, model)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `retrieve(query_embedding, chunk_embeddings, chunks, k = 5)`
  Input: `(query_embedding, chunk_embeddings, chunks, k = 5)`
  Output: `value (type unknown)`
  Internal calls: `compute_cosine_similarity`
  Config params: `None`
- `compute_cosine_similarity(query_embedding, chunk_embeddings)`
  Input: `(query_embedding, chunk_embeddings)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### baseline_rag/run_experiment_logicbench_rag.py
- `preprocess_text(text)`
  Input: `(text)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `convert_ground_truth(ground_truth)`
  Input: `(ground_truth)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_logicbench_experiment(logic_type, reasoning_patterns = None, max_examples_per_pattern = None, model_name = None)`
  Input: `(logic_type, reasoning_patterns = None, max_examples_per_pattern = None, model_name = None)`
  Output: `value (type unknown)`
  Internal calls: `convert_ground_truth, preprocess_text`
  Config params: `SBERT_MODEL`
- `save_results(results, output_path)`
  Input: `(results, output_path)`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `run_logicbench_experiment, save_results`
  Config params: `None`

### baseline_rag/test_baseline.py
- `test_chunker()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_retriever()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_evaluator()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_main_functions()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`
- `test_parse_response()`
  Input: `()`
  Output: `None (no explicit return)`
  Internal calls: `None`
  Config params: `None`

## config
- No Python functions found.

## experiments
### experiments/DocNLI/download_sample.py
- `count_words(text: str)`
  Input: `(text: str)`
  Output: `int`
  Internal calls: `None`
  Config params: `None`
- `download_and_group_by_premise()`
  Input: `()`
  Output: `Dict[str, Dict[str, Any]]`
  Internal calls: `None`
  Config params: `None`
- `filter_premises(premises_dict: Dict[str, Dict[str, Any]], min_words: int, max_words: int)`
  Input: `(premises_dict: Dict[str, Dict[str, Any]], min_words: int, max_words: int)`
  Output: `List[Tuple[str, Dict[str, Any], int]]`
  Internal calls: `count_words`
  Config params: `None`
- `sample_premises(filtered_premises: List[Tuple[str, Dict[str, Any], int]], num_premises: int, seed: int = 42)`
  Input: `(filtered_premises: List[Tuple[str, Dict[str, Any], int]], num_premises: int, seed: int = 42)`
  Output: `List[Dict[str, Any]]`
  Internal calls: `None`
  Config params: `None`
- `flatten_to_examples(premises_list: List[Dict[str, Any]])`
  Input: `(premises_list: List[Dict[str, Any]])`
  Output: `List[Dict[str, Any]]`
  Internal calls: `None`
  Config params: `None`
- `save_sample(premises_list: List[Dict[str, Any]], examples: List[Dict[str, Any]], output_path: Path, num_premises: int)`
  Input: `(premises_list: List[Dict[str, Any]], examples: List[Dict[str, Any]], output_path: Path, num_premises: int)`
  Output: `None`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `download_and_group_by_premise, filter_premises, flatten_to_examples, sample_premises, save_sample`
  Config params: `None`

### experiments/DocNLI/experiment_logify_DocNLI.py
- `load_sample_data(data_path: Path = SAMPLE_DATA_PATH)`
  Input: `(data_path: Path = SAMPLE_DATA_PATH)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `map_prediction_to_binary(prediction: Optional[str])`
  Input: `(prediction: Optional[str])`
  Output: `Optional[str]`
  Internal calls: `None`
  Config params: `None`
- `get_cached_logified_path(example_id: int)`
  Input: `(example_id: int)`
  Output: `Path`
  Internal calls: `None`
  Config params: `None`
- `logify_premise(text: str, premise_id: int, api_key: str, temperature: float, reasoning_effort: str, max_tokens: int, weights_model: str, k_weights: int)`
  Input: `(text: str, premise_id: int, api_key: str, temperature: float, reasoning_effort: str, max_tokens: int, weights_model: str, k_weights: int)`
  Output: `Dict[str, Any]`
  Internal calls: `get_cached_logified_path`
  Config params: `None`
- `query_hypothesis(hypothesis_text: str, logified_structure: Dict[str, Any], json_path: str, api_key: str, model: str, temperature: float, reasoning_effort: str, max_tokens: int, k_query: int)`
  Input: `(hypothesis_text: str, logified_structure: Dict[str, Any], json_path: str, api_key: str, model: str, temperature: float, reasoning_effort: str, max_tokens: int, k_query: int)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(api_key: str, data_path: Path = SAMPLE_DATA_PATH, query_model: str = 'openai/gpt-5-nano', weights_model: str = 'gpt-4o', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 128000, query_max_tokens: int = 64000, k_weights: int = 10, k_query: int = 20, limit: Optional[int] = None)`
  Input: `(api_key: str, data_path: Path = SAMPLE_DATA_PATH, query_model: str = 'openai/gpt-5-nano', weights_model: str = 'gpt-4o', temperature: float = 0.1, reasoning_effort: str = 'medium', max_tokens: int = 128000, query_max_tokens: int = 64000, k_weights: int = 10, k_query: int = 20, limit: Optional[int] = None)`
  Output: `Dict[str, Any]`
  Internal calls: `get_cached_logified_path, load_sample_data, logify_premise, map_prediction_to_binary, query_hypothesis`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `run_experiment`
  Config params: `None`

### experiments/DocNLI/experiment_rag_DocNLI.py
- `load_sample_data(data_path: Path = SAMPLE_DATA_PATH)`
  Input: `(data_path: Path = SAMPLE_DATA_PATH)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `map_prediction_to_binary(prediction: Optional[str])`
  Input: `(prediction: Optional[str])`
  Output: `Optional[str]`
  Internal calls: `None`
  Config params: `None`
- `parse_rag_response(response: str)`
  Input: `(response: str)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `call_llm(prompt: str, model_name: str, temperature: float = 0)`
  Input: `(prompt: str, model_name: str, temperature: float = 0)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `construct_prompt(hypothesis: str, retrieved_chunks: List[Dict])`
  Input: `(hypothesis: str, retrieved_chunks: List[Dict])`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `process_single_hypothesis(hypothesis_text: str, chunk_embeddings, chunks: List[Dict], sbert_model, model_name: str, temperature: float)`
  Input: `(hypothesis_text: str, chunk_embeddings, chunks: List[Dict], sbert_model, model_name: str, temperature: float)`
  Output: `Dict[str, Any]`
  Internal calls: `call_llm, construct_prompt, parse_rag_response`
  Config params: `None`
- `process_premise(premise_text: str, sbert_model)`
  Input: `(premise_text: str, sbert_model)`
  Output: `tuple`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(data_path: Path = SAMPLE_DATA_PATH, model_name: str = None, temperature: float = 0, limit: Optional[int] = None)`
  Input: `(data_path: Path = SAMPLE_DATA_PATH, model_name: str = None, temperature: float = 0, limit: Optional[int] = None)`
  Output: `Dict[str, Any]`
  Internal calls: `load_sample_data, map_prediction_to_binary, process_premise, process_single_hypothesis`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `run_experiment`
  Config params: `None`

### experiments/contractNLI/experiment_logify_contract_NLI.py
- `load_contractnli_dataset(dataset_path: str)`
  Input: `(dataset_path: str)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `get_ground_truth_label(choice: str)`
  Input: `(choice: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `get_cached_logified_path(doc_id: int)`
  Input: `(doc_id: int)`
  Output: `Path`
  Internal calls: `None`
  Config params: `None`
- `logify_document(text: str, doc_id: int, api_key: str, temperature: float, reasoning_effort: str, max_tokens: int, weights_model: str, k_weights: int)`
  Input: `(text: str, doc_id: int, api_key: str, temperature: float, reasoning_effort: str, max_tokens: int, weights_model: str, k_weights: int)`
  Output: `Dict[str, Any]`
  Internal calls: `get_cached_logified_path`
  Config params: `HARDNESS_CONSTANT`
- `query_hypothesis(hypothesis_text: str, logified_structure: Dict[str, Any], json_path: str, api_key: str, model: str, temperature: float, reasoning_effort: str, max_tokens: int, k_query: int)`
  Input: `(hypothesis_text: str, logified_structure: Dict[str, Any], json_path: str, api_key: str, model: str, temperature: float, reasoning_effort: str, max_tokens: int, k_query: int)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(dataset_path: str, api_key: str, query_model: str = TRANSLATE_MODEL, weights_model: str = 'gpt-4o', temperature: float = TEMPERATURE_LOGIC_CONVERTER, reasoning_effort: str = REASONING_EFFORT, max_tokens: int = MAX_TOKENS, query_max_tokens: int = MAX_TOKENS, k_weights: int = 10, k_query: int = SBERT_TOP_K, doc_ids: List[int] = None)`
  Input: `(dataset_path: str, api_key: str, query_model: str = TRANSLATE_MODEL, weights_model: str = 'gpt-4o', temperature: float = TEMPERATURE_LOGIC_CONVERTER, reasoning_effort: str = REASONING_EFFORT, max_tokens: int = MAX_TOKENS, query_max_tokens: int = MAX_TOKENS, k_weights: int = 10, k_query: int = SBERT_TOP_K, doc_ids: List[int] = None)`
  Output: `Dict[str, Any]`
  Internal calls: `get_cached_logified_path, get_ground_truth_label, load_contractnli_dataset, logify_document, query_hypothesis`
  Config params: `MAX_TOKENS, REASONING_EFFORT, SBERT_TOP_K, TEMPERATURE_LOGIC_CONVERTER, TRANSLATE_MODEL`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `run_experiment`
  Config params: `MAX_TOKENS, REASONING_EFFORT, SBERT_TOP_K, TEMPERATURE_LOGIC_CONVERTER, TRANSLATE_MODEL`

### experiments/contractNLI/experiment_rag_contract_NLI.py
- `load_contractnli_dataset(dataset_path: str)`
  Input: `(dataset_path: str)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `get_ground_truth_label(choice: str)`
  Input: `(choice: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `parse_rag_response(response: str)`
  Input: `(response: str)`
  Output: `Dict[str, Any]`
  Internal calls: `None`
  Config params: `None`
- `call_llm(prompt: str, model_name: str, temperature: float = 0)`
  Input: `(prompt: str, model_name: str, temperature: float = 0)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `construct_prompt(hypothesis: str, retrieved_chunks: List[Dict])`
  Input: `(hypothesis: str, retrieved_chunks: List[Dict])`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `process_single_hypothesis(hypothesis_text: str, chunk_embeddings, chunks: List[Dict], sbert_model, model_name: str, temperature: float)`
  Input: `(hypothesis_text: str, chunk_embeddings, chunks: List[Dict], sbert_model, model_name: str, temperature: float)`
  Output: `Dict[str, Any]`
  Internal calls: `call_llm, construct_prompt, parse_rag_response`
  Config params: `None`
- `process_document(doc_text: str, sbert_model)`
  Input: `(doc_text: str, sbert_model)`
  Output: `tuple`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(dataset_path: str, model_name: str = None, temperature: float = 0, num_docs: int = 20)`
  Input: `(dataset_path: str, model_name: str = None, temperature: float = 0, num_docs: int = 20)`
  Output: `Dict[str, Any]`
  Internal calls: `get_ground_truth_label, load_contractnli_dataset, process_document, process_single_hypothesis`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `run_experiment`
  Config params: `None`

### experiments/logicBench/experiment_logify_logicBench.py
- `load_logicbench_grouped(dataset_type = 'eval', task_type = 'BQA', logic_type = 'all', patterns = None, max_samples_per_pattern = None)`
  Input: `(dataset_type = 'eval', task_type = 'BQA', logic_type = 'all', patterns = None, max_samples_per_pattern = None)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `get_cache_path(sample_id: str)`
  Input: `(sample_id: str)`
  Output: `Path`
  Internal calls: `None`
  Config params: `None`
- `run_logify(text: str, sample_id: str, api_key: str, model: str = 'gpt-4o', verbose: bool = True)`
  Input: `(text: str, sample_id: str, api_key: str, model: str = 'gpt-4o', verbose: bool = True)`
  Output: `Tuple[Optional[Dict], float, bool, Optional[str]]`
  Internal calls: `get_cache_path`
  Config params: `None`
- `run_query(query: str, logified_structure: Dict, api_key: str, model: str = 'gpt-4o', verbose: bool = True)`
  Input: `(query: str, logified_structure: Dict, api_key: str, model: str = 'gpt-4o', verbose: bool = True)`
  Output: `Tuple[str, float, float, Optional[str], Optional[str]]`
  Internal calls: `None`
  Config params: `None`
- `run_experiment(logic_type: str = 'all', patterns: Optional[List[str]] = None, max_samples_per_pattern: Optional[int] = None, api_key: str = None, model: str = 'gpt-4o', verbose: bool = True)`
  Input: `(logic_type: str = 'all', patterns: Optional[List[str]] = None, max_samples_per_pattern: Optional[int] = None, api_key: str = None, model: str = 'gpt-4o', verbose: bool = True)`
  Output: `List[Dict]`
  Internal calls: `load_logicbench_grouped, run_logify, run_query`
  Config params: `None`
- `get_api_key(args_key: Optional[str] = None)`
  Input: `(args_key: Optional[str] = None)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `get_api_key, run_experiment`
  Config params: `None`

## fol_vs_boolean
### fol_vs_boolean/analyze_errors.py
- `load_results(filepath)`
  Input: `(filepath)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `analyze_errors(results, mode)`
  Input: `(results, mode)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (explicit return)`
  Internal calls: `analyze_errors, load_results`
  Config params: `None`

### fol_vs_boolean/extract_fol.py
- `extract_fol(text, query)`
  Input: `(text, query)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

### fol_vs_boolean/extract_propositional.py
- `get_logify_converter()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `extract_propositional(text, query = None)`
  Input: `(text, query = None)`
  Output: `value (type unknown)`
  Internal calls: `get_logify_converter`
  Config params: `None`

### fol_vs_boolean/load_logicbench.py
- `load_logicbench(logic_type = 'propositional_logic', reasoning_patterns = None, max_examples_per_pattern = None)`
  Input: `(logic_type = 'propositional_logic', reasoning_patterns = None, max_examples_per_pattern = None)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `load_all_propositional(max_examples_per_pattern = None)`
  Input: `(max_examples_per_pattern = None)`
  Output: `value (type unknown)`
  Internal calls: `load_logicbench`
  Config params: `None`
- `load_all_fol(max_examples_per_pattern = None)`
  Input: `(max_examples_per_pattern = None)`
  Output: `value (type unknown)`
  Internal calls: `load_logicbench`
  Config params: `None`

### fol_vs_boolean/run_dual_extraction.py
- `main()`
  Input: `()`
  Output: `None (explicit return)`
  Internal calls: `None`
  Config params: `None`

### fol_vs_boolean/run_logicbench_experiment.py
- `get_logify_converter()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `extract_propositional(text, query = None)`
  Input: `(text, query = None)`
  Output: `value (type unknown)`
  Internal calls: `get_logify_converter`
  Config params: `None`
- `extract_fol(text, query)`
  Input: `(text, query)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_dual_extraction(examples, verbose = True)`
  Input: `(examples, verbose = True)`
  Output: `value (type unknown)`
  Internal calls: `extract_fol, extract_propositional`
  Config params: `None`
- `analyze_errors(prop_results, fol_results, verbose = True)`
  Input: `(prop_results, fol_results, verbose = True)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (explicit return)`
  Internal calls: `analyze_errors, run_dual_extraction`
  Config params: `None`

### fol_vs_boolean/run_logicbench_fol_experiment.py
- `get_logify_converter()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `extract_propositional(text, query = None)`
  Input: `(text, query = None)`
  Output: `value (type unknown)`
  Internal calls: `get_logify_converter`
  Config params: `None`
- `extract_fol(text, query)`
  Input: `(text, query)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `run_dual_extraction(examples, verbose = True)`
  Input: `(examples, verbose = True)`
  Output: `value (type unknown)`
  Internal calls: `extract_fol, extract_propositional`
  Config params: `None`
- `analyze_errors(prop_results, fol_results, verbose = True)`
  Input: `(prop_results, fol_results, verbose = True)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `None (explicit return)`
  Internal calls: `analyze_errors, run_dual_extraction`
  Config params: `None`

### fol_vs_boolean/updated_load_logicbench.py
- `load_logicbench(dataset_type = 'eval', task_type = 'BQA', logic_type = 'all', patterns = None, max_examples_per_pattern = None, all_qa_pairs = False)`
  Input: `(dataset_type = 'eval', task_type = 'BQA', logic_type = 'all', patterns = None, max_examples_per_pattern = None, all_qa_pairs = False)`
  Output: `value (type unknown)`
  Internal calls: `_fetch_pattern`
  Config params: `None`
- `_fetch_pattern(url, pattern, logic_type, folder_name, dataset_type, max_examples = None, all_qa_pairs = False)`
  Input: `(url, pattern, logic_type, folder_name, dataset_type, max_examples = None, all_qa_pairs = False)`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `get_available_patterns(logic_type = 'all')`
  Input: `(logic_type = 'all')`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`

## from_text_to_logic
### from_text_to_logic/logify.py
- `extract_text_from_document(file_path: str)`
  Input: `(file_path: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `extract_text_from_document`
  Config params: `MAX_TOKENS, REASONING_EFFORT, TEMPERATURE_LOGIC_CONVERTER`

### from_text_to_logic/weights.py
- `extract_text_from_document(file_path: str)`
  Input: `(file_path: str)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `retrieve_top_k_chunks(query: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, k: int = 10)`
  Input: `(query: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, k: int = 10)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `None`
- `compute_nli_entailment(constraint_text: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, nli_model, k: int = 10)`
  Input: `(constraint_text: str, chunks: List[Dict], chunk_embeddings: np.ndarray, sbert_model, nli_model, k: int = 10)`
  Output: `float`
  Internal calls: `retrieve_top_k_chunks`
  Config params: `None`
- `assign_weights(pathfile: str, json_path: str, hardness_criterion: float = HARDNESS_CONSTANT, k: int = 10, chunk_size: int = 512, chunk_overlap: int = 50, sbert_model_name: str = 'all-MiniLM-L6-v2', nli_model_name: str = 'cross-encoder/nli-deberta-v3-large', verbose: bool = True)`
  Input: `(pathfile: str, json_path: str, hardness_criterion: float = HARDNESS_CONSTANT, k: int = 10, chunk_size: int = 512, chunk_overlap: int = 50, sbert_model_name: str = 'all-MiniLM-L6-v2', nli_model_name: str = 'cross-encoder/nli-deberta-v3-large', verbose: bool = True)`
  Output: `Dict[str, Any]`
  Internal calls: `compute_nli_entailment, extract_text_from_document`
  Config params: `HARDNESS_CONSTANT`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `assign_weights`
  Config params: `None`

## interface_with_user
### interface_with_user/negation_detection.py
- `detect_negation_in_hypothesis(hypothesis: str)`
  Input: `(hypothesis: str)`
  Output: `bool`
  Internal calls: `None`
  Config params: `None`
- `detect_negation_in_proposition(translation: str)`
  Input: `(translation: str)`
  Output: `bool`
  Internal calls: `None`
  Config params: `None`
- `check_polarity_match(hypothesis: str, formula: str, retrieved_props: List[Dict])`
  Input: `(hypothesis: str, formula: str, retrieved_props: List[Dict])`
  Output: `Tuple[bool, str, Optional[str]]`
  Internal calls: `detect_negation_in_hypothesis, detect_negation_in_proposition`
  Config params: `None`
- `apply_polarity_correction(formula: str, hypothesis: str, retrieved_props: List[Dict], auto_correct: bool = False)`
  Input: `(formula: str, hypothesis: str, retrieved_props: List[Dict], auto_correct: bool = False)`
  Output: `Tuple[str, bool, str]`
  Internal calls: `check_polarity_match`
  Config params: `None`

### interface_with_user/translate.py
- `tokenize_formula(formula: str)`
  Input: `(formula: str)`
  Output: `List[str]`
  Internal calls: `None`
  Config params: `None`
- `parse_infix_formula(formula_str: str)`
  Input: `(formula_str: str)`
  Output: `Formula`
  Internal calls: `_parse_iff, tokenize_formula`
  Config params: `None`
- `_parse_implies(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Any, List[str]]`
  Internal calls: `_parse_or`
  Config params: `None`
- `_parse_iff(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Formula, List[str]]`
  Internal calls: `_parse_implies`
  Config params: `None`
- `_parse_or(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Formula, List[str]]`
  Internal calls: `_parse_and`
  Config params: `None`
- `_parse_and(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Formula, List[str]]`
  Internal calls: `_parse_not`
  Config params: `None`
- `_parse_not(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Formula, List[str]]`
  Internal calls: `_parse_atom, _parse_not`
  Config params: `None`
- `_parse_atom(tokens: List[str])`
  Input: `(tokens: List[str])`
  Output: `Tuple[Formula, List[str]]`
  Internal calls: `_parse_iff`
  Config params: `None`
- `verbalize(formula: Formula, prop_map: Dict[str, str])`
  Input: `(formula: Formula, prop_map: Dict[str, str])`
  Output: `str`
  Internal calls: `verbalize`
  Config params: `None`
- `verbalize_from_string(formula_str: str, prop_map: Dict[str, str])`
  Input: `(formula_str: str, prop_map: Dict[str, str])`
  Output: `str`
  Internal calls: `parse_infix_formula, verbalize`
  Config params: `None`
- `extract_proposition_chunks(logified_structure: Dict[str, Any], hybrid_embedding: bool = ENABLE_HYBRID_EMBEDDING)`
  Input: `(logified_structure: Dict[str, Any], hybrid_embedding: bool = ENABLE_HYBRID_EMBEDDING)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `ENABLE_HYBRID_EMBEDDING`
- `retrieve_top_k_propositions(query: str, chunks: List[Dict], sbert_model, k: int = SBERT_TOP_K, minimal_similarity = SBERT_MIN_SIMILARITY)`
  Input: `(query: str, chunks: List[Dict], sbert_model, k: int = SBERT_TOP_K, minimal_similarity = SBERT_MIN_SIMILARITY)`
  Output: `List[Dict]`
  Internal calls: `None`
  Config params: `SBERT_MIN_SIMILARITY, SBERT_TOP_K`
- `is_yes_no_question(query: str)`
  Input: `(query: str)`
  Output: `bool`
  Internal calls: `None`
  Config params: `None`
- `get_configured_client(api_key: str, model: str)`
  Input: `(api_key: str, model: str)`
  Output: `Tuple[OpenAI, str]`
  Internal calls: `None`
  Config params: `None`
- `convert_yes_no_to_statement(query: str, api_key: str, model: str = REASONING_MODEL, temperature: float = TEMPERATURE_LOGIC_CONVERTER, reasoning_effort: str = REASONING_EFFORT, max_tokens: int = MAX_TOKENS)`
  Input: `(query: str, api_key: str, model: str = REASONING_MODEL, temperature: float = TEMPERATURE_LOGIC_CONVERTER, reasoning_effort: str = REASONING_EFFORT, max_tokens: int = MAX_TOKENS)`
  Output: `str`
  Internal calls: `None`
  Config params: `MAX_TOKENS, REASONING_EFFORT, REASONING_MODEL, TEMPERATURE_LOGIC_CONVERTER`
- `load_nli_model_singleton()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `None`
  Config params: `None`
- `generate_candidates_llm(prompt: str, api_key: str, model: str, temperature: float = TEMPERATURE_TRANSLATE)`
  Input: `(prompt: str, api_key: str, model: str, temperature: float = TEMPERATURE_TRANSLATE)`
  Output: `List[Dict]`
  Internal calls: `get_configured_client`
  Config params: `TEMPERATURE_TRANSLATE`
- `build_prompt(query: str, props_text: str, constraints_section: str, available_ids: str, query_is_negative: bool)`
  Input: `(query: str, props_text: str, constraints_section: str, available_ids: str, query_is_negative: bool)`
  Output: `str`
  Internal calls: `None`
  Config params: `None`
- `translate_query(query: str, json_path: str, api_key: str, model: str = TRANSLATE_MODEL, temperature: float = TEMPERATURE_TRANSLATE, reasoning_effort: str = REASONING_EFFORT_TRANSLATE, max_tokens: int = MAX_TOKENS, k: int = SBERT_TOP_K, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Input: `(query: str, json_path: str, api_key: str, model: str = TRANSLATE_MODEL, temperature: float = TEMPERATURE_TRANSLATE, reasoning_effort: str = REASONING_EFFORT_TRANSLATE, max_tokens: int = MAX_TOKENS, k: int = SBERT_TOP_K, sbert_model_name: str = 'all-MiniLM-L6-v2', verbose: bool = True)`
  Output: `Dict[str, Any]`
  Internal calls: `build_prompt, convert_yes_no_to_statement, extract_proposition_chunks, generate_candidates_llm, is_yes_no_question, load_nli_model_singleton, retrieve_top_k_propositions, verbalize_from_string`
  Config params: `MAX_TOKENS, REASONING_EFFORT_TRANSLATE, SBERT_TOP_K, TEMPERATURE_TRANSLATE, TRANSLATE_MODEL`
- `main()`
  Input: `()`
  Output: `value (type unknown)`
  Internal calls: `translate_query`
  Config params: `MAX_TOKENS, REASONING_EFFORT, SBERT_TOP_K, TEMPERATURE_TRANSLATE, TRANSLATE_MODEL`

## logic_solver
### logic_solver/encoding.py
- `encode_logified_structure(logified_structure: Dict[str, Any])`
  Input: `(logified_structure: Dict[str, Any])`
  Output: `Tuple[WCNF, LogicEncoder]`
  Internal calls: `None`
  Config params: `None`

### logic_solver/maxsat.py
- `solve_query(logified_structure: Dict[str, Any], query_formula: str)`
  Input: `(logified_structure: Dict[str, Any], query_formula: str)`
  Output: `SolverResult`
  Internal calls: `None`
  Config params: `None`

## Parse Errors
- `Ignore_old/comprehensive_test.py`: SyntaxError: unexpected character after line continuation character (<unknown>, line 21)
- `Ignore_old/debug_consistency.py`: SyntaxError: unexpected character after line continuation character (<unknown>, line 16)
- `Ignore_old/debug_solver.py`: SyntaxError: unexpected character after line continuation character (<unknown>, line 16)
- `Ignore_old/demo_complete_system.py`: SyntaxError: unexpected character after line continuation character (<unknown>, line 23)
- `Ignore_old/try_it_yourself.py`: SyntaxError: unexpected character after line continuation character (<unknown>, line 20)