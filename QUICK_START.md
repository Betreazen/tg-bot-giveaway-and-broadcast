# Быстрый старт (5 минут)

Минимальные шаги для запуска бота. Вся конфигурация — в одном файле `.env`.
Схема БД создаётся автоматически при старте (Alembic-миграции), отдельных команд
не требуется.

## ⚡ Перед началом

Установлены:
- ✅ Docker
- ✅ Docker Compose

## 🚀 Шаги

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Betreazen/tg-bot-giveaway-and-broadcast.git
cd tg-bot-giveaway-and-broadcast
```

### 2. Создайте и заполните `.env`

```bash
cp .env.example .env
```

Заполните **обязательные** параметры:

```env
# Уникальное имя стека (чтобы не конфликтовать с другими ботами на сервере)
COMPOSE_PROJECT_NAME=giveaway_bot

BOT_TOKEN=ваш_токен_от_botfather
ADMIN_IDS=ваш_telegram_id            # можно несколько через запятую
CHANNEL_ID=-100ваш_id_канала
JOIN_URL=https://t.me/ваш_бот?start=join

# Пароль БД — задайте свой и продублируйте его в DATABASE_URL
POSTGRES_PASSWORD=придумайте_пароль
DATABASE_URL=postgresql+asyncpg://giveaway_user:придумайте_пароль@postgres:5432/giveaway_bot
```

**Как получить:**
- `BOT_TOKEN` — у [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` — свой ID у [@userinfobot](https://t.me/userinfobot)
- `CHANNEL_ID` — перешлите сообщение из канала [@userinfobot](https://t.me/userinfobot).
  **Бот должен быть администратором канала** (для проверки подписки и анонсов).

> ⏰ Всё время в боте отображается по Москве (МСК, GMT+3) независимо от часового
> пояса сервера — настраивать ничего не нужно.

### 3. Запустите

```bash
docker compose up -d --build
```

Контейнер сам применит миграции (`alembic upgrade head`) и запустит бота.
Postgres и Redis поднимутся рядом и **не торчат портами на хост** — конфликтов
с другими ботами на сервере не будет.

### 4. Проверьте логи

```bash
docker compose logs -f bot
```

Должно появиться:
```
Running database migrations...
Bot started successfully!
Run polling for bot @ваш_бот
```

### 5. Тестируйте

1. Напишите боту `/start`
2. Напишите `/admin` (только для ID из `ADMIN_IDS`) — создание розыгрыша, анонс,
   завершение, выбор победителей, рассылка.

## 📊 Google Sheets (опционально)

Сам приватный ключ в `.env` не хранится — это отдельный файл, на который `.env`
лишь указывает:

1. Положите `service_account.json` рядом с `docker-compose.yml`.
2. В `.env`:
   ```env
   SHEETS_SYNC_ENABLED=true
   GOOGLE_CREDENTIALS_PATH=/app/service_account.json
   SPREADSHEET_ID=id_вашей_таблицы
   ```
3. В `docker-compose.yml` раскомментируйте строку монтирования:
   ```yaml
   - ./service_account.json:/app/service_account.json:ro
   ```
4. Дайте сервис-аккаунту (`client_email` из JSON) доступ **«Редактор»** к таблице.
5. `docker compose up -d --build`

Синхронизация запускается кнопкой в админ-панели.

## 🛑 Управление

```bash
docker compose down          # остановить (данные БД сохраняются)
docker compose down -v       # остановить и удалить данные БД
docker compose restart bot   # перезапустить только бота
docker compose up -d --build # применить изменения кода/конфига
```

## 🔄 Обновление сервера с существующей БД

Безопасный накат миграций без потери данных — см. [DEPLOY.md](DEPLOY.md)
(не забудьте `pg_dump` перед обновлением).

## ❓ Проблемы?

1. Логи: `docker compose logs bot`
2. Проверьте, что `.env` заполнен и пароль в `DATABASE_URL` совпадает с `POSTGRES_PASSWORD`
3. Убедитесь, что бот — администратор канала
