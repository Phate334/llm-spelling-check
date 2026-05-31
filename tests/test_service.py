from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from spelling_check.service import (
    ModelSettings,
    correct_cases,
    default_settings,
    evaluate_case_results,
    parse_cases,
    run_all,
)


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


def test_parse_cases_reads_json_object_array() -> None:
    cases = parse_cases(
        file_name="sample.json",
        file_content='[{"id":"a","input":"咖非","gold":"咖啡"}]'.encode(),
    )

    assert cases[0].id == "a"
    assert cases[0].input == "咖非"
    assert cases[0].gold == "咖啡"
    assert cases[0].source_format == "json"


def test_parse_cases_reads_sgml_upload() -> None:
    sgml = """
<ESSAY>
<TEXT><PASSAGE id="p1">咖非</PASSAGE></TEXT>
<MISTAKE id="p1" location="2"><WRONG>非</WRONG><CORRECTION>啡</CORRECTION></MISTAKE>
</ESSAY>
"""

    cases = parse_cases(file_name="sample.sgml", file_content=sgml.encode())

    assert cases[0].id == "p1"
    assert cases[0].input == "咖非"
    assert cases[0].gold == "咖啡"
    assert cases[0].source_format == "sgml"


def test_correct_and_evaluate_preserves_result_details() -> None:
    settings = default_settings({"config": {"risk_threshold": 7.0}})
    cases = parse_cases(text="咖非")
    cases[0] = replace(cases[0], gold="咖啡")

    result_cases = correct_cases(cases, settings, fake_client_factory)
    metrics = evaluate_case_results(result_cases)

    assert result_cases[0]["status"] == "corrected"
    assert result_cases[0]["corrected_text"] == "咖啡"
    assert metrics is not None
    assert metrics["detection_recall"] == 1.0
    assert metrics["correction_recall"] == 1.0


def test_default_settings_reads_environment(monkeypatch: Any) -> None:
    monkeypatch.setenv("SPELLING_BASE_URL", "http://env.example/v1")
    monkeypatch.setenv("SPELLING_MODEL", "gemma-env")
    monkeypatch.setenv("SPELLING_API_KEY", "env-secret")
    monkeypatch.setenv("SPELLING_TIMEOUT", "45")

    settings = default_settings()

    assert settings.base_url == "http://env.example/v1"
    assert settings.model == "gemma-env"
    assert settings.api_key == "env-secret"
    assert settings.timeout == 45.0


def test_run_all_without_gold_returns_null_metrics() -> None:
    result = run_all(
        text="咖非",
        settings_data={"config": {"risk_threshold": 7.0}},
        client_factory=fake_client_factory,
    )

    assert result["metrics"] is None
    summary = cast("dict[str, object]", result["summary"])
    cases = cast("list[dict[str, object]]", result["cases"])
    assert summary["case_count"] == 1
    assert cases[0]["corrected_text"] == "咖啡"
