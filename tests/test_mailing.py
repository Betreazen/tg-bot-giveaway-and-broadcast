"""Tests for the mass-mailing service with a mocked Bot."""

from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

import bot.services.mailing as mailing
from bot.services.mailing import (
    MessageContent,
    _send_media_message,
    send_mass_message,
    send_to_channel,
)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Never actually sleep during rate limiting / retries.
    monkeypatch.setattr(mailing.asyncio, "sleep", AsyncMock())


@pytest.mark.asyncio
async def test_all_messages_sent():
    bot = AsyncMock()
    result = await send_mass_message(bot, [1, 2, 3], MessageContent(text="hi"), rps=100)
    assert result.total_recipients == 3
    assert result.sent_count == 3
    assert result.failed_count == 0
    assert bot.send_message.await_count == 3


@pytest.mark.asyncio
async def test_blocked_users_counted_as_failed():
    bot = AsyncMock()
    bot.send_message.side_effect = TelegramForbiddenError.__new__(TelegramForbiddenError)
    result = await send_mass_message(bot, [1, 2], MessageContent(text="hi"), rps=100)
    assert result.sent_count == 0
    assert result.failed_count == 2
    assert result.error_summary.get("blocked") == 2


@pytest.mark.asyncio
async def test_retry_after_then_success():
    bot = AsyncMock()
    retry = TelegramRetryAfter.__new__(TelegramRetryAfter)
    retry.retry_after = 1
    # First send raises RetryAfter, the in-handler retry then succeeds.
    bot.send_message.side_effect = [retry, None]
    result = await send_mass_message(bot, [1], MessageContent(text="hi"), rps=100)
    assert result.sent_count == 1
    assert result.failed_count == 0
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_empty_content_skipped():
    bot = AsyncMock()
    result = await send_mass_message(bot, [1, 2], MessageContent(), rps=100)
    assert result.skipped_count == 2
    assert result.sent_count == 0


@pytest.mark.asyncio
async def test_send_media_dispatches_by_type():
    bot = AsyncMock()
    await _send_media_message(bot, 1, MessageContent(media_file_id="f", media_type="photo", text="c"))
    bot.send_photo.assert_awaited_once()

    await _send_media_message(bot, 1, MessageContent(media_file_id="f", media_type="video"))
    bot.send_video.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_media_invalid_type_raises():
    with pytest.raises(ValueError):
        await _send_media_message(AsyncMock(), 1, MessageContent(media_file_id="f", media_type="bogus"))


@pytest.mark.asyncio
async def test_send_to_channel_text_success():
    bot = AsyncMock()
    ok = await send_to_channel(bot, -100123, MessageContent(text="hello"))
    assert ok is True
    bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_to_channel_empty_content_fails():
    bot = AsyncMock()
    ok = await send_to_channel(bot, -100123, MessageContent())
    assert ok is False
