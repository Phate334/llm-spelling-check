from __future__ import annotations

import json
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class VllmClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]:
        return self.score_prompts([text], prompt_logprobs)[0]

    def score_prompts(
        self, texts: list[str], prompt_logprobs: int
    ) -> list[dict[str, Any]]:
        if not texts:
            return []
        payload = {
            "model": self.model,
            "prompt": texts[0] if len(texts) == 1 else texts,
            "max_tokens": 1,
            "temperature": 0,
            "prompt_logprobs": prompt_logprobs,
            "logprobs": 1,
        }
        response = self._post_completion(payload)
        return _split_completion_response(response, len(texts))

    def _post_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            f"{self.base_url}/completions", data=body, headers=headers, method="POST"
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return cast(
                    "dict[str, Any]", json.loads(response.read().decode("utf-8"))
                )
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"vLLM request failed: HTTP {exc.code}: {detail}")
        except URLError as exc:
            raise RuntimeError(f"vLLM request failed: {exc.reason}")


def _split_completion_response(
    response: dict[str, Any], expected_count: int
) -> list[dict[str, Any]]:
    choices = response.get("choices") or []
    if not isinstance(choices, list):
        raise RuntimeError("vLLM response choices must be a list")
    if len(choices) != expected_count:
        raise RuntimeError(
            "vLLM response choice count mismatch: "
            f"expected {expected_count}, got {len(choices)}"
        )
    if expected_count == 1:
        return [response]

    indexed_choices = sorted(
        enumerate(choices),
        key=lambda item: (
            item[1].get("index", item[0]) if isinstance(item[1], dict) else item[0]
        ),
    )
    return [
        {
            **response,
            "choices": [choice],
        }
        for _, choice in indexed_choices
    ]
