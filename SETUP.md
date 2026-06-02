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

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Проверка установки
docker --version
```

### Шаг 4: Установка Docker Compose

```bash
# Скачивание Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Установка прав на выполнение
sudo chmod +x /usr/local/bin/docker-compose

# Проверка
docker-compose --version
```

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
git clone https://github.com/your-username/tg-bot-giveaway-and-broadcast.git
cd tg-bot-giveaway-and-broadcast
```

## ⚙️ Настройка бота

### Шаг 1: Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните файл своими данными:

```env
# ===========================================
# ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
# ===========================================

# Токен бота от @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ID администраторов (через запятую, без пробелов)
ADMIN_IDS=123456789,987654321

# ID канала (начинается с -100)
CHANNEL_ID=-1001234567890

# ===========================================
# БАЗА ДАННЫХ (можно не менять)
# ===========================================
DATABASE_URL=postgresql+asyncpg://giveaway_user:giveaway_pass@postgres:5432/giveaway_bot

# ===========================================
# REDIS (можно не менять)
# ===========================================
REDIS_URL=redis://redis:6379/0

# ===========================================
# ЛОГИРОВАНИЕ
# ===========================================
LOG_LEVEL=INFO

# ===========================================
# GOOGLE SHEETS (опционально)
# ===========================================
# GOOGLE_CREDENTIALS_PATH=/app/service_account.json
# SPREADSHEET_ID=your_spreadsheet_id

# ===========================================
# SENTRY (опционально)
# ===========================================
# SENTRY_DSN=your_sentry_dsn
```

Сохраните файл: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 2: Создание config.json

```bash
cp bot/config/config.json.example bot/config/config.json
nano bot/config/config.json
```

Измените параметры:

```json
{
  "timezone": "Europe/Moscow",
  "join_url": "https://t.me/YOUR_BOT_USERNAME?start=join",
  "rate_limits": {
    "broadcast_rps": 20,
    "announce_rps": 20,
    "burst": 5,
    "max_retries": 5
  },
  "admin_panel": {
    "items_per_page": 10
  },
  "sheets_sync": {
    "enabled": false,
    "flush_sec": 1.0,
    "max_updates": 200,
    "max_appends": 200,
    "max_deletes": 200
  }
}
```

**Важно:** Замените `YOUR_BOT_USERNAME` на username вашего бота!

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 3: Настройка Google Sheets (опционально)

Если хотите синхронизировать данные с Google Sheets:

#### 3.1 Создание Service Account

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

#### 3.2 Загрузка ключа на сервер

```bash
# На вашем компьютере (в той же директории где service_account.json)
scp service_account.json user@your-server-ip:~/bots/tg-bot-giveaway-and-broadcast/
```

#### 3.3 Настройка Google Sheets

1. Создайте новую Google Таблицу
2. Нажмите "Поделиться"
3. Добавьте email из service_account.json (например: `bot@project.iam.gserviceaccount.com`)
4. Дайте права "Редактор"
5. Скопируйте ID таблицы из URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```

#### 3.4 Обновление конфигурации

В `.env` раскомментируйте и заполните:
```env
GOOGLE_CREDENTIALS_PATH=/app/service_account.json
SPREADSHEET_ID=ваш_id_таблицы
```

В `config.json` измените:
```json
"sheets_sync": {
  "enabled": true
}
```

В `docker-compose.yml` раскомментируйте строку:
```yaml
- ./service_account.json:/app/service_account.json:ro
```

## 🎬 Запуск и проверка

### Шаг 1: Создание директории для логов

```bash
mkdir -p logs
```

### Шаг 2: Сборка и запуск

```bash
# Сборка образов
docker-compose build

# Запуск в фоновом режиме
docker-compose up -d
```

### Шаг 3: Проверка статуса

```bash
# Проверка запущенных контейнеров
docker-compose ps

# Должно быть 3 контейнера: bot, postgres, redis
```

Ожидаемый вывод:
```
NAME                     STATUS              PORTS
giveaway_bot             Up 10 seconds       
giveaway_bot_postgres    Up 10 seconds       5432/tcp
giveaway_bot_redis       Up 10 seconds       6379/tcp
```

### Шаг 4: Проверка логов

```bash
# Просмотр логов бота
docker-compose logs -f bot

# Нажмите Ctrl+C для выхода
```

Должны увидеть сообщения вроде:
```
[INFO] Подключено к Google Sheets...
[INFO] Bot started
[INFO] Polling started
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
docker-compose logs -f bot

# Логи PostgreSQL
docker-compose logs -f postgres

# Логи Redis
docker-compose logs -f redis

# Все логи вместе
docker-compose logs -f
```

### Перезапуск бота

```bash
# Перезапуск только бота
docker-compose restart bot

# Перезапуск всех сервисов
docker-compose restart
```

### Остановка бота

```bash
# Остановка
docker-compose stop

# Остановка и удаление контейнеров (данные сохраняются)
docker-compose down

# Остановка и удаление всего включая данные (осторожно!)
docker-compose down -v
```

### Просмотр использования ресурсов

```bash
docker stats
```

### Резервное копирование базы данных

```bash
# Создание бэкапа
docker-compose exec postgres pg_dump -U giveaway_user giveaway_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
docker-compose exec -T postgres psql -U giveaway_user giveaway_bot < backup_20260104_120000.sql
```

## 🔄 Обновление бота

### Обновление кода

```bash
# Остановка бота
docker-compose stop bot

# Получение обновлений
git pull

# Пересборка образа
docker-compose build bot

# Запуск
docker-compose up -d bot

# Проверка логов
docker-compose logs -f bot
```

### Обновление конфигурации

```bash
# Редактирование config.json
nano bot/config/config.json

# Перезапуск бота
docker-compose restart bot
```

### Обновление зависимостей

```bash
# Если обновился requirements.txt
docker-compose build --no-cache bot
docker-compose up -d bot
```

## 🐛 Решение проблем

### Бот не запускается

**Проблема:** Контейнер `giveaway_bot` постоянно перезапускается

**Решение:**
```bash
# Проверьте логи
docker-compose logs bot

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
docker-compose ps postgres

# Подождите 10-15 секунд после запуска
docker-compose up -d
sleep 15
docker-compose logs bot
```

### Бот не отвечает на команды

**Проблема:** Бот онлайн, но не реагирует на `/start` или `/admin`

**Решение:**
```bash
# Проверьте что бот не запущен в режиме webhook
# Наш бот использует polling (long polling)

# Перезапустите бота
docker-compose restart bot

# Убедитесь что отправляете команды боту в ЛС, а не в группах
```

### Google Sheets не синхронизируется

**Проблема:** Данные не появляются в таблице

**Решение:**
```bash
# 1. Проверьте логи
docker-compose logs bot | grep -i sheets

# 2. Убедитесь что service_account.json смонтирован
docker-compose exec bot ls -la /app/service_account.json

# 3. Проверьте что Service Account имеет доступ к таблице
# Откройте таблицу → Поделиться → Проверьте email из service_account.json

# 4. Проверьте config.json
cat bot/config/config.json | grep -A5 sheets_sync
```

### Ошибка "Update is not handled"

**Проблема:** В логах много сообщений "Update ... is not handled"

**Решение:**
```bash
# Это нормально для сообщений/действий которые бот не обрабатывает
# Например, если пользователь отправил стикер или голосовое

# Если ошибки на inline-кнопках:
# 1. Перезапустите бота
docker-compose restart bot

# 2. Очистите состояние FSM в Redis (осторожно!)
docker-compose exec redis redis-cli FLUSHDB
```

### Высокое использование памяти

**Проблема:** Контейнер бота использует много RAM

**Решение:**
```bash
# Проверка использования
docker stats giveaway_bot

# Если > 500MB:
# 1. Проверьте что нет утечек памяти в логах
docker-compose logs bot | grep -i "memory\|leak"

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
docker-compose build bot
docker-compose up -d bot
```

## 📊 Мониторинг

### Проверка здоровья сервисов

```bash
# Проверка что все сервисы healthy
docker-compose ps

# Ручная проверка PostgreSQL
docker-compose exec postgres pg_isready -U giveaway_user

# Ручная проверка Redis
docker-compose exec redis redis-cli ping
```

### Статистика бота

Посмотреть статистику можно в админ-панели через кнопку "📊 Статус"

### Логи для анализа

```bash
# Количество пользователей (примерно)
docker-compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT COUNT(*) FROM users;"

# Количество активных розыгрышей
docker-compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT COUNT(*) FROM giveaways WHERE is_active=true;"

# Количество участников в текущем розыгрыше
docker-compose exec postgres psql -U giveaway_user giveaway_bot -c "SELECT g.id, g.description, COUNT(p.id) FROM giveaways g LEFT JOIN participants p ON g.id=p.giveaway_id WHERE g.is_active=true GROUP BY g.id;"
```

## 🔐 Безопасность

### Обязательные меры

1. **Смените пароль PostgreSQL в продакшене**

В `docker-compose.yml`:
```yaml
environment:
  POSTGRES_USER: giveaway_user
  POSTGRES_PASSWORD: ваш_сложный_пароль_здесь  # Измените!
```

И в `.env`:
```env
DATABASE_URL=postgresql+asyncpg://giveaway_user:ваш_сложный_пароль_здесь@postgres:5432/giveaway_bot
```

2. **Закройте порты PostgreSQL и Redis**

В `docker-compose.yml` удалите/закомментируйте:
```yaml
# ports:
#   - "5432:5432"  # Закомментируйте эти строки
```

3. **Настройте файрвол**

```bash
# Разрешите только SSH и необходимые порты
sudo ufw allow 22/tcp
sudo ufw enable
```

4. **Регулярно обновляйте систему**

```bash
sudo apt update && sudo apt upgrade -y
docker-compose pull
docker-compose up -d
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте этот документ
2. Изучите логи: `docker-compose logs -f bot`
3. Создайте Issue на GitHub с описанием проблемы и логами

---

**Готово!** Ваш бот для розыгрышей настроен и готов к работе! 🎉
