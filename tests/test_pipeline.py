from __future__ import annotations

from typing import Any

from spelling_check.pipeline import SpellingCheckConfig, spelling_check


class FakeClient:
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]:
        prompt_logprobs_payload = []
        prompt_token_ids = []
        for index, char in enumerate(text):
            token_id = index + 1
            prompt_token_ids.append(token_id)
            logprob = -8.0 if char == "非" else -1.0
            prompt_logprobs_payload.append(
                {
                    str(token_id): {
                        "decoded_token": char,
                        "logprob": logprob,
                        "rank": 1,
                    },
                    str(token_id + 1000): {
                        "decoded_token": "啡",
                        "logprob": -0.5,
                        "rank": 2,
                    },
                }
            )
        return {
            "choices": [
                {
                    "prompt_token_ids": prompt_token_ids,
                    "prompt_logprobs": prompt_logprobs_payload,
                }
            ]
        }


def test_spelling_check_corrects_trusted_candidate() -> None:
    result = spelling_check(
        "我今天想喝一杯咖非。",
        client=FakeClient(),
        config=SpellingCheckConfig(risk_threshold=7.0, strong_delta=0.5),
    )

    assert result.status == "corrected"
    assert result.corrected_text == "我今天想喝一杯咖啡。"
    assert result.corrections[0].candidate_char == "啡"


def test_spelling_check_keeps_clean_sentence() -> None:
    result = spelling_check(
        "我今天想喝一杯咖啡。",
        client=FakeClient(),
        config=SpellingCheckConfig(risk_threshold=7.0),
    )

    assert result.status == "no_error"
    assert result.corrected_text == "我今天想喝一杯咖啡。"
