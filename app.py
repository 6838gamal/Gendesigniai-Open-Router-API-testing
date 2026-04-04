import os
import streamlit as st
from openai import OpenAI

# قراءة مفتاح API من متغير البيئة
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    st.error("Please set the OPENROUTER_API_KEY environment variable.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

st.title("💬 OpenRouter Chat with Streamlit")

# إدخال المستخدم
user_input = st.text_input("اكتب رسالتك هنا:")

if st.button("Send") and user_input:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input},
    ]

    # Placeholder لعرض النص أثناء وصوله
    chat_placeholder = st.empty()
    chat_text = ""

    # استخدام Stream / تدفق النص
    with client.chat.completions.stream(
        model="openai/gpt-5.2",
        messages=messages
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                chat_text += event.delta
                chat_placeholder.text(chat_text)
          
