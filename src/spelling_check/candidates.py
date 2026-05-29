from __future__ import annotations

from typing import Any

from spelling_check.models import Candidate, CharRisk, TokenScore
from spelling_check.text import clean_token_text, is_single_cjk_char


def generate_candidates(
    text: str,
    risk: CharRisk,
    tokens: list[TokenScore],
    limit: int,
    *,
    filter_top_logprob_candidates: bool = True,
) -> list[Candidate]:
    candidates = _top_logprob_candidates(
        text,
        risk.index,
        tokens,
        filter_candidates=filter_top_logprob_candidates,
    )
    return deduplicate_candidates(candidates)[:limit]


def generate_next_token_candidates(
    risk: CharRisk,
    response: dict[str, Any],
    limit: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for token in _completion_candidate_tokens(response):
        token_text = clean_token_text(token)
        if token_text == risk.char or not is_single_cjk_char(token_text):
            continue
        candidates.append(
            Candidate(
                index=risk.index,
                original_char=risk.char,
                candidate_char=token_text,
                source="next_token_decode",
                original_span=risk.char,
                corrected_span=token_text,
            )
        )
    return deduplicate_candidates(candidates)[:limit]


def _top_logprob_candidates(
    text: str,
    index: int,
    tokens: list[TokenScore],
    *,
    filter_candidates: bool,
) -> list[Candidate]:
    original = text[index]
    candidates: list[Candidate] = []
    for token in tokens:
        if not (token.start <= index < token.end):
            continue
        for alternative in token.top_logprobs:
            alt_text = clean_token_text(str(alternative["token"]))
            if alt_text == original:
                continue
            if filter_candidates and not is_single_cjk_char(alt_text):
                continue
            if not filter_candidates and len(alt_text) != 1:
                continue
            candidates.append(
                Candidate(
                    index=index,
                    original_char=original,
                    candidate_char=alt_text,
                    source="vllm_top_logprob",
                    original_span=original,
                    corrected_span=alt_text,
                )
            )
    return candidates


def deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[tuple[int, str]] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = (candidate.index, candidate.candidate_char)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _completion_candidate_tokens(response: dict[str, Any]) -> list[str]:
    choice = response["choices"][0]
    tokens: list[str] = []
    generated_text = clean_token_text(str(choice.get("text") or ""))
    if generated_text:
        tokens.append(generated_text)

    logprobs = choice.get("logprobs") or {}
    top_logprobs = logprobs.get("top_logprobs") or []
    if top_logprobs:
        first_token_logprobs = top_logprobs[0] or {}
        tokens.extend(str(token) for token in first_token_logprobs)
    return tokens
