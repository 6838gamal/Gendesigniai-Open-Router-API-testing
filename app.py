import os
import json
import datetime
import streamlit as st
import pandas as pd
from io import BytesIO
from openai import OpenAI

# =========================
# إعداد الصفحة
# =========================
st.set_page_config(page_title="💬 OpenRouter Chat Pro", layout="wide")
st.title("💬 OpenRouter Chat Pro")

# =========================
# API
# =========================
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("❌ الرجاء تعيين OPENROUTER_API_KEY")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# =========================
# إعدادات
# =========================
DEBUG_MODE = st.sidebar.toggle("🐞 Debug Mode", value=False)
USE_STREAM = st.sidebar.toggle("⚡ Streaming", value=True)

# =========================
# Session State
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# دوال مساعدة
# =========================
def add_message(role, content):
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "timestamp": str(datetime.datetime.now())
    })

def extract_messages_from_json(data):
    """دعم عدة صيغ JSON"""
    if isinstance(data, list):
        return data

    if "messages" in data:
        return data["messages"]

    if "conversation" in data:
        return data["conversation"]

    return []

# =========================
# عرض الدردشة
# =========================
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# إدخال المستخدم
# =========================
user_input = st.chat_input("اكتب رسالتك...")

if user_input:
    add_message("user", user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""

        try:
            if USE_STREAM:
                try:
                    with client.chat.completions.stream(
                        model="openai/gpt-5.2",
                        messages=st.session_state.chat_history,
                    ) as stream:

                        for event in stream:
                            try:
                                delta = ""

                                if hasattr(event, "delta") and event.delta:
                                    delta = event.delta

                                elif hasattr(event, "choices"):
                                    delta = event.choices[0].delta.get("content", "")

                                if delta:
                                    full_text += delta
                                    placeholder.markdown(full_text)

                                if DEBUG_MODE:
                                    st.sidebar.write(str(event))

                            except Exception as e:
                                if DEBUG_MODE:
                                    st.sidebar.error(f"Stream inner error: {e}")

                except Exception as e:
                    if DEBUG_MODE:
                        st.sidebar.warning("Streaming failed → fallback")
                        st.sidebar.error(str(e))

                    response = client.chat.completions.create(
                        model="openai/gpt-5.2",
                        messages=st.session_state.chat_history,
                    )
                    full_text = response.choices[0].message.content
                    placeholder.markdown(full_text)

            else:
                response = client.chat.completions.create(
                    model="openai/gpt-5.2",
                    messages=st.session_state.chat_history,
                )
                full_text = response.choices[0].message.content
                placeholder.markdown(full_text)

        except Exception as e:
            full_text = "❌ حدث خطأ أثناء توليد الرد"
            placeholder.error(full_text)

            if DEBUG_MODE:
                st.sidebar.error(f"Fatal Error: {e}")

    add_message("assistant", full_text)

# =========================
# أدوات
# =========================
st.divider()
st.subheader("🧰 أدوات")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.chat_history = []
        st.rerun()

# =========================
# التصدير (متوافق OpenRouter)
# =========================
if st.session_state.chat_history:
    st.subheader("💾 تصدير")

    export_data = {
        "model": "openai/gpt-5.2",
        "created_at": str(datetime.datetime.now()),
        "messages": st.session_state.chat_history,
        "source": "Streamlit OpenRouter App"
    }

    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)

    st.download_button(
        "📄 OpenRouter JSON",
        json_data,
        file_name="openrouter_chat.json",
        mime="application/json"
    )

    # CSV / Excel
    df = pd.DataFrame(st.session_state.chat_history)

    st.download_button("📊 CSV", df.to_csv(index=False), "chat.csv")

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)

    buffer.seek(0)

    st.download_button(
        "📘 Excel",
        buffer,
        file_name="chat.xlsx"
    )

# =========================
# الاستيراد
# =========================
st.subheader("📂 استيراد محادثة")

uploaded_file = st.file_uploader("Upload JSON", type=["json"])

if uploaded_file:
    try:
        data = json.load(uploaded_file)
        messages = extract_messages_from_json(data)

        if messages:
            st.session_state.chat_history = messages
            st.success("✅ تم استيراد المحادثة")
            st.rerun()
        else:
            st.error("❌ صيغة الملف غير مدعومة")

    except Exception as e:
        st.error("❌ فشل قراءة الملف")
        if DEBUG_MODE:
            st.sidebar.error(str(e))

# =========================
# Debug
# =========================
if DEBUG_MODE:
    st.sidebar.subheader("📊 Debug")
    st.sidebar.write("Messages:", len(st.session_state.chat_history))
