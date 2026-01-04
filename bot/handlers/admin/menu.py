"""Admin panel main menu handler."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, participant_repo
from bot.messages.i18n import t

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "admin:status")
async def show_status(callback: CallbackQuery) -> None:
    """Show current giveaway status."""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    settings = get_settings()

    if not settings.is_admin(user_id):
        await callback.answer(t("admin.access_denied"), show_alert=True)
        return

    async with get_session() as session:
        giveaway = await giveaway_repo.get_active_giveaway(session)

        if not giveaway:
            await callback.answer(t("admin.status_no_active"), show_alert=True)
            return

        # Get participant count
        participant_count = await participant_repo.get_participant_count(session, giveaway.id)

        # Format end time to Moscow timezone
        import pytz

        moscow_tz = pytz.timezone("Europe/Moscow")
        end_at_moscow = giveaway.end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
        end_at_str = end_at_moscow.strftime("%Y-%m-%d %H:%M")

        status_text = t(
            "admin.status_active",
            description=giveaway.description,
            participants=participant_count,
            end_at=end_at_str,
            num_winners=giveaway.num_winners,
        )

    await callback.answer()
    await callback.message.answer(status_text)
    logger.info(f"Admin {user_id} viewed status")



@router.callback_query(F.data == "admin:sync_sheets")
async def sync_google_sheets(callback: CallbackQuery) -> None:
    """Синхронизация с Google Sheets."""
    if not callback.from_user:
        return

    user_id = callback.from_user.id
    settings = get_settings()

    if not settings.is_admin(user_id):
        await callback.answer(t("admin.access_denied"), show_alert=True)
        return

    await callback.answer("Синхронизация начата...")
    
    try:
        from bot.services.sheets_sync import sync_all_data
        
        result = await sync_all_data()
        
        if result:
            await callback.message.answer("✅ Синхронизация с Google Sheets успешно завершена!")
        else:
            await callback.message.answer("⚠️ Синхронизация не выполнена (возможно, отключена или нет credentials)")
            
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при синхронизации с Google Sheets")
    
    logger.info(f"Admin {user_id} triggered Google Sheets sync")
