"""Verification step handler for giveaway registration."""

import logging
import random
import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.base import get_session
from bot.db.repo import participant_repo
from bot.handlers.admin.states import VerificationStates
from bot.messages.i18n import t
from bot.services.redis_client import get_redis

logger = logging.getLogger(__name__)

router = Router()

# Verification timeout in seconds (3 minutes)
VERIFICATION_TIMEOUT = 180

# Maximum wrong attempts before blocking
MAX_ATTEMPTS = 3

# TTL for Redis keys (30 days in seconds)
REDIS_KEY_TTL = 30 * 24 * 3600


def generate_verification_keyboard(numbers: list[int]) -> InlineKeyboardMarkup:
    """
    Generate inline keyboard with verification buttons.

    Layout: row of 3 + row of 2.

    Args:
        numbers: List of 5 digits to display on buttons.

    Returns:
        InlineKeyboardMarkup with 5 number buttons.
    """
    buttons = [
        InlineKeyboardButton(text=str(n), callback_data=f"verify:{n}")
        for n in numbers
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[:3], buttons[3:]]
    )


def generate_verification_numbers(correct_number: int | None = None) -> tuple[int, list[int]]:
    """
    Generate 5 unique random digits (0-9), one designated as correct.

    Args:
        correct_number: If provided, use this as the correct number.
                       Otherwise pick a random one.

    Returns:
        Tuple of (correct_number, shuffled list of 5 numbers).
    """
    all_digits = list(range(10))

    if correct_number is None:
        # Pick 5 unique digits, one will be correct
        numbers = random.sample(all_digits, 5)
        correct_number = random.choice(numbers)
    else:
        # Keep the correct number, pick 4 others
        others = [d for d in all_digits if d != correct_number]
        distractors = random.sample(others, 4)
        numbers = distractors + [correct_number]
        random.shuffle(numbers)

    return correct_number, numbers


def get_attempts_key(giveaway_id: int, user_id: int) -> str:
    """Get Redis key for tracking wrong attempts."""
    return f"verify_attempts:{giveaway_id}:{user_id}"


def get_blocked_key(giveaway_id: int, user_id: int) -> str:
    """Get Redis key for block status."""
    return f"verify_blocked:{giveaway_id}:{user_id}"


@router.callback_query(F.data.startswith("verify:"), VerificationStates.waiting_for_button)
async def verification_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle verification button press."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Extract pressed number
    pressed_number = int(callback.data.split(":")[1])

    # Get state data
    data = await state.get_data()
    correct_number = data.get("correct_number")
    numbers = data.get("numbers")
    created_at = data.get("created_at", 0)
    giveaway_id = data.get("giveaway_id")
    user_id = data.get("user_id")
    username = data.get("username")
    giveaway_end_at = data.get("giveaway_end_at")
    giveaway_description = data.get("giveaway_description")
    giveaway_num_winners = data.get("giveaway_num_winners")

    if not all([correct_number is not None, numbers, giveaway_id, user_id]):
        await callback.answer(t("errors.generic"))
        await state.clear()
        return

    # Check timeout
    if time.time() - created_at > VERIFICATION_TIMEOUT:
        await state.clear()
        await callback.answer(t("user.verification_timeout"), show_alert=True)
        return

    redis = get_redis()

    if pressed_number == correct_number:
        # Correct! Register participant
        await state.clear()

        try:
            from datetime import datetime

            # Parse giveaway_end_at back to datetime
            giveaway_end_dt = datetime.fromisoformat(giveaway_end_at)

            async with get_session() as session:
                await participant_repo.add_participant(
                    session=session,
                    giveaway_id=giveaway_id,
                    user_id=user_id,
                    username_snapshot=username,
                    giveaway_end_snapshot=giveaway_end_dt,
                )

            logger.info(f"User {user_id} passed verification for giveaway {giveaway_id}")

            await callback.message.edit_text(
                t(
                    "user.participation_confirmed",
                    description=giveaway_description,
                    num_winners=giveaway_num_winners,
                )
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error registering user {user_id} after verification: {e}", exc_info=True)
            await callback.message.edit_text(t("errors.generic"))
            await callback.answer()

    else:
        # Wrong answer — increment attempts
        attempts_key = get_attempts_key(giveaway_id, user_id)
        current_attempts = await redis.incr(attempts_key)
        await redis.expire(attempts_key, REDIS_KEY_TTL)

        if current_attempts >= MAX_ATTEMPTS:
            # Block user
            blocked_key = get_blocked_key(giveaway_id, user_id)
            await redis.set(blocked_key, "1", ex=REDIS_KEY_TTL)
            await state.clear()

            logger.info(f"User {user_id} blocked from giveaway {giveaway_id} (failed verification)")

            await callback.message.edit_text(t("user.verification_blocked"))
            await callback.answer()
        else:
            # Reshuffle buttons (same numbers, new positions)
            remaining = MAX_ATTEMPTS - current_attempts
            random.shuffle(numbers)

            # Update state with new positions
            await state.update_data(numbers=numbers)

            keyboard = generate_verification_keyboard(numbers)
            await callback.message.edit_text(
                t("user.verification_wrong", remaining=remaining, number=correct_number),
                reply_markup=keyboard,
            )
            await callback.answer()
