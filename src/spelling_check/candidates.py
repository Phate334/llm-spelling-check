from __future__ import annotations

from spelling_check.models import Candidate, CharRisk, TokenScore
from spelling_check.text import clean_token_text, is_single_cjk_char


def generate_candidates(
    risk: CharRisk,
    tokens: list[TokenScore],
    limit: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for token in tokens:
        if not (token.start <= risk.index < token.end):
            continue
        for alternative in token.top_logprobs:
            alt_text = clean_token_text(str(alternative["token"]))
            if alt_text == risk.char:
                continue
            if not is_single_cjk_char(alt_text):
                continue
            candidates.append(
                Candidate(
                    index=risk.index,
                    original_char=risk.char,
                    candidate_char=alt_text,
                    source="vllm_top_logprob",
                )
            )
    return candidates[:limit]
