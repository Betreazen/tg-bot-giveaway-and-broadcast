# Руководство по публикации проекта на GitHub

Этот документ содержит пошаговые инструкции для публикации проекта как шаблона на GitHub.

## ✅ Подготовка завершена

Проект полностью подготовлен к публикации. Выполнены следующие действия:

### 🗑️ Удалено
- ❌ Все временные документы с исправлениями (FIXES_*.md, DUPLICATION_*.md и т.д.)
- ❌ Старый quickstart.md

### ✨ Добавлено
- ✅ **README.md** / **QUICK_START.md** - главная страница и быстрый старт
- ✅ **SETUP.md** / **DEPLOY.md** - установка и безопасный деплой/обновление БД
- ✅ **CONTRIBUTING.md** - руководство для разработчиков
- ✅ **CHANGELOG.md** - история изменений проекта
- ✅ **LICENSE** - MIT лицензия
- ✅ **.dockerignore** - оптимизация Docker сборки
- ✅ **Alembic** (`alembic.ini`, `bot/migrations/`) - миграции БД
- ✅ **tests/** + **requirements-dev.txt** - тесты (pytest) и dev-зависимости
- ✅ Обновленный **.gitignore** - исключает `.env`, `service_account.json`, секреты

### 🔧 Обновлено
- ✅ **Вся конфигурация в `.env`** - отдельный `config.json` удалён
- ✅ **docker-compose.yml** - изоляция (префиксы, без проброса портов),
  `service_account.json` монтируется опционально
- ✅ **docker-entrypoint.sh** - автоматический накат миграций перед запуском
- ✅ **.env.example** - единый актуальный пример конфигурации

## 📝 Шаги для публикации на GitHub

### Шаг 1: Финальная проверка

Убедитесь что в проекте НЕТ секретных данных:

```bash
# Проверьте что эти файлы НЕ добавлены в Git
git status

# Должны быть проигнорированы:
# - .env
# - service_account.json
# - docker-compose.override.yml
# - logs/
```

### Шаг 2: Коммит изменений

```bash
# Добавьте все изменения
git add .

# Создайте коммит
git commit -m "chore: Prepare project for GitHub publication

- Add comprehensive README, QUICK_START, SETUP, DEPLOY, CONTRIBUTING guides
- Add LICENSE (MIT) and CHANGELOG
- Update .gitignore and .dockerignore
- Single-file .env config + Alembic migrations + tests
- Make service_account.json (Google Sheets) optional"
```

### Шаг 3: Создание репозитория на GitHub

1. Перейдите на https://github.com/
2. Нажмите "New repository"
3. Заполните информацию:
   - **Repository name**: `tg-bot-giveaway-and-broadcast`
   - **Description**: `Professional Telegram bot for giveaways with full-featured admin panel on inline buttons`
   - **Visibility**: Public (или Private если хотите)
   - **НЕ** создавайте README, .gitignore, или LICENSE (у нас уже есть)
4. Нажмите "Create repository"

### Шаг 4: Подключение к GitHub

```bash
# Добавьте remote (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tg-bot-giveaway-and-broadcast.git

# Или если используете SSH
git remote add origin git@github.com:YOUR_USERNAME/tg-bot-giveaway-and-broadcast.git

# Проверьте remote
git remote -v
```

### Шаг 5: Push на GitHub

```bash
# Push в main ветку
git branch -M main
git push -u origin main
```

### Шаг 6: Настройка GitHub репозитория

После push перейдите в настройки репозитория на GitHub:

#### 6.1 Добавление описания и тегов

1. На главной странице репозитория нажмите ⚙️ (справа от About)
2. Заполните:
   - **Description**: `Professional Telegram bot for giveaways with admin panel`
   - **Website**: (если есть)
   - **Topics**: `telegram`, `bot`, `giveaway`, `python`, `aiogram`, `docker`, `postgresql`, `redis`, `asyncio`
3. Сохраните

#### 6.2 Создание Release

1. Перейдите в "Releases" → "Create a new release"
2. Заполните:
   - **Tag**: `v1.0.0`
   - **Release title**: `v1.0.0 - Initial Release`
   - **Description**: Скопируйте содержимое из CHANGELOG.md раздела [1.0.0]
3. Нажмите "Publish release"

#### 6.3 Настройка как Template Repository

1. Перейдите в Settings
2. В разделе "General" найдите "Template repository"
3. Поставьте галочку ✅ "Template repository"
4. Сохраните

Теперь пользователи смогут использовать кнопку "Use this template" для создания своих ботов!

#### 6.4 Настройка GitHub Actions (опционально)

Создайте файл `.github/workflows/ci.yml` для автоматических проверок:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Lint with ruff
        run: ruff check bot/ tests/
      - name: Run tests
        run: pytest -q
```

### Шаг 7: Обновление README с правильными ссылками

Отредактируйте README.md и замените `your-username` на ваш реальный GitHub username:

```bash
# Найдите и замените
sed -i 's/your-username/YOUR_ACTUAL_USERNAME/g' README.md CHANGELOG.md

# Или вручную отредактируйте файлы
nano README.md
nano CHANGELOG.md
```

Commit и push изменений:

```bash
git add README.md CHANGELOG.md
git commit -m "docs: Update GitHub username in documentation"
git push
```

## 🎯 Использование как Template

### Для пользователей вашего template:

1. Перейдите на страницу вашего репозитория
2. Нажмите "Use this template" → "Create a new repository"
3. Заполните данные нового репозитория
4. Clone нового репозитория:
   ```bash
   git clone https://github.com/USER/new-bot-name.git
   cd new-bot-name
   ```
5. Следуйте инструкциям из README.md и SETUP.md

## 📊 Рекомендуемая структура репозитория

После публикации ваш репозиторий должен выглядеть так:

```
tg-bot-giveaway-and-broadcast/
├── 📄 README.md / QUICK_START.md   ← Обзор и быстрый старт
├── 📄 SETUP.md / DEPLOY.md         ← Установка и деплой
├── 📄 CONTRIBUTING.md / CHANGELOG.md
├── 📄 LICENSE                       ← MIT лицензия
├── 🐳 Dockerfile / docker-compose.yml / docker-entrypoint.sh
├── 🔧 alembic.ini
├── 📋 requirements.txt / requirements-dev.txt
├── 📋 .env.example
├── 🔧 .gitignore / .dockerignore / .gitattributes
├── 🧪 tests/
└── 📁 bot/
    ├── config/settings.py          ← Конфиг из .env
    ├── db/  ├── migrations/  ├── handlers/  ├── middlewares/
    ├── keyboards/  ├── messages/  ├── services/  └── utils/
```

## ✨ Дополнительные улучшения

### Создание GitHub Topics

Добавьте топики для лучшей находимости:
- `telegram-bot`
- `giveaway`
- `contest`
- `raffle`
- `python3`
- `aiogram`
- `docker-compose`
- `postgresql`
- `redis`
- `admin-panel`

### Создание Wiki (опционально)

1. В Settings включите Wiki
2. Добавьте страницы:
   - FAQ - часто задаваемые вопросы
   - Examples - примеры использования
   - Troubleshooting - решение проблем

### Создание Issues Templates

Создайте `.github/ISSUE_TEMPLATE/` с шаблонами для:
- Bug report
- Feature request
- Question

## 🔐 Безопасность перед публикацией

**ВАЖНО!** Убедитесь что вы НЕ публикуете:

❌ **НЕ должно быть в Git:**
- `.env` файл с реальными токенами
- `service_account.json` с Google credentials
- `docker-compose.override.yml` (локальные оверрайды)
- `logs/` с реальными логами
- Любые файлы с паролями или токенами

✅ **Должно быть в Git:**
- `.env.example` с примерами
- Документация
- Исходный код без секретов

### Проверка на секреты

```bash
# Проверка что секреты не добавлены
git ls-files | grep -E '\.env$|service_account\.json'

# Должно вернуть пусто!
# Если что-то нашлось - удалите из Git:
git rm --cached .env service_account.json
git commit -m "Remove secrets from Git"
```

## 🎉 Готово!

После выполнения всех шагов ваш проект:
- ✅ Опубликован на GitHub
- ✅ Настроен как Template
- ✅ Имеет подробную документацию
- ✅ Готов к использованию другими пользователями
- ✅ Не содержит секретных данных
- ✅ Легко клонируется и настраивается

## 📣 Продвижение проекта

### Где поделиться:

1. **Reddit**:
   - r/python
   - r/telegram
   - r/selfhosted

2. **Telegram**:
   - @pythonru
   - @aiogram_live

3. **Хабр**:
   - Напишите статью о создании бота

4. **Dev.to**:
   - Поделитесь опытом разработки

---

**Поздравляем!** Ваш проект готов к публикации! 🚀
