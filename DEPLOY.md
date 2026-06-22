# Деплой и обновление

Вся конфигурация — в одном файле `.env`. Схема БД управляется Alembic-миграциями,
которые применяются автоматически при старте контейнера (`alembic upgrade head`
в [docker-entrypoint.sh](docker-entrypoint.sh)).

## 1. Первый запуск (чистый сервер)

```bash
cp .env.example .env
nano .env                 # заполнить BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, JOIN_URL,
                          # POSTGRES_PASSWORD, DATABASE_URL, COMPOSE_PROJECT_NAME
docker compose up -d --build
```

При первом старте Alembic создаст все таблицы. Готово.

## 2. Обновление сервера, где УЖЕ есть БД с данными

> Главное: данные не теряются. Начальная миграция идемпотентна — если таблицы
> уже существуют, она ничего не пересоздаёт, а только помечает БД как
> «версионированную». Поэтому отдельный `alembic stamp` вручную не нужен.

Рекомендуемый порядок:

```bash
# 0. БЭКАП (обязательно перед любым обновлением)
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%F).sql

# 1. Забрать новый код
git pull

# 2. Перенести настройки из старого config.json в .env (см. .env.example):
#    join_url -> JOIN_URL, sheets_sync.enabled -> SHEETS_SYNC_ENABLED,
#    rate_limits.* -> BROADCAST_RPS / ANNOUNCE_RPS / MAX_RETRIES
#    (timezone больше не нужен — время всегда московское, МСК)
nano .env

# 3. Пересобрать и перезапустить. Entrypoint сам применит миграции.
docker compose up -d --build
```

Проверить, что миграции прошли и бот поднялся:

```bash
docker compose logs -f bot      # ждём "Running database migrations..." -> "Starting bot..."
docker compose exec bot alembic current
```

## 3. Будущие изменения схемы БД

Меняем модели в [bot/db/models.py](bot/db/models.py), затем:

```bash
# сгенерировать миграцию (локально, с поднятой БД)
docker compose exec bot alembic revision --autogenerate -m "describe change"
# проверить сгенерированный файл в bot/migrations/versions/, затем задеплоить —
# upgrade применится автоматически при следующем старте.
```

## Изоляция от других ботов на сервере

- `COMPOSE_PROJECT_NAME` в `.env` задаёт префикс контейнеров/томов/сети — у каждого
  бота он свой, поэтому пересечений нет.
- Postgres и Redis **не публикуются** на хост (нет проброса портов) — конфликтов
  портов с другими ботами не будет. Если доступ с хоста всё же нужен, раскомментируй
  `ports` в [docker-compose.yml](docker-compose.yml) и задай свободный
  `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT`.
- `REDIS_FSM_PREFIX` изолирует FSM-ключи, если несколько ботов смотрят в один Redis.

## Google Sheets (опционально)

1. Положить `service_account.json` рядом с `docker-compose.yml`.
2. Раскомментировать строку монтирования `service_account.json` в compose.
3. В `.env`: `SHEETS_SYNC_ENABLED=true`, `GOOGLE_CREDENTIALS_PATH=/app/service_account.json`,
   `SPREADSHEET_ID=...`.
