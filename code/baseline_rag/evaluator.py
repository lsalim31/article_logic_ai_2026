"""
Evaluation module for RAG baseline experiments.

This module computes standard classification metrics for logical reasoning
and natural language inference tasks. It handles both 3-way classification
schemes used in the datasets (True/False/Unknown for FOLIO/ProofWriter,
and Entailed/Contradicted/NotMentioned for ContractNLI).

Metrics include accuracy, precision, recall, F1-score, and confusion matrices.
"""


def evaluate(predictions, ground_truth, label_set=None):
    """
    Compute evaluation metrics for predictions against ground truth.

    Args:
        predictions: List of predicted labels (strings)
        ground_truth: List of true labels (strings)
        label_set: Optional list of valid labels (for validation)

    Returns:
        Dictionary containing:
            - 'accuracy': Overall accuracy (float in [0.0, 1.0])
            - 'precision': Macro-averaged precision (float in [0.0, 1.0])
            - 'recall': Macro-averaged recall (float in [0.0, 1.0])
            - 'f1': Macro-averaged F1 score (float in [0.0, 1.0])
            - 'confusion_matrix': Dict mapping (true_label, pred_label) -> count
            - 'per_class_metrics': Dict mapping label -> {'precision', 'recall', 'f1'}
    """
    if label_set is None:
        label_set = sorted(set(predictions + ground_truth))

    accuracy = compute_accuracy(predictions, ground_truth)
    confusion_matrix = compute_confusion_matrix(predictions, ground_truth, label_set)
    per_class_metrics = compute_per_class_metrics(predictions, ground_truth, label_set)
    macro_metrics = compute_macro_metrics(per_class_metrics)

    return {
        'accuracy': accuracy,
        'precision': macro_metrics['macro_precision'],
        'recall': macro_metrics['macro_recall'],
        'f1': macro_metrics['macro_f1'],
        'confusion_matrix': confusion_matrix,
        'per_class_metrics': per_class_metrics
    }


def compute_accuracy(predictions, ground_truth):
    """
    Compute classification accuracy.

    Args:
        predictions: List of predicted labels
        ground_truth: List of true labels

    Returns:
        Float accuracy value (fraction correct) in range [0.0, 1.0]
    """
    correct = sum(1 for pred, true in zip(predictions, ground_truth) if pred == true)
    total = len(predictions)
    return correct / total if total > 0 else 0.0


def compute_confusion_matrix(predictions, ground_truth, labels):
    """
    Compute confusion matrix for multi-class classification.

    Args:
        predictions: List of predicted labels
        ground_truth: List of true labels
        labels: List of all possible labels

    Returns:
        Dictionary mapping (true_label, pred_label) -> count
        Example: {('True', 'True'): 50, ('True', 'False'): 5, ...}
    """
    matrix = {}
    for true_label in labels:
        for pred_label in labels:
            matrix[(true_label, pred_label)] = 0

    for pred, true in zip(predictions, ground_truth):
        if (true, pred) in matrix:
            matrix[(true, pred)] += 1

    return matrix


def compute_per_class_metrics(predictions, ground_truth, labels):
    """
    Compute precision, recall, and F1 for each class.

    Args:
        predictions: List of predicted labels
        ground_truth: List of true labels
        labels: List of all possible labels

    Returns:
        Dictionary mapping label -> {'precision', 'recall', 'f1'}
        Example: {'True': {'precision': 0.85, 'recall': 0.90, 'f1': 0.87}, ...}
        Precision/recall/f1 are floats in [0.0, 1.0], or 0.0 if undefined
    """
    metrics = {}

    for label in labels:
        true_positives = sum(1 for pred, true in zip(predictions, ground_truth)
                            if pred == label and true == label)
        false_positives = sum(1 for pred, true in zip(predictions, ground_truth)
                             if pred == label and true != label)
        false_negatives = sum(1 for pred, true in zip(predictions, ground_truth)
                             if pred != label and true == label)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    return metrics


def compute_macro_metrics(per_class_metrics):
    """
    Compute macro-averaged metrics across all classes.

    Args:
        per_class_metrics: Dict from compute_per_class_metrics

    Returns:
        Dictionary containing:
            - 'macro_precision': Average precision across classes (float in [0.0, 1.0])
            - 'macro_recall': Average recall across classes (float in [0.0, 1.0])
            - 'macro_f1': Average F1 across classes (float in [0.0, 1.0])
    """
    num_classes = len(per_class_metrics)

    if num_classes == 0:
        return {'macro_precision': 0.0, 'macro_recall': 0.0, 'macro_f1': 0.0}

    total_precision = sum(metrics['precision'] for metrics in per_class_metrics.values())
    total_recall = sum(metrics['recall'] for metrics in per_class_metrics.values())
    total_f1 = sum(metrics['f1'] for metrics in per_class_metrics.values())

    return {
        'macro_precision': total_precision / num_classes,
        'macro_recall': total_recall / num_classes,
        'macro_f1': total_f1 / num_classes
    }


def format_results(metrics, dataset_name):
    """
    Format evaluation results for display and logging.

    Args:
        metrics: Dictionary from evaluate()
        dataset_name: Name of the dataset being evaluated

    Returns:
        Formatted string with results table
    """
    pass
