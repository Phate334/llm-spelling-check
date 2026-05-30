from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

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
