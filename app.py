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
        "english": "You are an emergency first-aid assistant. First, answer using the provided emergency information. Then, offer your own tips and warnings. Be clear and use bullet points.",
        "urdu": "آپ ایک ایمرجنسی فرسٹ ایڈ اسسٹنٹ ہیں۔ پہلے دی گئی ایمرجنسی معلومات سے جواب دیں، پھر اپنی معلومات سے مزید ہدایات اور احتیاطی تدابیر دیں۔ جواب نکات کی صورت میں دیں۔",
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



