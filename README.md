# شات بوت بسيط

بوت تيليجرام بسيط يستخدم Gemini AI للمحادثة.

## التشغيل

1. ثبت المتطلبات:
```bash
pip install -r requirements.txt
```

2. أضف مفاتيح API في ملف `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
GEMINI_API_KEY=your_key
```

3. شغل البوت:
```bash
python simple_bot.py
```

## النشر على Render

- ارفع الملفات على GitHub
- أنشئ خدمة جديدة على Render
- اربطها بالمستودع
- أضف المتغيرات البيئية

## الاستخدام

- `/start` - بداية المحادثة
- ثم اكتب أي سؤال
