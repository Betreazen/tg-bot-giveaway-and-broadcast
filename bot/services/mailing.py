"""Сервис массовых рассылок с rate limiting."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import FSInputFile, InlineKeyboardMarkup

from bot.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MessageContent:
    """Контент для массовой рассылки."""

    text: str | None = None
    media_file_id: str | None = None
    media_type: str | None = None  # "photo", "video", "animation", "document"
    reply_markup: InlineKeyboardMarkup | None = None


@dataclass
class MailingResult:
    """Результат массовой рассылки."""

    total_recipients: int
    sent_count: int
    failed_count: int
    skipped_count: int
    duration_seconds: float
    error_summary: dict[str, int]


async def send_mass_message(
    bot: Bot, recipients: list[int], content: MessageContent, rps: int = 20
) -> MailingResult:
    """
    Отправить сообщение массово с rate limiting.

    Args:
        bot: Bot instance
        recipients: Список user_id получателей
        content: Контент сообщения
        rps: Сообщений в секунду (rate limit)

    Returns:
        MailingResult с статистикой отправки
    """
    start_time = datetime.now()
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    error_summary: dict[str, int] = {}

    delay = 1.0 / rps  # Задержка между сообщениями

    logger.info(f"Начало массовой рассылки для {len(recipients)} получателей (RPS: {rps})")

    for idx, user_id in enumerate(recipients, 1):
        try:
            # Отправка в зависимости от типа контента
            if content.media_file_id and content.media_type:
                await _send_media_message(bot, user_id, content)
            elif content.text:
                await bot.send_message(user_id, content.text, reply_markup=content.reply_markup)
            else:
                logger.warning(f"Пустой контент для пользователя {user_id}, пропуск")
                skipped_count += 1
                continue

            sent_count += 1

            # Rate limiting
            if idx < len(recipients):
                await asyncio.sleep(delay)

        except TelegramRetryAfter as e:
            # Telegram попросил подождать
            logger.warning(f"RetryAfter для {user_id}: ждем {e.retry_after}с")
            await asyncio.sleep(e.retry_after)
            # Повторная попытка
            try:
                if content.media_file_id and content.media_type:
                    await _send_media_message(bot, user_id, content)
                elif content.text:
                    await bot.send_message(user_id, content.text, reply_markup=content.reply_markup)
                sent_count += 1
            except Exception as retry_error:
                logger.error(f"Ошибка повторной отправки для {user_id}: {retry_error}")
                failed_count += 1
                _update_error_summary(error_summary, "retry_failed")

        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            logger.debug(f"Пользователь {user_id} заблокировал бота")
            failed_count += 1
            _update_error_summary(error_summary, "blocked")

        except TelegramAPIError as e:
            # Другие ошибки Telegram API
            logger.warning(f"Telegram API ошибка для {user_id}: {e}")
            failed_count += 1
            _update_error_summary(error_summary, f"api_error_{e.error_code}" if hasattr(e, "error_code") else "api_error")

        except Exception as e:
            # Неожиданные ошибки
            logger.error(f"Неожиданная ошибка для {user_id}: {e}", exc_info=True)
            failed_count += 1
            _update_error_summary(error_summary, "unexpected")

        # Логирование прогресса каждые 100 сообщений
        if idx % 100 == 0:
            logger.info(f"Прогресс рассылки: {idx}/{len(recipients)} ({sent_count} отправлено, {failed_count} неудач)")

    duration = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"Рассылка завершена: {sent_count} отправлено, {failed_count} неудач, "
        f"{skipped_count} пропущено за {duration:.1f}с"
    )

    return MailingResult(
        total_recipients=len(recipients),
        sent_count=sent_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        duration_seconds=duration,
        error_summary=error_summary,
    )


async def _send_media_message(bot: Bot, user_id: int, content: MessageContent) -> None:
    """Отправить медиа-сообщение."""
    if not content.media_file_id or not content.media_type:
        raise ValueError("media_file_id и media_type обязательны")

    caption = content.text or None

    if content.media_type == "photo":
        await bot.send_photo(user_id, content.media_file_id, caption=caption, reply_markup=content.reply_markup)
    elif content.media_type == "video":
        await bot.send_video(user_id, content.media_file_id, caption=caption, reply_markup=content.reply_markup)
    elif content.media_type == "animation":
        await bot.send_animation(user_id, content.media_file_id, caption=caption, reply_markup=content.reply_markup)
    elif content.media_type == "document":
        await bot.send_document(user_id, content.media_file_id, caption=caption, reply_markup=content.reply_markup)
    else:
        raise ValueError(f"Неподдерживаемый тип медиа: {content.media_type}")


def _update_error_summary(summary: dict[str, int], error_type: str) -> None:
    """Обновить счетчик ошибок."""
    summary[error_type] = summary.get(error_type, 0) + 1


async def send_to_channel(bot: Bot, channel_id: int, content: MessageContent) -> bool:
    """
    Отправить сообщение в канал.

    Args:
        bot: Bot instance
        channel_id: ID канала
        content: Контент сообщения

    Returns:
        True если успешно, False иначе
    """
    try:
        if content.media_file_id and content.media_type:
            await _send_media_message(bot, channel_id, content)
        elif content.text:
            await bot.send_message(channel_id, content.text, reply_markup=content.reply_markup)
        else:
            logger.error("Пустой контент для отправки в канал")
            return False

        logger.info(f"Сообщение успешно отправлено в канал {channel_id}")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки в канал {channel_id}: {e}", exc_info=True)
        return False
