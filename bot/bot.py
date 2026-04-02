#!/usr/bin/env python3
"""
WorkTable Telegram Bot - Упрощённая версия для теста
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print(f"🔑 TOKEN: {'OK' if TELEGRAM_BOT_TOKEN else 'MISSING'}")

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("👥 Партнёры")],
        [KeyboardButton("📅 Меню"), KeyboardButton("📊 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 *WorkTable Bot*\n\nВаш ID: `{user.id}`\n\nВыберите:",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 /start - Меню")

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📋 Заказы":
        await update.message.reply_text("📋 Заказы: пока пусто")
    elif text == "👥 Партнёры":
        await update.message.reply_text("👥 Партнёры: пока пусто")
    elif text == "📅 Меню":
        await update.message.reply_text("📅 Меню на сегодня: завтрак/обед/ужин")
    elif text == "📊 Статистика":
        await update.message.reply_text("📊 Статистика: 0 заказов")

def main():
    print("🚀 WorkTable Bot starting...")
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    
    print("✅ Bot ready!")
    
    # Webhook mode для Render
    PORT = int(os.environ.get("PORT", 8443))
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        print(f"🔗 Webhook: {webhook_url}")
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path="webhook", webhook_url=webhook_url)
    else:
        print("⚠️ Using polling")
        app.run_polling()

if __name__ == '__main__':
    main()
