#!/usr/bin/env python3
"""
بوت بسيط للاختبار المحلي - يعمل بـ polling
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل المتغيرات
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
    user_name = update.effective_user.first_name or "صديقي"
    welcome_text = f"""مرحباً {user_name}! 👋

أنا بوت ذكي مدعوم بـ Gemini AI 🤖
اكتب لي أي سؤال وسأجيبك فوراً!

جرب:
• اسألني عن أي موضوع
• اطلب مني كتابة شيء
• أو ببساطة تحدث معي!"""
    
    await update.message.reply_text(welcome_text)
    logger.info(f"New user: {update.effective_user.id}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from {user_id}: {user_message[:50]}...")
    
    # إنشاء محادثة جديدة إذا لم تكن موجودة
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
        logger.info(f"New chat for user {user_id}")
    
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

def main():
    """تشغيل البوت"""
    if not BOT_TOKEN or not GEMINI_API_KEY:
        logger.error("Missing API keys!")
        return
    
    logger.info("🚀 Starting local bot...")
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # تشغيل بـ polling (للاختبار المحلي)
    logger.info("✅ Bot running locally...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
