from __future__ import annotations

from statistics import mean

from spelling_check.models import CharRisk, TokenScore
from spelling_check.text import is_cjk, is_punctuation_or_space


def compute_char_risks(text: str, tokens: list[TokenScore], span_lengths: tuple[int, ...] = (1, 2, 3)) -> list[CharRisk]:
    risks: list[CharRisk] = []
    for index, char in enumerate(text):
        if not is_cjk(char) or is_punctuation_or_space(char):
            continue

        token_logprob = _char_logprob(index, tokens)
        span_score = _lowest_span_score(text, index, tokens, span_lengths)
        score_candidates = [value for value in [token_logprob, span_score] if value is not None]
        if not score_candidates:
            continue
        score_basis = min(score_candidates)
        risks.append(
            CharRisk(
                index=index,
                char=char,
                risk_score=-score_basis,
                token_logprob=token_logprob,
                span_score=span_score,
                reason="低字元或局部 span likelihood",
            )
        )
    return risks


def select_suspicious_chars(risks: list[CharRisk], threshold: float, limit: int) -> list[CharRisk]:
    selected = [risk for risk in risks if risk.risk_score >= threshold]
    return sorted(selected, key=lambda risk: risk.risk_score, reverse=True)[:limit]


def mean_logprob_per_char(text: str, tokens: list[TokenScore]) -> float:
    if not text or not tokens:
        return float("-inf")
    covered = [token.logprob for token in tokens if token.end > token.start]
    return sum(covered) / len(text)


def _char_logprob(index: int, tokens: list[TokenScore]) -> float | None:
    overlapping = [token.logprob for token in tokens if token.start <= index < token.end]
    return mean(overlapping) if overlapping else None


def _lowest_span_score(text: str, index: int, tokens: list[TokenScore], span_lengths: tuple[int, ...]) -> float | None:
    scores: list[float] = []
    for length in span_lengths:
        for start in range(max(0, index - length + 1), min(index + 1, len(text) - length + 1)):
            end = start + length
            if not any(token.start < end and token.end > start for token in tokens):
                continue
            token_sum = sum(token.logprob for token in tokens if token.start < end and token.end > start)
            scores.append(token_sum / length)
    return min(scores) if scores else None
