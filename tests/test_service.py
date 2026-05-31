from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from spelling_check.service import (
    correct_cases,
    default_settings,
    evaluate_case_results,
    parse_cases,
    run_all,
)
from tests.fakes import fake_client_factory


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
