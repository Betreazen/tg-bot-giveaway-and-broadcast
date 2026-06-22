# Подробная инструкция по установке и настройке

Этот документ содержит полное пошаговое руководство по развертыванию Telegram Giveaway Bot на сервере Ubuntu Linux с использованием Docker.

## 📋 Содержание

1. [Системные требования](#системные-требования)
2. [Предварительная подготовка](#предварительная-подготовка)
3. [Установка на сервер](#установка-на-сервер)
4. [Настройка бота](#настройка-бота)
5. [Запуск и проверка](#запуск-и-проверка)
6. [Обслуживание](#обслуживание)
7. [Обновление бота](#обновление-бота)
8. [Решение проблем](#решение-проблем)

## 🖥 Системные требования

### Минимальные требования

| Компонент | Требование |
|-----------|------------|
| ОС | Ubuntu 20.04 LTS или новее |
| CPU | 1 ядро |
| RAM | 1 GB |
| Диск | 5 GB свободного места |
| Docker | 20.10+ |
| Docker Compose | 2.0+ |

### Рекомендуемые требования для продакшена

| Компонент | Требование |
|-----------|------------|
| ОС | Ubuntu 22.04 LTS |
| CPU | 2 ядра |
| RAM | 2 GB |
| Диск | 20 GB SSD |

## 🔧 Предварительная подготовка

### Шаг 1: Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "My Giveaway Bot")
   - Введите username бота (должен заканчиваться на `bot`, например: `my_giveaway_bot`)
4. Сохраните полученный **BOT_TOKEN** (например: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Важно:** Никогда не публикуйте токен бота!

### Шаг 2: Получение ID канала

1. Создайте канал в Telegram (если еще нет)
2. Добавьте вашего бота в канал как администратора
3. Добавьте бота [@userinfobot](https://t.me/userinfobot) в канал
4. Перешлите любое сообщение из канала боту @userinfobot
5. Он ответит с информацией, найдите строку "Forwarded from chat" - это **CHANNEL_ID**
6. Пример ID: `-1001234567890` (всегда начинается с `-100`)

Альтернативный способ:
1. Откройте канал в браузере
2. ID будет в URL после `https://t.me/c/` (добавьте `-100` в начало)

### Шаг 3: Получение ID администраторов

Способ 1 - через [@userinfobot](https://t.me/userinfobot):
1. Отправьте любое сообщение боту
2. Он ответит с вашим ID

Способ 2 - через [@raw_data_bot](https://t.me/raw_data_bot):
1. Отправьте `/start` боту
2. Найдите строку `"id": 123456789` - это ваш ID

Если администраторов несколько, соберите все ID через запятую: `123456789,987654321,555666777`

## 🚀 Установка на сервер

### Шаг 1: Подключение к серверу

```bash
ssh user@your-server-ip
```

### Шаг 2: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 3: Установка Docker

```bash
# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление репозитория Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker + плагина Compose v2
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Проверка установки
docker --version
docker compose version
```

### Шаг 4: (Compose устанавливается вместе с Docker)

Современный Docker включает плагин Compose v2 — команда `docker compose`
(без дефиса). Отдельно ставить ничего не нужно.

### Шаг 5: Добавление пользователя в группу Docker (опционально)

```bash
sudo usermod -aG docker $USER
```

После этого нужно перелогиниться:
```bash
exit
# Подключитесь заново
ssh user@your-server-ip
```

### Шаг 6: Клонирование проекта

```bash
# Создание директории для проекта
mkdir -p ~/bots
cd ~/bots

# Клонирование репозитория
git clone https://github.com/Betreazen/tg-bot-giveaway-and-broadcast.git
cd tg-bot-giveaway-and-broadcast
```

## ⚙️ Настройка бота

### Шаг 1: Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните файл своими данными (вся конфигурация — здесь; отдельный `config.json`
больше не используется):

```env
# ===========================================
# ИЗОЛЯЦИЯ (уникальное имя стека на сервере)
# ===========================================
COMPOSE_PROJECT_NAME=giveaway_bot

# ===========================================
# ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
# ===========================================
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321            # через запятую, без пробелов
CHANNEL_ID=-1001234567890                # начинается с -100; бот — админ канала
JOIN_URL=https://t.me/YOUR_BOT_USERNAME?start=join

# ===========================================
# БАЗА ДАННЫХ (задайте свой пароль и продублируйте его в DATABASE_URL)
# ===========================================
POSTGRES_USER=giveaway_user
POSTGRES_PASSWORD=придумайте_сложный_пароль
POSTGRES_DB=giveaway_bot
DATABASE_URL=postgresql+asyncpg://giveaway_user:придумайте_сложный_пароль@postgres:5432/giveaway_bot

# ===========================================
# REDIS (можно не менять; префикс изолирует FSM-ключи)
# ===========================================
REDIS_URL=redis://redis:6379/0
REDIS_FSM_PREFIX=giveaway_fsm

# ===========================================
# ПОВЕДЕНИЕ (лимиты рассылки в сообщениях/сек)
# ===========================================
BROADCAST_RPS=20
ANNOUNCE_RPS=20
MAX_RETRIES=5

# ===========================================
# GOOGLE SHEETS (опционально)
# ===========================================
SHEETS_SYNC_ENABLED=false
# GOOGLE_CREDENTIALS_PATH=/app/service_account.json
# SPREADSHEET_ID=your_spreadsheet_id

# ===========================================
# ЛОГИРОВАНИЕ / SENTRY (опционально)
# ===========================================
LOG_LEVEL=INFO
# SENTRY_DSN=your_sentry_dsn
```

Сохраните файл: `Ctrl+O`, `Enter`, `Ctrl+X`

> ⏰ Время в боте всегда московское (МСК, GMT+3) независимо от часового пояса
> сервера — настраивать не нужно.

> 🗄 Схема БД создаётся/обновляется автоматически при старте контейнера
> (Alembic-миграции в [docker-entrypoint.sh](docker-entrypoint.sh)). Отдельных
> команд запускать не требуется.

### Шаг 2: Настройка Google Sheets (опционально)

Если хотите синхронизировать данные с Google Sheets:

#### 2.1 Создание Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API:
   - APIs & Services → Library
   - Найдите "Google Sheets API"
   - Нажмите "Enable"
4. Создайте Service Account:
   - IAM & Admin → Service Accounts
   - Create Service Account
   - Укажите имя и описание
   - Нажмите "Create and Continue"
   - Skip роли и permissions
   - Нажмите "Done"
5. Создайте ключ:
   - Нажмите на созданный Service Account
   - Keys → Add Key → Create new key
   - Выберите JSON
   - Скачайте файл

#### 2.2 Загрузка ключа на сервер

```bash
# На вашем компьютере (в той же директории где service_account.json)
scp service_account.json user@your-server-ip:~/bots/tg-bot-giveaway-and-broadcast/
```

#### 2.3 Настройка Google Sheets

1. Создайте новую Google Таблицу
2. Нажмите "Поделиться"
3. Добавьте email из service_account.json (например: `bot@project.iam.gserviceaccount.com`)
4. Дайте права "Редактор"
5. Скопируйте ID таблицы из URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```

#### 2.4 Обновление конфигурации

В `.env` включите синхронизацию:
```env
SHEETS_SYNC_ENABLED=true
GOOGLE_CREDENTIALS_PATH=/app/service_account.json
SPREADSHEET_ID=ваш_id_таблицы
```

В `docker-compose.yml` раскомментируйте строку монтирования:
```yaml
- ./service_account.json:/app/service_account.json:ro
```

Синхронизация запускается кнопкой в админ-панели.

## 🎬 Запуск и проверка

### Шаг 1: Создание директории для логов

```bash
mkdir -p logs
```

### Шаг 2: Сборка и запуск

```bash
# Сборка и запуск в фоне (entrypoint сам применит миграции БД)
docker compose up -d --build
```

### Шаг 3: Проверка статуса

```bash
docker compose ps
# Должно быть 3 сервиса: bot, postgres, redis (имена с префиксом из
# COMPOSE_PROJECT_NAME, например giveaway_bot-bot-1). Порты БД на хост не торчат.
```

### Шаг 4: Проверка логов

```bash
docker compose logs -f bot   # Ctrl+C для выхода
```

Должны увидеть:
```
Running database migrations...
Bot started successfully!
Run polling for bot @ваш_бот
```

### Шаг 5: Тестирование бота

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте `/start` - должно прийти сообщение о подписке на канал
4. Подпишитесь на канал
5. Снова отправьте `/start` - появится сообщение с верификацией и 5 кнопками
6. Нажмите на указанное число - должно прийти подтверждение участия
7. Отправьте `/admin` - должна открыться админ-панель

> ℹ️ Администраторы регистрируются без верификации. Обычные пользователи должны пройти CAPTCHA (нажать правильную кнопку).

### Шаг 6: Создание тестового розыгрыша

В админ-панели:
1. Нажмите "✅ Создать розыгрыш"
2. Выберите время начала: "Сейчас"
3. Выберите длительность: "1 день"
4. Введите описание: "Тестовый розыгрыш"
5. Введите количество победителей: 1
6. Отправьте фото для анонса
7. Подтвердите создание
8. Выберите куда отправить анонс

## 🔄 Обслуживание

### Просмотр логов

```bash
# Логи бота
docker compose logs -f bot

# Логи PostgreSQL
docker compose logs -f postgres

# Логи Redis
docker compose logs -f redis

# Все логи вместе
docker compose logs -f
```

### Перезапуск бота

```bash
# Перезапуск только бота
docker compose restart bot

# Перезапуск всех сервисов
docker compose restart
```

### Остановка бота

```bash
# Остановка
docker compose stop

# Остановка и удаление контейнеров (данные сохраняются)
docker compose down

# Остановка и удаление всего включая данные (осторожно!)
docker compose down -v
```

### Просмотр использования ресурсов

```bash
docker stats
```

### Резервное копирование базы данных

```bash
# Создание бэкапа
docker compose exec postgres pg_dump -U giveaway_user giveaway_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
docker compose exec -T postgres psql -U giveaway_user giveaway_bot < backup_20260104_120000.sql
```

## 🔄 Обновление бота

> ⚠️ Перед обновлением сервера с данными — **обязательно сделайте бэкап БД**
> (см. ниже). Подробный безопасный сценарий — в [DEPLOY.md](DEPLOY.md).

### Обновление кода

```bash
# Бэкап БД перед обновлением
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%F).sql

# Получение обновлений и пересборка
git pull
docker compose up -d --build

# Миграции применятся автоматически при старте контейнера.
# Проверка логов:
docker compose logs -f bot
```

### Обновление конфигурации

```bash
# Вся конфигурация в .env
nano .env

# Применить изменения
docker compose up -d
```

### Обновление зависимостей

```bash
# Если обновился requirements.txt
docker compose build --no-cache bot
docker compose up -d bot
```

## 🐛 Решение проблем

### Бот не запускается

**Проблема:** Контейнер `giveaway_bot` постоянно перезапускается

**Решение:**
```bash
# Проверьте логи
docker compose logs bot

# Частые причины:
# 1. Неверный BOT_TOKEN - проверьте .env
# 2. Неверный DATABASE_URL - проверьте что postgres запущен
# 3. Неверный формат ADMIN_IDS - должны быть числа через запятую
```

### Ошибка подключения к базе данных

**Проблема:** `could not connect to server: Connection refused`

**Решение:**
```bash
# Проверьте что postgres запущен
docker compose ps postgres

# Подождите 10-15 секунд после запуска
docker compose up -d
sleep 15
docker compose logs bot
```

### Бот не отвечает на команды

**Проблема:** Бот онлайн, но не реагирует на `/start` или `/admin`

**Решение:**
```bash
# Проверьте что бот не запущен в режиме webhook
# Наш бот использует polling (long polling)

# Перезапустите бота
docker compose restart bot

# Убедитесь что отправляете команды боту в ЛС, а не в группах
```

### Google Sheets не синхронизируется

**Проблема:** Данные не появляются в таблице

**Решение:**
```bash
# 1. Проверьте логи
docker compose logs bot | grep -i sheets

# 2. Убедитесь что service_account.json смонтирован
docker compose exec bot ls -la /app/service_account.json

# 3. Проверьте что Service Account имеет доступ "Редактор" к таблице
# Откройте таблицу → Поделиться → проверьте email (client_email) из service_account.json

# 4. Проверьте, что в .env включена синхронизация
grep -E "SHEETS_SYNC_ENABLED|SPREADSHEET_ID" .env
```

### Ошибка "Update is not handled"

**Проблема:** В логах много сообщений "Update ... is not handled"

**Решение:**
```bash
# Это нормально для сообщений/действий которые бот не обрабатывает
# Например, если пользователь отправил стикер или голосовое

# Если ошибки на inline-кнопках:
# 1. Перезапустите бота
docker compose restart bot

# 2. Очистите состояние FSM в Redis (осторожно!)
docker compose exec redis redis-cli FLUSHDB
```

### Высокое использование памяти

**Проблема:** Контейнер бота использует много RAM

**Решение:**
```bash
# Проверка использования
docker stats giveaway_bot

# Если > 500MB:
# 1. Проверьте что нет утечек памяти в логах
docker compose logs bot | grep -i "memory\|leak"

# 2. Ограничьте память для контейнера
# В docker-compose.yml добавьте:
# services:
#   bot:
#     mem_limit: 512m
```

### Не работают кнопки навигации

**Проблема:** Кнопки "Назад", "Отмена" не работают

**Решение:**
```bash
# Эта проблема уже исправлена в текущей версии
# Убедитесь что используете последнюю версию:
git pull
docker compose build bot
docker compose up -d bot
```

## 📊 Мониторинг

### Проверка здоровья сервисов

```bash
# Проверка что все сервисы healthy
docker compose ps

# Ручная проверка PostgreSQL
docker compose exec postgres pg_isready -U giveaway_user

# Ручная проверка Redis
docker compose exec redis redis-cli ping
```

### Статистика бота

Посмотреть статистику можно в админ-панели через кнопку "📊 Статус"

### Логи для анализа

```bash
# Количество пользователей (примерно)
docker compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT COUNT(*) FROM users;"

# Количество активных розыгрышей
docker compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT COUNT(*) FROM giveaways WHERE is_active=true;"

# Количество участников в текущем розыгрыше
docker compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT g.id, g.description, COUNT(p.id) FROM giveaways g LEFT JOIN participants p ON g.id=p.giveaway_id WHERE g.is_active=true GROUP BY g.id;"
```

## 🔐 Безопасность

### Обязательные меры

1. **Смените пароль PostgreSQL в продакшене**

Пароль задаётся только в `.env` (compose берёт его оттуда):
```env
POSTGRES_PASSWORD=ваш_сложный_пароль_здесь
DATABASE_URL=postgresql+asyncpg://giveaway_user:ваш_сложный_пароль_здесь@postgres:5432/giveaway_bot
```

2. **Порты PostgreSQL и Redis**

По умолчанию они **не публикуются** на хост (в `docker-compose.yml` проброс
портов закомментирован) — отдельно закрывать ничего не нужно.

3. **Настройте файрвол**

```bash
# Разрешите только SSH и необходимые порты
sudo ufw allow 22/tcp
sudo ufw enable
```

4. **Регулярно обновляйте систему**

```bash
sudo apt update && sudo apt upgrade -y
docker compose pull
docker compose up -d
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте этот документ
2. Изучите логи: `docker compose logs -f bot`
3. Создайте Issue на GitHub с описанием проблемы и логами

---

**Готово!** Ваш бот для розыгрышей настроен и готов к работе! 🎉
