import os
import tempfile
import json

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ─────────────────────────────────────────
#  App — الاسم app مباشرة لأمر: uvicorn main:app
# ─────────────────────────────────────────
app = FastAPI(title="مساعد الإدخال الصوتي الذكي")

# ─────────────────────────────────────────
#  Templates — مجلد templates/
# ─────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
templates  = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ─────────────────────────────────────────
#  Pydantic Schema — Structured JSON Output
# ─────────────────────────────────────────
class CustomerData(BaseModel):
    customer_name: str   = Field(description="اسم العميل كاملاً")
    phone_number:  str   = Field(description="رقم الجوال 10 أرقام يبدأ بـ 05")
    district:      str   = Field(description="اسم الحي")
    invoice_value: float = Field(description="قيمة الفاتورة رقماً (مية وخمسين = 150)")


# ─────────────────────────────────────────
#  Gemini Client — يقرأ المفتاح من البيئة
# ─────────────────────────────────────────
def get_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY غير موجود — عيّن متغير البيئة أولاً"
        )
    return genai.Client(api_key=api_key)


# ─────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """الصفحة الرئيسية — تُقدَّم من templates/index.html"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """استقبل ملفاً صوتياً وأرجع JSON ببيانات العميل"""

    content_type = file.content_type or "audio/webm"
    suffix = ".webm" if "webm" in content_type else ".audio"

    # حفظ مؤقت على القرص
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        client = get_gemini_client()

        # رفع الملف إلى Gemini Files API
        with open(tmp_path, "rb") as audio_file:
            uploaded = client.files.upload(
                file=audio_file,
                config=types.UploadFileConfig(
                    mime_type=content_type,
                    display_name="customer_audio"
                )
            )

        prompt = """أنت مساعد ذكي متخصص في استخراج بيانات العملاء من الرسائل الصوتية العربية.

استمع للتسجيل واستخرج بدقة:
1. اسم العميل (customer_name)
2. رقم الجوال (phone_number) — 10 أرقام يبدأ بـ 05
3. الحي (district)
4. قيمة الفاتورة (invoice_value) — حوّل المنطوق لرقم: "مية وخمسين" = 150

أخرج JSON فقط بدون أي نص إضافي:
{
  "customer_name": "...",
  "phone_number": "05XXXXXXXX",
  "district": "...",
  "invoice_value": 0.0
}

إذا لم تُذكر قيمة اتركها فارغة أو صفراً."""

        # استدعاء Gemini 2.5 Flash مع Structured Output
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_uri(
                    file_uri=uploaded.uri,
                    mime_type=uploaded.mime_type
                ),
                types.Part.from_text(text=prompt)
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CustomerData,
                temperature=0.1
            )
        )

        # تنظيف وتحقق
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])

        validated = CustomerData(**json.loads(raw))

        # حذف الملف من Gemini
        client.files.delete(name=uploaded.name)

        return JSONResponse(content=validated.model_dump())

    except HTTPException:
        raise
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"فشل تحليل رد النموذج: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"خطأ في المعالجة: {exc}")
    finally:
        os.unlink(tmp_path)
