from __future__ import annotations

from dataclasses import asdict, dataclass

from spelling_check.models import CorrectionResult


@dataclass
class CscMetrics:
    detection_precision: float
    detection_recall: float
    detection_f1: float
    correction_precision: float
    correction_recall: float
    correction_f1: float
    false_positive_rate: float
    detected_positions: int
    gold_error_positions: int
    correct_detected_positions: int
    predicted_corrections: int
    gold_corrections: int
    correct_corrections: int
    false_positive_positions: int
    gold_non_error_positions: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def evaluate_csc(results: list[CorrectionResult], gold_texts: list[str]) -> CscMetrics:
    if len(results) != len(gold_texts):
        raise ValueError("results and gold_texts must have the same length")

    detected_positions = 0
    gold_error_positions = 0
    correct_detected_positions = 0
    predicted_corrections = 0
    gold_corrections = 0
    correct_corrections = 0
    false_positive_positions = 0
    gold_non_error_positions = 0

    for result, gold_text in zip(results, gold_texts, strict=True):
        if len(result.input) != len(gold_text):
            raise ValueError("CSC metrics require equal-length input and gold text")

        gold_errors = {
            index
            for index, (original, gold) in enumerate(
                zip(result.input, gold_text, strict=True)
            )
            if original != gold
        }
        detected = {risk.index for risk in result.suspicious_chars}
        predicted = {
            correction.index: correction.candidate_char
            for correction in result.corrections
            if result.status == "corrected"
        }

        detected_positions += len(detected)
        gold_error_positions += len(gold_errors)
        correct_detected_positions += len(detected & gold_errors)
        predicted_corrections += len(predicted)
        gold_corrections += len(gold_errors)
        false_positive_positions += len(detected - gold_errors)
        gold_non_error_positions += len(result.input) - len(gold_errors)

        for index, candidate_char in predicted.items():
            if index in gold_errors and gold_text[index] == candidate_char:
                correct_corrections += 1

    detection_precision = _safe_div(correct_detected_positions, detected_positions)
    detection_recall = _safe_div(correct_detected_positions, gold_error_positions)
    correction_precision = _safe_div(correct_corrections, predicted_corrections)
    correction_recall = _safe_div(correct_corrections, gold_corrections)

    return CscMetrics(
        detection_precision=detection_precision,
        detection_recall=detection_recall,
        detection_f1=_f1(detection_precision, detection_recall),
        correction_precision=correction_precision,
        correction_recall=correction_recall,
        correction_f1=_f1(correction_precision, correction_recall),
        false_positive_rate=_safe_div(
            false_positive_positions, gold_non_error_positions
        ),
        detected_positions=detected_positions,
        gold_error_positions=gold_error_positions,
        correct_detected_positions=correct_detected_positions,
        predicted_corrections=predicted_corrections,
        gold_corrections=gold_corrections,
        correct_corrections=correct_corrections,
        false_positive_positions=false_positive_positions,
        gold_non_error_positions=gold_non_error_positions,
    )


def _safe_div(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
