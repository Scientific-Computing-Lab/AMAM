from __future__ import annotations

from typing import Dict

import numpy as np

SEGMENTATION_METRIC_VERSION = "present-classes-per-image-v1"
ABSENT_CLASS_POLICY = "exclude_if_absent_in_gt_and_prediction"
METRIC_AGGREGATION = "per_image_present_class_macro_then_subset_macro"


def segmentation_metrics(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    class_count: int,
) -> Dict[str, float]:
    if prediction.shape != ground_truth.shape:
        raise ValueError("prediction and ground truth must have the same shape")
    if prediction.size == 0:
        raise ValueError("prediction and ground truth must not be empty")
    if class_count < 1:
        raise ValueError("class_count must be positive")
    if (
        np.any(prediction < 0)
        or np.any(prediction >= class_count)
        or np.any(ground_truth < 0)
        or np.any(ground_truth >= class_count)
    ):
        raise ValueError("prediction and ground truth labels must be within class_count")

    ious: list[float] = []
    dices: list[float] = []
    for class_id in range(class_count):
        predicted = prediction == class_id
        expected = ground_truth == class_id
        intersection = int(np.logical_and(predicted, expected).sum())
        union = int(np.logical_or(predicted, expected).sum())
        if union == 0:
            continue
        denominator = int(predicted.sum() + expected.sum())
        ious.append(intersection / union)
        dices.append((2 * intersection) / denominator)

    return {
        "miou": float(np.mean(ious)),
        "dice": float(np.mean(dices)),
        "pixel_acc": float((prediction == ground_truth).mean()),
    }


def segmentation_metric_protocol_metadata() -> Dict[str, str]:
    return {
        "segmentation_metric_version": SEGMENTATION_METRIC_VERSION,
        "absent_class_policy": ABSENT_CLASS_POLICY,
        "metric_aggregation": METRIC_AGGREGATION,
    }
