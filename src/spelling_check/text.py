from __future__ import annotations


def is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def is_single_cjk_char(value: str) -> bool:
    return len(value) == 1 and is_cjk(value)


def is_punctuation_or_space(char: str) -> bool:
    return char.isspace() or char in "，。！？、；：「」『』（）()[]【】,.!?;:'\""


def clean_token_text(token: str) -> str:
    return token.replace("▁", "").replace("Ġ", "").replace(" ", "")


def replace_char(text: str, index: int, char: str) -> str:
    return text[:index] + char + text[index + 1 :]


def local_window(text: str, index: int, radius: int) -> str:
    start = max(0, index - radius)
    end = min(len(text), index + radius + 1)
    return text[start:end]
