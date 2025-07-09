import os
import logging
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل المتغيرات من .env
load_dotenv()

# إعداد المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# متغير لحفظ المحادثات
chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية المحادثة"""
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    chats[user_id] = model.start_chat(history=[])
    
    await update.message.reply_text(f"مرحبا {name}! أنا بوت ذكي، اسألني أي شيء!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع الرسائل"""
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

async def conflict_resolver():
    """حل مشكلة التعارض مع البوتات الأخرى"""
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.delete_webhook()
        await bot.get_updates(offset=-1)
        logger.info("Conflict resolved: Webhook deleted and pending updates cleared")
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")

def main():
    """تشغيل البوت"""
    # تحقق من مفاتيح API
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found!")
        return
    
    logger.info("Starting bot...")
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # تشغيل البوت مع حل شامل للتعارض
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'edited_message'],
        timeout=30,
        bootstrap_retries=3,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )

if __name__ == '__main__':
    main()
