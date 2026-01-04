"""Google Sheets синхронизация (опциональная)."""

import logging
from datetime import datetime
from typing import Any

import pytz

logger = logging.getLogger(__name__)

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

    def sync_users(self, users: list[dict[str, Any]]) -> bool:
        """Синхронизация пользователей."""
        if not self.spreadsheet:
            return False

        try:
            # Получаем или создаем лист Users
            try:
                sheet = self.spreadsheet.worksheet("Users")
                sheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                sheet = self.spreadsheet.add_worksheet(title="Users", rows=1000, cols=10)

            # Заголовки
            headers = ["User ID", "Username", "Joined At (MSK)"]
            sheet.append_row(headers)

            # Данные
            moscow_tz = pytz.timezone("Europe/Moscow")
            rows = []
            for user in users:
                joined_at = user.get("joined_at")
                if joined_at and isinstance(joined_at, datetime):
                    joined_at_msk = joined_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    joined_at_msk = str(joined_at) if joined_at else ""

                rows.append([user.get("user_id", ""), user.get("username", ""), joined_at_msk])

            if rows:
                sheet.append_rows(rows)

            logger.info(f"Синхронизировано пользователей: {len(rows)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации пользователей: {e}", exc_info=True)
            return False

    def sync_participants(self, participants: list[dict[str, Any]]) -> bool:
        """Синхронизация участников розыгрышей."""
        if not self.spreadsheet:
            return False

        try:
            try:
                sheet = self.spreadsheet.worksheet("Participants")
                sheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                sheet = self.spreadsheet.add_worksheet(title="Participants", rows=1000, cols=10)

            headers = [
                "Giveaway ID",
                "User ID",
                "Username",
                "Joined At (MSK)",
                "Giveaway Start (MSK)",
                "Giveaway End (MSK)",
            ]
            sheet.append_row(headers)

            moscow_tz = pytz.timezone("Europe/Moscow")
            rows = []
            for p in participants:
                joined_at = p.get("joined_at")
                if joined_at and isinstance(joined_at, datetime):
                    joined_at_msk = joined_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    joined_at_msk = str(joined_at) if joined_at else ""

                # Даты розыгрыша
                giveaway_start = p.get("giveaway_start")
                giveaway_end = p.get("giveaway_end")

                if giveaway_start and isinstance(giveaway_start, datetime):
                    start_msk = giveaway_start.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    start_msk = str(giveaway_start) if giveaway_start else ""

                if giveaway_end and isinstance(giveaway_end, datetime):
                    end_msk = giveaway_end.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    end_msk = str(giveaway_end) if giveaway_end else ""

                rows.append(
                    [
                        p.get("giveaway_id", ""),
                        p.get("user_id", ""),
                        p.get("username_snapshot", ""),
                        joined_at_msk,
                        start_msk,
                        end_msk,
                    ]
                )

            if rows:
                sheet.append_rows(rows)

            logger.info(f"Синхронизировано участников: {len(rows)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации участников: {e}", exc_info=True)
            return False

    def sync_winners(self, winners: list[dict[str, Any]]) -> bool:
        """Синхронизация победителей."""
        if not self.spreadsheet:
            return False

        try:
            try:
                sheet = self.spreadsheet.worksheet("Winners")
                sheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                sheet = self.spreadsheet.add_worksheet(title="Winners", rows=1000, cols=10)

            headers = ["Giveaway ID", "User ID", "Username", "Selected At (MSK)"]
            sheet.append_row(headers)

            moscow_tz = pytz.timezone("Europe/Moscow")
            rows = []
            for w in winners:
                created_at = w.get("created_at")
                if created_at and isinstance(created_at, datetime):
                    created_at_msk = created_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                else:
                    created_at_msk = str(created_at) if created_at else ""

                rows.append(
                    [
                        w.get("giveaway_id", ""),
                        w.get("user_id", ""),
                        w.get("username_snapshot", ""),
                        created_at_msk,
                    ]
                )

            if rows:
                sheet.append_rows(rows)

            logger.info(f"Синхронизировано победителей: {len(rows)}")
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
            try:
                sheet = self.spreadsheet.worksheet("Giveaways Summary")
                sheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                sheet = self.spreadsheet.add_worksheet(title="Giveaways Summary", rows=1000, cols=15)

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
            sheet.append_row(headers)

            moscow_tz = pytz.timezone("Europe/Moscow")
            rows = []
            
            for g in giveaways_data:
                # Форматирование дат
                start_at = g.get("start_at")
                end_at = g.get("end_at")
                created_at = g.get("created_at")

                if start_at and isinstance(start_at, datetime):
                    start_msk = start_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    start_msk = str(start_at) if start_at else ""

                if end_at and isinstance(end_at, datetime):
                    end_msk = end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    end_msk = str(end_at) if end_at else ""

                if created_at and isinstance(created_at, datetime):
                    created_msk = created_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M")
                else:
                    created_msk = str(created_at) if created_at else ""

                # Длительность
                if start_at and end_at and isinstance(start_at, datetime) and isinstance(end_at, datetime):
                    duration = (end_at - start_at).days
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

            if rows:
                sheet.append_rows(rows)

            logger.info(f"Синхронизировано розыгрышей в сводную таблицу: {len(rows)}")
            return True

        except Exception as e:
            logger.error(f"Ошибка синхронизации сводной таблицы: {e}", exc_info=True)
            return False


async def sync_all_data() -> bool:
    """Полная синхронизация всех данных."""
    from bot.config.settings import get_settings
    from bot.db.base import get_session
    from bot.db.repo import participant_repo, user_repo, winner_repo

    settings = get_settings()

    # Проверяем настройки
    if not settings.app_config or not settings.app_config.sheets_sync.enabled:
        logger.info("Google Sheets синхронизация отключена в конфиге")
        return False

    if not settings.google_credentials_path or not settings.spreadsheet_id:
        logger.warning("Отсутствуют credentials для Google Sheets")
        return False

    if not SHEETS_AVAILABLE:
        logger.warning("Google Sheets библиотеки не установлены")
        return False

    try:
        # Инициализация
        sync = SheetsSync(settings.google_credentials_path, settings.spreadsheet_id)
        if not sync.connect():
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
            result = await session.execute(select(Giveaway))
            giveaways = result.scalars().all()
            
            giveaways_data = []
            for g in giveaways:
                # Подсчет участников
                participants_count = await session.scalar(
                    select(func.count()).select_from(Participant).where(Participant.giveaway_id == g.id)
                )
                
                # Подсчет победителей
                winners_count = await session.scalar(
                    select(func.count()).select_from(Winner).where(Winner.giveaway_id == g.id)
                )
                
                # Подсчет новых пользователей (присоединившихся во время розыгрыша)
                from bot.db.models import User
                new_users_count = await session.scalar(
                    select(func.count()).select_from(User)
                    .where(User.joined_at >= g.start_at)
                    .where(User.joined_at <= g.end_at)
                )
                
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

        # Синхронизация
        sync.sync_users(users_data)
        sync.sync_participants(participants_data)
        sync.sync_winners(winners_data)
        sync.sync_giveaways_summary(giveaways_data)

        logger.info("Полная синхронизация с Google Sheets завершена")
        return True

    except Exception as e:
        logger.error(f"Ошибка синхронизации с Google Sheets: {e}", exc_info=True)
        return False
