# 🎙️ المساعد الصوتي الذكي — Voice AI Assistant

تطبيق ويب يستخدم Gemini 2.5 Flash لاستخراج بيانات العملاء تلقائياً من التسجيلات الصوتية.

---

## ⚡ التشغيل السريع

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. إعداد مفتاح Gemini API
احصل على مفتاحك من: https://aistudio.google.com/app/apikey

**على Linux/Mac:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**على Windows:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

### 3. تشغيل الخادم
```bash
python main.py
```

### 4. افتح المتصفح
```
http://localhost:8000
```

---

## 📁 هيكل المشروع
```
voice-assistant/
├── main.py              ← FastAPI Backend
├── requirements.txt     ← المكتبات المطلوبة
├── README.md
└── templates/
    └── index.html       ← الواجهة الأمامية
```

---

## 🎯 كيف يعمل

1. **ارفع ملفاً صوتياً** (MP3/WAV/M4A) أو **سجّل مباشرة** من المتصفح
2. اضغط **"بدء التحليل الذكي"**
3. Gemini يستمع ويستخرج:
   - اسم العميل
   - رقم الجوال (10 أرقام، يبدأ بـ 05)
   - الحي
   - قيمة الفاتورة (يحوّل الأرقام المنطوقة إلى أرقام)
4. تظهر النتائج في نموذج قابل للتعديل
5. اضغط **"تأكيد وصحة المعلومات"** للحفظ

---

## 🔌 API Endpoint

```
POST /analyze-audio
Content-Type: multipart/form-data

Body: file (audio file)

Response:
{
  "customer_name": "محمد أحمد",
  "phone_number": "0501234567",
  "district": "النزهة",
  "invoice_value": 150.0
}
```
