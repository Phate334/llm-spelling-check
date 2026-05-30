from __future__ import annotations

from spelling_check.evaluation import evaluate_csc
from spelling_check.models import CandidateCorrection, CharRisk, CorrectionResult


def test_evaluate_csc_counts_detection_correction_and_false_positive() -> None:
    results = [
        CorrectionResult(
            input="甲乙丙",
            status="corrected",
            confidence="high",
            corrected_text="甲丁丙",
            suspicious_chars=[
                CharRisk(1, "乙", 8.0, -8.0, None, "test"),
                CharRisk(2, "丙", 7.0, -7.0, None, "test"),
            ],
            corrections=[
                CandidateCorrection(
                    index=1,
                    original_char="乙",
                    candidate_char="丁",
                    source="test",
                    original_text="甲乙丙",
                    candidate_text="甲丁丙",
                    original_score=-2.0,
                    candidate_score=-1.0,
                    delta=1.0,
                    original_span="乙",
                    corrected_span="丁",
                )
            ],
        ),
        CorrectionResult(
            input="戊己",
            status="no_error",
            confidence="none",
            corrected_text="戊己",
            suspicious_chars=[],
            corrections=[],
        ),
    ]

    metrics = evaluate_csc(results, ["甲丁丙", "戊己"])

    assert metrics.detected_positions == 2
    assert metrics.gold_error_positions == 1
    assert metrics.correct_detected_positions == 1
    assert metrics.predicted_corrections == 1
    assert metrics.correct_corrections == 1
    assert metrics.false_positive_positions == 1
    assert metrics.gold_non_error_positions == 4
    assert metrics.detection_precision == 0.5
    assert metrics.detection_recall == 1.0
    assert metrics.correction_precision == 1.0
    assert metrics.correction_recall == 1.0
    assert metrics.false_positive_rate == 0.25
