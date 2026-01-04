"""FSM состояния для админ-панели."""

from aiogram.fsm.state import State, StatesGroup


class GiveawayCreationStates(StatesGroup):
    """Состояния мастера создания розыгрыша."""

    select_start_date = State()
    enter_start_time = State()
    select_end_date = State()
    enter_end_time = State()
    enter_winner_count = State()
    enter_description = State()
    upload_media = State()
    preview = State()
    select_announce_target = State()


class BroadcastStates(StatesGroup):
    """Состояния мастера рассылки."""

    select_type = State()
    enter_text = State()
    upload_media = State()
    preview = State()
    confirm = State()


class AnnounceStates(StatesGroup):
    """Состояния мастера анонсирования."""

    select_target = State()
    sending = State()


class WinnersStates(StatesGroup):
    """Состояния мастера выбора победителей."""

    confirm_end = State()
    select_winners = State()
    select_publish_target = State()
