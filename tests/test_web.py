from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from spelling_check.service import ModelSettings
from spelling_check.web import create_app


class FakeClient:
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


def fake_client_factory(settings: ModelSettings) -> FakeClient:
    del settings
    return FakeClient()


def test_get_index_returns_webui_html() -> None:
    client = TestClient(create_app(fake_client_factory))

    response = client.get("/")
    script = client.get("/static/app.js")
    styles = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "<textarea" in response.text
    assert "Risk threshold" in response.text
    assert "Detection Precision" in response.text
    assert "FPR" in response.text
    assert "/static/app.js" in response.text
    assert "/static/styles.css" in response.text
    assert script.status_code == 200
    assert styles.status_code == 200
    assert "renderAlignment" in script.text
    assert "candidateJudgment" in script.text


def test_defaults_api_hides_api_key() -> None:
    client = TestClient(create_app(fake_client_factory))

    response = client.get("/api/defaults")

    data = response.json()
    assert response.status_code == 200
    assert "settings" in data
    assert "api_key" not in data["settings"]


def test_run_api_corrects_text_and_hides_api_key() -> None:
    client = TestClient(create_app(fake_client_factory))

    response = client.post(
        "/api/run",
        json={
            "text": "咖非",
            "settings": {
                "base_url": "http://localhost:7072/v1",
                "model": "gemma-4-26b-a4b",
                "api_key": "secret",
                "config": {"risk_threshold": 7.0},
            },
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["settings"]["model"] == "gemma-4-26b-a4b"
    assert "api_key" not in data["settings"]
    assert data["cases"][0]["corrected_text"] == "咖啡"
    assert data["metrics"] is None


def test_run_api_uploads_sgml_and_returns_metrics() -> None:
    client = TestClient(create_app(fake_client_factory))
    sgml = """
<ESSAY>
<TEXT><PASSAGE id="p1">咖非</PASSAGE></TEXT>
<MISTAKE id="p1" location="2"><WRONG>非</WRONG><CORRECTION>啡</CORRECTION></MISTAKE>
</ESSAY>
"""

    response = client.post(
        "/api/run",
        data={"settings": '{"config":{"risk_threshold":7.0}}'},
        files={"file": ("sample.sgml", sgml, "text/plain")},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["summary"]["case_count"] == 1
    assert data["metrics"]["correction_recall"] == 1.0
    assert data["cases"][0]["gold"] == "咖啡"


def test_parse_and_evaluate_endpoints() -> None:
    client = TestClient(create_app(fake_client_factory))

    parsed = client.post(
        "/api/parse",
        json={"cases": [{"id": "a", "input": "咖非", "gold": "咖啡"}]},
    )
    corrected = client.post(
        "/api/correct",
        json={
            "cases": parsed.json()["cases"],
            "settings": {"config": {"risk_threshold": 7.0}},
        },
    )
    evaluated = client.post(
        "/api/evaluate",
        json={"cases": corrected.json()["cases"]},
    )

    assert parsed.status_code == 200
    assert corrected.status_code == 200
    assert evaluated.status_code == 200
    assert evaluated.json()["metrics"]["detection_f1"] == 1.0
