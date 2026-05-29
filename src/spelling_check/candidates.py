from __future__ import annotations

from spelling_check.models import Candidate, CharRisk, TokenScore
from spelling_check.text import clean_token_text

WORD_CONFUSIONS = {
    "咖非": "咖啡",
    "公圜": "公園",
    "檢察": "檢查",
    "抽提": "抽屜",
    "車戰": "車站",
    "信相": "信箱",
    "服誤": "服務",
    "天汽": "天氣",
    "整李": "整理",
    "細結": "細節",
    "因該": "應該",
    "在來": "再來",
    "以經": "已經",
    "創億": "創意",
}

CHAR_CONFUSIONS = {
    "非": ["啡"],
    "圜": ["園"],
    "察": ["查"],
    "提": ["屜"],
    "戰": ["站"],
    "相": ["箱"],
    "誤": ["務"],
    "汽": ["氣"],
    "李": ["理"],
    "結": ["節"],
    "在": ["再"],
    "以": ["已"],
    "己": ["已", "巳"],
    "已": ["以", "己"],
    "未": ["末"],
    "末": ["未"],
    "的": ["得", "地"],
    "得": ["的", "地"],
    "地": ["的", "得"],
}


def generate_candidates(text: str, risk: CharRisk, tokens: list[TokenScore], limit: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    candidates.extend(_word_candidates(text, risk.index))
    candidates.extend(_char_confusion_candidates(text, risk.index))
    candidates.extend(_top_logprob_candidates(text, risk.index, tokens))
    return _deduplicate(candidates)[:limit]


def _word_candidates(text: str, index: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    for wrong, fixed in WORD_CONFUSIONS.items():
        start = text.find(wrong)
        while start >= 0:
            end = start + len(wrong)
            if start <= index < end and wrong[index - start] != fixed[index - start]:
                candidates.append(
                    Candidate(
                        index=index,
                        original_char=wrong[index - start],
                        candidate_char=fixed[index - start],
                        source="word_lexicon",
                        original_span=wrong,
                        corrected_span=fixed,
                    )
                )
            start = text.find(wrong, start + 1)
    return candidates


def _char_confusion_candidates(text: str, index: int) -> list[Candidate]:
    original = text[index]
    return [
        Candidate(
            index=index,
            original_char=original,
            candidate_char=candidate,
            source="char_confusion",
            original_span=original,
            corrected_span=candidate,
        )
        for candidate in CHAR_CONFUSIONS.get(original, [])
    ]


def _top_logprob_candidates(text: str, index: int, tokens: list[TokenScore]) -> list[Candidate]:
    original = text[index]
    candidates: list[Candidate] = []
    for token in tokens:
        if not (token.start <= index < token.end):
            continue
        for alternative in token.top_logprobs:
            alt_text = clean_token_text(str(alternative["token"]))
            if len(alt_text) == 1 and alt_text != original:
                candidates.append(
                    Candidate(
                        index=index,
                        original_char=original,
                        candidate_char=alt_text,
                        source="vllm_top_logprob",
                        original_span=original,
                        corrected_span=alt_text,
                    )
                )
    return candidates


def _deduplicate(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[tuple[int, str]] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = (candidate.index, candidate.candidate_char)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped
