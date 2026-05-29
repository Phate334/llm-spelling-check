from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from spelling_check.alignment import align_tokens_to_chars
from spelling_check.candidates import generate_candidates
from spelling_check.decision import decide_result
from spelling_check.models import Candidate, CandidateCorrection, CorrectionResult
from spelling_check.risk import (
    compute_char_risks,
    mean_logprob_per_char,
    select_suspicious_chars,
)
from spelling_check.text import local_window, replace_char


class PromptScorer(Protocol):
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]: ...


class BatchPromptScorer(PromptScorer, Protocol):
    def score_prompts(
        self, texts: list[str], prompt_logprobs: int
    ) -> list[dict[str, Any]]: ...


class SpellingCheckClient(PromptScorer, Protocol):
    pass


@dataclass
class SpellingCheckConfig:
    prompt_logprobs: int = 5
    risk_threshold: float = 7.0
    suspicious_limit: int = 5
    candidate_limit: int = 8
    window_radius: int = 12
    score_batch_size: int = 1
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

    corrections: list[CandidateCorrection] = []
    window_score_cache: dict[str, float] = {}
    deduped_candidates = _deduplicate_candidates(candidates)
    windows_to_score = []
    for candidate in deduped_candidates:
        original_window = local_window(text, candidate.index, config.window_radius)
        candidate_text = replace_char(text, candidate.index, candidate.candidate_char)
        candidate_window = local_window(
            candidate_text, candidate.index, config.window_radius
        )
        windows_to_score.extend([original_window, candidate_window])

    _score_windows(windows_to_score, client, config, window_score_cache)

    for candidate in deduped_candidates:
        original_window = local_window(text, candidate.index, config.window_radius)
        candidate_text = replace_char(text, candidate.index, candidate.candidate_char)
        candidate_window = local_window(
            candidate_text, candidate.index, config.window_radius
        )
        original_score = window_score_cache[original_window]
        candidate_score = window_score_cache[candidate_window]
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


def _score_windows(
    windows: list[str],
    client: PromptScorer,
    config: SpellingCheckConfig,
    cache: dict[str, float],
) -> None:
    missing = list(dict.fromkeys(window for window in windows if window not in cache))
    batch_size = max(1, config.score_batch_size)
    for start in range(0, len(missing), batch_size):
        batch = missing[start : start + batch_size]
        responses = _score_prompt_batch(client, batch, config.prompt_logprobs)
        for window, response in zip(batch, responses, strict=True):
            tokens = align_tokens_to_chars(window, response)
            cache[window] = mean_logprob_per_char(window, tokens)


def _score_prompt_batch(
    client: PromptScorer, windows: list[str], prompt_logprobs: int
) -> list[dict[str, Any]]:
    score_prompts = getattr(client, "score_prompts", None)
    if callable(score_prompts) and len(windows) > 1:
        return list(score_prompts(windows, prompt_logprobs))
    return [client.score_prompt(window, prompt_logprobs) for window in windows]


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
