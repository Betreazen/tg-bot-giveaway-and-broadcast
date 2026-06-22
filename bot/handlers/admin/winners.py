"""Мастер завершения розыгрыша и выбора победителей."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, user_repo, winner_repo
from bot.handlers.admin.states import WinnersStates
from bot.keyboards.admin import (
    get_end_giveaway_confirm_keyboard,
    get_results_target_keyboard,
    get_select_winners_keyboard,
)
from bot.messages.i18n import t
from bot.services.giveaway_service import NoParticipantsError, format_winner_list, select_winners
from bot.services.mailing import MessageContent, send_mass_message, send_to_channel
from bot.utils.datetimes import fmt_local

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "admin:complete_giveaway")
async def start_complete_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало завершения розыгрыша."""
    if not callback.message or not callback.from_user:
        return

    async with get_session() as session:
        giveaway = await giveaway_repo.get_active_giveaway(session)

        if not giveaway:
            await callback.answer("Нет активного розыгрыша", show_alert=True)
            return

        end_at_str = fmt_local(giveaway.end_at)

        text = (
            f"🏁 <b>Завершение розыгрыша</b>\n\n"
            f"📝 {giveaway.description}\n"
            f"⏰ Окончание: {end_at_str} МСК\n\n"
            f"Завершить розыгрыш сейчас?"
        )

    await callback.message.edit_text(text, reply_markup=get_end_giveaway_confirm_keyboard())
    await state.update_data(giveaway_id=giveaway.id)
    await state.set_state(WinnersStates.confirm_end)
    await callback.answer()


@router.callback_query(F.data == "giveaway:end_confirm", WinnersStates.confirm_end)
async def confirm_end_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение завершения розыгрыша."""
    if not callback.message:
        return

    data = await state.get_data()

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.end_giveaway(session, data['giveaway_id'])

        if not giveaway:
            await callback.message.edit_text("❌ Розыгрыш не найден")
            await state.clear()
            return

        await callback.message.edit_text(
            "✅ Розыгрыш завершен!\n\n🎲 Выбрать победителей?",
            reply_markup=get_select_winners_keyboard()
        )
        await state.set_state(WinnersStates.select_winners)

    except Exception as e:
        logger.error(f"Ошибка завершения розыгрыша: {e}", exc_info=True)
        await callback.message.edit_text(t("errors.database"))
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "giveaway:end_cancel", WinnersStates.confirm_end)
async def cancel_end_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена завершения."""
    if not callback.message:
        return
    await callback.message.edit_text("❌ Отменено")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "winners:select", WinnersStates.select_winners)
async def select_winners_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор победителей."""
    if not callback.message:
        return

    data = await state.get_data()

    await callback.message.edit_text("🎲 Выбираю победителей...")
    await callback.answer()

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.get_giveaway(session, data['giveaway_id'])

            if not giveaway:
                await callback.message.edit_text("❌ Розыгрыш не найден")
                await state.clear()
                return

            # Выбираем победителей
            try:
                winners = await select_winners(session, giveaway)
            except NoParticipantsError:
                await callback.message.edit_text(t("admin.no_participants"))
                await state.clear()
                return

            # Форматируем список победителей
            winners_text = format_winner_list(winners)

            result_text = (
                f"🎉 <b>Победители выбраны!</b>\n\n"
                f"📝 {giveaway.description}\n"
                f"🏆 Победителей: {len(winners)}\n\n"
                f"<b>Победители:</b>\n{winners_text}\n\n"
                f"📣 Куда опубликовать результаты?"
            )

            await callback.message.edit_text(result_text, reply_markup=get_results_target_keyboard())
            await state.set_state(WinnersStates.select_publish_target)

    except Exception as e:
        logger.error(f"Ошибка выбора победителей: {e}", exc_info=True)
        await callback.message.edit_text(t("errors.generic"))
        await state.clear()


@router.callback_query(F.data.startswith("results:"), WinnersStates.select_publish_target)
async def publish_results(callback: CallbackQuery, state: FSMContext) -> None:
    """Публикация результатов."""
    if not callback.message or not callback.from_user:
        return

    target = callback.data.split(":")[1]
    data = await state.get_data()
    settings = get_settings()

    await callback.message.edit_text("📤 Публикую результаты...")
    await callback.answer()

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.get_giveaway(session, data['giveaway_id'])
            winners = await winner_repo.get_winners(session, data['giveaway_id'])

            if not giveaway or not winners:
                await callback.message.edit_text("❌ Данные не найдены")
                await state.clear()
                return

            # Форматируем результаты
            winners_text = format_winner_list(winners)
            result_text = (
                f"🏆 <b>Результаты розыгрыша!</b>\n\n"
                f"📝 {giveaway.description}\n\n"
                f"<b>Победители:</b>\n{winners_text}\n\n"
                f"Поздравляем! 🎊"
            )

            # Список получателей собираем внутри сессии, рассылку делаем вне её.
            user_ids: list[int] = []
            if target in ("users", "everywhere"):
                user_ids = await user_repo.get_all_user_ids(session)

        content = MessageContent(text=result_text)
        sent_count = 0

        if target in ("channel", "everywhere"):
            if await send_to_channel(callback.message.bot, settings.channel_id, content):
                sent_count += 1

        if target == "admins":
            result = await send_mass_message(
                callback.message.bot, settings.get_admin_ids(), content, rps=settings.announce_rps
            )
            sent_count += result.sent_count
        elif user_ids:
            result = await send_mass_message(
                callback.message.bot, user_ids, content, rps=settings.broadcast_rps
            )
            sent_count += result.sent_count

        await callback.message.edit_text(
            f"✅ Результаты опубликованы!\n\n"
            f"📊 Отправлено: {sent_count}"
        )

    except Exception as e:
        logger.error(f"Ошибка публикации результатов: {e}", exc_info=True)
        await callback.message.edit_text("❌ Ошибка публикации")

    await state.clear()
