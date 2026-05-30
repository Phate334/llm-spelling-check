from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SgmlMistake:
    location: int
    index: int
    wrong: str
    correction: str


@dataclass(frozen=True)
class SgmlCase:
    case_id: str
    input_text: str
    gold_text: str
    mistakes: list[SgmlMistake]


@dataclass(frozen=True)
class SgmlDataset:
    path: Path
    cases: list[SgmlCase]

    @property
    def gold_error_count(self) -> int:
        return sum(len(case.mistakes) for case in self.cases)


def load_texts(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("JSON input file must contain an array")
        return [str(item) for item in data]
    return [line.strip() for line in raw.splitlines() if line.strip()]


def load_sgml_dataset(path: Path) -> SgmlDataset:
    raw = path.read_text(encoding="utf-8")
    return parse_sgml_dataset(raw, path=path)


def parse_sgml_dataset(raw: str, path: Path | None = None) -> SgmlDataset:
    try:
        root = ET.fromstring(f"<ROOT>{raw}</ROOT>")
    except ET.ParseError as exc:
        raise ValueError(f"Invalid SGML/XML input: {exc}") from exc

    cases: list[SgmlCase] = []
    for essay in root.findall("ESSAY"):
        passage = essay.find("./TEXT/PASSAGE")
        if passage is None:
            raise ValueError("Each ESSAY must contain TEXT/PASSAGE")

        passage_id = passage.attrib.get("id")
        if not passage_id:
            raise ValueError("PASSAGE must have an id attribute")

        input_text = passage.text or ""
        mistakes = [
            _parse_mistake(mistake, passage_id, input_text)
            for mistake in essay.findall("MISTAKE")
        ]
        gold_text = _apply_mistakes(input_text, mistakes)
        cases.append(
            SgmlCase(
                case_id=passage_id,
                input_text=input_text,
                gold_text=gold_text,
                mistakes=mistakes,
            )
        )

    return SgmlDataset(path=path or Path("<memory>"), cases=cases)


def _parse_mistake(
    element: ET.Element, passage_id: str, input_text: str
) -> SgmlMistake:
    mistake_id = element.attrib.get("id")
    if mistake_id != passage_id:
        raise ValueError(
            f"MISTAKE id must match PASSAGE id: expected {passage_id}, got {mistake_id}"
        )

    location_text = element.attrib.get("location")
    if location_text is None:
        raise ValueError(f"MISTAKE for {passage_id} must have a location attribute")
    try:
        location = int(location_text)
    except ValueError as exc:
        raise ValueError(
            f"MISTAKE location must be a 1-based integer: {location_text}"
        ) from exc
    if location < 1:
        raise ValueError(f"MISTAKE location must be 1-based: {location}")

    wrong = _required_child_text(element, "WRONG", passage_id)
    correction = _required_child_text(element, "CORRECTION", passage_id)
    if len(wrong) != len(correction):
        raise ValueError(
            "Only equal-length SGML replacements are supported: "
            f"{passage_id} location {location}"
        )

    index = location - 1
    if input_text[index : index + len(wrong)] != wrong:
        actual = input_text[index : index + len(wrong)]
        raise ValueError(
            "SGML WRONG text does not match PASSAGE at location "
            f"{location} for {passage_id}: expected {wrong!r}, got {actual!r}"
        )

    return SgmlMistake(
        location=location,
        index=index,
        wrong=wrong,
        correction=correction,
    )


def _required_child_text(element: ET.Element, name: str, passage_id: str) -> str:
    child = element.find(name)
    if child is None or child.text is None:
        raise ValueError(f"MISTAKE for {passage_id} must contain {name}")
    return child.text


def _apply_mistakes(input_text: str, mistakes: list[SgmlMistake]) -> str:
    chars = list(input_text)
    for mistake in mistakes:
        chars[mistake.index : mistake.index + len(mistake.wrong)] = list(
            mistake.correction
        )
    return "".join(chars)
