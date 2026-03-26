from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from datetime import datetime
from groq import Groq
import google.generativeai as genai
import re

# 1. تهيئة السيرفر
app = FastAPI()

# 2. الجدار الأمني (CORS): هذا يسمح لموقعك في Vercel بالتحدث مع هذا السيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # يسمح باستقبال الطلبات من الواجهة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. هيكل الرسالة المستقبلة
class ChatRequest(BaseModel):
    message: str

# 4. نقطة فحص عمل السيرفر (لتتأكد أنه شغال)
@app.get("/")
def read_root():
    return {"status": "Massilya Backend is Running 🚀"}

# 5. نقطة المحادثة الأساسية (العقل)
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message
    
    # جلب المفاتيح من سيرفر Render
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    system_instruction = f"""
    أنت طبيب أمراض جلدية وخبير مبيعات محترف تعمل في مختبرات 'Massilya Dermo-Cosmétiques' في الجزائر. 
    تاريخ اليوم هو {current_date}.
    
    [تحذير أمني صارم 🛑]: 
    يُمنع منعاً باتاً طباعة أي حروف آسيوية (صينية، كورية، يابانية) أو رموز غريبة. استخدم فقط الحروف العربية الفصحى، والحروف اللاتينية لأسماء المنتجات.
    
    [قواعد التحدث]: 
    1. تحدث بالعربية الفصحى المبسطة.
    2. إجاباتك يجب أن تكون متوسطة الطول (حوالي 4 إلى 6 أسطر). اشرح فوائد المنتج.
    3. ضع اسم المنتج بالفرنسية بين قوسين ( ).
    4. اطلب في النهاية (الاسم، الولاية، رقم الهاتف) لتأكيد الطلب.
    5. التوصيل: العاصمة 400 دج، باقي الولايات 600 دج.
    
    [الكتالوج]:
    1. (MASSILYA Gel Exfoliant Moussant 2% BHA 200ml) - السعر: 950 د.ج
    2. (MASSILYA Gel Nettoyant Purifiant Peaux Grasses 250ml) - السعر: 500 د.ج
    3. (MASSILYA Gel Nettoyant Visage Peaux Normales et Mixtes 250ml) - السعر: 500 د.ج
    4. (MASSILYA Gel Nettoyant Visage Ultra Doux 250ml) - السعر: 500 د.ج
    5. (MASSILYA Gel Moussant Pour Peaux Acnéiques 250ml) - السعر: 500 د.ج
    6. (MASSILYA Lotion Anti Chute 150ml) - السعر: 1100 د.ج
    7. (MASSILYA Shampooing Anti-Pelliculaire 200ml) - السعر: 750 د.ج
    8. (MASSILYA Shampoing Cheveux Secs et Abimés 200ml) - السعر: 800 د.ج
    9. (MASSILYA Shampooing Anti Pelliculaire PSO F 200ml) - السعر: 780 د.ج
    10. (MASSILYA Crème Anti-Rugosité 30% Urée 120ml) - السعر: 850 د.ج
    11. (MASSILYA Lait Hydratant Emollient 5% Visage et Corps) - السعر: 850 د.ج
    12. (MASSILYA Lait Hydratant Emollient 10% Corps) - السعر: 1050 د.ج
    13. (MASSILYA Crème de Douche Lavante 400ml) - السعر: 500 د.ج
    """
    
    answer = ""
    
    try:
        # المحاولة الأولى عبر Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1, 
            max_completion_tokens=1024,
            top_p=0.9,
            stream=False 
        )
        answer = completion.choices[0].message.content

    except Exception as groq_error:
        try:
            # المحاولة البديلة عبر Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            response = gemini_model.generate_content(user_message)
            answer = response.text
        except Exception as gemini_error:
            answer = "عذراً، الأطباء في المختبر مشغولون حالياً باستشارات أخرى. يرجى المحاولة بعد قليل! ⏳"

    # 🧹 فلتر مسح الحروف الآسيوية (الهلوسة)
    answer = re.sub(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', '', answer)

    # 📡 جاسوس التليجرام
    try:
        bot_token = "8758469394:AAFnu5x88Bn1XZSPyEvninIoQ5-TB3JMpPw"
        chat_id = "5111187631"
        if sum(char.isdigit() for char in user_message) >= 8:
            spy_message = f"💰🚨 طلبية جديدة!\n\n👤 الزبون:\n{user_message}\n\n🤖 المندوب:\n{answer}"
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": spy_message})
    except:
        pass

    # إرجاع الرد إلى واجهة Vercel
    return {"reply": answer}
