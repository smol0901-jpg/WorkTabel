# WorkTable — Система управления питанием

Веб-приложение для управления питанием в общепите с интеграцией Telegram бота.

## 🚀 Быстрый старт

### 1. Supabase (База данных)

1. Создайте проект на [supabase.com](https://supabase.com)
2. Откройте **SQL Editor**
3. Скопируйте содержимое файла `supabase/migration.sql` и выполните
4. Скопируйте **Project URL** и **anon public key** из Settings → API

### 2. Веб-приложение

```bash
# Клонирование
git clone https://github.com/smol0901-jpg/WorkTabel.git
cd WorkTabel

# Установка зависимостей
npm install

# Настройка переменных
cp .env.example .env
# Отредактируйте .env с вашими данными Supabase

# Запуск локально
npm run dev
```

### 3. Деплой на Netlify

1. Подключите репозиторий к [Netlify](https://netlify.com)
2. В настройках добавьте переменные:
   - `VITE_SUPABASE_URL` = ваш-url
   - `VITE_SUPABASE_ANON_KEY` = ваш-ключ
3. Деплой произойдёт автоматически

### 4. Telegram Бот

```bash
cd bot

# Установка зависимостей
pip install -r requirements.txt

# Настройка
cp ../scripts/.env.example .env
# Отредактируйте .env

# Запуск
python3 bot.py
```

## 📁 Структура проекта

```
WorkTable/
├── src/                    # React приложение
│   ├── pages/             # Страницы
│   │   ├── Login.jsx      # Вход/регистрация
│   │   ├── Dashboard.jsx  # Главная
│   │   ├── Menu.jsx       # Меню
│   │   ├── Orders.jsx     # Заказы
│   │   └── Admin.jsx      # Админ-панель
│   ├── lib/supabase.js    # Подключение к БД
│   ├── App.jsx            # Главный компонент
│   └── index.css          # Стили
├── supabase/
│   └── migration.sql      # Миграция БД
├── scripts/
│   └── sync_menu.py       # Синхронизация из Google Таблицы
├── bot/
│   └── bot.py             # Telegram бот
├── netlify.toml           # Конфиг Netlify
└── package.json
```

## 🔧 Настройка Google Таблицы (опционально)

1. Создайте таблицу с двумя листами: `5/2` и `7/0`
2. Формат:
   | Дата     | Завтрак | Обед   | Ужин   |
   |----------|---------|--------|--------|
   | 2026-04-01| Каша   | Борщ  | Рыба   |
3. Опубликуйте таблицу (Файл → Опубликовать в интернете)
4. Настройте CRON для запуска `scripts/sync_menu.py`

## 👥 Роли

- **partner** — партнёр (пользователь)
- **admin** — администратор

## 📝 API Endpoints

### Menus
- `GET /menus` — получить меню
- `POST /menus` — создать меню (админ)
- `PUT /menus/:id` — обновить меню (админ)

### Orders
- `GET /orders` — получить заказы пользователя
- `POST /orders` — создать заказ
- `PUT /orders/:id` — обновить статус (админ)

### Users
- `GET /users` — список пользователей (админ)
- `PUT /users/:id` — активировать/деактивировать (админ)

## 🛠 Технологии

- **Frontend:** React + Vite
- **Backend:** Supabase (PostgreSQL + Auth)
- **Hosting:** Netlify
- **Bot:** Python + python-telegram-bot
- **Sync:** Python + Google Sheets API