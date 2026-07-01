"""Управление подозрительными аккаунтами.

Админ помечает аккаунты как подозрительные (по username в любом виде — @name,
ссылка t.me/name, просто name). Такие аккаунты продолжают участвовать в
розыгрышах, но никогда не побеждают (фильтруются при выборе победителей).
Пользователю об этом не сообщается.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.base import get_session
from bot.db.repo import user_repo
from bot.handlers.admin.states import SuspiciousStates
from bot.keyboards.admin import get_suspicious_menu_keyboard
from bot.keyboards.common import get_navigation_keyboard
from bot.utils.usernames import parse_username

logger = logging.getLogger(__name__)

router = Router()

_MENU_TEXT = (
    "🚩 <b>Подозрительные аккаунты</b>\n\n"
    "Помеченные аккаунты участвуют в розыгрышах, но <b>никогда не выигрывают</b>. "
    "Пользователь об этом не узнаёт.\n\n"
    "Выберите действие:"
)

_ENTER_TEXT = (
    "Введите username пользователя в любом виде:\n"
    "<code>@username</code>, <code>https://t.me/username</code> или просто <code>username</code>."
)


@router.callback_query(F.data == "admin:suspicious")
async def suspicious_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Показать меню управления подозрительными аккаунтами."""
    if not callback.message:
        return
    await state.clear()
    await callback.message.edit_text(_MENU_TEXT, reply_markup=get_suspicious_menu_keyboard())
    await callback.answer()


def _paginate(header: str, lines: list[str], limit: int = 3800) -> list[str]:
    """Split a header + list of lines into messages under Telegram's length limit."""
    pages: list[str] = []
    current = header
    for line in lines:
        if len(current) + len(line) + 1 > limit:
            pages.append(current.rstrip())
            current = ""
        current += line + "\n"
    if current.strip():
        pages.append(current.rstrip())
    return pages or [header.rstrip()]


@router.callback_query(F.data == "suspicious:list")
async def list_suspicious(callback: CallbackQuery, state: FSMContext) -> None:
    """Показать список всех подозрительных аккаунтов."""
    if not callback.message:
        return
    await state.clear()

    async with get_session() as session:
        users = await user_repo.get_suspicious_users(session)

    if not users:
        await callback.message.edit_text(
            "📋 Список подозрительных пуст.", reply_markup=get_suspicious_menu_keyboard()
        )
        await callback.answer()
        return

    lines = [
        f"{i}. {'@' + u.username if u.username else 'без username'} "
        f"(ID <code>{u.user_id}</code>)"
        for i, u in enumerate(users, 1)
    ]
    pages = _paginate(f"📋 <b>Подозрительные аккаунты ({len(users)})</b>\n\n", lines)

    # First page replaces the menu message (with the menu keyboard), rest as follow-ups.
    await callback.message.edit_text(pages[0], reply_markup=get_suspicious_menu_keyboard())
    for page in pages[1:]:
        await callback.message.answer(page)
    await callback.answer()


@router.callback_query(F.data == "suspicious:mark")
async def prompt_mark(callback: CallbackQuery, state: FSMContext) -> None:
    """Запросить username для пометки."""
    if not callback.message:
        return
    await callback.message.edit_text(
        f"🚩 <b>Пометить подозрительным</b>\n\n{_ENTER_TEXT}",
        reply_markup=get_navigation_keyboard(cancel=True, main_menu=True),
    )
    await state.set_state(SuspiciousStates.enter_username_to_mark)
    await callback.answer()


@router.callback_query(F.data == "suspicious:unmark")
async def prompt_unmark(callback: CallbackQuery, state: FSMContext) -> None:
    """Запросить username для снятия метки."""
    if not callback.message:
        return
    await callback.message.edit_text(
        f"✅ <b>Снять метку подозрительного</b>\n\n{_ENTER_TEXT}",
        reply_markup=get_navigation_keyboard(cancel=True, main_menu=True),
    )
    await state.set_state(SuspiciousStates.enter_username_to_unmark)
    await callback.answer()


async def _apply(message: Message, state: FSMContext, *, mark: bool) -> None:
    if not message.text:
        return

    username = parse_username(message.text)
    if not username:
        await message.answer(
            "❌ Не удалось распознать username. Пришлите его в виде "
            "<code>@username</code>, ссылки или просто <code>username</code>.",
            reply_markup=get_suspicious_menu_keyboard(),
        )
        await state.clear()
        return

    async with get_session() as session:
        user = await user_repo.set_suspicious(session, username, mark)

    if user is None:
        await message.answer(
            f"⚠️ Пользователь <code>@{username}</code> не найден в базе "
            "(он должен был хотя бы раз запустить бота).",
            reply_markup=get_suspicious_menu_keyboard(),
        )
    elif mark:
        logger.info("Admin marked user %s (@%s) as suspicious", user.user_id, username)
        await message.answer(
            f"🚩 <code>@{username}</code> (ID <code>{user.user_id}</code>) помечен как "
            "подозрительный. Участвует, но не выигрывает.",
            reply_markup=get_suspicious_menu_keyboard(),
        )
    else:
        logger.info("Admin cleared suspicious flag for user %s (@%s)", user.user_id, username)
        await message.answer(
            f"✅ С <code>@{username}</code> (ID <code>{user.user_id}</code>) снята метка "
            "«подозрительный».",
            reply_markup=get_suspicious_menu_keyboard(),
        )

    await state.clear()


@router.message(SuspiciousStates.enter_username_to_mark)
async def process_mark(message: Message, state: FSMContext) -> None:
    """Пометить пользователя подозрительным по введённому username."""
    await _apply(message, state, mark=True)


@router.message(SuspiciousStates.enter_username_to_unmark)
async def process_unmark(message: Message, state: FSMContext) -> None:
    """Снять метку подозрительного по введённому username."""
    await _apply(message, state, mark=False)
