from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from spelling_check.alignment import align_tokens_to_chars
from spelling_check.candidates import generate_candidates
from spelling_check.decision import decide_result
from spelling_check.fim_candidates import (
    StructuredCandidateClient,
    generate_fim_candidates,
)
from spelling_check.models import Candidate, CandidateCorrection, CorrectionResult
from spelling_check.risk import (
    compute_char_risks,
    mean_logprob_per_char,
    select_suspicious_chars,
)
from spelling_check.text import local_window, replace_char


class PromptScorer(Protocol):
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]: ...


class SpellingCheckClient(PromptScorer, StructuredCandidateClient, Protocol):
    pass


@dataclass
class SpellingCheckConfig:
    prompt_logprobs: int = 5
    risk_threshold: float = 7.0
    suspicious_limit: int = 5
    candidate_limit: int = 8
    fim_candidate_limit: int = 0
    fim_max_tokens: int = 96
    window_radius: int = 12
    strong_delta: float = 1.0
    weak_delta: float = 0.3
    margin: float = 0.4


def spelling_check(
    text: str, client: SpellingCheckClient, config: SpellingCheckConfig
) -> CorrectionResult:
    original_response = client.score_prompt(text, config.prompt_logprobs)
    original_tokens = align_tokens_to_chars(text, original_response)
    risks = compute_char_risks(text, original_tokens)
    suspicious = select_suspicious_chars(
        risks, threshold=config.risk_threshold, limit=config.suspicious_limit
    )

    candidates = []
    for risk in suspicious:
        candidates.extend(
            generate_candidates(
                risk,
                original_tokens,
                limit=config.candidate_limit,
            )
        )
        if config.fim_candidate_limit > 0:
            candidates.extend(
                generate_fim_candidates(
                    text,
                    risk,
                    client,
                    window_radius=config.window_radius,
                    limit=config.fim_candidate_limit,
                    max_tokens=config.fim_max_tokens,
                )
            )

    corrections: list[CandidateCorrection] = []
    window_score_cache: dict[str, float] = {}
    for candidate in _deduplicate_candidates(candidates):
        original_window = local_window(text, candidate.index, config.window_radius)
        original_score = _score_window(
            original_window, client, config, window_score_cache
        )
        candidate_text = replace_char(text, candidate.index, candidate.candidate_char)
        candidate_window = local_window(
            candidate_text, candidate.index, config.window_radius
        )
        candidate_score = _score_window(
            candidate_window, client, config, window_score_cache
        )
        corrections.append(
            CandidateCorrection(
                index=candidate.index,
                original_char=candidate.original_char,
                candidate_char=candidate.candidate_char,
                source=candidate.source,
                original_text=text,
                candidate_text=candidate_text,
                original_score=original_score,
                candidate_score=candidate_score,
                delta=candidate_score - original_score,
                original_span=candidate.original_char,
                corrected_span=candidate.candidate_char,
            )
        )

    ranked = sorted(corrections, key=lambda correction: correction.delta, reverse=True)
    return decide_result(
        text=text,
        suspicious=suspicious,
        ranked=ranked,
        strong_delta=config.strong_delta,
        weak_delta=config.weak_delta,
        margin=config.margin,
    )


def _score_window(
    window: str,
    client: PromptScorer,
    config: SpellingCheckConfig,
    cache: dict[str, float],
) -> float:
    if window not in cache:
        response = client.score_prompt(window, config.prompt_logprobs)
        tokens = align_tokens_to_chars(window, response)
        cache[window] = mean_logprob_per_char(window, tokens)
    return cache[window]


def _deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[tuple[int, str]] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = (candidate.index, candidate.candidate_char)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped
