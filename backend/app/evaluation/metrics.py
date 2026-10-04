"""
Evaluation Metrics & Benchmark Engine for FinLens AI.
Calculates Precision, Recall, F1-Score, and Accuracy for Document AI and Agent Intent Routing.
"""

from collections import defaultdict
from typing import Any


def calculate_classification_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    """
    Computes per-class and macro-averaged Precision, Recall, and F1-score without external sklearn dependency.
    """
    assert len(y_true) == len(y_pred), "y_true and y_pred must have equal length"

    total = len(y_true)
    if total == 0:
        return {"accuracy": 0.0, "macro_f1": 0.0, "per_class": {}}

    classes = sorted(list(set(y_true) | set(y_pred)))

    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    correct = 0
    for true_label, pred_label in zip(y_true, y_pred):
        if true_label == pred_label:
            correct += 1
            tp[true_label] += 1
        else:
            fp[pred_label] += 1
            fn[true_label] += 1

    accuracy = correct / total

    per_class = {}
    f1_list = []

    for c in classes:
        c_tp = tp[c]
        c_fp = fp[c]
        c_fn = fn[c]

        precision = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        recall = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[c] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": c_tp + c_fn,
        }
        if (c_tp + c_fn) > 0:  # Only count classes present in ground truth
            f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "total_samples": total,
        "correct_samples": correct,
        "per_class": per_class,
    }
