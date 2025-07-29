import streamlit as st
import json
import speech_recognition as sr
import tempfile
import os
from groq import Groq
from gtts import gTTS
from langdetect import detect
import base64


# ========================== Config ==========================
st.set_page_config(page_title="Emergency First-Aid Assistant", layout="centered", page_icon="🩺")
API_KEY = "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"
MODEL = "llama3-8b-8192"  # Ya koi aur supported model
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

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="ur-PK")
        except:
            return ""

def build_prompt(question, extracted_json, language):
    instruction = {
        "english": "You are an emergency first-aid assistant. If any structured data is provided, use it first. Then offer your own tips. Be clear and use bullet points.",
        "urdu": "آپ ایک ایمرجنسی فرسٹ ایڈ اسسٹنٹ ہیں۔ اگر کوئی ڈیٹا دیا گیا ہو تو پہلے اس کا استعمال کریں، پھر اپنی ہدایات دیں۔ جواب نکات کی صورت میں دیں۔",
    }

    if extracted_json:
        return f"{instruction[language]}\n\nUser asked: {question}\n\nRelevant emergency information:\n{json.dumps(extracted_json, ensure_ascii=False)}"
    else:
        return f"{instruction[language]}\n\nUser asked: {question}"


def search_json(query):
    results = []
    for entry in data:
        if query.lower() in str(entry.get("emergency_type", "")).lower():
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
        st.markdown(f'<audio controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

# ========================== Custom CSS ==========================
st.markdown("""
    <style>
        .title { font-size: 30px; font-weight: bold; color: #075985; }
        .section { font-size: 22px; color: #0f172a; margin-top: 30px; }
        .label { font-weight: bold; font-size: 18px; }
        .json-box { background-color: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ========================== UI Layout ==========================
st.markdown('<div class="title">🩺 Emergency First-Aid Assistant</div>', unsafe_allow_html=True)
st.write("Ask your emergency question in **English or Urdu**. You can use voice or type your query.")

with st.expander("🔧 Input Options"):
    input_mode = st.radio("Choose input method:", ["🎤 Voice", "⌨️ Text"], horizontal=True)

user_query = ""
if input_mode == "🎤 Voice":
    audio_data = st.file_uploader("Upload a WAV voice file:", type=["wav"])
    if audio_data:
        with st.spinner("Transcribing..."):
            user_query = transcribe_audio(audio_data)
            if user_query:
                st.success(f"📢 Detected: {user_query}")
            else:
                st.error("❌ Could not understand the audio. Please try again.")
else:
    user_query = st.text_input("Type your emergency question:")

# ========================== Main Processing ==========================

# Initialize variables
json_match = []
lang = ""
prompt = ""
ai_output = ""
audio_file = None

if st.button("🚑 Get Emergency Help") and user_query:
    with st.spinner("Analyzing your request..."):
        lang = detect_language(user_query)
        json_match = search_json(user_query)
        prompt = build_prompt(user_query, json_match, lang)
        ai_output = generate_answer(prompt)
        audio_file = text_to_audio(ai_output, lang)


    # Show emergency data only if match found
    if json_match:
        st.markdown('<div class="section">📄 Emergency Information</div>', unsafe_allow_html=True)
        st.markdown('<div class="json-box">', unsafe_allow_html=True)

        for item in json_match:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        st.markdown(f"**{key.capitalize().replace('_', ' ')}:**")
                        st.code(json.dumps(value, indent=4, ensure_ascii=False), language="json")
                    else:
                        st.markdown(f"**{key.capitalize().replace('_', ' ')}:** {value}")
            else:
                st.markdown(f"- {item}")

        st.markdown('</div>', unsafe_allow_html=True)



    # AI answer section
    st.markdown('<div class="section">☤ Emergency First Aid Guidance</div>', unsafe_allow_html=True)

# ✅ Set direction based on detected language
text_direction = "rtl" if lang == "urdu" else "ltr"
text_align = "right" if lang == "urdu" else "left"

# ✅ Apply direction + alignment to output box
st.markdown(
    f"<div class='json-box' style='direction: {text_direction}; text-align: {text_align};'>{ai_output}</div>",
    unsafe_allow_html=True
)


    # Voice output
    # Voice output
if audio_file:
        st.markdown('<div class="section">🔊 Voice Output</div>', unsafe_allow_html=True)
        play_audio(audio_file)

