

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

# ========================== Custom CSS + Urdu Font ==========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    <style>
        .title { font-size: 30px; font-weight: bold; color: #075985; }
        .section { font-size: 22px; color: #0f172a; margin-top: 30px; }
        .label { font-weight: bold; font-size: 18px; }
        .json-box { background-color: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ========================== UI Layout ==========================
st.markdown('<div class="title">🩺 Emergency First-Aid Assistant</div>', unsafe_allow_html=True)
st.write("Ask your emergency question in **English or Urdu**. Type your query below.")

user_query = st.text_input("Type your emergency question:")

# ========================== Main Processing ==========================
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

# ✅ Show AI output based on lang
if ai_output:
    st.markdown('<div class="section">🤖 Assistant Guidance</div>', unsafe_allow_html=True)

    if lang == "urdu":
        st.markdown(f"""
        <div class='json-box' style='direction: rtl; text-align: right; font-family: "Noto Nastaliq Urdu", "Arial", sans-serif;'>
            {ai_output}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='json-box'>{ai_output}</div>", unsafe_allow_html=True)

    st.markdown('<div class="section">🔊 Voice Output</div>', unsafe_allow_html=True)
    play_audio(audio_file)
