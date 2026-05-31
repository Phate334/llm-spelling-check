from __future__ import annotations

from pathlib import Path

import pytest

from spelling_check.dataset import load_sgml_dataset, load_texts

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_texts_reads_json_array(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text('["甲", "乙"]', encoding="utf-8")

    assert load_texts(path) == ["甲", "乙"]


def test_load_texts_reads_nonempty_lines(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("甲\n\n乙\n", encoding="utf-8")

    assert load_texts(path) == ["甲", "乙"]


def test_load_sgml_dataset_reads_sample_fixture() -> None:
    dataset = load_sgml_dataset(FIXTURE_DIR / "sample_sentences.sgml")

    assert len(dataset.cases) == 4
    assert dataset.gold_error_count == 4
    first = dataset.cases[0]
    assert first.case_id == "sample-1"
    assert first.mistakes[0].location == 11
    assert first.mistakes[0].index == 10
    assert first.mistakes[0].span_index == 10
    assert first.mistakes[0].wrong == "非"
    assert first.input_text[10] == "非"
    assert first.gold_text == "我今天早上喝了一杯咖啡，然後去公園散步。"


def test_load_sgml_dataset_reads_multiple_passages_in_one_essay(
    tmp_path: Path,
) -> None:
    path = tmp_path / "multi.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT>
<PASSAGE id="p1">甲錯</PASSAGE>
<PASSAGE id="p2">乙誤</PASSAGE>
</TEXT>
<MISTAKE id="p1" location="2"><WRONG>錯</WRONG><CORRECTION>正</CORRECTION></MISTAKE>
<MISTAKE id="p2" location="2"><WRONG>誤</WRONG><CORRECTION>對</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )

    dataset = load_sgml_dataset(path)

    assert [case.case_id for case in dataset.cases] == ["p1", "p2"]
    assert [case.gold_text for case in dataset.cases] == ["甲正", "乙對"]


def test_load_sgml_dataset_accepts_location_inside_wrong_span(
    tmp_path: Path,
) -> None:
    path = tmp_path / "inside.sgml"
    path.write_text(
        """
<ESSAY>
<TEXT><PASSAGE id="p1">宅男打藍求</PASSAGE></TEXT>
<MISTAKE id="p1" location="4"><WRONG>藍求</WRONG><CORRECTION>籃球</CORRECTION></MISTAKE>
<MISTAKE id="p1" location="5"><WRONG>藍求</WRONG><CORRECTION>籃球</CORRECTION></MISTAKE>
</ESSAY>
""",
        encoding="utf-8",
    )

    dataset = load_sgml_dataset(path)

    case = dataset.cases[0]
    assert case.mistakes[0].index == 3
    assert case.mistakes[0].span_index == 3
    assert case.mistakes[1].index == 4
    assert case.mistakes[1].span_index == 3
    assert case.gold_text == "宅男打籃球"


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

    with pytest.raises(ValueError, match="MISTAKE id must reference a PASSAGE id"):
        load_sgml_dataset(path)


def test_load_sgml_dataset_rejects_location_outside_wrong_span(
    tmp_path: Path,
) -> None:
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

    with pytest.raises(ValueError, match="location does not fall within WRONG"):
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
