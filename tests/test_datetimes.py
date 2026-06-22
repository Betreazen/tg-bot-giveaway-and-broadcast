"""Tests for the fixed-Moscow datetime helpers."""

from datetime import UTC, datetime

from bot.utils.datetimes import TZ_LABEL, fmt_local, get_tz, now_utc, to_local


def test_label_is_msk():
    assert TZ_LABEL == "МСК"


def test_timezone_is_moscow():
    assert "Moscow" in str(get_tz())


def test_naive_is_treated_as_utc_and_shifted_plus3():
    # Naive datetime is assumed UTC; Moscow is GMT+3 year-round.
    local = to_local(datetime(2024, 1, 1, 9, 0, 0))
    assert local.hour == 12
    assert local.utcoffset().total_seconds() == 3 * 3600


def test_aware_utc_converted_to_moscow():
    local = to_local(datetime(2024, 7, 1, 0, 0, 0, tzinfo=UTC))
    assert local.hour == 3
    # No DST in Moscow: offset is +3 in summer too.
    assert local.utcoffset().total_seconds() == 3 * 3600


def test_fmt_local_format():
    assert fmt_local(datetime(2024, 1, 1, 9, 0, 0)) == "01.01.2024 12:00"


def test_fmt_local_custom_format():
    assert fmt_local(datetime(2024, 1, 1, 9, 0, 0), "%Y-%m-%d %H:%M") == "2024-01-01 12:00"


def test_now_utc_is_timezone_aware():
    assert now_utc().tzinfo is not None
