# Руководство по внесению вклада

Спасибо за интерес к проекту! Этот документ описывает процесс внесения изменений в Telegram Giveaway Bot.

## 📋 Содержание

- [Код поведения](#код-поведения)
- [Как внести вклад](#как-внести-вклад)
- [Стандарты разработки](#стандарты-разработки)
- [Процесс разработки](#процесс-разработки)

## 🤝 Код поведения

- Будьте вежливы и уважительны
- Конструктивная критика приветствуется
- Помогайте другим участникам

## 🔧 Как внести вклад

### Сообщение об ошибках

Если вы нашли ошибку, создайте Issue с следующей информацией:

1. **Описание проблемы**: Что произошло?
2. **Как воспроизвести**: Шаги для воспроизведения ошибки
3. **Ожидаемое поведение**: Что должно было произойти?
4. **Логи**: Вывод `docker compose logs bot`
5. **Окружение**: ОС, версия Docker, версия бота

### Предложение новых функций

Создайте Issue с описанием:

1. **Что**: Краткое описание функции
2. **Зачем**: Какую проблему это решает?
3. **Как**: Предлагаемая реализация (если есть идеи)

### Pull Requests

1. Fork репозитория
2. Создайте feature branch: `git checkout -b feature/amazing-feature`
3. Внесите изменения
4. Напишите тесты (если применимо)
5. Убедитесь что код проходит линтеры
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Создайте Pull Request

## 📏 Стандарты разработки

### Стиль кода

Проект использует **ruff** для линтинга и форматирования:

```bash
# Проверка кода
ruff check bot/

# Автоматическое форматирование
ruff format bot/
```

### Соглашения об именовании

- **Файлы**: snake_case (например: `giveaway_service.py`)
- **Классы**: PascalCase (например: `GiveawayService`)
- **Функции/методы**: snake_case (например: `create_giveaway`)
- **Константы**: UPPER_SNAKE_CASE (например: `MAX_RETRIES`)

### Документация кода

```python
def create_giveaway(session: AsyncSession, description: str) -> Giveaway:
    """
    Создать новый розыгрыш.
    
    Args:
        session: Сессия базы данных
        description: Описание розыгрыша
        
    Returns:
        Созданный объект Giveaway
        
    Raises:
        ValueError: Если description пустое
    """
    pass
```

### Коммиты

Используйте понятные сообщения коммитов:

```
feat: Add winner notification feature
fix: Fix navigation back button
docs: Update setup instructions
refactor: Improve mailing service performance
test: Add tests for giveaway service
```

Типы коммитов:
- `feat`: Новая функция
- `fix`: Исправление ошибки
- `docs`: Изменения в документации
- `style`: Форматирование кода
- `refactor`: Рефакторинг
- `test`: Добавление тестов
- `chore`: Обслуживание проекта

## 🔄 Процесс разработки

### Локальная разработка

1. **Клонирование репозитория**
```bash
git clone https://github.com/Betreazen/tg-bot-giveaway-and-broadcast.git
cd tg-bot-giveaway-and-broadcast
```

2. **Настройка окружения**
```bash
cp .env.example .env
# Заполните .env (вся конфигурация — в одном файле, config.json больше нет)
```

3. **Запуск**
```bash
docker compose up -d --build   # entrypoint сам применит миграции
```
После изменений в коде пересоберите: `docker compose up -d --build`.

4. **Тесты и линтинг локально** (без Docker, нужен Python 3.12)
```bash
pip install -r requirements-dev.txt
pytest                 # все тесты
pytest --cov=bot       # с покрытием
ruff check bot/ tests/
ruff format bot/ tests/
```

### Работа с базой данных (миграции)

Схема управляется Alembic; при старте контейнера миграции применяются
автоматически (`alembic upgrade head` в [docker-entrypoint.sh](docker-entrypoint.sh)).
При изменении моделей сгенерируйте новую миграцию:

```bash
# при поднятой БД
docker compose exec bot alembic revision --autogenerate -m "Add new field"
# проверьте файл в bot/migrations/versions/ и задеплойте — upgrade применится сам
```

### Отладка

```bash
# Просмотр логов
docker compose logs -f bot

# Доступ к базе данных
docker compose exec postgres psql -U giveaway_user giveaway_bot

# Доступ к Redis
docker compose exec redis redis-cli
```

## ✅ Чеклист перед Pull Request

- [ ] Код проходит `ruff check` и `ruff format`
- [ ] Все тесты проходят
- [ ] Добавлены тесты для новой функциональности
- [ ] Обновлена документация (если нужно)
- [ ] Коммиты имеют понятные сообщения
- [ ] Pull Request имеет описание изменений

## 📝 Структура Pull Request

Хороший PR должен содержать:

### Название
`[Тип] Краткое описание`

Пример: `[Feature] Add automatic winner notification`

### Описание

```markdown
## Что изменено
- Добавлена автоматическая отправка уведомлений победителям
- Обновлена админ-панель с новой кнопкой

## Зачем
Победители теперь сразу узнают о выигрыше

## Как проверить
1. Создайте розыгрыш
2. Завершите и выберите победителей
3. Проверьте что победители получили уведомление

## Скриншоты (если применимо)
[Добавьте скриншоты]

## Связанные Issue
Closes #123
```

## 🧪 Тестирование

### Написание тестов

Тесты лежат в `tests/` (чистая логика + моки, без реальных токенов). Пример с
моками репозиториев (как в [tests/test_giveaway_service.py](tests/test_giveaway_service.py)):

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot.services.giveaway_service as gs
from bot.services.giveaway_service import select_winners


@pytest.mark.asyncio
async def test_select_winners_picks_requested_count(monkeypatch):
    parts = [SimpleNamespace(user_id=i, username_snapshot=f"u{i}") for i in range(10)]
    monkeypatch.setattr(gs.participant_repo, "get_participants", AsyncMock(return_value=parts))

    async def fake_add_winners(**kwargs):
        return [object() for _ in kwargs["user_ids"]]

    monkeypatch.setattr(gs.winner_repo, "add_winners", AsyncMock(side_effect=fake_add_winners))

    giveaway = SimpleNamespace(id=1, num_winners=3, ended_at=None, end_at=None)
    winners = await select_winners(session=None, giveaway=giveaway)
    assert len(winners) == 3
```

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретный файл
pytest tests/test_giveaway_service.py

# С покрытием
pytest --cov=bot --cov-report=html
```

## 📚 Полезные ресурсы

- [aiogram документация](https://docs.aiogram.dev/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)
- [Docker документация](https://docs.docker.com/)
- [Python Style Guide](https://peps.python.org/pep-0008/)

## ❓ Вопросы?

Если у вас есть вопросы:
1. Проверьте [README.md](README.md) и [SETUP.md](SETUP.md)
2. Поищите в существующих Issues
3. Создайте новый Issue с вопросом

---

Спасибо за вклад в проект! 🎉
