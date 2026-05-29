from __future__ import annotations

from typing import Any

from spelling_check.candidates import generate_candidates
from spelling_check.models import CharRisk, TokenScore
from spelling_check.pipeline import SpellingCheckConfig, spelling_check


class FakeClient:
    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]:
        prompt_logprobs_payload = []
        prompt_token_ids = []
        for index, char in enumerate(text):
            token_id = index + 1
            prompt_token_ids.append(token_id)
            logprob = -8.0 if char == "非" else -1.0
            prompt_logprobs_payload.append(
                {
                    str(token_id): {
                        "decoded_token": char,
                        "logprob": logprob,
                        "rank": 1,
                    },
                    str(token_id + 1000): {
                        "decoded_token": "啡",
                        "logprob": -0.5,
                        "rank": 2,
                    },
                }
            )
        return {
            "choices": [
                {
                    "prompt_token_ids": prompt_token_ids,
                    "prompt_logprobs": prompt_logprobs_payload,
                }
            ]
        }


class StaticTopLogprobClient:
    def __init__(
        self,
        *,
        char_scores: dict[str, float],
        alternatives: dict[str, list[str]] | None = None,
    ) -> None:
        self.char_scores = char_scores
        self.alternatives = alternatives or {}

    def score_prompt(self, text: str, prompt_logprobs: int) -> dict[str, Any]:
        prompt_logprobs_payload = []
        prompt_token_ids = []
        for index, char in enumerate(text):
            token_id = index + 1
            prompt_token_ids.append(token_id)
            alternatives = {
                str(token_id): {
                    "decoded_token": char,
                    "logprob": self.char_scores.get(char, -1.0),
                    "rank": 1,
                }
            }
            for offset, alternative in enumerate(
                self.alternatives.get(char, []), start=1
            ):
                alternatives[str(token_id + offset * 1000)] = {
                    "decoded_token": alternative,
                    "logprob": -0.1,
                    "rank": offset + 1,
                }
            prompt_logprobs_payload.append(alternatives)
        return {
            "choices": [
                {
                    "prompt_token_ids": prompt_token_ids,
                    "prompt_logprobs": prompt_logprobs_payload,
                }
            ]
        }


def test_spelling_check_corrects_trusted_candidate() -> None:
    result = spelling_check(
        "我今天想喝一杯咖非。",
        client=FakeClient(),
        config=SpellingCheckConfig(risk_threshold=7.0, strong_delta=0.5),
    )

    assert result.status == "corrected"
    assert result.corrected_text == "我今天想喝一杯咖啡。"
    assert result.corrections[0].candidate_char == "啡"


def test_spelling_check_keeps_clean_sentence() -> None:
    result = spelling_check(
        "我今天想喝一杯咖啡。",
        client=FakeClient(),
        config=SpellingCheckConfig(risk_threshold=7.0),
    )

    assert result.status == "no_error"
    assert result.corrected_text == "我今天想喝一杯咖啡。"


def test_top_logprob_filters_non_cjk_candidates() -> None:
    risk = CharRisk(
        index=0,
        char="測",
        risk_score=8.0,
        token_logprob=-8.0,
        span_score=None,
        reason="test",
    )
    token = TokenScore(
        token_id=1,
        token_text="測",
        start=0,
        end=1,
        logprob=-8.0,
        top_logprobs=[
            {"token": "T", "logprob": -0.1},
            {"token": "#", "logprob": -0.2},
            {"token": "_", "logprob": -0.3},
            {"token": "가", "logprob": -0.4},
            {"token": "試", "logprob": -0.5},
        ],
    )

    candidates = generate_candidates("測", risk, [token], limit=10)

    assert [candidate.candidate_char for candidate in candidates] == ["試"]


def test_word_lexicon_candidate_bypasses_suspicious_threshold() -> None:
    result = spelling_check(
        "咖非",
        client=StaticTopLogprobClient(char_scores={"非": -8.0, "啡": -0.1}),
        config=SpellingCheckConfig(risk_threshold=99.0, strong_delta=0.5),
    )

    assert result.status == "corrected"
    assert result.corrected_text == "咖啡"
    assert result.corrections[0].source == "word_lexicon"


def test_untrusted_top_logprob_does_not_block_trusted_correction() -> None:
    result = spelling_check(
        "車戰",
        client=StaticTopLogprobClient(
            char_scores={"戰": -8.0, "上": -0.1, "站": -1.0},
            alternatives={"戰": ["上", "站"]},
        ),
        config=SpellingCheckConfig(risk_threshold=7.0, strong_delta=0.5, margin=0.4),
    )

    assert result.status == "corrected"
    assert result.corrected_text == "車站"
    assert result.corrections[0].source == "word_lexicon"


def test_suspicious_without_candidates_returns_no_error() -> None:
    result = spelling_check(
        "測",
        client=StaticTopLogprobClient(
            char_scores={"測": -8.0},
            alternatives={"測": ["T", "#", "_", "가"]},
        ),
        config=SpellingCheckConfig(risk_threshold=7.0),
    )

    assert result.status == "no_error"
    assert result.corrected_text == "測"
    assert result.suspicious_chars
