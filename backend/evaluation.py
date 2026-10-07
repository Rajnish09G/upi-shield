import csv
from pathlib import Path

from .detection.scorer import score


def evaluate_labels(path: str | Path = "data/labels.csv") -> dict:
    """Evaluate labelled local captures with precision, recall, and F1."""
    rows = list(csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines()))
    true_positive = false_positive = false_negative = true_negative = 0
    for row in rows:
        result = score(
            row["url"], row["screenshot"], row["dom"],
            [row["brand"]] if row.get("brand") else [],
        )
        predicted = result["verdict"] == "phishing"
        actual = row["label"].lower() in {"phishing", "malicious", "1", "true"}
        if predicted and actual:
            true_positive += 1
        elif predicted:
            false_positive += 1
        elif actual:
            false_negative += 1
        else:
            true_negative += 1
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "samples": len(rows), "true_positive": true_positive,
        "false_positive": false_positive, "false_negative": false_negative,
        "true_negative": true_negative, "precision": round(precision, 4),
        "recall": round(recall, 4), "f1": round(f1, 4),
    }
