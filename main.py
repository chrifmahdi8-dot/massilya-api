from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import requests
from datetime import datetime
from groq import Groq
import google.generativeai as genai
import re

# 1. تهيئة السيرفر
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. هيكل رسائل الذاكرة (الجديد 🧠)
class MessageItem(BaseModel):
    role: str
    content: str

# 3. هيكل الطلب (يحتوي على الرسالة الحالية + الذاكرة السابقة)
class ChatRequest(BaseModel):
    message: str
    history: List[MessageItem] = [] 

@app.get("/")
def read_root():
    return {"status": "Massilya Backend is Running 🚀"}

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
    يُمنع منعاً باتاً طباعة أي حروف آسيوية أو رموز غريبة.
    
    [قواعد التحدث والذاكرة 🧠 - التزم بها حرفياً]: 
    1. [الإيجاز الشديد]: في الردود العادية (الترحيب، التأكيد) كن مختصراً جداً (سطر أو سطرين).
    2. [استثناء الفوائد 💡]: فقط عند اقتراح منتج، اشرح فوائده في 4 إلى 5 أسطر لتقنع الزبون.
    3. [منع النسيان والتكرار 🚨]: أنت الآن تقرأ تاريخ المحادثة بالكامل. إذا رأيت أن الزبون قد أعطاك سابقاً (الاسم، الولاية، أو رقم الهاتف)، وقال لك "نعم" أو أكد الطلب، **إياك أن تطلب معلوماته مرة أخرى!** بل قل له فوراً: "تم تأكيد طلبك بنجاح يا [اسم الزبون]، سيتصل بك فريق التوصيل قريباً، شكراً لثقتك!" وتوقف.
    4. ضع اسم المنتج بالفرنسية دائماً بين قوسين ( ).
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
        # بناء قائمة الرسائل للذكاء الاصطناعي (Groq) لتشمل الذاكرة
        api_messages = [{"role": "system", "content": system_instruction}]
        for msg in request.history:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        # إضافة رسالة الزبون الحالية
        api_messages.append({"role": "user", "content": user_message})

        groq_client = Groq(api_key=GROQ_API_KEY)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
            temperature=0.1, 
            max_completion_tokens=1024,
            top_p=0.9,
            stream=False 
        )
        answer = completion.choices[0].message.content

    except Exception as groq_error:
        try:
            # المحاولة البديلة عبر Gemini مع الذاكرة
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            
            gemini_history = []
            for msg in request.history:
                role = "user" if msg.role == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg.content]})
                
            chat = gemini_model.start_chat(history=gemini_history)
            response = chat.send_message(user_message)
            answer = response.text
        except Exception as gemini_error:
            answer = "عذراً، الأطباء في المختبر مشغولون حالياً باستشارات أخرى. يرجى المحاولة بعد قليل! ⏳"

    # 🧹 فلتر مسح الحروف الآسيوية
    answer = re.sub(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', '', answer)

    # 📡 جاسوس التليجرام (يعمل فقط إذا أعطى رقمه)
    try:
        bot_token = "8758469394:AAFnu5x88Bn1XZSPyEvninIoQ5-TB3JMpPw"
        chat_id = "5111187631"
        if sum(char.isdigit() for char in user_message) >= 8:
            spy_message = f"💰🚨 طلبية جديدة!\n\n👤 الزبون:\n{user_message}\n\n🤖 المندوب:\n{answer}"
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": spy_message})
    except:
        pass

    return {"reply": answer}
