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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[MessageItem] = [] 

@app.get("/")
def read_root():
    return {"status": "Massilya Backend is Running 🚀"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 🧠 العقل المدبر (النسخة المضادة للهلوسة)
    system_instruction = f"""
    أنت طبيب أمراض جلدية وخبير مبيعات محترف تعمل في مختبرات 'Massilya Dermo-Cosmétiques' في الجزائر. 
    تاريخ اليوم هو {current_date}.
    
    [تحذير أمني صارم ضد الهلوسة 🛑]: 
    1. يُمنع منعاً باتاً طباعة أي حروف آسيوية أو رموز غريبة.
    2. [قاعدة المعلومات الحديدية]: التزم حرفياً بالأسعار والفوائد المكتوبة في الكتالوج أدناه. يُمنع منعاً باتاً اختراع، أو تأليف أي فوائد طبية، أو منتجات، أو أسعار من خارج هذا النص. اعتمد فقط على المكتوب.
    
    [قواعد المبيعات 💰]: 
    1. عند اقتراح منتج، اذكر فائدته (المكتوبة في الكتالوج فقط) باختصار شديد.
    2. في نهاية رسالة اقتراح المنتج قل مباشرة: "هل ترغب في طلب هذا المنتج؟ يرجى تزويدي باسمك، ولايتك، ورقم هاتفك لتأكيد الطلب."
    3. إذا وافق على الشراء، تأكد من وجود (الاسم، الولاية، رقم الهاتف). إذا نقصت معلومة، اطلبها.
    4. إذا اكتملت المعلومات (الاسم + الولاية + الهاتف)، قم فوراً بإنهاء المحادثة قائلاً: "تم تأكيد طلبك بنجاح يا [اسم الزبون]، سيتصل بك فريق التوصيل قريباً، شكراً لثقتك!". ولا تضف أي كلمة أخرى.
    5. التوصيل: المسيلة 200 دج، باقي الولايات 400 دج.
    6.لا تتحدث عن اي موضوع اخر او تعطي معلومات خارج موضوع المختبر 
    7.اقترح منتجات بناءا على نوع بشرته ,اعرف نوع مشكلته ثم اقترح
    8.لا تطل الحديث وتكتب مقالات طويلة،الحد الاخير ستة اسطر
    
    [الكتالوج ووصف المنتجات الرسمي]:
    1. (MASSILYA Gel Exfoliant Moussant 2% BHA 200ml) - السعر: 950 د.ج
       الفوائد: مقشر قوي لحب الشباب والرؤوس السوداء.
    2. (MASSILYA Gel Nettoyant Purifiant Peaux Grasses 250ml) - السعر: 500 د.ج
       الفوائد: منظف عميق للبشرة الدهنية ويقلل الإفرازات.
    3. (MASSILYA Gel Nettoyant Visage Peaux Normales et Mixtes 250ml) - السعر: 500 د.ج
       الفوائد: ينظف البشرة العادية والمختلطة بلطف ويحافظ على توازنها.
    4. (MASSILYA Gel Nettoyant Visage Ultra Doux 250ml) - السعر: 500 د.ج
       الفوائد: عناية فائقة ومنظف لطيف جداً للبشرة الجافة والحساسة.
    5. (MASSILYA Gel Moussant Pour Peaux Acnéiques 250ml) - السعر: 500 د.ج
       الفوائد: عناية يومية تنظف البشرة المعرضة للحبوب.
    6. (MASSILYA Lotion Anti Chute 150ml) - السعر: 1100 د.ج
       الفوائد: محلول مكثف يقوي البصيلات ويعالج تساقط الشعر.
    7. (MASSILYA Shampooing Anti-Pelliculaire 200ml) - السعر: 750 د.ج
       الفوائد: علاج فعال يقضي على القشرة وحكة الفروة.
    8. (MASSILYA Shampoing Cheveux Secs et Abimés 200ml) - السعر: 800 د.ج
       الفوائد: يغذي ويرمم الشعر الجاف والتالف.
    9. (MASSILYA Shampooing Anti Pelliculaire PSO F 200ml) - السعر: 780 د.ج
       الفوائد: شامبو متخصص للقشرة الصعبة والصدفية.
    10. (MASSILYA Crème Anti-Rugosité 30% Urée 120ml) - السعر: 850 د.ج
        الفوائد: علاج مكثف لجلد الدجاجة والخشونة الشديدة.
    11. (MASSILYA Lait Hydratant Emollient 5% Visage et Corps) - السعر: 850 د.ج
        الفوائد: حليب مرطب لطيف للوجه والجسم.
    12. (MASSILYA Lait Hydratant Emollient 10% Corps) - السعر: 1050 د.ج
        الفوائد: حليب مرطب مكثف ومغذي مخصص للجسم فقط.
    13. (MASSILYA Crème de Douche Lavante 400ml) - السعر: 500 د.ج
        الفوائد: كريم استحمام ينظف ويرطب الجسم في نفس الوقت.
    
    (ملاحظة هامة للمندوب: التزم فقط بالفوائد المكتوبة أعلاه ولا تضف شروحات من عندك).
    """
    
    answer = ""
    
    try:
        api_messages = [{"role": "system", "content": system_instruction}]
        for msg in request.history:
            api_messages.append({"role": msg.role, "content": msg.content})
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

    answer = re.sub(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', '', answer)

    try:
        bot_token = "8758469394:AAFnu5x88Bn1XZSPyEvninIoQ5-TB3JMpPw"
        chat_id = "-5299529077"
        if sum(char.isdigit() for char in user_message) >= 8:
            spy_message = f"💰🚨 طلبية جديدة!\n\n👤 الزبون:\n{user_message}\n\n🤖 المندوب:\n{answer}"
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": spy_message})
    except:
        pass

    return {"reply": answer}
