from __future__ import annotations

from typing import Any, cast

from spelling_check.models import TokenScore
from spelling_check.text import clean_token_text


def align_tokens_to_chars(text: str, response: dict[str, Any]) -> list[TokenScore]:
    choice = response["choices"][0]
    prompt_logprobs = choice.get("prompt_logprobs") or []
    prompt_token_ids = choice.get("prompt_token_ids") or []
    tokens: list[TokenScore] = []
    cursor = 0

    for i, alternatives in enumerate(prompt_logprobs):
        if not alternatives:
            continue
        token_id = prompt_token_ids[i] if i < len(prompt_token_ids) else None
        token_info = _actual_prompt_token(alternatives, token_id)
        token_text = clean_token_text(
            str(token_info.get("decoded_token") or token_info.get("token") or "")
        )
        if not token_text:
            continue
        start = text.find(token_text, cursor)
        if start < 0:
            continue
        end = start + len(token_text)
        tokens.append(
            TokenScore(
                token_id=token_id,
                token_text=token_text,
                start=start,
                end=end,
                logprob=float(token_info["logprob"]),
                top_logprobs=_top_logprobs(alternatives),
            )
        )
        cursor = end
    return tokens


def _actual_prompt_token(
    alternatives: dict[str, Any], token_id: int | None
) -> dict[str, Any]:
    if token_id is not None and str(token_id) in alternatives:
        return cast("dict[str, Any]", alternatives[str(token_id)])
    return cast("dict[str, Any]", next(iter(alternatives.values())))


def _top_logprobs(alternatives: dict[str, Any]) -> list[dict[str, object]]:
    values = sorted(
        alternatives.values(), key=lambda item: item["logprob"], reverse=True
    )
    return [
        {
            "token": clean_token_text(
                str(item.get("decoded_token") or item.get("token") or "")
            ),
            "logprob": float(item["logprob"]),
        }
        for item in values
    ]
