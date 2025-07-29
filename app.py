import streamlit as st
from groq import Groq
import json
import speech_recognition as sr
import os

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="AidMate Bot", layout="centered")
st.title("🩺 AidMate - Emergency First Aid Assistant")

# ---------------------- Load JSON Emergency Data ----------------------
with open("emergency_data.json", "r", encoding="utf-8") as f:
    emergency_data = json.load(f)

# ---------------------- Groq Response Function ----------------------
def generate_answer(prompt):
    client = Groq()  # It uses the GROQ_API_KEY from environment variables

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )

    return response.choices[0].message.content

# ---------------------- Voice Input Function ----------------------
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Speak now...")
        audio = r.listen(source, timeout=5)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand your voice."
    except sr.RequestError:
        return "Sorry, speech recognition service is not working."

# ---------------------- Main Input Section ----------------------
option = st.radio("Choose input method:", ["📝 Text", "🎤 Voice"])

if option == "📝 Text":
    user_input = st.text_input("Enter your emergency situation:")
elif option == "🎤 Voice":
    if st.button("Start Recording"):
        user_input = recognize_speech()
        st.write("You said:", user_input)
    else:
        user_input = ""

# ---------------------- Process & Respond ----------------------
if st.button("🚑 Get First Aid Guidance") and user_input:
    matched_info = None
    for condition in emergency_data["emergencies"]:
        if condition["keyword"].lower() in user_input.lower():
            matched_info = condition
            break

    if matched_info:
        st.subheader("📘 Emergency Information:")
        st.write(matched_info["description"])

        prompt = f"""Based on the following emergency: "{matched_info['description']}", provide clear and simple step-by-step first aid instructions. Respond in bullet points."""
    else:
        # ⚠️ Line removed as per your request – user won't know
        prompt = f"""The user described an emergency as: "{user_input}". Provide first aid guidance in simple steps. Respond in bullet points."""

    ai_output = generate_answer(prompt)
    st.subheader("🤖 AI First Aid Guidance:")
    st.write(ai_output)

