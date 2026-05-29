from __future__ import annotations

from spelling_check.models import CandidateCorrection, CharRisk, CorrectionResult
from spelling_check.text import replace_char


def decide_result(
    text: str,
    suspicious: list[CharRisk],
    ranked: list[CandidateCorrection],
    strong_delta: float,
    weak_delta: float,
    margin: float,
) -> CorrectionResult:
    if not ranked:
        return CorrectionResult(
            input=text,
            status="no_error",
            confidence="high",
            corrected_text=text,
            corrections=[],
            suspicious_chars=suspicious,
        )

    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    clear_margin = second is None or best.delta - second.delta >= margin

    if best.delta >= strong_delta and clear_margin:
        return CorrectionResult(
            input=text,
            status="corrected",
            confidence="high",
            corrected_text=replace_char(text, best.index, best.candidate_char),
            corrections=[best],
            suspicious_chars=suspicious,
        )

    if best.delta >= weak_delta:
        return CorrectionResult(
            input=text,
            status="uncertain",
            confidence="medium",
            corrected_text=None,
            corrections=ranked[:3],
            suspicious_chars=suspicious,
        )

    return CorrectionResult(
        input=text,
        status="no_error",
        confidence="high",
        corrected_text=text,
        corrections=[],
        suspicious_chars=suspicious,
    )
