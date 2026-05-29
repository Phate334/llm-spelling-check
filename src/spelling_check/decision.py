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
    trusted_sources: tuple[str, ...],
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

    trusted_ranked = [
        correction for correction in ranked if correction.source in trusted_sources
    ]
    best_trusted = trusted_ranked[0] if trusted_ranked else None
    second_trusted = trusted_ranked[1] if len(trusted_ranked) > 1 else None
    clear_trusted_margin = best_trusted is not None and (
        second_trusted is None or best_trusted.delta - second_trusted.delta >= margin
    )

    if (
        best_trusted is not None
        and best_trusted.delta >= strong_delta
        and clear_trusted_margin
    ):
        return CorrectionResult(
            input=text,
            status="corrected",
            confidence="high",
            corrected_text=replace_char(
                text, best_trusted.index, best_trusted.candidate_char
            ),
            corrections=[best_trusted],
            suspicious_chars=suspicious,
        )

    best = ranked[0]
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
