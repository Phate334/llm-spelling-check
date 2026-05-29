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
        payload = {
            "model": self.model,
            "prompt": text,
            "max_tokens": 1,
            "temperature": 0,
            "prompt_logprobs": prompt_logprobs,
            "logprobs": 1,
        }
        return self._post_completion(payload)

    def complete_next_token(self, prefix: str, logprobs: int) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": prefix,
            "max_tokens": 1,
            "temperature": 0,
            "logprobs": logprobs,
        }
        return self._post_completion(payload)

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
