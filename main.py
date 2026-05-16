import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import json

app = FastAPI(title="مساعد الإدخال الصوتي الذكي")

# ========================
# Pydantic Model - الهيكل المطلوب
# ========================
class CustomerData(BaseModel):
    customer_name: str = Field(description="اسم العميل كاملاً")
    phone_number: str = Field(description="رقم الجوال المكون من 10 أرقام يبدأ بـ 05")
    district: str = Field(description="اسم الحي")
    invoice_value: float = Field(description="قيمة الفاتورة كرقم مثلاً 150.0")


# ========================
# Gemini Client
# ========================
def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY غير موجود. يرجى تعيين متغير البيئة GEMINI_API_KEY"
        )
    return genai.Client(api_key=api_key)


# ========================
# Routes
# ========================
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    # التحقق من نوع الملف
    allowed_types = [
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg",
        "audio/webm", "audio/mp4", "audio/x-m4a", "audio/aac",
        "video/webm"  # بعض المتصفحات ترسل تسجيل الصوت بهذا النوع
    ]
    
    content_type = file.content_type or ""
    if not any(t in content_type for t in ["audio", "video/webm"]):
        # نتساهل قليلاً لأن بعض المتصفحات ترسل أنواعاً مختلفة
        pass

    # حفظ الملف مؤقتاً
    suffix = ".webm" if "webm" in content_type else ".audio"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        client = get_gemini_client()

        # رفع الملف الصوتي إلى Gemini Files API
        with open(tmp_path, "rb") as audio_file:
            uploaded_file = client.files.upload(
                file=audio_file,
                config=types.UploadFileConfig(
                    mime_type=content_type if content_type else "audio/webm",
                    display_name="customer_audio"
                )
            )

        # بناء الـ Prompt
        system_prompt = """أنت مساعد ذكي متخصص في استخراج بيانات العملاء من الرسائل الصوتية باللغة العربية.

مهمتك: استمع للتسجيل الصوتي واستخرج المعلومات التالية بدقة:
1. اسم العميل (customer_name)
2. رقم الجوال (phone_number) - يجب أن يكون 10 أرقام ويبدأ بـ 05
3. الحي (district)
4. قيمة الفاتورة (invoice_value) - حوّل الأرقام المنطوقة إلى أرقام (مثل: "مية وخمسين" = 150)

أخرج النتيجة كـ JSON فقط بهذا الشكل بالضبط، بدون أي نص إضافي:
{
  "customer_name": "...",
  "phone_number": "05XXXXXXXX",
  "district": "...",
  "invoice_value": 0.0
}

إذا لم تجد قيمة معينة، اترك الحقل فارغاً أو صفراً للأرقام."""

        # استدعاء Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type=uploaded_file.mime_type
                ),
                types.Part.from_text(text=system_prompt)
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CustomerData,
                temperature=0.1
            )
        )

        # تحليل النتيجة
        result_text = response.text.strip()
        
        # تنظيف النص من أي markdown
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])
        
        data = json.loads(result_text)
        validated = CustomerData(**data)

        # حذف الملف المؤقت
        client.files.delete(name=uploaded_file.name)

        return JSONResponse(content=validated.model_dump())

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"فشل في تحليل الرد من النموذج: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في المعالجة: {str(e)}")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
