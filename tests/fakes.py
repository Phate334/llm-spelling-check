from __future__ import annotations

from typing import Any

from spelling_check.service import ModelSettings


class FakePromptClient:
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]:
        del prompt_logprobs
        prompt_logprobs_payload = []
        prompt_token_ids = []
        for index, char in enumerate(text):
            token_id = index + 1
            prompt_token_ids.append(token_id)
            alternatives = {
                str(token_id): {
                    "decoded_token": char,
                    "logprob": -8.0 if char == "非" else -1.0,
                    "rank": 1,
                }
            }
            if char == "非":
                alternatives[str(token_id + 1000)] = {
                    "decoded_token": "啡",
                    "logprob": -0.1,
                    "rank": 2,
                }
            prompt_logprobs_payload.append(alternatives)
        return {
            "choices": [
                {
                    "prompt_token_ids": prompt_token_ids,
                    "prompt_logprobs": prompt_logprobs_payload,
                }
            ]
        }

    def score_prompts(
        self, texts: list[str], prompt_logprobs: int
    ) -> list[dict[str, Any]]:
        return [self.score_prompt(text, prompt_logprobs) for text in texts]


def fake_client_factory(settings: ModelSettings) -> FakePromptClient:
    del settings
    return FakePromptClient()
