#!/usr/bin/env python3
"""
WorkTable Telegram Bot - Полный админ-кабинет с Supabase
Управление заказами, меню, партнёрами через Telegram

Токен: 6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y
Группа: -1002583331823
Supabase: https://xpxewmimbfiekbkigbxc.supabase.co
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
from supabase import create_client

# === КОНФИГУРАЦИЯ ===
TELEGRAM_BOT_TOKEN = "6706048508:AAF-8INmBKwP1x7DA-_ET8D282c5pp0Rn2Y"
TELEGRAM_GROUP_ID = "-1002583331823"

# Supabase настройки
SUPABASE_URL = "https://xpxewmimbfiekbkigbxc.supabase.co"
SUPABASE_KEY = "n2Kh7KWcCXRqQucIIamnAky7gbWGI4kr4U74H90z+MVLCXGSVzAeluS8i001Y1aAWsTBo5bFZnSNdfTvgNp2nw=="

# Инициализация Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    user = update.effective_user
    
    welcome_text = f"""
👋 *Добро пожаловать в WorkTable!*

База данных: ✅ Подключена
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
    help_text = """
📖 *Справка WorkTable*

/start - Главное меню
/menu - Меню на сегодня
/orders - Последние заказы
/stats - Статистика
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_menu_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    pending = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'pending').execute()
    confirmed = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'confirmed').execute()
    sent = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'sent').execute()
    
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
    text = """
⚙️ *Настройки*

*Подключение:*
• Supabase: ✅ Подключён
• URL: `xpxewmimbfiekbkigbxc.supabase.co`

*Бот:*
• Токен: `6706048508:AAF-...`
• Группа: `-1002583331823`
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
        supabase.table('orders').update({'status': 'confirmed'}).eq('id', order_id).execute()
        await query.edit_message_text("✅ Заказ подтверждён!")
    elif data.startswith("order_reject_"):
        order_id = data.split("_")[2]
        supabase.table('orders').update({'status': 'rejected'}).eq('id', order_id).execute()
        await query.edit_message_text("❌ Заказ отклонён")

# === MAIN ===

def main():
    print("🚀 Запуск WorkTable Admin Bot...")
    print(f"✅ Supabase: {SUPABASE_URL}")
    
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
    if text == "🔙 Главное меню":
        return 1
    return 2

def handle_partners_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Главное меню":
        return 1
    return 3

def handle_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Главное меню":
        return 1
    return 4

if __name__ == '__main__':
    main()