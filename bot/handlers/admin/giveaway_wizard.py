"""Упрощенный мастер создания розыгрышей (минимальная рабочая версия)."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, user_repo
from bot.handlers.admin.states import GiveawayCreationStates
from bot.keyboards.admin import get_announce_target_keyboard, get_preview_keyboard
from bot.keyboards.common import get_navigation_keyboard
from bot.messages.i18n import t
from bot.services.mailing import MessageContent, send_mass_message, send_to_channel

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "admin:create_giveaway")
async def start_giveaway_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало создания розыгрыша - выбор времени начала."""
    if not callback.message or not callback.from_user:
        return

    from bot.handlers.admin.date_picker import get_start_time_keyboard

    await callback.message.edit_text(
        "🗓 <b>Создание розыгрыша</b>\n\n"
        "Когда начать розыгрыш?",
        reply_markup=get_start_time_keyboard(),
    )
    await state.set_state(GiveawayCreationStates.select_start_date)
    await callback.answer()


@router.callback_query(F.data.startswith("start_time:"), GiveawayCreationStates.select_start_date)
async def select_start_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор времени начала."""
    if not callback.message:
        return

    start_option = callback.data.split(":")[1]
    await state.update_data(start_option=start_option)

    from bot.handlers.admin.date_picker import get_duration_keyboard

    await callback.message.edit_text(
        "📅 <b>Длительность розыгрыша</b>\n\n"
        "Сколько будет длиться розыгрыш?",
        reply_markup=get_duration_keyboard(),
    )
    await state.set_state(GiveawayCreationStates.select_end_date)
    await callback.answer()


@router.callback_query(F.data.startswith("duration:"), GiveawayCreationStates.select_end_date)
async def select_duration(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор длительности."""
    if not callback.message:
        return

    duration_days = int(callback.data.split(":")[1])
    data = await state.get_data()

    # Рассчитываем даты
    from bot.handlers.admin.date_picker import calculate_dates
    start_at_utc, end_at_utc = calculate_dates(data['start_option'], duration_days)

    await state.update_data(
        start_at=start_at_utc.isoformat(),
        end_at=end_at_utc.isoformat()
    )

    # Переходим к описанию
    await callback.message.edit_text(
        "📝 <b>Описание розыгрыша</b>\n\n"
        "Введите описание розыгрыша (что разыгрываете):",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.enter_description)
    await callback.answer()


@router.message(GiveawayCreationStates.enter_description)
async def process_description(message: Message, state: FSMContext) -> None:
    """Обработка описания."""
    if not message.text or not message.from_user:
        return

    if len(message.text) > 4096:
        await message.answer(t("wizard.description_too_long"))
        return

    await state.update_data(description=message.text)

    # Запрашиваем количество победителей
    await message.answer(
        "🏆 <b>Количество победителей</b>\n\n" "Введите число победителей (например: 1, 3, 5):",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.enter_winner_count)


@router.message(GiveawayCreationStates.enter_winner_count)
async def process_winner_count(message: Message, state: FSMContext) -> None:
    """Обработка количества победителей."""
    if not message.text or not message.from_user:
        return

    try:
        num_winners = int(message.text)
        if num_winners < 1:
            raise ValueError()
    except ValueError:
        await message.answer(t("wizard.invalid_winner_count"))
        return

    await state.update_data(num_winners=num_winners)

    # Запрашиваем медиа
    await message.answer(
        "📸 <b>Медиа для анонса</b>\n\n"
        "Отправьте одно фото, видео, GIF или документ для анонса розыгрыша:",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.upload_media)


@router.message(GiveawayCreationStates.upload_media)
async def process_media(message: Message, state: FSMContext) -> None:
    """Обработка медиа."""
    if not message.from_user:
        return

    # Определяем тип медиа
    media_file_id = None
    media_type = None

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

    await state.update_data(media_file_id=media_file_id, media_type=media_type)

    # Показываем предпросмотр
    data = await state.get_data()

    # Форматируем даты для предпросмотра
    from bot.handlers.admin.date_picker import format_dates_display
    dates_text = format_dates_display(data['start_at'], data['end_at'])

    preview_text = (
        "👁️ <b>Предпросмотр розыгрыша</b>\n\n"
        f"{dates_text}\n"
        f"🏆 Победителей: {data['num_winners']}\n"
        f"📝 Описание: {data['description']}\n"
        f"📎 Медиа: {media_type}\n\n"
        "Подтвердить создание?"
    )

    await message.answer(preview_text, reply_markup=get_preview_keyboard())
    await state.set_state(GiveawayCreationStates.preview)


@router.callback_query(F.data == "preview:confirm", GiveawayCreationStates.preview)
async def confirm_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение создания розыгрыша."""
    if not callback.message or not callback.from_user:
        return

    data = await state.get_data()

    try:
        # Конвертируем ISO строки обратно в datetime
        from dateutil import parser
        start_at = parser.isoparse(data['start_at'])
        end_at = parser.isoparse(data['end_at'])

        # Деактивируем все активные розыгрыши
        async with get_session() as session:
            await giveaway_repo.deactivate_all_giveaways(session)

            # Создаем новый розыгрыш
            giveaway = await giveaway_repo.create_giveaway(
                session=session,
                start_at=start_at,
                end_at=end_at,
                description=data['description'],
                num_winners=data['num_winners'],
                announce_media_file_id=data['media_file_id'],
                announce_media_type=data['media_type'],
                created_by_admin_id=callback.from_user.id,
            )

        logger.info(f"Создан розыгрыш {giveaway.id} админом {callback.from_user.id}")

        # Предлагаем выбрать куда отправить анонс
        await callback.message.edit_text(
            "✅ Розыгрыш успешно создан!\n\n📣 Куда отправить анонс?",
            reply_markup=get_announce_target_keyboard(),
        )
        await state.update_data(giveaway_id=giveaway.id)
        await state.set_state(GiveawayCreationStates.select_announce_target)

    except Exception as e:
        logger.error(f"Ошибка создания розыгрыша: {e}", exc_info=True)
        await callback.message.edit_text(t("errors.database"))
        await state.clear()


@router.callback_query(F.data == "preview:edit", GiveawayCreationStates.preview)
async def edit_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование розыгрыша - возврат к началу."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "📝 <b>Редактирование розыгрыша</b>\n\n"
        "Введите новое описание розыгрыша:",
        reply_markup=get_navigation_keyboard(back=False, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.enter_description)
    await callback.answer()


@router.callback_query(F.data.startswith("announce:"), GiveawayCreationStates.select_announce_target)
async def handle_announce_target(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора цели анонса."""
    if not callback.message or not callback.from_user:
        return

    target = callback.data.split(":")[1]
    data = await state.get_data()
    settings = get_settings()

    if target == "skip":
        await callback.message.edit_text("✅ Розыгрыш создан без анонса!")
        await state.clear()
        await callback.answer()
        return

    await callback.message.edit_text("📤 Отправляю анонс...")
    await callback.answer()

    try:
        async with get_session() as session:
            giveaway = await giveaway_repo.get_giveaway(session, data['giveaway_id'])
            if not giveaway:
                await callback.message.edit_text("❌ Розыгрыш не найден")
                await state.clear()
                return

            # Создаем кнопку участия
            join_button = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="🎁 Участвовать", url=settings.join_url)
                ]]
            )

            announce_text = (
                f"🎉 <b>Новый розыгрыш!</b>\n\n"
                f"{giveaway.description}\n\n"
                f"🏆 Победителей: {giveaway.num_winners}\n\n"
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

            user_ids: list[int] = []
            if target in ["users", "everywhere"]:
                user_ids = await user_repo.get_all_user_ids(session)

        # Рассылка выполняется вне сессии БД, чтобы не держать соединение из пула.
        if user_ids:
            result = await send_mass_message(
                callback.message.bot, user_ids, content, rps=settings.announce_rps
            )
            sent_count += result.sent_count

        await callback.message.edit_text(
            f"✅ Анонс отправлен!\n\n"
            f"📊 Отправлено: {sent_count}\n"
            f"🎁 Розыгрыш активен!"
        )

    except Exception as e:
        logger.error(f"Ошибка отправки анонса: {e}", exc_info=True)
        await callback.message.edit_text("❌ Ошибка отправки анонса, но розыгрыш создан")

    await state.clear()


# Навигационные обработчики
@router.callback_query(F.data == "nav:back", GiveawayCreationStates.select_start_date)
async def back_from_start_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат назад из выбора времени начала в главное меню."""
    if not callback.message:
        return

    from bot.keyboards.admin import get_admin_main_menu

    await callback.message.edit_text(
        "📋 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_main_menu(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "nav:back", GiveawayCreationStates.select_end_date)
async def back_from_duration(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат назад из выбора длительности к выбору времени начала."""
    if not callback.message:
        return

    from bot.handlers.admin.date_picker import get_start_time_keyboard

    await callback.message.edit_text(
        "🗓 <b>Создание розыгрыша</b>\n\n"
        "Когда начать розыгрыш?",
        reply_markup=get_start_time_keyboard(),
    )
    await state.set_state(GiveawayCreationStates.select_start_date)
    await callback.answer()


@router.callback_query(F.data == "nav:back", GiveawayCreationStates.enter_description)
async def back_from_description(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат назад из описания к выбору длительности."""
    if not callback.message:
        return

    from bot.handlers.admin.date_picker import get_duration_keyboard

    await callback.message.edit_text(
        "📅 <b>Длительность розыгрыша</b>\n\n"
        "Сколько будет длиться розыгрыш?",
        reply_markup=get_duration_keyboard(),
    )
    await state.set_state(GiveawayCreationStates.select_end_date)
    await callback.answer()


@router.callback_query(F.data == "nav:back", GiveawayCreationStates.enter_winner_count)
async def back_from_winner_count(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат назад из количества победителей к описанию."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "📝 <b>Описание розыгрыша</b>\n\n"
        "Введите описание розыгрыша (что разыгрываете):",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.enter_description)
    await callback.answer()


@router.callback_query(F.data == "nav:back", GiveawayCreationStates.upload_media)
async def back_from_media(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат назад из загрузки медиа к количеству победителей."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "🏆 <b>Количество победителей</b>\n\n"
        "Введите число победителей (например: 1, 3, 5):",
        reply_markup=get_navigation_keyboard(back=True, cancel=True, main_menu=True),
    )
    await state.set_state(GiveawayCreationStates.enter_winner_count)
    await callback.answer()


@router.callback_query(F.data == "nav:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена мастера."""
    if not callback.message:
        return
    await callback.message.edit_text(t("admin.operation_cancelled"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "nav:main_menu")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню (общий обработчик для всех мастеров)."""
    if not callback.message:
        return

    from bot.keyboards.admin import get_admin_main_menu

    async with get_session() as session:
        has_active = await giveaway_repo.get_active_giveaway(session) is not None

    await state.clear()
    await callback.message.edit_text(
        t("admin.main_menu"),
        reply_markup=get_admin_main_menu(has_active_giveaway=has_active),
    )
    await callback.answer()
