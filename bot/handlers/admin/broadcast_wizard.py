"""Мастер рассылки сообщений."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.base import get_session
from bot.db.repo import user_repo
from bot.handlers.admin.states import BroadcastStates
from bot.keyboards.admin import get_broadcast_type_keyboard, get_preview_keyboard
from bot.keyboards.common import get_navigation_keyboard
from bot.messages.i18n import t
from bot.services.mailing import MessageContent, send_mass_message

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало рассылки."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n" "Выберите тип рассылки:",
        reply_markup=get_broadcast_type_keyboard(),
    )
    await state.set_state(BroadcastStates.select_type)
    await callback.answer()


@router.callback_query(F.data == "broadcast:text", BroadcastStates.select_type)
async def select_text_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбран текстовый режим."""
    if not callback.message:
        return

    await state.update_data(broadcast_type="text")
    await callback.message.edit_text(
        "✏️ <b>Текстовая рассылка</b>\n\n" "Введите текст сообщения:",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(BroadcastStates.enter_text)
    await callback.answer()


@router.callback_query(F.data == "broadcast:media", BroadcastStates.select_type)
async def select_media_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбран режим с медиа."""
    if not callback.message:
        return

    await state.update_data(broadcast_type="media")
    await callback.message.edit_text(
        "📎 <b>Рассылка с медиа</b>\n\n" "Отправьте фото, видео, GIF или документ с подписью (необязательно):",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(BroadcastStates.upload_media)
    await callback.answer()


@router.message(BroadcastStates.enter_text)
async def process_broadcast_text(message: Message, state: FSMContext) -> None:
    """Обработка текста рассылки."""
    if not message.text:
        return

    if len(message.text) > 4096:
        await message.answer("❌ Текст слишком длинный (максимум 4096 символов)")
        return

    await state.update_data(text=message.text)

    # Показываем предпросмотр
    preview_text = (
        f"👁️ <b>Предпросмотр рассылки</b>\n\n"
        f"{message.text}\n\n"
        f"📏 Символов: {len(message.text)}\n\n"
        f"Подтвердить отправку?"
    )

    await message.answer(preview_text, reply_markup=get_preview_keyboard())
    await state.set_state(BroadcastStates.confirm)


@router.message(BroadcastStates.upload_media)
async def process_broadcast_media(message: Message, state: FSMContext) -> None:
    """Обработка медиа для рассылки."""
    if not message.from_user:
        return

    # Определяем тип медиа
    media_file_id = None
    media_type = None
    caption = message.caption or ""

    if message.photo:
        media_file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        media_file_id = message.video.file_id
        media_type = "video"
    elif message.animation:
        media_file_id = message.animation.file_id
        media_type = "animation"
    elif message.document:
        media_file_id = message.document.file_id
        media_type = "document"
    else:
        await message.answer(t("wizard.invalid_media"))
        return

    await state.update_data(media_file_id=media_file_id, media_type=media_type, text=caption)

    # Показываем предпросмотр
    preview_text = (
        f"👁️ <b>Предпросмотр рассылки</b>\n\n"
        f"📎 Медиа: {media_type}\n"
        f"📝 Подпись: {caption if caption else '(нет)'}\n"
        f"📏 Символов: {len(caption)}\n\n"
        f"Подтвердить отправку?"
    )

    await message.answer(preview_text, reply_markup=get_preview_keyboard())
    await state.set_state(BroadcastStates.confirm)


@router.callback_query(F.data == "preview:confirm", BroadcastStates.confirm)
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение и отправка рассылки."""
    if not callback.message:
        return

    data = await state.get_data()

    await callback.message.edit_text("📤 Начинаю рассылку...")
    await callback.answer()

    try:
        async with get_session() as session:
            # Получаем всех пользователей
            user_ids = await user_repo.get_all_user_ids(session)

            if not user_ids:
                await callback.message.edit_text("❌ В базе нет пользователей для рассылки")
                await state.clear()
                return

            # Создаем контент
            content = MessageContent(
                text=data.get("text"),
                media_file_id=data.get("media_file_id"),
                media_type=data.get("media_type"),
            )

            # Отправляем рассылку
            result = await send_mass_message(callback.message.bot, user_ids, content, rps=20)

            # Показываем результат
            result_text = (
                f"✅ <b>Рассылка завершена!</b>\n\n"
                f"📊 Всего пользователей: {result.total_recipients}\n"
                f"✉️ Отправлено: {result.sent_count}\n"
                f"❌ Не доставлено: {result.failed_count}\n"
                f"⏱️ Длительность: {result.duration_seconds:.1f}с"
            )

            await callback.message.edit_text(result_text)

    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}", exc_info=True)
        await callback.message.edit_text("❌ Ошибка при рассылке")

    await state.clear()


@router.callback_query(F.data == "preview:edit", BroadcastStates.confirm)
async def edit_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование рассылки."""
    if not callback.message:
        return

    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "text")

    if broadcast_type == "text":
        await callback.message.edit_text(
            "✏️ Введите новый текст:",
            reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
        )
        await state.set_state(BroadcastStates.enter_text)
    else:
        await callback.message.edit_text(
            "📎 Отправьте новое медиа с подписью:",
            reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
        )
        await state.set_state(BroadcastStates.upload_media)

    await callback.answer()
