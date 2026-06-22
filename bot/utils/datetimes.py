"""Timezone-aware datetime helpers.

The bot stores all timestamps in UTC and always displays them in Moscow time
(MSK, GMT+3, no DST), regardless of the server's local timezone. This is a hard
product requirement — the display timezone is fixed, not configurable.
"""

from datetime import UTC, datetime

import pytz

# Fixed display timezone for the whole bot. Europe/Moscow is GMT+3 year-round.
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Label shown next to formatted times.
TZ_LABEL = "МСК"


def get_tz() -> pytz.BaseTzInfo:
    """Return the bot's fixed display timezone (Moscow, GMT+3)."""
    return MOSCOW_TZ


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def to_local(dt: datetime) -> datetime:
    """Convert a datetime to Moscow time.

    Naive datetimes are assumed to be in UTC (that is how rows are stored).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(MOSCOW_TZ)


def fmt_local(dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
    """Format a datetime in Moscow time."""
    return to_local(dt).strftime(fmt)
