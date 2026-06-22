"""Tests for Settings parsing / admin checks."""

from bot.config.settings import Settings


def _make(monkeypatch, **overrides):
    env = {
        "BOT_TOKEN": "123:abc",
        "ADMIN_IDS": "111, 222 ,333",
        "CHANNEL_ID": "-1001234567890",
        "JOIN_URL": "https://t.me/x?start=join",
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
    }
    env.update(overrides)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    # _env_file=None so a developer's local .env never leaks into the test.
    return Settings(_env_file=None)


def test_admin_ids_parsed_and_trimmed(monkeypatch):
    s = _make(monkeypatch)
    assert s.get_admin_ids() == [111, 222, 333]


def test_is_admin(monkeypatch):
    s = _make(monkeypatch)
    assert s.is_admin(222) is True
    assert s.is_admin(999) is False


def test_channel_id_is_int(monkeypatch):
    s = _make(monkeypatch)
    assert s.channel_id == -1001234567890
    assert isinstance(s.channel_id, int)


def test_defaults(monkeypatch):
    s = _make(monkeypatch)
    assert s.broadcast_rps == 20
    assert s.announce_rps == 20
    assert s.sheets_sync_enabled is False
    assert s.redis_fsm_prefix == "fsm"


def test_sheets_enabled_from_env(monkeypatch):
    s = _make(monkeypatch, SHEETS_SYNC_ENABLED="true")
    assert s.sheets_sync_enabled is True
