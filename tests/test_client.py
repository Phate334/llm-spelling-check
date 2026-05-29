from __future__ import annotations

import pytest

from spelling_check.client import _split_completion_response


def test_split_completion_response_orders_batch_choices_by_index() -> None:
    response = {
        "id": "cmpl-test",
        "choices": [
            {"index": 1, "text": "second"},
            {"index": 0, "text": "first"},
        ],
    }

    split = _split_completion_response(response, expected_count=2)

    assert [item["choices"][0]["text"] for item in split] == ["first", "second"]


def test_split_completion_response_rejects_choice_count_mismatch() -> None:
    response = {
        "id": "cmpl-test",
        "choices": [
            {"index": 0, "text": "first"},
        ],
    }

    with pytest.raises(RuntimeError, match="choice count mismatch"):
        _split_completion_response(response, expected_count=2)
