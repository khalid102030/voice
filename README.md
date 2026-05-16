# 🎙️ المساعد الصوتي الذكي

تطبيق ويب يستخدم **Gemini 2.5 Flash** لاستخراج بيانات العملاء تلقائياً من التسجيلات الصوتية.

---

## 📁 هيكل المشروع

```
voice-assistant/
├── main.py              ← FastAPI Backend  (uvicorn main:app)
├── requirements.txt
├── .env.example         ← انسخه إلى .env
├── .gitignore
└── templates/
    └── index.html       ← واجهة المستخدم
```

---

## ⚡ تشغيل المشروع

```bash
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. إعداد مفتاح Gemini
cp .env.example .env
# افتح .env وضع مفتاحك من: https://aistudio.google.com/app/apikey

# 3. تصدير متغير البيئة
export GEMINI_API_KEY="مفتاحك_هنا"   # Linux/Mac
# أو
set GEMINI_API_KEY=مفتاحك_هنا        # Windows

# 4. تشغيل الخادم
uvicorn main:app --reload

# 5. افتح المتصفح
# http://localhost:8000
```

---

## 🔌 API

```
POST /analyze-audio
Content-Type: multipart/form-data
Body: file (audio)

Response 200:
{
  "customer_name": "محمد أحمد",
  "phone_number":  "0501234567",
  "district":      "النزهة",
  "invoice_value": 150.0
}
```

---

## 🛡️ الأمان

- المفتاح يُقرأ **فقط** من متغير البيئة `GEMINI_API_KEY`
- ملف `.env` مُستثنى من Git عبر `.gitignore`
- لا يوجد أي مفتاح مكتوب داخل الكود
