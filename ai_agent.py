import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

with open("lab_data.json", "r", encoding="utf-8") as f:
    LAB_KNOWLEDGE = json.load(f)

SYSTEM_INSTRUCTION = f"""
أنت المساعد الذكي الآلي لـ "{LAB_KNOWLEDGE['lab_info']['name']}".
مهمتك الرد على استفسارات المراجعين عبر الواتساب/تيليجرام بدقة ولباقة واختصار يناسب رسائل الدردشة.

بيانات المختبر الثابتة المعتمدة حصراً:
- العنوان: {LAB_KNOWLEDGE['lab_info']['location']}
- رابط الخريطة: {LAB_KNOWLEDGE['lab_info']['maps_link']}
- أوقات العمل: {LAB_KNOWLEDGE['lab_info']['working_hours']}

قائمة الفحوصات والأسعار وشروط التحضير:
{json.dumps(LAB_KNOWLEDGE['tests'], ensure_ascii=False, indent=2)}

قواعد الرد الصارمة:
1. أجب باختصار وترتيب (استخدم النقاط والإيموجي المناسب).
2. في حال السؤال عن فحص متوفر بالقائمة، اذكر الاسم، السعر، وشروط الصيام أو التحضير بدقة.
3. إذا سأل المريض عن فحص غير موجود، أخبره بلطف أن يتصل بالاستعلامات لتأكيد توفره فوراً.
4. لا تشخص أمراضاً ولا تصرف أدوية، واختم أي استشارة بنصيحة مراجعة الطبيب المختص.
5. تحدث بلهجة عربية مهذبة وودودة ومفهومة محلياً.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

def generate_reply(user_message: str) -> str:
    try:
        response = model.generate_content(
            user_message,
            generation_config={"temperature": 0.2, "max_output_tokens": 300}
        )
        return response.text.strip()
    except Exception as e:
        return "أهلاً بك في مختبر النخبة. نعتذر، نواجه ضغطاً في الرد حالياً. يرجى الاتصال المباشر برقم الاستعلامات: 07700000000."