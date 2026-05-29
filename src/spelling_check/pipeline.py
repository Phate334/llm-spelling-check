from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from spelling_check.alignment import align_tokens_to_chars
from spelling_check.candidates import (
    deduplicate_candidates,
    generate_candidates,
    generate_word_candidates,
)
from spelling_check.decision import decide_result
from spelling_check.models import CandidateCorrection, CorrectionResult
from spelling_check.risk import (
    compute_char_risks,
    mean_logprob_per_char,
    select_suspicious_chars,
)
from spelling_check.text import local_window, replace_char


class PromptScorer(Protocol):
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]: ...


@dataclass
class SpellingCheckConfig:
    prompt_logprobs: int = 5
    risk_threshold: float = 7.0
    suspicious_limit: int = 5
    candidate_limit: int = 8
    window_radius: int = 12
    strong_delta: float = 1.0
    weak_delta: float = 0.3
    margin: float = 0.4
    trusted_sources: tuple[str, ...] = ("word_lexicon", "char_confusion")
    word_lexicon_bypass_risk: bool = True
    filter_top_logprob_candidates: bool = True


def spelling_check(
    text: str, client: PromptScorer, config: SpellingCheckConfig
) -> CorrectionResult:
    original_response = client.score_prompt(text, config.prompt_logprobs)
    original_tokens = align_tokens_to_chars(text, original_response)
    risks = compute_char_risks(text, original_tokens)
    suspicious = select_suspicious_chars(
        risks, threshold=config.risk_threshold, limit=config.suspicious_limit
    )

    candidates = (
        generate_word_candidates(text) if config.word_lexicon_bypass_risk else []
    )
    for risk in suspicious:
        candidates.extend(
            generate_candidates(
                text,
                risk,
                original_tokens,
                limit=config.candidate_limit,
                include_word_lexicon=not config.word_lexicon_bypass_risk,
                filter_top_logprob_candidates=config.filter_top_logprob_candidates,
            )
        )

    corrections: list[CandidateCorrection] = []
    window_score_cache: dict[str, float] = {}
    for candidate in deduplicate_candidates(candidates):
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
                original_span=candidate.original_span,
                corrected_span=candidate.corrected_span,
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
        trusted_sources=config.trusted_sources,
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
