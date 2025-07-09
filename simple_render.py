#!/usr/bin/env python3
"""
أبسط بوت ممكن - يعمل 100% على Render
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask
import threading
import asyncio

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل المتغيرات
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') 
PORT = int(os.environ.get('PORT', 10000))

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chats = {}

# Flask للحفاظ على Render يعمل
app = Flask(__name__)

@app.route('/')
def health():
    return "🤖 Bot is running!", 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية المحادثة"""
    await update.message.reply_text("مرحباً! أنا بوت ذكي 🤖\nأرسل لي أي رسالة وسأرد عليك!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"💬 {user_id}: {user_message}")
    
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    try:
        await update.message.chat.send_action('typing')
        response = await chats[user_id].send_message_async(user_message)
        await update.message.reply_text(response.text)
        logger.info("✅ Reply sent")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await update.message.reply_text("عذراً، حدث خطأ. حاول مرة أخرى.")

def run_bot():
    """تشغيل البوت"""
    logger.info("🚀 Starting bot...")
    
    # إنشاء التطبيق
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # تشغيل بـ polling (أبسط طريقة)
    app_bot.run_polling(drop_pending_updates=True)

def run_flask():
    """تشغيل Flask"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

def main():
    """تشغيل كل شيء"""
    if not BOT_TOKEN or not GEMINI_API_KEY:
        logger.error("❌ Missing API keys!")
        return
    
    logger.info("🔥 Starting SIMPLE bot...")
    
    # تشغيل Flask في thread منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # تشغيل البوت في thread منفصل  
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # إبقاء البرنامج يعمل
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")

if __name__ == '__main__':
    main()
