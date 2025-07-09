#!/usr/bin/env python3
"""
Telegram Bot for Render - Fixed Threading Issues
"""
import os
import logging
import asyncio
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تحميل المتغيرات
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

# Flask app
app = Flask(__name__)

# Telegram app
telegram_app = None
async_loop = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية المحادثة"""
    user_name = update.effective_user.first_name or "صديقي"
    welcome_text = f"""مرحباً {user_name}! 👋

أنا بوت ذكي مدعوم بـ Gemini AI 🤖
اكتب لي أي سؤال وسأجيبك فوراً!"""
    
    await update.message.reply_text(welcome_text)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"💬 Message from {user_id}: {user_message[:50]}...")
    
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    try:
        await update.message.chat.send_action('typing')
        response = await chats[user_id].send_message_async(user_message)
        await update.message.reply_text(response.text)
        logger.info(f"✅ Reply sent to {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        await update.message.reply_text("عذراً، حدث خطأ. حاول مرة أخرى.")

def process_update_sync(update_data):
    """معالجة التحديث بشكل متزامن"""
    try:
        update = Update.de_json(update_data, telegram_app.bot)
        # تشغيل في event loop منفصل
        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update), 
            async_loop
        )
        logger.info("✅ Update processed successfully")
    except Exception as e:
        logger.error(f"❌ Process update error: {e}")

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """استقبال التحديثات من Telegram"""
    try:
        json_data = request.get_json()
        logger.info("📲 Webhook received")
        
        if json_data:
            # معالجة في thread منفصل
            threading.Thread(
                target=process_update_sync, 
                args=(json_data,),
                daemon=True
            ).start()
        
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return "Error", 500

@app.route('/')
def health():
    return "🤖 Bot is running!", 200

@app.route('/status')  
def status():
    return {"status": "running", "users": len(chats)}

async def setup_webhook():
    """إعداد webhook"""
    webhook_url = f"https://bot2-zak5.onrender.com/webhook/{BOT_TOKEN}"
    
    try:
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
        return False

def run_async_loop():
    """تشغيل event loop في thread منفصل"""
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    
    async def keep_alive():
        while True:
            await asyncio.sleep(1)
    
    async_loop.run_until_complete(keep_alive())

def main():
    """تشغيل البوت"""
    global telegram_app
    
    if not BOT_TOKEN or not GEMINI_API_KEY:
        logger.error("❌ Missing API keys!")
        return
    
    logger.info("🚀 Starting Render bot...")
    
    # إنشاء Telegram application
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # تشغيل async loop في thread منفصل
    loop_thread = threading.Thread(target=run_async_loop, daemon=True)
    loop_thread.start()
    
    # انتظار حتى يكون async_loop جاهز
    import time
    time.sleep(2)
    
    # إعداد webhook
    asyncio.run_coroutine_threadsafe(setup_webhook(), async_loop)
    
    logger.info(f"✅ Bot ready on port {PORT}")
    
    # تشغيل Flask
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
