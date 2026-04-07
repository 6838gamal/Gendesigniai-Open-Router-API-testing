import os
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
# إعداد API
# =========================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("❌ الرجاء تعيين OPENROUTER_API_KEY")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
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
# عرض الدردشة
# =========================
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# إدخال المستخدم
# =========================
user_input = st.chat_input("اكتب رسالتك...")

# =========================
# إرسال الرسالة
# =========================
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""

        try:
            # -------------------------
            # STREAMING MODE
            # -------------------------
            if USE_STREAM:
                try:
                    with client.chat.completions.stream(
                        model="openai/gpt-5.2",
                        messages=st.session_state.chat_history,
                    ) as stream:

                        for event in stream:
                            try:
                                delta = ""

                                # الحالة 1 (بعض النماذج)
                                if hasattr(event, "delta") and event.delta:
                                    delta = event.delta

                                # الحالة 2 (OpenAI-style)
                                elif hasattr(event, "choices"):
                                    delta = event.choices[0].delta.get("content", "")

                                if delta:
                                    full_text += delta
                                    placeholder.markdown(full_text)

                                if DEBUG_MODE:
                                    st.sidebar.write("EVENT:", str(event))

                            except Exception as e:
                                if DEBUG_MODE:
                                    st.sidebar.error(f"⚠️ Stream inner error: {e}")
                                continue

                except Exception as stream_error:
                    # -------------------------
                    # FALLBACK إلى non-stream
                    # -------------------------
                    if DEBUG_MODE:
                        st.sidebar.warning("⚠️ Streaming failed → fallback")
                        st.sidebar.error(stream_error)

                    response = client.chat.completions.create(
                        model="openai/gpt-5.2",
                        messages=st.session_state.chat_history,
                    )

                    full_text = response.choices[0].message.content
                    placeholder.markdown(full_text)

            # -------------------------
            # NON-STREAM MODE
            # -------------------------
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
                st.sidebar.error(f"🔥 Fatal Error: {str(e)}")

    # حفظ الرد
    st.session_state.chat_history.append(
        {"role": "assistant", "content": full_text}
    )

# =========================
# أدوات إضافية
# =========================
st.divider()
st.subheader("🧰 أدوات")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.chat_history = []
        st.rerun()

with col2:
    if st.session_state.chat_history:
        st.success("✔️ المحادثة جاهزة للتصدير")

# =========================
# التصدير
# =========================
if st.session_state.chat_history:
    df = pd.DataFrame(st.session_state.chat_history)

    st.subheader("💾 تصدير المحادثة")

    # JSON
    st.download_button(
        "📄 Download JSON",
        df.to_json(orient="records", force_ascii=False),
        file_name="chat.json",
        mime="application/json",
    )

    # CSV
    st.download_button(
        "📊 Download CSV",
        df.to_csv(index=False),
        file_name="chat.csv",
        mime="text/csv",
    )

    # Excel (آمن)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Chat")

    buffer.seek(0)

    st.download_button(
        "📘 Download Excel",
        buffer,
        file_name="chat.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# =========================
# Debug Info
# =========================
if DEBUG_MODE:
    st.sidebar.subheader("📊 Debug Info")
    st.sidebar.write("Messages Count:", len(st.session_state.chat_history))
