"""Telegram username parsing.

Admins may enter a username in any form — ``@name``, ``https://t.me/name``,
``t.me/name``, ``telegram.me/name`` or just ``name``. ``parse_username`` strips
all of that and returns the bare, normalised (lowercase) username, or ``None``
if the input doesn't contain a valid Telegram username.
"""

import re

# Telegram usernames: letters, digits, underscores; 5–32 chars (bots can be
# shorter historically, so we accept 4+ to be lenient).
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{4,32}$")


def parse_username(raw: str) -> str | None:
    """Extract a bare, lowercased Telegram username from arbitrary input."""
    if not raw:
        return None

    text = raw.strip()
    # Drop a query string / fragment if a link was pasted.
    text = text.split("?", 1)[0].split("#", 1)[0]
    text = text.rstrip("/")
    # For links like t.me/name or https://t.me/name — keep the last path segment.
    text = text.rsplit("/", 1)[-1]
    # Strip a leading @ (possibly repeated) and surrounding spaces.
    text = text.strip().lstrip("@").strip()

    return text.lower() if _USERNAME_RE.match(text) else None
