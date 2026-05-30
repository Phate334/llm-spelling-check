from __future__ import annotations

from pathlib import Path

import pytest

from spelling_check.dataset import load_sgml_dataset, load_texts


def test_load_texts_reads_json_array(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text('["甲", "乙"]', encoding="utf-8")

    assert load_texts(path) == ["甲", "乙"]


def test_load_texts_reads_nonempty_lines(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("甲\n\n乙\n", encoding="utf-8")

    assert load_texts(path) == ["甲", "乙"]


def test_load_sgml_dataset_reads_training_fixture() -> None:
    dataset = load_sgml_dataset(Path("data/fiona_wrong_results_Training.sgml"))

    assert len(dataset.cases) == 17
    assert dataset.gold_error_count == 24
    first = dataset.cases[0]
    assert first.case_id == "fiona_wrong_results-1"
    assert first.mistakes[0].location == 11
    assert first.mistakes[0].index == 10
    assert first.mistakes[0].wrong == "雞"
    assert first.input_text[10] == "雞"
    assert "質的績效管理" in first.gold_text


def test_load_sgml_dataset_rejects_unknown_passage_id(tmp_path: Path) -> None:
    path = tmp_path / "bad.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT><PASSAGE id="p1">甲乙</PASSAGE></TEXT>
<MISTAKE id="p2" location="1"><WRONG>甲</WRONG><CORRECTION>丙</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="MISTAKE id must match PASSAGE id"):
        load_sgml_dataset(path)


def test_load_sgml_dataset_rejects_wrong_text_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "bad.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT><PASSAGE id="p1">甲乙</PASSAGE></TEXT>
<MISTAKE id="p1" location="1"><WRONG>乙</WRONG><CORRECTION>丙</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="WRONG text does not match"):
        load_sgml_dataset(path)


def test_load_sgml_dataset_rejects_non_equal_length_replacement(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT><PASSAGE id="p1">甲乙</PASSAGE></TEXT>
<MISTAKE id="p1" location="1"><WRONG>甲</WRONG><CORRECTION>丙丁</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="equal-length"):
        load_sgml_dataset(path)
