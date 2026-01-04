"""Мастер завершения розыгрыша и выбора победителей."""

import logging

import pytz
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo
from bot.handlers.admin.states import WinnersStates
from bot.keyboards.admin import get_end_giveaway_confirm_keyboard, get_results_target_keyboard, get_select_winners_keyboard
from bot.messages.i18n import t
from bot.services.giveaway_service import NoParticipantsError, format_winner_list, select_winners
from bot.services.mailing import MessageContent, send_mass_message, send_to_channel
from bot.db.repo import user_repo

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
            
        moscow_tz = pytz.timezone("Europe/Moscow")
        end_at_moscow = giveaway.end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
        end_at_str = end_at_moscow.strftime("%d.%m.%Y %H:%M")
        
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
            from bot.db.repo import winner_repo
            
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
            
            content = MessageContent(text=result_text)
            sent_count = 0
            
            if target == "channel":
                success = await send_to_channel(callback.message.bot, settings.channel_id, content)
                sent_count = 1 if success else 0
                
            elif target == "admins":
                admin_ids = settings.get_admin_ids()
                result = await send_mass_message(callback.message.bot, admin_ids, content, rps=10)
                sent_count = result.sent_count
                
            elif target == "users":
                user_ids = await user_repo.get_all_user_ids(session)
                result = await send_mass_message(callback.message.bot, user_ids, content, rps=20)
                sent_count = result.sent_count
                
            elif target == "everywhere":
                # В канал
                await send_to_channel(callback.message.bot, settings.channel_id, content)
                # Всем пользователям
                user_ids = await user_repo.get_all_user_ids(session)
                result = await send_mass_message(callback.message.bot, user_ids, content, rps=20)
                sent_count = result.sent_count + 1
                
        await callback.message.edit_text(
            f"✅ Результаты опубликованы!\n\n"
            f"📊 Отправлено: {sent_count}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка публикации результатов: {e}", exc_info=True)
        await callback.message.edit_text("❌ Ошибка публикации")
        
    await state.clear()
