#!/usr/bin/env python3
"""
سكريبت لحذف webhook وإزالة التعارض في بوت التليجرام
"""
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

# تحميل المتغيرات
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def reset_bot():
    """حذف webhook وإزالة جميع التعارضات"""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        print("🔄 Deleting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted")
        
        print("🔄 Getting pending updates...")
        updates = await bot.get_updates()
        print(f"📥 Found {len(updates)} pending updates")
        
        if updates:
            # احصل على آخر update_id لحذف جميع التحديثات المعلقة
            last_update_id = updates[-1].update_id
            await bot.get_updates(offset=last_update_id + 1, limit=1)
            print("🗑️ Cleared all pending updates")
        
        print("✅ Bot reset successfully!")
        print("🚀 Now you can run your bot on Render")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_bot())
