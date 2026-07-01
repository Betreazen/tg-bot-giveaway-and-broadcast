"""Tests for username parsing from arbitrary admin input."""

import pytest

from bot.utils.usernames import parse_username


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("john_doe", "john_doe"),
        ("@john_doe", "john_doe"),
        ("  @John_Doe  ", "john_doe"),          # trimmed + lowercased
        ("https://t.me/john_doe", "john_doe"),
        ("http://t.me/john_doe", "john_doe"),
        ("t.me/john_doe", "john_doe"),
        ("telegram.me/john_doe", "john_doe"),
        ("https://t.me/john_doe?start=x", "john_doe"),
        ("t.me/john_doe/", "john_doe"),
        ("@@john_doe", "john_doe"),             # repeated @
        ("JohnDoe123", "johndoe123"),
    ],
)
def test_valid_usernames(raw, expected):
    assert parse_username(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "@",
        "ab",                    # too short
        "has spaces",
        "bad-char!",
        "with.dot",              # dots not allowed in usernames
        "https://example.com/",  # no username segment
    ],
)
def test_invalid_usernames(raw):
    assert parse_username(raw) is None
