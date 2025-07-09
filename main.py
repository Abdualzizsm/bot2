#!/usr/bin/env python3
"""
Simple Telegram Bot - WEBHOOK ONLY (No Conflicts!)
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request
import asyncio
import json

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تحميل المتغيرات
load_dotenv()

# إعداد المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') 
PORT = int(os.environ.get('PORT', 10000))

# التحقق من وجود المتغيرات
if not BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("Missing environment variables!")
    exit(1)

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# متغير لحفظ المحادثات
chats = {}

# Flask app
app = Flask(__name__)

# Telegram app (سيتم إعداده لاحقاً)
telegram_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية المحادثة"""
    user_name = update.effective_user.first_name or "صديقي"
    welcome_text = f"""مرحباً {user_name}! 👋

أنا بوت ذكي مدعوم بـ Gemini AI 🤖
اكتب لي أي سؤال وسأجيبك فوراً!"""
    
    await update.message.reply_text(welcome_text)
    logger.info(f"New user started: {update.effective_user.id}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from {user_id}: {user_message[:50]}...")
    
    # إنشاء محادثة جديدة إذا لم تكن موجودة
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    try:
        # إظهار أن البوت يكتب
        await update.message.chat.send_action('typing')
        
        # إرسال الرسالة إلى Gemini
        response = await chats[user_id].send_message_async(user_message)
        
        # إرسال الرد
        await update.message.reply_text(response.text)
        logger.info(f"Reply sent to {user_id}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("عذراً، حدث خطأ. حاول مرة أخرى.")

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """استقبال التحديثات من Telegram"""
    try:
        json_data = request.get_json()
        if json_data:
            update = Update.de_json(json_data, telegram_app.bot)
            asyncio.create_task(telegram_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route('/')
def health():
    """فحص صحة الخدمة"""
    return f"🤖 Bot is running on port {PORT}", 200

@app.route('/status')
def status():
    """حالة البوت"""
    return {
        "status": "running",
        "users": len(chats),
        "port": PORT
    }

async def setup_webhook():
    """إعداد webhook"""
    webhook_url = f"https://simple-chatbot.onrender.com/webhook/{BOT_TOKEN}"
    
    try:
        # حذف أي webhook سابق
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Old webhook deleted")
        
        # إعداد webhook جديد
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "edited_message"]
        )
        logger.info(f"✅ Webhook set: {webhook_url}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
        return False

def main():
    """تشغيل البوت"""
    global telegram_app
    
    logger.info("🚀 Starting Telegram Bot...")
    
    # إنشاء Telegram application
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # إعداد webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    logger.info(f"✅ Bot ready on port {PORT}")
    
    # تشغيل Flask server
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
