"""Tests for the admin-only access middleware."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from bot.config.settings import init_settings
from bot.middlewares.admin import AdminOnlyMiddleware


@pytest.fixture(autouse=True)
def _settings():
    # conftest sets ADMIN_IDS=111,222 in the environment.
    init_settings()


def _user(uid: int):
    u = MagicMock()
    u.id = uid
    return u


@pytest.mark.asyncio
async def test_admin_passes_through():
    mw = AdminOnlyMiddleware()
    handler = AsyncMock(return_value="handled")
    event = MagicMock(spec=CallbackQuery)

    result = await mw(handler, event, {"event_from_user": _user(111)})

    handler.assert_awaited_once()
    assert result == "handled"


@pytest.mark.asyncio
async def test_non_admin_callback_blocked():
    mw = AdminOnlyMiddleware()
    handler = AsyncMock()
    event = MagicMock(spec=CallbackQuery)
    event.answer = AsyncMock()

    result = await mw(handler, event, {"event_from_user": _user(999)})

    handler.assert_not_called()
    event.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_non_admin_message_blocked():
    mw = AdminOnlyMiddleware()
    handler = AsyncMock()
    event = MagicMock(spec=Message)
    event.answer = AsyncMock()

    result = await mw(handler, event, {"event_from_user": _user(999)})

    handler.assert_not_called()
    event.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_no_user_passes_through():
    # Updates without a user (rare) should not be blocked by the user check.
    mw = AdminOnlyMiddleware()
    handler = AsyncMock(return_value="ok")
    event = MagicMock(spec=CallbackQuery)

    result = await mw(handler, event, {})
    handler.assert_awaited_once()
    assert result == "ok"
