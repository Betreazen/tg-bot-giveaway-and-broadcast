"""Выбор дат для розыгрышей с inline кнопками."""

from datetime import UTC, datetime, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.datetimes import get_tz, to_local


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности розыгрыша."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 1 день", callback_data="duration:1"),
                InlineKeyboardButton(text="📅 3 дня", callback_data="duration:3"),
            ],
            [
                InlineKeyboardButton(text="📅 7 дней", callback_data="duration:7"),
                InlineKeyboardButton(text="📅 14 дней", callback_data="duration:14"),
            ],
            [
                InlineKeyboardButton(text="📅 30 дней", callback_data="duration:30"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="nav:cancel"),
            ],
        ]
    )


def get_start_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора времени начала розыгрыша."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🕐 Сейчас", callback_data="start_time:now"),
                InlineKeyboardButton(text="🕐 Через 1 час", callback_data="start_time:1h"),
            ],
            [
                InlineKeyboardButton(text="🕐 Через 3 часа", callback_data="start_time:3h"),
                InlineKeyboardButton(text="🕐 Через 6 часов", callback_data="start_time:6h"),
            ],
            [
                InlineKeyboardButton(text="🕐 Завтра в 12:00", callback_data="start_time:tomorrow"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="nav:cancel"),
            ],
        ]
    )


def calculate_dates(start_option: str, duration_days: int) -> tuple[datetime, datetime]:
    """
    Рассчитать даты начала и окончания.

    Args:
        start_option: Опция начала ("now", "1h", "3h", "6h", "tomorrow")
        duration_days: Длительность в днях

    Returns:
        Tuple[start_at_utc, end_at_utc]
    """
    tz = get_tz()
    now_local = datetime.now(tz)

    # Определяем время начала
    if start_option == "1h":
        start_at_local = now_local + timedelta(hours=1)
    elif start_option == "3h":
        start_at_local = now_local + timedelta(hours=3)
    elif start_option == "6h":
        start_at_local = now_local + timedelta(hours=6)
    elif start_option == "tomorrow":
        tomorrow = now_local + timedelta(days=1)
        start_at_local = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
    else:  # "now" or unknown
        start_at_local = now_local

    # Рассчитываем время окончания
    end_at_local = start_at_local + timedelta(days=duration_days)

    # Конвертируем в UTC
    return start_at_local.astimezone(UTC), end_at_local.astimezone(UTC)


def format_dates_display(start_at_iso: str, end_at_iso: str) -> str:
    """
    Форматировать даты для отображения.

    Args:
        start_at_iso: ISO строка даты начала
        end_at_iso: ISO строка даты окончания

    Returns:
        Отформатированная строка
    """
    from dateutil import parser

    start_at = parser.isoparse(start_at_iso)
    end_at = parser.isoparse(end_at_iso)

    start_str = to_local(start_at).strftime("%d.%m.%Y %H:%M")
    end_str = to_local(end_at).strftime("%d.%m.%Y %H:%M")

    days = (end_at - start_at).days

    return (
        f"🗓 Начало: {start_str} МСК\n"
        f"⏰ Окончание: {end_str} МСК\n"
        f"📅 Длительность: {days} дн."
    )
