#!/usr/bin/env python3
"""
WorkTable Telegram Bot
Бот для уведомлений о новых заказах

Запуск: python3 bot/bot.py
"""

import os
import sys
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from supabase import create_client

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

async def start(update, context):
    await update.message.reply_text(
        "👋 Привет! Я бот WorkTable.\n\n"
        "Команды:\n"
        "/menu - Меню на сегодня\n"
        "/orders - Ваши заказы\n"
        "/help - Помощь"
    )

async def help_command(update, context):
    await update.message.reply_text(
        "📖 *Справка*\n\n"
        "/start - Начать\n"
        "/menu - Меню\n"
        "/orders - Заказы\n"
        "/help - Помощь",
        parse_mode='Markdown'
    )

async def show_menu(update, context):
    if not supabase:
        await update.message.reply_text("❌ База не настроена")
        return
    
    today = datetime.now().date()
    result = supabase.table('menus').select('*').eq('date', str(today)).execute()
    
    if result.data:
        menu = result.data[0]
        text = f"🍽 *Меню на {today.strftime('%d.%m.%Y')}*\n\n"
        text += f"🌅 *Завтрак:* {menu.get('breakfast', '—')}\n"
        text += f"☀️ *Обед:* {menu.get('lunch', '—')}\n"
        text += f"🌙 *Ужин:* {menu.get('dinner', '—')}"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Меню не найдено")

async def show_orders(update, context):
    await update.message.reply_text(
        "📝 Используйте веб-приложение:\nhttps://worktable-app.netlify.app"
    )

async def handle_message(update, context):
    await update.message.reply_text("Используйте команды /menu, /orders или /help")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: TELEGRAM_BOT_TOKEN не задан")
        sys.exit(1)
    
    print("Запуск бота...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
    print("Бот запущен!")

if __name__ == '__main__':
    main()