from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SgmlMistake:
    location: int
    index: int
    span_index: int
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
        passages = essay.findall("./TEXT/PASSAGE")
        if not passages:
            raise ValueError("Each ESSAY must contain TEXT/PASSAGE")

        passage_texts: dict[str, str] = {}
        for passage in passages:
            passage_id = passage.attrib.get("id")
            if not passage_id:
                raise ValueError("PASSAGE must have an id attribute")
            if passage_id in passage_texts:
                raise ValueError(f"Duplicate PASSAGE id: {passage_id}")
            passage_texts[passage_id] = passage.text or ""

        mistakes_by_passage: dict[str, list[SgmlMistake]] = {
            passage_id: [] for passage_id in passage_texts
        }
        for mistake in essay.findall("MISTAKE"):
            mistake_id = mistake.attrib.get("id")
            if mistake_id is None or mistake_id not in passage_texts:
                raise ValueError(
                    "MISTAKE id must reference a PASSAGE id in the same ESSAY: "
                    f"got {mistake_id}"
                )
            mistakes_by_passage[mistake_id].append(
                _parse_mistake(mistake, mistake_id, passage_texts[mistake_id])
            )

        for passage_id, input_text in passage_texts.items():
            mistakes = mistakes_by_passage[passage_id]
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
    span_index = _find_wrong_span(input_text, wrong, index, passage_id, location)

    return SgmlMistake(
        location=location,
        index=index,
        span_index=span_index,
        wrong=wrong,
        correction=correction,
    )


def _find_wrong_span(
    input_text: str, wrong: str, index: int, passage_id: str, location: int
) -> int:
    if index >= len(input_text):
        raise ValueError(
            f"SGML MISTAKE location is outside PASSAGE for {passage_id}: {location}"
        )

    start = input_text.find(wrong)
    while start != -1:
        if start <= index < start + len(wrong):
            return start
        start = input_text.find(wrong, start + 1)

    if wrong in input_text:
        raise ValueError(
            "SGML MISTAKE location does not fall within WRONG text for "
            f"{passage_id} at location {location}: {wrong!r}"
        )
    raise ValueError(
        "SGML WRONG text does not appear in PASSAGE for "
        f"{passage_id} at location {location}: {wrong!r}"
    )


def _required_child_text(element: ET.Element, name: str, passage_id: str) -> str:
    child = element.find(name)
    if child is None or child.text is None:
        raise ValueError(f"MISTAKE for {passage_id} must contain {name}")
    return child.text


def _apply_mistakes(input_text: str, mistakes: list[SgmlMistake]) -> str:
    replacements: dict[int, str] = {}
    seen_spans: set[tuple[int, str, str]] = set()
    for mistake in mistakes:
        span_key = (mistake.span_index, mistake.wrong, mistake.correction)
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)
        for offset, replacement_char in enumerate(mistake.correction):
            target_index = mistake.span_index + offset
            existing = replacements.get(target_index)
            if existing is not None and existing != replacement_char:
                raise ValueError(
                    f"Conflicting SGML replacements at location {target_index + 1}"
                )
            replacements[target_index] = replacement_char

    chars = list(input_text)
    for target_index, replacement_char in replacements.items():
        chars[target_index] = replacement_char
    return "".join(chars)
