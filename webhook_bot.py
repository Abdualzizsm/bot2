#!/usr/bin/env python3
"""
Telegram Bot with Webhook for Production (Render)
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request
import asyncio
import threading

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل المتغيرات من .env
load_dotenv()

# إعداد المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PORT = int(os.environ.get('PORT', 10000))

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# متغير لحفظ المحادثات
chats = {}

# إنشاء Flask app
app = Flask(__name__)

# إنشاء Telegram application
telegram_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية المحادثة"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "مستخدم"
    logger.info(f"New user started bot: {user_id} - {user_name}")
    
    welcome_message = f"""
مرحباً {user_name}! 👋

أنا بوت ذكي مدعوم بـ Gemini AI 🤖
يمكنني الإجابة على أسئلتك ومساعدتك في أي شيء!

فقط اكتب لي أي سؤال وسأجيبك فوراً ⚡
"""
    
    await update.message.reply_text(welcome_message)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    user_id = update.effective_user.id
    user_message = update.message.text
    logger.info(f"Received message from user {user_id}: {user_message}")
    
    # إنشاء محادثة جديدة إذا لم تكن موجودة
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
        logger.info(f"Created new chat for user {user_id}")
    
    try:
        # إظهار أن البوت يكتب
        await update.message.chat.send_action('typing')
        
        # إرسال الرسالة إلى Gemini والحصول على الرد
        logger.info("Sending message to Gemini...")
        response = await chats[user_id].send_message_async(user_message)
        logger.info(f"Received response from Gemini: {response.text[:100]}...")
        
        # إرسال الرد للمستخدم
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await update.message.reply_text(f"عذراً، حدث خطأ: {str(e)}")

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """معالجة webhook من Telegram"""
    try:
        # استقبال التحديث من Telegram
        json_data = request.get_json()
        
        if json_data:
            update = Update.de_json(json_data, telegram_app.bot)
            
            # معالجة التحديث بشكل غير متزامن
            asyncio.create_task(telegram_app.process_update(update))
            
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route('/')
def health_check():
    """فحص صحة الخدمة"""
    return "Bot is running! 🤖", 200

async def setup_webhook():
    """إعداد webhook"""
    webhook_url = f"https://simple-chatbot.onrender.com/{BOT_TOKEN}"
    
    try:
        # حذف webhook القديم
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Old webhook deleted")
        
        # إعداد webhook جديد
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

def run_flask():
    """تشغيل Flask server"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

async def main():
    """إعداد وتشغيل البوت"""
    global telegram_app
    
    # تحقق من مفاتيح API
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found!")
        return
    
    logger.info("Starting webhook bot...")
    
    # إنشاء Telegram application
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # إعداد webhook
    await setup_webhook()
    
    # تشغيل Flask في thread منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info(f"✅ Webhook bot started on port {PORT}")
    
    # إبقاء البرنامج يعمل
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
