import os
import requests
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv

# استيراد دالة التوليد ودالة جلب البيانات مع خيار التحديث الإجباري
from ai_agent import generate_reply
from sheets_loader import get_lab_data

load_dotenv()

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secret_token_123")

# استخراج أرقام المدراء وتخزينها كـ Set لسرعة التحقق
admin_raw = os.getenv("ADMIN_PHONE_NUMBERS", "")
ADMIN_NUMBERS = {num.strip() for num in admin_raw.split(",") if num.strip()}


def send_whatsapp_message(to_number: str, text: str):
    """إرسال رسالة نصية عبر WhatsApp Cloud API"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")


def handle_admin_commands(sender_id: str, command: str) -> str:
    """معالجة الأوامر الإدارية للمدير"""
    cmd = command.strip().lower()

    if cmd in ["/refresh", "تحديث", "ريفرش"]:
        try:
            # إجبار الكود على إعادة سحب البيانات من Google Sheets وتخطي الـ Cache
            data = get_lab_data(force_refresh=True)
            total_tests = len(data.get("tests", []))
            lab_name = data.get("lab_info", {}).get("lab_name", "المختبر")
            
            return (
                f"✅ تم تحديث بيانات {lab_name} بنجاح!\n\n"
                f"📊 عدد الفحوصات المسجلة الآن: {total_tests}\n"
                f"⏱️ التحديث سارٍ ومباشر لجميع المراجعين."
            )
        except Exception as e:
            return f"❌ فشل تحديث البيانات من Google Sheets.\nالسبب: {str(e)}"

    elif cmd in ["/status", "الحالة"]:
        return "🟢 البوت يعمل بشكل طبيعي والاتصال بجوجل شيتس نشط."

    # تم إصلاح الخطأ البرمجي هنا
    return (
        "⚠ أمر غير معروف. الأوامر المتاحة:\n"
        "▫️ `/refresh` أو `تحديث` : لتحديث الأسعار من الشيت.\n"
        "▫️ `/status` أو `الحالة` : لفحص حالة البوت."
    )


def process_incoming_message(sender_id: str, message_text: str):
    """تحديد مسار المعالجة: أمر إداري أم سؤال مراجع عادي"""
    clean_text = message_text.strip()

    # تم إصلاح خطأ الترقيم هنا
    # إذا كان المرسل هو المدير والرسالة تبدأ برمز أمر أو كلمات مفتاحية
    if sender_id in ADMIN_NUMBERS and (clean_text.startswith("/") or clean_text in ["تحديث", "ريفرش", "الحالة"]):
        reply = handle_admin_commands(sender_id, clean_text)
        send_whatsapp_message(sender_id, reply)
        return

    # إذا كان مراجعاً عادياً (أو المدير يطرح سؤالاً عادياً لاختبار الذكاء الاصطناعي)
    reply = generate_reply(clean_text)
    send_whatsapp_message(sender_id, reply)


# --- Webhook Endpoints ---

@app.get("/webhook/whatsapp")
async def verify_whatsapp(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@app.post("/webhook/whatsapp")
async def receive_whatsapp(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            if msg.get("type") == "text":
                sender_id = msg.get("from")
                user_text = msg.get("text", {}).get("body", "")

                # تشغيل المعالجة في الخلفية للرد على سيرفرات ميتا فوراً بـ 200 OK
                background_tasks.add_task(process_incoming_message, sender_id, user_text)
    except Exception as e:
        print(f"Webhook processing error: {e}")

    return {"status": "success"}
