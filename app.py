import streamlit as st
import json
import tempfile
import os
from groq import Groq
from gtts import gTTS
from langdetect import detect
import base64

# ========================== Config ==========================
st.set_page_config(page_title="Emergency First-Aid Assistant", layout="centered", page_icon="🩺")
API_KEY = "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"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
JSON_FILE = "data.json"

# ========================== Load JSON ==========================
@st.cache_data
def load_json():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_json()

# ========================== Utility Functions ==========================
def detect_language(text):
    try:
        lang = detect(text)
        return "urdu" if lang == "ur" else "english"
    except:
        return "english"

def build_prompt(question, extracted_json, language):
    instruction = {
        "english": """You are a senior emergency first aid specialist trusted by hospitals, paramedics, and thousands of users. Your role is to calmly and clearly guide people in crisis using professional, life-saving instructions.

Based on the provided emergency data and symptoms, generate a structured, expert-level response with **two distinct sections**:

1. ✅ Adult First Aid Guidance  
2. 🧒 Child First Aid Guidance  

For each section:
- Use clear bullet points and explain actions step-by-step  
- Speak in a calm, confident, and compassionate tone  
- Include practical natural remedies only if they are medically sound and safe (e.g., honey, aloe vera, cool water)  
- Avoid any mention of AI, data processing, or how the response is generated  
- Write like a trusted paramedic, EMT, or nurse — human, not robotic

Your response must:
- Begin with first aid steps from the emergency info provided  
- Follow up with expert tips, potential risks, and aftercare  
- Clearly separate adult and child guidance to avoid confusion

Always prioritize user safety, trust, and understanding.

Formatting Guidelines:
- Use clear bullet points (• or ✅) for each instruction.
- Keep each bullet short, but informative and direct.
- Begin with a **short heading or subheading** (bolded or emoji-highlighted if needed).
- Break complex instructions into numbered steps (1, 2, 3) where needed.
- Add expert tips and aftercare advice under a separate section (e.g., **⚠️ Tips & Warnings**).
- When mentioning natural remedies, clearly state how and when to use them safely.
- Structure response like this:

✅ **Adult First Aid Guidance**
• [Title/Condition Summary]  
• Step-by-step actions  
• Safe remedies  
• Tips and risks  

🧒 **Child First Aid Guidance**
• [Title/Condition Summary]  
• Step-by-step actions  
• Safe remedies  
• Tips and risks

Avoid repetition and always write in a **reassuring, professional tone** like a trusted emergency responder.
""",
        "urdu": """آپ ایک سینیئر ایمرجنسی فرسٹ ایڈ ماہر ہیں جن پر اسپتال، پیرامیڈکس، اور ہزاروں افراد اعتماد کرتے ہیں۔ آپ کا کام ہے کہ ایمرجنسی کی حالت میں لوگوں کو پُر اعتماد اور ہمدردی سے درست طبی رہنمائی فراہم کریں۔

دی گئی علامات اور معلومات کی بنیاد پر درج ذیل دو الگ الگ حصوں میں ماہر سطح کی رہنمائی فراہم کریں:

1. ✅ بڑوں کے لیے ابتدائی طبی امداد  
2. 🧒 بچوں کے لیے ابتدائی طبی امداد  

ہر سیکشن میں:
- نکات کی شکل میں قدم بہ قدم آسان اور عملی ہدایات دیں  
- لہجہ پرسکون، پراعتماد اور ہمدردانہ ہو  
- اگر طبی طور پر محفوظ ہوں تو قدرتی علاج بھی شامل کریں (جیسے ٹھنڈا پانی، شہد، ایلو ویرا وغیرہ)  
- AI، ڈیٹا، یا سورس کے بارے میں کچھ بھی نہ لکھیں  
- ماہر ڈاکٹر یا پیرامیڈک کی طرح بات کریں — مشینی انداز سے پرہیز کریں

آپ کی رہنمائی میں شامل ہو:
- سب سے پہلے ابتدائی طبی امداد کی عملی معلومات  
- پھر اضافی ماہر تجاویز، خطرات، اور بعد ازاں احتیاطی تدابیر  
- بڑوں اور بچوں کے لیے رہنمائی بالکل الگ ہو تاکہ کوئی کنفیوژن نہ ہو

ہمیشہ صارف کی سلامتی، بھروسا، اور سمجھ بوجھ کو اولین ترجیح دیں۔

فارمیٹنگ ہدایات:
- ہر ہدایت کے لیے واضح نقطہ وار انداز استعمال کریں (• یا ✅).
- ہر نکتہ مختصر، براہِ راست اور معلوماتی ہونا چاہیے.
- اگر ممکن ہو تو ہر سیکشن کا آغاز ایک چھوٹے عنوان یا سرخی سے کریں (bold یا emoji کے ساتھ).
- اگر کوئی عمل پیچیدہ ہو تو اسے نمبر وار مراحل میں توڑ کر لکھیں (1، 2، 3).
- اضافی معلومات اور احتیاطی تدابیر ایک الگ سیکشن میں لکھیں (جیسے: ⚠️ ماہرانہ مشورے یا احتیاطیں).
- اگر کوئی قدرتی علاج شامل کریں تو یہ بھی واضح کریں کہ کب اور کیسے استعمال کرنا محفوظ ہے.
- اس انداز میں ترتیب دیں:

✅ **بڑوں کے لیے ابتدائی طبی امداد**  
• [مرض یا حادثے کا خلاصہ]  
• قدم بہ قدم اقدامات  
• محفوظ قدرتی علاج  
• احتیاطی تدابیر اور ماہر مشورے  

🧒 **بچوں کے لیے ابتدائی طبی امداد**  
• [مرض یا چوٹ کا خلاصہ]  
• مکمل اقدامات  
• علاج اور نرمی کے طریقے  
• اہم مشورے

انداز ہمیشہ پراعتماد، ماہر اور انسانی ہونا چاہیے — ایسا جیسے کوئی قابلِ اعتماد پیرامیڈک مدد کر رہا ہو۔

"""
    }

    if extracted_json:
        pretty_info = ""
        for item in extracted_json:
            for key, value in item.items():
                pretty_info += f"{key}:\n"
                if isinstance(value, list):
                    for v in value:
                        pretty_info += f"- {v}\n"
                else:
                    pretty_info += f"{value}\n"
        info_part = f"\n\nHere is some emergency information that may help:\n{pretty_info}"
    else:
        info_part = ""

    return f"{instruction[language]}\n\nUser asked: {question}{info_part}"

def search_json(query):
    results = []
    for entry in data:
        emergency_type = entry.get("emergency_type", "")
        if query.lower() in emergency_type.lower():
            results.append(entry)
    return results

def generate_answer(prompt):
    client = Groq(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )
    return response.choices[0].message.content

def text_to_audio(text, language_code):
    tts = gTTS(text=text, lang="ur" if language_code == "urdu" else "en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        return f.name

def play_audio(path):
    with open(path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

# ========================== Sidebar ==========================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3771/3771563.png", width=100)
    st.markdown("### 🩺 AidMate Assistant")
    st.markdown("Ask questions like:")
    st.markdown("- Burn treatment\n- Nose bleeding\n- Fracture steps")
    st.markdown("---")
    st.markdown("Build for emergency support.")

# ========================== Custom CSS ==========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    <style>
        .stTextInput > div > div > input {
            border: 2px solid #4F46E5;
            border-radius: 10px;
            padding: 8px;
        }
        .stButton > button {
            background-color: #0ea5e9;
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
            border: none;
            margin-top: 15px;
        }
        .stButton > button:hover {
            background-color: #0369a1;
        }
    </style>
""", unsafe_allow_html=True)

# ========================== Gradient Title ==========================
st.markdown("""
    <h2 style='
        background: linear-gradient(to right, #2563eb, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 36px;
        font-weight: 800;
        text-align: center;
        margin-top: 20px;
    '>AidMate - Smart First Aid Assistant</h2>
""", unsafe_allow_html=True)

# ========================== Input UI ==========================
st.write("Ask your emergency question in **English or Urdu**.")
user_query = st.text_input("Type your emergency question:")

# ========================== Main Logic ==========================
lang = None
ai_output = None
audio_file = None
json_match = []

if st.button("🚑 Get Emergency Help") and user_query:
    with st.spinner("Analyzing your request..."):
        lang = detect_language(user_query)
        json_match = search_json(user_query)
        prompt = build_prompt(user_query, json_match, lang)
        ai_output = generate_answer(prompt)
        audio_file = text_to_audio(ai_output, lang)

        if json_match:
            st.markdown('<div class="section">📄 Matched Emergency Info (from JSON)</div>', unsafe_allow_html=True)
            st.code(json.dumps(json_match, ensure_ascii=False, indent=2), language="json")

# ========================== AI Response Output ==========================
if ai_output:
    st.markdown('<div class="section">🤖 Assistant Guidance</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class='json-box' style='
            direction: {"rtl" if lang == "urdu" else "ltr"};
            text-align: {"right" if lang == "urdu" else "left"};
            font-family: {"Noto Nastaliq Urdu" if lang == "urdu" else "Segoe UI"}, sans-serif;
            font-size: 18px;
            background-color: #f1f5f9;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #cbd5e1;
            margin-top: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        '>
            {ai_output}
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section">🔊 Voice Output</div>', unsafe_allow_html=True)
    play_audio(audio_file)

# ========================== Footer ==========================
st.markdown("""
    <hr style='margin-top:40px;'>
    <p style='text-align: center; font-size: 14px; color: gray;'>
        © 2025 AidMate | Made by Aleeza
    </p>
""", unsafe_allow_html=True)



