"""Tests for the Google Sheets cell datetime formatter."""

from datetime import UTC, datetime

from bot.services.sheets_sync import _fmt_dt


def test_naive_datetime_formatted_in_moscow():
    assert _fmt_dt(datetime(2024, 1, 1, 9, 0, 0)) == "2024-01-01 12:00"


def test_aware_datetime_formatted_in_moscow():
    assert _fmt_dt(datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC)) == "2024-01-01 12:00"


def test_none_becomes_empty_string():
    assert _fmt_dt(None) == ""


def test_non_datetime_passthrough():
    assert _fmt_dt("already-a-string") == "already-a-string"
