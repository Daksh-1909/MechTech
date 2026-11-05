from typing import Any

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.ml.datasets import SYNTHETIC_LABELS


def classification_metrics(y_true, y_pred) -> dict[str, Any]:
    labels = list(SYNTHETIC_LABELS)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "labels": labels,
        "test_samples": len(y_true),
    }


def anomaly_metrics(y_true: list[bool], y_pred: list[bool]) -> dict[str, Any]:
    """Report event detection quality and the normal-window false-positive rate."""
    positive_true = [int(value) for value in y_true]
    positive_pred = [int(value) for value in y_pred]
    normal_count = sum(not value for value in y_true)
    abnormal_count = sum(y_true)
    false_positives = sum(
        predicted for actual, predicted in zip(y_true, y_pred, strict=True) if not actual
    )
    true_positives = sum(
        actual and predicted for actual, predicted in zip(y_true, y_pred, strict=True)
    )
    return {
        "accuracy": float(accuracy_score(positive_true, positive_pred)),
        "precision": float(precision_score(positive_true, positive_pred, zero_division=0)),
        "recall": float(recall_score(positive_true, positive_pred, zero_division=0)),
        "f1": float(f1_score(positive_true, positive_pred, zero_division=0)),
        "false_positive_rate_on_normal": false_positives / normal_count if normal_count else None,
        "detection_rate_on_abnormal": true_positives / abnormal_count if abnormal_count else None,
        "normal_windows": normal_count,
        "abnormal_windows": abnormal_count,
    }
