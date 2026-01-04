"""Admin panel entry point handler."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo
from bot.keyboards.admin import get_admin_main_menu
from bot.messages.i18n import t

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("admin"))
async def admin_command_handler(message: Message) -> None:
    """
    Handle /admin command - entry point to admin panel.

    Access rules:
    - Must be admin (user_id in ADMIN_IDS)
    - Must be in private chat
    """
    if not message.from_user:
        return

    user_id = message.from_user.id
    settings = get_settings()

    # Check if user is admin
    if not settings.is_admin(user_id):
        await message.answer(t("admin.access_denied"))
        logger.warning(f"Non-admin user {user_id} attempted to access admin panel")
        return

    # Check if in private chat
    if message.chat.type != "private":
        await message.answer(t("admin.use_private_chat"))
        logger.info(f"Admin {user_id} tried to use /admin in {message.chat.type} chat")
        return

    logger.info(f"Admin {user_id} accessed admin panel")

    # Check if active giveaway exists
    async with get_session() as session:
        active_giveaway = await giveaway_repo.get_active_giveaway(session)
        has_active = active_giveaway is not None

    # Show main menu
    await message.answer(
        t("admin.main_menu"),
        reply_markup=get_admin_main_menu(has_active_giveaway=has_active),
    )


@router.callback_query(F.data == "nav:main_menu")
async def show_main_menu_callback(callback: CallbackQuery) -> None:
    """Show main menu from navigation button."""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    settings = get_settings()

    if not settings.is_admin(user_id):
        await callback.answer(t("admin.access_denied"), show_alert=True)
        return

    # Check if active giveaway exists
    async with get_session() as session:
        active_giveaway = await giveaway_repo.get_active_giveaway(session)
        has_active = active_giveaway is not None

    await callback.message.edit_text(
        t("admin.main_menu"),
        reply_markup=get_admin_main_menu(has_active_giveaway=has_active),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def close_admin_panel(callback: CallbackQuery) -> None:
    """Close admin panel."""
    if not callback.message:
        return

    await callback.message.delete()
    await callback.answer()
    logger.info(f"Admin {callback.from_user.id if callback.from_user else 'unknown'} closed admin panel")
