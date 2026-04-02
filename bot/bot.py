#!/usr/bin/env python3
"""
WorkTable Telegram Bot - Управление графиком работы
С интеграцией Supabase
"""

import os
import sys
from datetime import datetime, date, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from supabase import create_client, Client

# === НАСТРОЙКИ ===

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")

# Supabase настройки
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("supabase_url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("supabase_key")

print(f"DEBUG: SUPABASE_URL = {SUPABASE_URL}")
print(f"DEBUG: SUPABASE_KEY = {SUPABASE_KEY[:10] if SUPABASE_KEY else None}...")

# Подключение к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === КЛАВИАТУРЫ ===

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("👥 Партнёры")],
        [KeyboardButton("📅 Меню"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_orders_keyboard():
    keyboard = [
        [KeyboardButton("📋 Все заказы")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_partners_keyboard():
    keyboard = [
        [KeyboardButton("👥 Все партнёры")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_menu_keyboard():
    keyboard = [
        [KeyboardButton("📅 Меню на сегодня")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === ОБРАБОТЧИКИ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = f"""
👋 *Добро пожаловать в WorkTable!*

📋 Управление заказами и партнёрами:

👤 Ваш ID: `{user.id}`

Выберите действие:
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return 1

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📌 *WorkTable*

/start - Главное меню
/menu - Меню на сегодня
/orders - Список заказов
/статс - Статистика
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_menu_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = str(date.today())
    result = supabase.table('menus').select('*').eq('date', today).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"📅 *Меню на {today}*\n\n"
        text += f"🥪 *Завтрак:*\n{menu.get('breakfast', '-')}\n\n"
        text += f"🍲 *Обед:*\n{menu.get('lunch', '-')}\n\n"
        text += f"🍛 *Ужин:*\n{menu.get('dinner', '-')}"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📅 Меню на сегодня не найдено.\n\nИспользуйте /menu для просмотра разделов.")

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).limit(10).execute()
    
    if result.data:
        text = "📋 *Все заказы:*\n\n"
        for order in result.data:
            user_name = order.get('users', {}).get('name', 'Unknown')
            text += f"• {user_name} | {order.get('person_count')} чел. | {order.get('status')}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📋 Заказов пока нет.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'pending').execute()
    confirmed = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'confirmed').execute()
    sent = supabase.table('orders').select('id', count='exact', head=True).eq('status', 'sent').execute()
    
    all_users = supabase.table('users').select('id', count='exact', head=True).eq('role', 'partner').execute()
    active = supabase.table('users').select('id', count='exact', head=True).eq('role', 'partner').eq('is_active', True).execute()
    
    text = f"""
📊 *Статистика:*

⏳ В ожидании: {pending.count or 0}
✅ Подтверждено: {confirmed.count or 0}
📤 Отправлено: {sent.count or 0}

👥 Всего партнёров: {all_users.count or 0}
🔥 Активных: {active.count or 0}
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# === ГЛАВНОЕ МЕНЮ ===

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📋 Заказы":
        return await show_all_orders(update, context)
    elif text == "👥 Партнёры":
        return await show_all_partners(update, context)
    elif text == "📅 Меню":
        return await show_menu_section(update, context)
    elif text == "📊 Статистика":
        return await show_stats(update, context)
    elif text == "⚙️ Настройки":
        await update.message.reply_text("⚙️ Настройки:\n\nSupabase: ✅ Подключён\nURL: `xpwewmibfiekbigxc.supabase.co`\nID: `-1002583331823`", parse_mode='Markdown')
        return 100
    elif text == "🔙 Назад":
        return await start(update, context)
    
    return 1

async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table('orders').select('*, users(name, email)').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("📋 Заказов пока нет.", reply_markup=get_orders_keyboard())
        return 2
    
    text = "📋 *Все заказы:*\n\n"
    for i, order in enumerate(result.data, 1):
        user_name = order.get('users', {}).get('name', 'Unknown')
        start = order.get('start_date', '')
        end = order.get('end_date', '')
        persons = order.get('person_count', 0)
        status = order.get('status', '')
        
        emoj = {'pending': '⏳', 'confirmed': '✅', 'sent': '📤'}.get(status, '❓')
        
        text += f"{i}. {emoj} *{user_name}*\n"
        text += f"   📅 {start} - {end}\n"
        text += f"   👥 {persons} чел.\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_orders_keyboard())
    return 2

async def show_all_partners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table('users').select('*').eq('role', 'partner').order('created_at', ascending=False).execute()
    
    if not result.data:
        await update.message.reply_text("👥 Партнёров пока нет.", reply_markup=get_partners_keyboard())
        return 3
    
    text = "👥 *Все партнёры:*\n\n"
    for i, user in enumerate(result.data, 1):
        name = user.get('name', 'Unknown')
        email = user.get('email', 'Unknown')
        active = user.get('is_active', False)
        
        status = "✅" if active else "❌"
        text += f"{i}. {status} *{name}*\n"
        text += f"   📧 {email}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_partners_keyboard())
    return 3

async def show_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = str(date.today())
    result = supabase.table('menus').select('*').eq('date', today).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"📅 *Меню на {today}*\n\n"
        text += f"🥪 *Завтрак:*\n{menu.get('breakfast', '-')}\n\n"
        text += f"🍲 *Обед:*\n{menu.get('lunch', '-')}\n\n"
        text += f"🍛 *Ужин:*\n{menu.get('dinner', '-')}"
    else:
        text = "📅 Меню на сегодня не найдено."
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_menu_keyboard())
    return 4

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
⚙️ *Настройки:*

• Supabase: ✅ Подключён
• URL: `xpwewmibfiekbigxc.supabase.co`
• ID: `-1002583331823`
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
    print("🚀 WorkTable Admin Bot...")
    print(f"📡 Supabase: {SUPABASE_URL}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_orders_menu)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_partners_menu)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_section)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("help", help_command)],
        states={},
        fallbacks=[]
    ))
    app.add_handler(CommandHandler("menu", show_menu_today))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(CommandHandler("статс", show_stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот запущен! /start")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path="webhook",
        webhook_url=f"https://worktable-bot.onrender.com/webhook"
    )

def handle_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        return 1
    return 2

def handle_partners_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        return 1
    return 3

def handle_menu_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        return 1
    return 4

if __name__ == '__main__':
    main()
