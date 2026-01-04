"""Common navigation keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.messages.i18n import t


def get_back_button() -> InlineKeyboardButton:
    """Get back navigation button."""
    return InlineKeyboardButton(text=t("buttons.back"), callback_data="nav:back")


def get_cancel_button() -> InlineKeyboardButton:
    """Get cancel button."""
    return InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")


def get_main_menu_button() -> InlineKeyboardButton:
    """Get main menu button."""
    return InlineKeyboardButton(text=t("buttons.main_menu"), callback_data="nav:main_menu")


def get_navigation_keyboard(
    back: bool = True, cancel: bool = True, main_menu: bool = False
) -> InlineKeyboardMarkup:
    """
    Get navigation keyboard with optional buttons.

    Args:
        back: Include back button
        cancel: Include cancel button
        main_menu: Include main menu button

    Returns:
        InlineKeyboardMarkup with requested buttons
    """
    buttons = []

    if back:
        buttons.append(get_back_button())
    if cancel:
        buttons.append(get_cancel_button())
    if main_menu:
        buttons.append(get_main_menu_button())

    # Arrange in rows (max 2 buttons per row)
    keyboard = []
    for i in range(0, len(buttons), 2):
        keyboard.append(buttons[i : i + 2])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Get confirmation dialog keyboard.

    Returns:
        Keyboard with Yes/No buttons
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("buttons.yes_cancel"), callback_data="confirm:yes"),
                InlineKeyboardButton(text=t("buttons.no_continue"), callback_data="confirm:no"),
            ]
        ]
    )


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Get generic confirmation keyboard.

    Args:
        action: Action identifier for callback data

    Returns:
        Keyboard with Confirm/Cancel buttons
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("buttons.confirm"), callback_data=f"confirm:{action}"),
                InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel"),
            ]
        ]
    )
