from __future__ import annotations

import json
import re
from typing import Protocol

from spelling_check.models import Candidate, CharRisk
from spelling_check.text import is_single_cjk_char, local_window_with_offset

FIM_SOURCE = "fim_structured_output"


class StructuredCandidateClient(Protocol):
    def complete_json_array(self, prompt: str, max_tokens: int) -> str: ...


def generate_fim_candidates(
    text: str,
    risk: CharRisk,
    client: StructuredCandidateClient,
    *,
    window_radius: int,
    limit: int,
    max_tokens: int,
) -> list[Candidate]:
    window, offset = local_window_with_offset(text, risk.index, window_radius)
    prompt = build_fim_prompt(window, offset, risk.char)
    raw = client.complete_json_array(prompt, max_tokens=max_tokens)
    return [
        Candidate(
            index=risk.index,
            original_char=risk.char,
            candidate_char=char,
            source=FIM_SOURCE,
        )
        for char in parse_candidate_chars(raw, original_char=risk.char, limit=limit)
    ]


def build_fim_prompt(window: str, target_offset: int, original_char: str) -> str:
    blanked = f"{window[:target_offset]}＿{window[target_offset + 1 :]}"
    marked = f"{window[:target_offset]}[{original_char}]{window[target_offset + 1 :]}"
    return f"""你是繁體中文錯字修正工具。方括號中的目標字可能是錯字，請只替換這一個位置，不要改其他字。

原文片段：{marked}
填空片段：{blanked}
目標字：{original_char}

請根據左右文列出所有合理、可填入「＿」位置的繁體中文單字候選。
每個候選只能是一個中文字。不要輸出原本的目標字。不要輸出詞語或解釋。
輸出必須是 JSON 字串陣列。"""


def parse_candidate_chars(raw: str, *, original_char: str, limit: int) -> list[str]:
    data = _extract_json_array(raw)
    if not isinstance(data, list):
        return []

    seen: set[str] = set()
    chars: list[str] = []
    for item in data:
        value = str(item).strip()
        if is_single_cjk_char(value):
            candidates = [value]
        else:
            candidates = [char for char in value if is_single_cjk_char(char)]
        for char in candidates:
            if char == original_char or char in seen:
                continue
            seen.add(char)
            chars.append(char)
            break
        if len(chars) >= limit:
            break
    return chars


def _extract_json_array(raw: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
