import streamlit as st
import json
import tempfile
import os
from groq import Groq
from gtts import gTTS
from langdetect import detect
import base64

# ========================== Config ==========================
st.set_page_config(page_title="AidMate Emergency First-Aid Assistant", layout="centered", page_icon="🩺")
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
        "english": """You are a highly experienced emergency first aid assistant trusted by thousands of users. 
Based on the given data, generate expert-level first aid guidance with two clearly separated sections:

1. ✅ Adult First Aid Guidance  
2. 🧒 Child First Aid Guidance  

Each section must be:
- Clear, bulleted, and step-by-step  
- Calm, confident, and compassionate in tone  
- Include natural remedies if they are safe and medically sound (like honey, aloe vera, or clean cool water)  
- Avoid any mention of data sources, AI, or technical process  
- Speak like a professional medical assistant or paramedic — not like an AI

You are a trusted emergency first-aid assistant. First, provide detailed and accurate guidance for **adults**, then for **children**.

Follow this format:
1. Start with first aid instructions based on the provided emergency information.
2. Add additional expert tips, risks, and natural remedies where possible.
3. Separate sections clearly: one for Adults, one for Children.

Answer in bullet points using a clear and calm tone.
""",
        "urdu": """آپ ایک نہایت تجربہ کار اور قابلِ اعتماد ایمرجنسی فرسٹ ایڈ ماہر ہیں۔ دی گئی معلومات کی بنیاد پر دو واضح حصوں میں ہدایات فراہم کریں:

1. ✅ بڑوں کے لیے ابتدائی طبی امداد  
2. 🧒 بچوں کے لیے ابتدائی طبی امداد  

ہر سیکشن میں درج ذیل باتوں کا خیال رکھیں:
- نکات کی صورت میں آسان اور واضح اقدامات لکھیں  
- انداز پُرامن، پراعتماد اور ہمدرد ہو  
- اگر طبی طور پر محفوظ ہو تو قدرتی علاج (جیسے شہد، ایلو ویرا، یا ٹھنڈا پانی) شامل کریں  
- کسی بھی قسم کا سورس، AI یا ڈیٹا کا ذکر نہ کریں  
- ماہرِ طب یا پیرامیڈک کی طرح سیدھی، اعتماد والی بات کریں — مشورہ دینے والے AI کی طرح نہیں

آپ ایک قابلِ اعتماد ایمرجنسی فرسٹ ایڈ اسسٹنٹ ہیں۔ پہلے **بالغ افراد** کے لیے تفصیلی اور درست ہدایات دیں، پھر **بچوں** کے لیے دیں۔

مندرجہ ذیل انداز میں جواب دیں:
1. دی گئی ایمرجنسی معلومات کی بنیاد پر پہلے فرسٹ ایڈ بتائیں۔
2. پھر ماہرانہ تجاویز، خطرات، اور قدرتی علاج کے طریقے شامل کریں۔
3. بالغ اور بچوں کی رہنمائی کو واضح طور پر الگ الگ سیکشن میں لکھیں۔

نکات کی شکل میں صاف اور پر اعتماد لہجے میں جواب دیں۔
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
    st.image("https://aidmate-app.netlify.app/AidMate-removebg-preview.png", width=150)
    st.markdown("### 🩺 AidMate Assistant")
    st.markdown("Ask questions like:")
    st.markdown("- Burn treatment\n- Nose bleeding\n- Fracture steps")
    st.markdown("---")
    st.markdown("**Build For Emergency Support.**")

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

# st.markdown("""
# <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;'>
#     <img src='https://aidmate-app.netlify.app/AidMate-removebg-preview.png' alt='AidMate Logo' style='height: 180px;' />
#     <h2 style='color: black; font-weight: bold; font-size: 24px; margin: 0;'>AidMate – Smart First Aid Emergency Assistant</h2>
# </div>
# """, unsafe_allow_html=True)


st.markdown("""
<div style='
    display: flex; 
    align-items: center; 
    gap: 20px; 
    flex-wrap: wrap; 
    justify-content: center;
    margin-bottom: 30px;
'>

    <div style='flex-shrink: 0;'>
        <img src='https://aidmate-app.netlify.app/AidMate-removebg-preview.png' alt='AidMate Logo' style='height: 180px;' />
    </div>

    <div style='flex-grow: 1; min-width: 250px; text-align: left;'>
        <h2 style='color: black; font-size: 26px; margin: 0;'>
            AidMate – Smart First Aid Emergency Assistant
        </h2>
    </div>

</div>
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



