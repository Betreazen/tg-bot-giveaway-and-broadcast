"""Admin panel inline keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.messages.i18n import t


def get_admin_main_menu(has_active_giveaway: bool = False) -> InlineKeyboardMarkup:
    """
    Get main admin menu keyboard.

    Args:
        has_active_giveaway: Whether an active giveaway exists

    Returns:
        Main menu keyboard with appropriate buttons
    """
    keyboard = [
        [InlineKeyboardButton(text=t("buttons.create_giveaway"), callback_data="admin:create_giveaway")],
        [InlineKeyboardButton(text=t("buttons.broadcast"), callback_data="admin:broadcast")],
        [InlineKeyboardButton(text=t("buttons.view_status"), callback_data="admin:status")],
        [InlineKeyboardButton(text="📊 Синхронизация Google Sheets", callback_data="admin:sync_sheets")],
    ]

    # Add giveaway-specific buttons only if active giveaway exists
    if has_active_giveaway:
        keyboard.insert(
            1,
            [
                InlineKeyboardButton(
                    text=t("buttons.announce_giveaway"), callback_data="admin:announce_giveaway"
                )
            ],
        )
        keyboard.insert(
            2,
            [
                InlineKeyboardButton(
                    text=t("buttons.complete_giveaway"), callback_data="admin:complete_giveaway"
                )
            ],
        )

    keyboard.append([InlineKeyboardButton(text=t("buttons.close"), callback_data="admin:close")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_announce_target_keyboard() -> InlineKeyboardMarkup:
    """Get announcement target selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.to_channel"), callback_data="announce:channel")],
            [InlineKeyboardButton(text=t("buttons.to_users"), callback_data="announce:users")],
            [InlineKeyboardButton(text=t("buttons.everywhere"), callback_data="announce:everywhere")],
            [InlineKeyboardButton(text=t("buttons.skip"), callback_data="announce:skip")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
        ]
    )


def get_manual_announce_keyboard() -> InlineKeyboardMarkup:
    """Get manual announcement target selection keyboard (without skip)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.to_channel"), callback_data="announce_manual:channel")],
            [InlineKeyboardButton(text=t("buttons.to_users"), callback_data="announce_manual:users")],
            [InlineKeyboardButton(text=t("buttons.everywhere"), callback_data="announce_manual:everywhere")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
        ]
    )


def get_results_target_keyboard() -> InlineKeyboardMarkup:
    """Get results announcement target selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.to_channel"), callback_data="results:channel")],
            [InlineKeyboardButton(text=t("buttons.to_admins"), callback_data="results:admins")],
            [InlineKeyboardButton(text=t("buttons.to_users"), callback_data="results:users")],
            [InlineKeyboardButton(text=t("buttons.everywhere"), callback_data="results:everywhere")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
        ]
    )


def get_broadcast_type_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast type selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.text_only"), callback_data="broadcast:text")],
            [InlineKeyboardButton(text=t("buttons.media_caption"), callback_data="broadcast:media")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
        ]
    )


def get_winner_count_keyboard(current: int = 1) -> InlineKeyboardMarkup:
    """
    Get winner count adjustment keyboard.

    Args:
        current: Current winner count

    Returns:
        Keyboard with increment/decrement buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(text="-10", callback_data="winners:dec_10"),
            InlineKeyboardButton(text="-5", callback_data="winners:dec_5"),
            InlineKeyboardButton(text="-1", callback_data="winners:dec_1"),
        ],
        [InlineKeyboardButton(text=f"Current: {current}", callback_data="winners:current")],
        [
            InlineKeyboardButton(text="+1", callback_data="winners:inc_1"),
            InlineKeyboardButton(text="+5", callback_data="winners:inc_5"),
            InlineKeyboardButton(text="+10", callback_data="winners:inc_10"),
        ],
        [InlineKeyboardButton(text=t("buttons.confirm"), callback_data="winners:confirm")],
        [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_draft_resume_keyboard() -> InlineKeyboardMarkup:
    """Get draft resume options keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.resume_draft"), callback_data="draft:resume")],
            [InlineKeyboardButton(text=t("buttons.start_fresh"), callback_data="draft:fresh")],
        ]
    )


def get_preview_keyboard() -> InlineKeyboardMarkup:
    """Get preview confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.confirm_send"), callback_data="preview:confirm")],
            [InlineKeyboardButton(text=t("buttons.edit"), callback_data="preview:edit")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="nav:cancel")],
        ]
    )


def get_end_giveaway_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get giveaway end confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.yes_end_now"), callback_data="giveaway:end_confirm")],
            [InlineKeyboardButton(text=t("buttons.no_continue"), callback_data="giveaway:end_cancel")],
        ]
    )


def get_select_winners_keyboard() -> InlineKeyboardMarkup:
    """Get select winners action keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.select_winners"), callback_data="winners:select")],
            [InlineKeyboardButton(text=t("buttons.back"), callback_data="nav:back")],
        ]
    )
