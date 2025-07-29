import streamlit as st
import json
from groq import Groq
from langdetect import detect

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
        "english": "You are an emergency first-aid assistant. If any structured data is provided, use it first. Then offer your own tips. Be clear and use bullet points and emojis if helpful.",
        "urdu": "آپ ایک ایمرجنسی فرسٹ ایڈ اسسٹنٹ ہیں۔ اگر کوئی ڈیٹا دیا گیا ہو تو پہلے اس کا استعمال کریں، پھر اپنی ہدایات دیں۔ جواب نکات اور ایموجیز کی مدد سے واضح انداز میں دیں۔",
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
    client = Groq(api_key=API_KEY)  # ✅ Fixed here
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )
    return response.choices[0].message.content

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
st.write("Ask your emergency question in **English or Urdu**. You can type your query below:")

user_query = st.text_input("🔍 Type your emergency question:")

# ========================== Main Processing ==========================
json_match = []
lang = ""
prompt = ""
ai_output = ""

if st.button("🚑 Get Emergency Help") and user_query:
    with st.spinner("Analyzing your request..."):
        lang = detect_language(user_query)
        json_match = search_json(user_query)
        prompt = build_prompt(user_query, json_match, lang)
        ai_output = generate_answer(prompt)

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

    st.markdown('<div class="section">☤ Emergency First Aid Guidance</div>', unsafe_allow_html=True)

    text_direction = "rtl" if lang == "urdu" else "ltr"
    text_align = "right" if lang == "urdu" else "left"

    st.markdown(
        f"<div class='json-box' style='direction: {text_direction}; text-align: {text_align}; white-space: pre-wrap;'>{ai_output}</div>",
        unsafe_allow_html=True
    )
