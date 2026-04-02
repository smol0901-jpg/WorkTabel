#!/usr/bin/env python3
"""
WorkTable Telegram Bot - Полный админ-кабинет
Управление заказами, меню, партнёрами через Telegram

Токен: 6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y
Группа: -1002583331823
"""

import os
import sys
import asyncio
from datetime import datetime, date, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, ChatMember
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from supabase import create_client

# === КОНФИГУРАЦИЯ ===
TELEGRAM_BOT_TOKEN = "6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y"
TELEGRAM_GROUP_ID = "-1002583331823"
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Инициализация Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Состояния для ConversationHandler
(MAIN_MENU, ORDERS_MENU, PARTNERS_MENU, MENU_MENU, ADD_MENU, 
 EDIT_ORDER, ADD_PARTNER, ADD_MENU_ITEM) = range(8)

# === КЛАВИАТУРЫ ===

def get_main_keyboard():
    """Главное меню админ-кабинета"""
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
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === ОБРАБОТЧИКИ КОМАНД ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и главное меню"""
    user = update.effective_user
    
    welcome_text = f"""
👋 *Добро пожаловать в WorkTable!* 

Ваш ID: `{user.id}`

Выберите раздел:
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return MAIN_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    help_text = """
📖 *Справка WorkTable*

*Команды:*
/start - Главное меню
/help - Эта справка
/menu - Меню на сегодня
/orders - Последние заказы
/stats - Статистика

*Админ-панель:*
/panel - Открыть админ-кабинет
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_menu_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню на сегодня"""
    if not supabase:
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
        await update.message.reply_text("📭 Меню на сегодня не найдено")

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать последние заказы"""
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return
    
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).limit(10).execute()
    
    if result.data:
        text = "📋 *Последние заказы:*\n\n"
        for order in result.data:
            user_name = order.get('users', {}).get('name', 'Unknown')
            text += f"• {user_name} | {order.get('person_count')} чел. | {order.get('status')}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Заказов пока нет")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return
    
    # Статистика заказов
    pending = supabase.table('orders').select('*', count='exact', head=True).eq('status', 'pending').execute()
    confirmed = supabase.table('orders').select('*', count='exact', head=True).eq('status', 'confirmed').execute()
    sent = supabase.table('orders').select('*', count='exact', head=True).eq('status', 'sent').execute()
    
    # Статистика партнёров
    all_partners = supabase.table('users').select('*', count='exact', head=True).eq('role', 'partner').execute()
    active_partners = supabase.table('users').select('*', count='exact', head=True).eq('role', 'partner').eq('is_active', True).execute()
    
    text = f"""
📊 *Статистика WorkTable*

*Заказы:*
⏳ Ожидают: {pending.count or 0}
✅ Подтверждено: {confirmed.count or 0}
📤 Отправлено: {sent.count or 0}

*Партнёры:*
👥 Всего: {all_partners.count or 0}
✅ Активных: {active_partners.count or 0}
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# === ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ===

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню"""
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
        await update.message.reply_text("📢 *Рассылка*\n\nВведите текст для отправки всем партнёрам:", parse_mode='Markdown')
        return 100  # BROADCAST state
    elif text == "⚙️ Настройки":
        return await show_settings(update, context)
    elif text == "🔙 Назад":
        await update.message.reply_text("До свидания! 👋")
        return ConversationHandler.END
    
    return MAIN_MENU

async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все заказы"""
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return MAIN_MENU
    
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("📭 Заказов пока нет", reply_markup=get_orders_keyboard())
        return ORDERS_MENU
    
    text = "📋 *Все заказы:*\n\n"
    for i, order in enumerate(result.data, 1):
        user_name = order.get('users', {}).get('name', 'Unknown')
        start = order.get('start_date', '')
        end = order.get('end_date', '')
        persons = order.get('person_count', 0)
        mode = order.get('mode', '')
        status = order.get('status', '')
        
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'sent': '📤'
        }.get(status, '❓')
        
        text += f"{i}. {status_emoji} *{user_name}*\n"
        text += f"   📅 {start} - {end}\n"
        text += f"   👥 {persons} чел. | 📋 {mode}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_orders_keyboard())
    return ORDERS_MENU

async def show_all_partners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать всех партнёров"""
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return MAIN_MENU
    
    result = supabase.table('users').select('*').eq('role', 'partner').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("📭 Партнёров пока нет", reply_markup=get_partners_keyboard())
        return PARTNERS_MENU
    
    text = "👥 *Все партнёры:*\n\n"
    for i, user in enumerate(result.data, 1):
        name = user.get('name', '—')
        email = user.get('email', '—')
        active = user.get('is_active', False)
        
        status = "✅" if active else "❌"
        text += f"{i}. {status} *{name}*\n   📧 {email}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_partners_keyboard())
    return PARTNERS_MENU

async def show_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел меню"""
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return MAIN_MENU
    
    today = str(date.today())
    result = supabase.table('menus').select('*').eq('date', today).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"🍽 *Меню на {today}*\n\n"
        text += f"🌅 *Завтрак:*\n{menu.get('breakfast', '—')}\n\n"
        text += f"☀️ *Обед:*\n{menu.get('lunch', '—')}\n\n"
        text += f"🌙 *Ужин:*\n{menu.get('dinner', '—')}"
    else:
        text = "📭 Меню на сегодня не найдено"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_menu_keyboard())
    return MENU_MENU

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки бота"""
    text = """
⚙️ *Настройки*

*Информация о боте:*
• Токен: `6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y`
• Группа: `-1002583331823`
• Supabase: {'✅ Подключён' if supabase else '❌ Не подключён'}

*Функции:*
• Автоуведомления о заказах
• Синхронизация с Google Таблицей
• Управление партнёрами
    """
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    return MAIN_MENU

# === ОБРАБОТЧИК ЗАКАЗОВ ===

async def handle_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню заказов"""
    text = update.message.text
    
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return ORDERS_MENU
    
    if text == "📋 Все заказы":
        return await show_all_orders(update, context)
    elif text == "⏳ Ожидают":
        result = supabase.table('orders').select('*, users(name)').eq('status', 'pending').execute()
        return await show_orders_by_status(update, result.data, "⏳ Ожидают")
    elif text == "✅ Подтверждённые":
        result = supabase.table('orders').select('*, users(name)').eq('status', 'confirmed').execute()
        return await show_orders_by_status(update, result.data, "✅ Подтверждённые")
    elif text == "📤 Отправленные":
        result = supabase.table('orders').select('*, users(name)').eq('status', 'sent').execute()
        return await show_orders_by_status(update, result.data, "📤 Отправленные")
    elif text == "🔙 Главное меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        return MAIN_MENU
    
    return ORDERS_MENU

async def show_orders_by_status(update, orders, title):
    """Показать заказы по статусу"""
    if not orders:
        await update.message.reply_text(f"{title}: нет заказов", reply_markup=get_orders_keyboard())
        return ORDERS_MENU
    
    text = f"{title}:\n\n"
    for order in orders:
        user_name = order.get('users', {}).get('name', 'Unknown')
        text += f"• {user_name} | {order.get('person_count')} чел.\n"
    
    await update.message.reply_text(text, reply_markup=get_orders_keyboard())
    return ORDERS_MENU

# === ОБРАБОТЧИК ПАРТНЁРОВ ===

async def handle_partners_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню партнёров"""
    text = update.message.text
    
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return PARTNERS_MENU
    
    if text == "👥 Все партнёры":
        return await show_all_partners(update, context)
    elif text == "✅ Активные":
        result = supabase.table('users').select('*').eq('role', 'partner').eq('is_active', True).execute()
        return await show_partners_by_status(update, result.data, "✅ Активные")
    elif text == "❌ Неактивные":
        result = supabase.table('users').select('*').eq('role', 'partner').eq('is_active', False).execute()
        return await show_partners_by_status(update, result.data, "❌ Неактивные")
    elif text == "➕ Добавить партнёра":
        await update.message.reply_text("➕ *Добавить партнёра*\n\nВведите email нового партнёра:", parse_mode='Markdown')
        return ADD_PARTNER
    elif text == "🔙 Главное меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        return MAIN_MENU
    
    return PARTNERS_MENU

async def show_partners_by_status(update, partners, title):
    """Показать партнёров по статусу"""
    if not partners:
        await update.message.reply_text(f"{title}: нет партнёров", reply_markup=get_partners_keyboard())
        return PARTNERS_MENU
    
    text = f"{title}:\n\n"
    for p in partners:
        text += f"• {p.get('name', '—')} | {p.get('email', '—')}\n"
    
    await update.message.reply_text(text, reply_markup=get_partners_keyboard())
    return PARTNERS_MENU

# === ОБРАБОТЧИК МЕНЮ ===

async def handle_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню блюд"""
    text = update.message.text
    
    if not supabase:
        await update.message.reply_text("❌ База данных не подключена")
        return MENU_MENU
    
    if text == "🍽 Меню на сегодня":
        return await show_menu_section(update, context)
    elif text == "📅 Меню на неделю":
        # Показать меню на 7 дней
        week_start = date.today()
        result = supabase.table('menus').select('*').gte('date', str(week_start)).lte('date', str(week_start + timedelta(days=7))).order('date').execute()
        
        if result.data:
            text = "📅 *Меню на неделю:*\n\n"
            for menu in result.data:
                text += f"*{menu.get('date')}:*\n"
                text += f"🌅 {menu.get('breakfast', '—')}\n"
                text += f"☀️ {menu.get('lunch', '—')}\n"
                text += f"🌙 {menu.get('dinner', '—')}\n\n"
        else:
            text = "📭 Меню на неделю не найдено"
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_menu_keyboard())
        return MENU_MENU
    elif text == "➕ Добавить блюдо":
        await update.message.reply_text("➕ *Добавить блюдо*\n\nВведите дату в формате ГГГГ-ММ-ДД:", parse_mode='Markdown')
        return ADD_MENU_ITEM
    elif text == "🔙 Главное меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        return MAIN_MENU
    
    return MENU_MENU

# === ФУНКЦИИ УВЕДОМЛЕНИЙ ===

async def notify_new_order(order_data, context):
    """Отправить уведомление о новом заказе в группу"""
    text = f"📢 *Новый заказ!*\n\n"
    text += f"👤 Партнёр: {order_data.get('user_name')}\n"
    text += f"📅 Период: {order_data.get('start_date')} - {order_data.get('end_date')}\n"
    text += f"👥 Количество: {order_data.get('person_count')} чел.\n"
    text += f"📋 Режим: {order_data.get('mode')}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"order_confirm_{order_data.get('id')}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"order_reject_{order_data.get('id')}")
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=TELEGRAM_GROUP_ID,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")

# === ОБРАБОТЧИК CALLBACK QUERY ===

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("order_confirm_"):
        order_id = data.split("_")[2]
        if supabase:
            supabase.table('orders').update({'status': 'confirmed'}).eq('id', order_id).execute()
        await query.edit_message_text("✅ Заказ подтверждён!")
    
    elif data.startswith("order_reject_"):
        order_id = data.split("_")[2]
        if supabase:
            supabase.table('orders').update({'status': 'rejected'}).eq('id', order_id).execute()
        await query.edit_message_text("❌ Заказ отклонён")

# === MAIN ===

def main():
    """Запуск бота"""
    print("🚀 Запуск WorkTable Admin Bot...")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler для главного меню
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            ORDERS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_orders_menu)],
            PARTNERS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_partners_menu)],
            MENU_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_section)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", show_menu_today))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот готов!")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()