from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from spelling_check import cli
from spelling_check.models import CandidateCorrection, CharRisk, CorrectionResult
from spelling_check.pipeline import SpellingCheckConfig


class DummyClient:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


def fake_spelling_check(
    text: str, client: object, config: SpellingCheckConfig
) -> CorrectionResult:
    del client, config
    corrections = []
    status = "no_error"
    corrected_text = text
    if "錯" in text:
        corrected_text = text.replace("錯", "正", 1)
        status = "corrected"
        corrections = [
            CandidateCorrection(
                index=text.index("錯"),
                original_char="錯",
                candidate_char="正",
                source="test",
                original_text=text,
                candidate_text=corrected_text,
                original_score=-2.0,
                candidate_score=-1.0,
                delta=1.0,
                original_span="錯",
                corrected_span="正",
            )
        ]
    return CorrectionResult(
        input=text,
        status=status,
        confidence="high" if status == "corrected" else "none",
        corrected_text=corrected_text,
        suspicious_chars=[CharRisk(text.index("錯"), "錯", 8.0, -8.0, None, "test")]
        if "錯" in text
        else [],
        corrections=corrections,
    )


def test_sgml_input_outputs_single_json_object(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    path = tmp_path / "sample.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT><PASSAGE id="p1">甲錯丙</PASSAGE></TEXT>
<MISTAKE id="p1" location="2"><WRONG>錯</WRONG><CORRECTION>正</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "VllmClient", DummyClient)
    monkeypatch.setattr(cli, "spelling_check", fake_spelling_check)
    monkeypatch.setattr(sys, "argv", ["spelling-check", "--input-file", str(path)])

    assert cli.main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["dataset"]["format"] == "sgml"
    assert output["dataset"]["case_count"] == 1
    assert output["dataset"]["gold_error_count"] == 1
    assert output["metrics"]["correction_recall"] == 1.0
    assert len(output["cases"]) == 1
    assert output["cases"][0]["id"] == "p1"
    assert output["cases"][0]["gold"] == "甲正丙"


def test_non_sgml_json_lines_behavior_is_unchanged(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    path = tmp_path / "sample.json"
    path.write_text('["甲乙"]', encoding="utf-8")
    monkeypatch.setattr(cli, "VllmClient", DummyClient)
    monkeypatch.setattr(cli, "spelling_check", fake_spelling_check)
    monkeypatch.setattr(
        sys, "argv", ["spelling-check", "--input-file", str(path), "--json"]
    )

    assert cli.main() == 0

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["input"] == "甲乙"


def test_parse_args_reads_environment_defaults(monkeypatch: Any) -> None:
    monkeypatch.setenv("SPELLING_BASE_URL", "http://env.example/v1")
    monkeypatch.setenv("SPELLING_MODEL", "gemma-env")
    monkeypatch.setenv("SPELLING_API_KEY", "secret-from-env")
    monkeypatch.setenv("SPELLING_TIMEOUT", "12.5")
    monkeypatch.setattr(sys, "argv", ["spelling-check", "測試句子"])

    args = cli.parse_args()

    assert args.base_url == "http://env.example/v1"
    assert args.model == "gemma-env"
    assert args.api_key == "secret-from-env"
    assert args.timeout == 12.5


def test_cli_options_override_environment_and_feed_client_config(
    monkeypatch: Any,
    capsys: Any,
) -> None:
    captured: dict[str, object] = {}

    class CapturingClient(DummyClient):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            captured["client_kwargs"] = kwargs

    def capturing_spelling_check(
        text: str, client: object, config: SpellingCheckConfig
    ) -> CorrectionResult:
        captured["text"] = text
        captured["client"] = client
        captured["config"] = config
        return CorrectionResult(
            input=text,
            status="no_error",
            confidence="high",
            corrected_text=text,
            suspicious_chars=[],
            corrections=[],
        )

    monkeypatch.setenv("SPELLING_BASE_URL", "http://env.example/v1")
    monkeypatch.setenv("SPELLING_MODEL", "gemma-env")
    monkeypatch.setenv("SPELLING_API_KEY", "secret-from-env")
    monkeypatch.setenv("SPELLING_TIMEOUT", "12.5")
    monkeypatch.setattr(cli, "VllmClient", CapturingClient)
    monkeypatch.setattr(cli, "spelling_check", capturing_spelling_check)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "spelling-check",
            "--base-url",
            "http://cli.example/v1",
            "--model",
            "gemma-cli",
            "--api-key",
            "cli-secret",
            "--timeout",
            "8.5",
            "--prompt-logprobs",
            "7",
            "--risk-threshold",
            "8.0",
            "--suspicious-limit",
            "2",
            "--candidate-limit",
            "3",
            "--window-radius",
            "4",
            "--score-batch-size",
            "2",
            "--strong-delta",
            "1.2",
            "--weak-delta",
            "0.6",
            "--margin",
            "0.25",
            "--json",
            "測試句子",
        ],
    )

    assert cli.main() == 0

    output = json.loads(capsys.readouterr().out)
    config = cast("SpellingCheckConfig", captured["config"])

    assert output["input"] == "測試句子"
    assert captured["text"] == "測試句子"
    assert captured["client_kwargs"] == {
        "base_url": "http://cli.example/v1",
        "model": "gemma-cli",
        "api_key": "cli-secret",
        "timeout": 8.5,
    }
    assert config.prompt_logprobs == 7
    assert config.risk_threshold == 8.0
    assert config.suspicious_limit == 2
    assert config.candidate_limit == 3
    assert config.window_radius == 4
    assert config.score_batch_size == 2
    assert config.strong_delta == 1.2
    assert config.weak_delta == 0.6
    assert config.margin == 0.25
