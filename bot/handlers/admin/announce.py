"""Обработчик анонсирования активного розыгрыша."""

import logging

import pytz
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, user_repo
from bot.keyboards.admin import get_manual_announce_keyboard
from bot.messages.i18n import t
from bot.services.mailing import MessageContent, send_mass_message, send_to_channel

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "admin:announce_giveaway")
async def announce_giveaway(callback: CallbackQuery) -> None:
    """Анонсирование активного розыгрыша."""
    if not callback.message or not callback.from_user:
        return

    settings = get_settings()

    if not settings.is_admin(callback.from_user.id):
        await callback.answer(t("admin.access_denied"), show_alert=True)
        return

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.get_active_giveaway(session)

            if not giveaway:
                await callback.answer("Нет активного розыгрыша для анонсирования", show_alert=True)
                return

            # Показываем выбор куда отправить
            moscow_tz = pytz.timezone("Europe/Moscow")
            end_at_moscow = giveaway.end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
            end_at_str = end_at_moscow.strftime("%d.%m.%Y %H:%M")

            text = (
                f"📣 <b>Анонсирование розыгрыша</b>\n\n"
                f"📝 {giveaway.description}\n"
                f"🏆 Победителей: {giveaway.num_winners}\n"
                f"⏰ До: {end_at_str} МСК\n\n"
                f"Куда отправить анонс?"
            )

            await callback.message.edit_text(text, reply_markup=get_manual_announce_keyboard())

            # Сохраняем ID розыгрыша для последующей отправки
            # Используем callback_data с префиксом для отличия от создания
            logger.info(f"Admin {callback.from_user.id} initiated manual announcement for giveaway {giveaway.id}")

    except Exception as e:
        logger.error(f"Ошибка при подготовке анонса: {e}", exc_info=True)
        await callback.answer("Ошибка при подготовке анонса", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("announce_manual:"))
async def handle_manual_announce(callback: CallbackQuery) -> None:
    """Обработка отправки ручного анонса."""
    if not callback.message or not callback.from_user:
        return

    target = callback.data.split(":")[1]
    settings = get_settings()

    await callback.message.edit_text("📤 Отправляю анонс...")
    await callback.answer()

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.get_active_giveaway(session)

            if not giveaway:
                await callback.message.edit_text("❌ Активный розыгрыш не найден")
                return

            # Форматируем дату окончания
            moscow_tz = pytz.timezone("Europe/Moscow")
            end_at_moscow = giveaway.end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
            end_at_str = end_at_moscow.strftime("%d.%m.%Y %H:%M")

            # Создаем кнопку участия
            join_button = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🎁 Участвовать",
                            url=settings.app_config.join_url if settings.app_config else "https://t.me/your_bot",
                        )
                    ]
                ]
            )

            announce_text = (
                f"🎉 <b>Новый розыгрыш!</b>\n\n"
                f"{giveaway.description}\n\n"
                f"🏆 Победителей: {giveaway.num_winners}\n"
                f"⏰ До: {end_at_str} МСК\n\n"
                f"👉 Нажми кнопку ниже для участия!"
            )

            content = MessageContent(
                text=announce_text,
                media_file_id=giveaway.announce_media_file_id,
                media_type=giveaway.announce_media_type,
                reply_markup=join_button,
            )

            sent_count = 0

            if target in ["channel", "everywhere"]:
                # Отправка в канал
                success = await send_to_channel(callback.message.bot, settings.channel_id, content)
                if success:
                    sent_count += 1

            if target in ["users", "everywhere"]:
                # Отправка всем пользователям
                user_ids = await user_repo.get_all_user_ids(session)
                result = await send_mass_message(callback.message.bot, user_ids, content, rps=20)
                sent_count += result.sent_count

        await callback.message.edit_text(f"✅ Анонс отправлен!\n\n" f"📊 Отправлено: {sent_count}")

    except Exception as e:
        logger.error(f"Ошибка отправки анонса: {e}", exc_info=True)
        await callback.message.edit_text("❌ Ошибка отправки анонса")
