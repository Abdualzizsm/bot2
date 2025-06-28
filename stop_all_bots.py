#!/usr/bin/env python3
"""
إيقاف جميع عمليات البوت وحذف webhook
"""

import os
import signal
import subprocess
import requests
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def kill_python_processes():
    """إيقاف جميع عمليات Python"""
    try:
        # البحث عن عمليات Python التي تحتوي على bot.py
        result = subprocess.run(['pgrep', '-f', 'bot.py'], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ تم إيقاف العملية: {pid}")
                    except:
                        pass
        
        # إيقاف جميع عمليات Python الأخرى المتعلقة بـ telegram
        result = subprocess.run(['pgrep', '-f', 'telegram'], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ تم إيقاف العملية المتعلقة بـ telegram: {pid}")
                    except:
                        pass
                        
    except Exception as e:
        print(f"خطأ في إيقاف العمليات: {e}")

def delete_webhook():
    """حذف webhook للبوت"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url)
        if response.status_code == 200:
            print("✅ تم حذف webhook بنجاح!")
            return True
        else:
            print(f"❌ فشل في حذف webhook: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطأ في حذف webhook: {e}")
        return False

if __name__ == "__main__":
    print("🛑 إيقاف جميع عمليات البوت...")
    
    # إيقاف العمليات
    kill_python_processes()
    
    # انتظار قليل
    import time
    time.sleep(2)
    
    # حذف webhook
    delete_webhook()
    
    print("✅ تم إيقاف جميع العمليات وحذف webhook!")
    print("🚀 يمكنك الآن تشغيل البوت مرة أخرى")
