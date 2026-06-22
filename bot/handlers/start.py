"""User /start command handler."""

import logging
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, participant_repo, user_repo
from bot.handlers.admin.states import VerificationStates
from bot.handlers.verification import (
    MAX_ATTEMPTS,
    VERIFICATION_TIMEOUT,
    generate_verification_keyboard,
    generate_verification_numbers,
    get_attempts_key,
    get_blocked_key,
)
from bot.messages.i18n import t
from bot.services.redis_client import get_redis
from bot.services.subscription import check_subscription
from bot.utils.datetimes import fmt_local

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    """
    Handle /start command for user participation.

    Flow:
    1. Upsert user in database
    2. Check channel subscription
    3. Get active giveaway
    4. Check if already participating
    5. Admin bypass or verification step
    6. Add participant (after verification)
    """
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username

    logger.info(f"User {user_id} (@{username}) started bot")

    try:
        # Get settings
        settings = get_settings()

        # Upsert user in database
        async with get_session() as session:
            user = await user_repo.create_or_update_user(session, user_id, username)
            logger.debug(f"User record updated: {user}")

            # Check subscription
            is_subscribed = await check_subscription(message.bot, user_id, settings.channel_id)

            if not is_subscribed:
                await message.answer(t("user.not_subscribed"))
                logger.info(f"User {user_id} is not subscribed to channel")
                return

            # Get active giveaway
            giveaway = await giveaway_repo.get_active_giveaway(session)

            if not giveaway:
                await message.answer(t("user.no_active_giveaway"))
                logger.info(f"User {user_id} attempted to participate but no active giveaway")
                return

            # Check if already participating
            already_participating = await participant_repo.check_participation(session, giveaway.id, user_id)

            if already_participating:
                await message.answer(t("user.already_participating"))
                logger.info(f"User {user_id} is already participating in giveaway {giveaway.id}")
                return

            # Admin bypass — skip verification
            if settings.is_admin(user_id):
                await participant_repo.add_participant(
                    session=session,
                    giveaway_id=giveaway.id,
                    user_id=user_id,
                    username_snapshot=username,
                    giveaway_end_snapshot=giveaway.end_at,
                )
                logger.info(f"Admin {user_id} joined giveaway {giveaway.id} (verification skipped)")

                end_at_str = fmt_local(giveaway.end_at, "%Y-%m-%d %H:%M")

                await message.answer(
                    t(
                        "user.participation_confirmed",
                        description=giveaway.description,
                        end_at=end_at_str,
                        num_winners=giveaway.num_winners,
                    )
                )
                return

            # Check if user is blocked for this giveaway
            redis = get_redis()
            blocked_key = get_blocked_key(giveaway.id, user_id)
            is_blocked = await redis.get(blocked_key)

            if is_blocked:
                await message.answer(t("user.verification_blocked"))
                logger.info(f"User {user_id} is blocked from giveaway {giveaway.id}")
                return

            # Check if already in verification state
            current_state = await state.get_state()
            if current_state == VerificationStates.waiting_for_button:
                data = await state.get_data()
                created_at = data.get("created_at", 0)

                if time.time() - created_at <= VERIFICATION_TIMEOUT:
                    # Active verification — remind user
                    await message.answer(t("user.verification_in_progress"))
                    return
                else:
                    # Expired — clear state and start fresh
                    await state.clear()

            # Check total attempts (might be blocked but key wasn't set due to edge case)
            attempts_key = get_attempts_key(giveaway.id, user_id)
            attempts_str = await redis.get(attempts_key)
            if attempts_str and int(attempts_str) >= MAX_ATTEMPTS:
                await redis.set(blocked_key, "1", ex=30 * 24 * 3600)
                await message.answer(t("user.verification_blocked"))
                return

            # Start verification
            correct_number, numbers = generate_verification_numbers()

            await state.set_state(VerificationStates.waiting_for_button)
            await state.update_data(
                correct_number=correct_number,
                numbers=numbers,
                created_at=time.time(),
                giveaway_id=giveaway.id,
                user_id=user_id,
                username=username,
                giveaway_end_at=giveaway.end_at.isoformat(),
                giveaway_description=giveaway.description,
                giveaway_num_winners=giveaway.num_winners,
            )

            keyboard = generate_verification_keyboard(numbers)
            await message.answer(
                t("user.verification_prompt", number=correct_number),
                reply_markup=keyboard,
            )

            logger.info(f"Verification started for user {user_id}, giveaway {giveaway.id}")

    except Exception as e:
        logger.error(f"Error in start handler for user {user_id}: {e}", exc_info=True)
        await message.answer(t("errors.generic"))
