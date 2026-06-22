"""Admin-only access middleware.

Applied to the admin routers so that every admin handler is protected in one
place, instead of each handler repeating ``settings.is_admin(...)`` checks (and
some wizard steps previously not checking at all).
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config.settings import get_settings
from bot.messages.i18n import t

logger = logging.getLogger(__name__)


class AdminOnlyMiddleware(BaseMiddleware):
    """Reject updates from non-admin users on admin routers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None and not get_settings().is_admin(user.id):
            logger.warning("Non-admin user %s blocked from admin handler", user.id)
            if isinstance(event, CallbackQuery):
                await event.answer(t("admin.access_denied"), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(t("admin.access_denied"))
            return None
        return await handler(event, data)
