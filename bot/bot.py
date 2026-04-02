#!/usr/bin/env python3
"""
WorkTable Telegram Bot - Полный админ-кабинет с Supabase
Управление заказами, меню, партнёрами через Telegram

Токен: 6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y
Группа: -1002583331823
"""

import os
import sys
from datetime import datetime, date, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from supabase import create_client, create_client_from_env

# === КОНФИГУРАЦИЯ ===
TELEGRAM_BOT_TOKEN = "6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y"
TELEGRAM_GROUP_ID = "-1002583331823"

# Supabase настройки
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Инициализация Supabase
supabase = None
db_connected = False

def init_supabase():
    """Инициализация подключения к Supabase"""
    global supabase, db_connected
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase не настроен. Используйте переменные окружения:")
        print("  export SUPABASE_URL='https://your-project.supabase.co'")
        print("  export SUPABASE_KEY='your-anon-key'")
        db_connected = False
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Проверка подключения
        result = supabase.table('users').select('id').limit(1).execute()
        db_connected = True
        print("✅ Supabase подключён!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        db_connected = False
        return False

# === КЛАВИАТУРЫ ===

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("👥 Партнёры")],
        [KeyboardButton("🍽 Меню"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("📢 Рассылка"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_orders_keyboard():
    keyboard = [
        [KeyboardButton("📋 Все заказы")],
        [KeyboardButton("⏳ Ожидают"), KeyboardButton("✅ Подтверждённые")],
        [KeyboardButton("📤 Отправленные")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_partners_keyboard():
    keyboard = [
        [KeyboardButton("👥 Все партнёры")],
        [KeyboardButton("✅ Активные"), KeyboardButton("❌ Неактивные")],
        [KeyboardButton("➕ Добавить партнёра")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_menu_keyboard():
    keyboard = [
        [KeyboardButton("🍽 Меню на сегодня")],
        [KeyboardButton("📅 Меню на неделю")],
        [KeyboardButton("➕ Добавить блюдо")],
        [KeyboardButton("✏️ Редактировать")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === ОБРАБОТЧИКИ КОМАНД ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и главное меню"""
    user = update.effective_user
    db_status = "✅" if db_connected else "❌"
    
    welcome_text = f"""
👋 *Добро пожаловать в WorkTable!*

База данных: {db_status}
Ваш ID: `{user.id}`

Выберите раздел:
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return 1

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка"""
    help_text = """
📖 *Справка WorkTable*

/start - Главное меню
/menu - Меню на сегодня
/orders - Последние заказы
/stats - Статистика
/panel - Админ-кабинет
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_menu_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню на сегодня"""
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return
    
    today = str(date.today())
    result = supabase.table('menus').select('*').eq('date', today).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"🍽 *Меню на {today}*\n\n"
        text += f"🌅 *Завтрак:*\n{menu.get('breakfast', '—')}\n\n"
        text += f"☀️ *Обед:*\n{menu.get('lunch', '—')}\n\n"
        text += f"🌙 *Ужин:*\n{menu.get('dinner', '—')}"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Меню на сегодня не найдено\n\nИспользуйте /menu для добавления")

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать заказы"""
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return
    
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).limit(10).execute()
    
    if result.data:
        text = "📋 *Заказы:*\n\n"
        for order in result.data:
            user_name = order.get('users', {}).get('name', 'Unknown')
            text += f"• {user_name} | {order.get('person_count')} чел. | {order.get('status')}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Заказов пока нет")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return
    
    # Заказы
    pending = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'pending').execute()
    confirmed = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'confirmed').execute()
    sent = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'sent').execute()
    
    # Партнёры
    all_users = supabase.table('users').select('id', count='exact', head=True).eq('role', 'partner').execute()
    active = supabase.table('users').select('id', count='exact', head=True).eq('role', 'partner').eq('is_active', True).execute()
    
    text = f"""
📊 *Статистика*

*Заказы:*
⏳ Ожидают: {pending.count or 0}
✅ Подтверждено: {confirmed.count or 0}
📤 Отправлено: {sent.count or 0}

*Партнёры:*
👥 Всего: {all_users.count or 0}
✅ Активных: {active.count or 0}
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# === ОБРАБОТЧИКИ МЕНЮ ===

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📋 Заказы":
        return await show_all_orders(update, context)
    elif text == "👥 Партнёры":
        return await show_all_partners(update, context)
    elif text == "🍽 Меню":
        return await show_menu_section(update, context)
    elif text == "📊 Статистика":
        return await show_stats(update, context)
    elif text == "📢 Рассылка":
        await update.message.reply_text("📢 Введите текст для рассылки:")
        return 100
    elif text == "⚙️ Настройки":
        return await show_settings(update, context)
    elif text == "🔙 Назад":
        await update.message.reply_text("До свидания! 👋")
        return ConversationHandler.END
    
    return 1

async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return 1
    
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("📭 Заказов пока нет", reply_markup=get_orders_keyboard())
        return 2
    
    text = "📋 *Все заказы:*\n\n"
    for i, order in enumerate(result.data, 1):
        user_name = order.get('users', {}).get('name', 'Unknown')
        start = order.get('start_date', '')
        end = order.get('end_date', '')
        persons = order.get('person_count', 0)
        status = order.get('status', '')
        
        emoji = {'pending': '⏳', 'confirmed': '✅', 'sent': '📤'}.get(status, '❓')
        
        text += f"{i}. {emoji} *{user_name}*\n"
        text += f"   📅 {start} - {end}\n"
        text += f"   👥 {persons} чел.\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_orders_keyboard())
    return 2

async def show_all_partners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return 1
    
    result = supabase.table('users').select('*').eq('role', 'partner').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("📭 Партнёров пока нет", reply_markup=get_partners_keyboard())
        return 3
    
    text = "👥 *Все партнёры:*\n\n"
    for i, user in enumerate(result.data, 1):
        name = user.get('name', '—')
        email = user.get('email', '—')
        active = user.get('is_active', False)
        
        status = "✅" if active else "❌"
        text += f"{i}. {status} *{name}*\n   📧 {email}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_partners_keyboard())
    return 3

async def show_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_connected:
        await update.message.reply_text("❌ База данных не подключена")
        return 1
    
    today = str(date.today())
    result = supabase.table('menus').select('*').eq('date', today).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"🍽 *Меню на {today}*\n\n"
        text += f"🌅 *Завтрак:* {menu.get('breakfast', '—')}\n"
        text += f"☀️ *Обед:* {menu.get('lunch', '—')}\n"
        text += f"🌙 *Ужин:* {menu.get('dinner', '—')}"
    else:
        text = "📭 Меню на сегодня не найдено"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_menu_keyboard())
    return 4

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
⚙️ *Настройки*

*Подключение:*
• Supabase: {'✅ Подключён' if db_connected else '❌ Не подключён'}
• URL: `{SUPABASE_URL[:30]}...` если настроен

*Бот:*
• Токен: `6706048508:AAF-...`
• Группа: `-1002583331823`

*Команды для настройки Supabase:*
```
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="xxx"
```
    """
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    return 1

# === CALLBACK ===

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("order_confirm_"):
        order_id = data.split("_")[2]
        if db_connected:
            supabase.table('orders').update({'status': 'confirmed'}).eq('id', order_id).execute()
        await query.edit_message_text("✅ Заказ подтверждён!")
    elif data.startswith("order_reject_"):
        order_id = data.split("_")[2]
        if db_connected:
            supabase.table('orders').update({'status': 'rejected'}).eq('id', order_id).execute()
        await query.edit_message_text("❌ Заказ отклонён")

# === MAIN ===

def main():
    print("🚀 Запуск WorkTable Admin Bot...")
    
    # Инициализация Supabase
    init_supabase()
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_orders_menu)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_partners_menu)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_section)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", show_menu_today))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот готов! Нажмите /start")
    app.run_polling(allowed_updates=["message", "callback_query"])

def handle_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📋 Все заказы":
        return 2
    elif text == "⏳ Ожидают":
        return 2
    elif text == "✅ Подтверждённые":
        return 2
    elif text == "📤 Отправленные":
        return 2
    elif text == "🔙 Главное меню":
        return 1
    
    return 2

def handle_partners_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "👥 Все партнёры":
        return 3
    elif text == "✅ Активные":
        return 3
    elif text == "❌ Неактивные":
        return 3
    elif text == "➕ Добавить партнёра":
        return 3
    elif text == "🔙 Главное меню":
        return 1
    
    return 3

def handle_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🍽 Меню на сегодня":
        return 4
    elif text == "📅 Меню на неделю":
        return 4
    elif text == "➕ Добавить блюдо":
        return 4
    elif text == "✏️ Редактировать":
        return 4
    elif text == "🔙 Главное меню":
        return 1
    
    return 4

if __name__ == '__main__':
    main()