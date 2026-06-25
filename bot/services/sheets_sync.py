"""Google Sheets синхронизация (опциональная)."""

import logging
from datetime import datetime
from typing import Any

from bot.utils.datetimes import fmt_local

logger = logging.getLogger(__name__)


def _fmt_dt(value: Any) -> str:
    """Format a datetime value in the configured local timezone for a sheet cell."""
    if isinstance(value, datetime):
        return fmt_local(value, "%Y-%m-%d %H:%M")
    return str(value) if value else ""

# Флаг доступности Google Sheets
SHEETS_AVAILABLE = False

try:
    import gspread
    from google.oauth2.service_account import Credentials

    SHEETS_AVAILABLE = True
except ImportError:
    logger.warning("Google Sheets библиотеки не установлены, синхронизация отключена")


class SheetsSync:
    """Сервис синхронизации с Google Sheets."""

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Инициализация."""
        if not SHEETS_AVAILABLE:
            raise ImportError("gspread не установлен")

        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None

    def connect(self) -> bool:
        """Подключение к Google Sheets."""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info(f"Подключено к Google Sheets: {self.spreadsheet.title}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}", exc_info=True)
            return False

    def _rewrite(self, title: str, headers: list[str], rows: list[list[Any]]) -> int:
        """Полностью перезаписать лист одним запросом (без потери строк).

        Раньше использовался clear()+append_rows, который при большом объёме мог
        не дописать часть строк. Здесь грид сначала растягивается под объём данных,
        затем все значения пишутся одним update — строки не теряются.
        """
        all_values = [headers, *rows]
        needed_rows = len(all_values) + 10
        cols = max(len(headers), 1)

        try:
            sheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=title, rows=needed_rows, cols=cols)

        # Грид должен вмещать все строки/столбцы до записи.
        if sheet.row_count < needed_rows:
            sheet.add_rows(needed_rows - sheet.row_count)
        if sheet.col_count < cols:
            sheet.add_cols(cols - sheet.col_count)

        sheet.clear()
        sheet.update(range_name="A1", values=all_values, value_input_option="RAW")
        return len(rows)

    def sync_users(self, users: list[dict[str, Any]]) -> bool:
        """Синхронизация пользователей."""
        if not self.spreadsheet:
            return False

        try:
            headers = ["User ID", "Username", "Joined At (MSK)"]
            rows = [
                [user.get("user_id", ""), user.get("username", ""), _fmt_dt(user.get("joined_at"))]
                for user in users
            ]
            count = self._rewrite("Users", headers, rows)
            logger.info(f"Синхронизировано пользователей: {count}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации пользователей: {e}", exc_info=True)
            return False

    def sync_participants(self, participants: list[dict[str, Any]]) -> bool:
        """Синхронизация участников розыгрышей."""
        if not self.spreadsheet:
            return False

        try:
            headers = [
                "Giveaway ID",
                "User ID",
                "Username",
                "Joined At (MSK)",
                "Giveaway Start (MSK)",
                "Giveaway End (MSK)",
            ]
            rows = [
                [
                    p.get("giveaway_id", ""),
                    p.get("user_id", ""),
                    p.get("username_snapshot", ""),
                    _fmt_dt(p.get("joined_at")),
                    _fmt_dt(p.get("giveaway_start")),
                    _fmt_dt(p.get("giveaway_end")),
                ]
                for p in participants
            ]
            count = self._rewrite("Participants", headers, rows)
            logger.info(f"Синхронизировано участников: {count}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации участников: {e}", exc_info=True)
            return False

    def sync_winners(self, winners: list[dict[str, Any]]) -> bool:
        """Синхронизация победителей."""
        if not self.spreadsheet:
            return False

        try:
            headers = ["Giveaway ID", "User ID", "Username", "Selected At (MSK)"]
            rows = [
                [
                    w.get("giveaway_id", ""),
                    w.get("user_id", ""),
                    w.get("username_snapshot", ""),
                    _fmt_dt(w.get("created_at")),
                ]
                for w in winners
            ]
            count = self._rewrite("Winners", headers, rows)
            logger.info(f"Синхронизировано победителей: {count}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации победителей: {e}", exc_info=True)
            return False

    def sync_giveaways_summary(self, giveaways_data: list[dict[str, Any]]) -> bool:
        """
        Синхронизация сводной таблицы по розыгрышам.

        Статистика по каждому розыгрышу:
        - ID розыгрыша
        - Описание
        - Дата начала / окончания
        - Количество участников
        - Количество победителей
        - Новых пользователей
        - Статус
        """
        if not self.spreadsheet:
            return False

        try:
            headers = [
                "ID",
                "Description",
                "Start (MSK)",
                "End (MSK)",
                "Duration (days)",
                "Total Participants",
                "Winners Count",
                "New Users",
                "Status",
                "Created At (MSK)",
                "Created By Admin",
            ]

            rows = []

            for g in giveaways_data:
                # Форматирование дат
                start_at = g.get("start_at")
                end_at = g.get("end_at")

                start_msk = _fmt_dt(start_at)
                end_msk = _fmt_dt(end_at)
                created_msk = _fmt_dt(g.get("created_at"))

                # Длительность
                if isinstance(start_at, datetime) and isinstance(end_at, datetime):
                    duration: int | str = (end_at - start_at).days
                else:
                    duration = ""

                # Статус
                status = "Активен" if g.get("is_active") else "Завершен"

                # Описание (ограничиваем 50 символами для таблицы)
                description = g.get("description", "")
                if len(description) > 50:
                    description = description[:47] + "..."

                rows.append(
                    [
                        g.get("id", ""),
                        description,
                        start_msk,
                        end_msk,
                        duration,
                        g.get("participants_count", 0),
                        g.get("winners_count", 0),
                        g.get("new_users_count", 0),
                        status,
                        created_msk,
                        g.get("created_by_admin_id", ""),
                    ]
                )

            count = self._rewrite("Giveaways Summary", headers, rows)
            logger.info(f"Синхронизировано розыгрышей в сводную таблицу: {count}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации сводной таблицы: {e}", exc_info=True)
            return False


async def sync_all_data() -> bool:
    """Полная синхронизация всех данных."""
    from bot.config.settings import get_settings
    from bot.db.base import get_session
    from bot.db.repo import user_repo

    settings = get_settings()

    # Проверяем настройки
    if not settings.sheets_sync_enabled:
        logger.info("Google Sheets синхронизация отключена (SHEETS_SYNC_ENABLED=false)")
        return False

    if not settings.google_credentials_path or not settings.spreadsheet_id:
        logger.warning("Отсутствуют credentials для Google Sheets")
        return False

    if not SHEETS_AVAILABLE:
        logger.warning("Google Sheets библиотеки не установлены")
        return False

    try:
        # gspread синхронный — выносим в поток, чтобы не блокировать event loop бота.
        import asyncio

        sync = SheetsSync(settings.google_credentials_path, settings.spreadsheet_id)
        if not await asyncio.to_thread(sync.connect):
            return False

        # Получаем данные из БД
        async with get_session() as session:
            # Пользователи
            users = await user_repo.get_all_users(session)
            users_data = [{"user_id": u.user_id, "username": u.username, "joined_at": u.joined_at} for u in users]

            # Участники с датами розыгрышей
            from sqlalchemy import func, select

            from bot.db.models import Giveaway, Participant

            result = await session.execute(
                select(Participant, Giveaway.start_at, Giveaway.end_at)
                .join(Giveaway, Participant.giveaway_id == Giveaway.id)
            )
            participants_rows = result.all()
            participants_data = [
                {
                    "giveaway_id": p.giveaway_id,
                    "user_id": p.user_id,
                    "username_snapshot": p.username_snapshot,
                    "joined_at": p.joined_at,
                    "giveaway_start": start_at,
                    "giveaway_end": end_at,
                }
                for p, start_at, end_at in participants_rows
            ]

            # Победители
            from bot.db.models import Winner

            result = await session.execute(select(Winner))
            winners = result.scalars().all()
            winners_data = [
                {
                    "giveaway_id": w.giveaway_id,
                    "user_id": w.user_id,
                    "username_snapshot": w.username_snapshot,
                    "created_at": w.created_at,
                }
                for w in winners
            ]

            # Розыгрыши со статистикой
            from bot.db.models import User

            result = await session.execute(select(Giveaway))
            giveaways = result.scalars().all()

            # Счётчики участников/победителей одним запросом каждый (без N+1).
            part_counts = dict(
                (
                    await session.execute(
                        select(Participant.giveaway_id, func.count()).group_by(Participant.giveaway_id)
                    )
                ).all()
            )
            win_counts = dict(
                (
                    await session.execute(
                        select(Winner.giveaway_id, func.count()).group_by(Winner.giveaway_id)
                    )
                ).all()
            )

            giveaways_data = []
            for g in giveaways:
                # Новые пользователи в окне розыгрыша зависят от диапазона дат — отдельный запрос.
                new_users_count = await session.scalar(
                    select(func.count()).select_from(User)
                    .where(User.joined_at >= g.start_at)
                    .where(User.joined_at <= g.end_at)
                )

                participants_count = part_counts.get(g.id, 0)
                winners_count = win_counts.get(g.id, 0)

                giveaways_data.append({
                    "id": g.id,
                    "description": g.description,
                    "start_at": g.start_at,
                    "end_at": g.end_at,
                    "is_active": g.is_active,
                    "created_at": g.created_at,
                    "created_by_admin_id": g.created_by_admin_id,
                    "participants_count": participants_count or 0,
                    "winners_count": winners_count or 0,
                    "new_users_count": new_users_count or 0,
                })

        # Синхронизация (блокирующие вызовы gspread — в отдельном потоке)
        await asyncio.to_thread(sync.sync_users, users_data)
        await asyncio.to_thread(sync.sync_participants, participants_data)
        await asyncio.to_thread(sync.sync_winners, winners_data)
        await asyncio.to_thread(sync.sync_giveaways_summary, giveaways_data)

        logger.info("Полная синхронизация с Google Sheets завершена")
        return True

    except Exception as e:
        logger.error(f"Ошибка синхронизации с Google Sheets: {e}", exc_info=True)
        return False
