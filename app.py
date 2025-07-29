import streamlit as st 
import json
import speech_recognition as sr
import tempfile
import os
from groq import Groq
from gtts import gTTS
from langdetect import detect
import base64
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import wave
import io

# Custom base class since AudioProcessorBase is not available
class AudioProcessorBase:
    pass

# ========================== Config ==========================
st.set_page_config(page_title="Emergency First-Aid Assistant", layout="centered", page_icon="🩺")
API_KEY = "API_Key"
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

# ========================== UI ==========================
st.markdown('<div style="font-size:30px;font-weight:bold;color:#075985;">🩺 Emergency First-Aid Assistant</div>', unsafe_allow_html=True)
st.write("Ask your emergency question in **English or Urdu**. You can use voice or type your query.")

with st.expander("🔧 Input Options"):
    input_mode = st.radio("Choose input method:", ["🎤 Voice", "⌨️ Text"], horizontal=True)

user_query = ""

# 🎤 Voice Mode
if input_mode == "🎤 Voice":
    st.write("🎙️ Click below to record your voice")

    class AudioProcessor(AudioProcessorBase):
        def __init__(self):
            self.audio_data = b""

        def recv(self, frame):
            audio = frame.to_ndarray()
            self.audio_data += audio.tobytes()
            return frame

    ctx = webrtc_streamer(
        key="voice",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        rtc_configuration={},
        media_stream_constraints={"audio": True, "video": False},
        audio_processor_factory=AudioProcessor,
    )

    if ctx.state.playing:
        if ctx.audio_processor:
            audio_bytes = ctx.audio_processor.audio_data
            if audio_bytes:
                with st.spinner("🧠 Transcribing your voice..."):
                    # Save as WAV
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_bytes)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(wav_buffer.getvalue())
                        temp_wav_path = f.name

                    user_query = transcribe_audio(temp_wav_path)

                    if user_query:
                        st.success(f"📢 Detected: {user_query}")
                    else:
                        st.error("❌ Could not understand the audio.")

# ========================== Processing ==========================
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

    if json_match:
        st.markdown('<h3>📄 Emergency Information</h3>', unsafe_allow_html=True)
        st.markdown('<div style="background-color:#f8fafc;padding:10px;border-radius:8px;border:1px solid #e2e8f0;">', unsafe_allow_html=True)
        for item in json_match:
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    st.markdown(f"**{key.replace('_', ' ').title()}**")
                    st.code(json.dumps(value, indent=4, ensure_ascii=False), language="json")
                else:
                    st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Show AI Guidance
    st.markdown('<h3>☤ Emergency First Aid Guidance</h3>', unsafe_allow_html=True)
    direction = "rtl" if lang == "urdu" else "ltr"
    align = "right" if lang == "urdu" else "left"
    st.markdown(f'<div style="direction:{direction};text-align:{align};background:#f1f5f9;padding:10px;border-radius:8px;">{ai_output}</div>', unsafe_allow_html=True)

    # Voice Output
    if audio_file:
        st.markdown('<h3>🔊 Voice Output</h3>', unsafe_allow_html=True)
        play_audio(audio_file)
