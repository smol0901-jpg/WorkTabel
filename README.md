# WorkTable Bot

Telegram бот для управления заказами питания с Supabase базой данных.

## 🚀 Деплой на Render (бесплатно)

1. Зарегистрируйся на [render.com](https://render.com) через GitHub
2. Нажми **New +** → **Web Service**
3. Выбери репозиторий **WorkTabel**
4. Настрой:
   - Name: `worktable-bot`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 bot/bot.py`
5. Нажми **Create Web Service**

Бот запустится автоматически!

## Команды бота

- `/start` — Главное меню
- `/menu` — Меню на сегодня
- `/orders` — Последние заказы
- `/stats` — Статистика