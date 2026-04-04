import os
import streamlit as st
import pandas as pd
import json
from openai import OpenAI

# --- إعداد API ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    st.error("Please set the OPENROUTER_API_KEY environment variable.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- واجهة المستخدم ---
st.set_page_config(page_title="💬 Chat with OpenRouter", layout="wide")
st.title("💬 OpenRouter Chat")

# تخزين الدردشة في Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# إدخال المستخدم
user_input = st.text_input("اكتب رسالتك هنا:")

if st.button("Send") and user_input:
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    
    # إضافة الدردشة السابقة
    for entry in st.session_state.chat_history:
        messages.append({"role": entry["role"], "content": entry["message"]})
    
    # إضافة رسالة المستخدم الجديدة
    messages.append({"role": "user", "content": user_input})
    
    # Placeholder لعرض النص أثناء وصوله
    chat_placeholder = st.empty()
    chat_text = ""
    
    # --- تدفق النص ---
    with client.chat.completions.stream(
        model="openai/gpt-5.2",
        messages=messages
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                chat_text += event.delta
                chat_placeholder.text(chat_text)
    
    # حفظ الرسائل في Session State
    st.session_state.chat_history.append({"role": "user", "message": user_input})
    st.session_state.chat_history.append({"role": "assistant", "message": chat_text})

# --- عرض الدردشة السابقة ---
st.subheader("📝 Chat History")
for entry in st.session_state.chat_history:
    role = "You" if entry["role"] == "user" else "Assistant"
    st.markdown(f"**{role}:** {entry['message']}")

# --- تصدير الدردشة ---
st.subheader("💾 Export Chat")
if st.session_state.chat_history:
    df = pd.DataFrame(st.session_state.chat_history)

    # JSON
    json_data = df.to_json(orient="records", force_ascii=False)
    st.download_button("Download JSON", json_data, file_name="chat.json", mime="application/json")

    # CSV
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", csv_data, file_name="chat.csv", mime="text/csv")

    # XLSX
    excel_buffer = pd.ExcelWriter("chat.xlsx", engine="xlsxwriter")
    df.to_excel(excel_buffer, index=False, sheet_name="Chat")
    excel_buffer.close()
    with open("chat.xlsx", "rb") as f:
        st.download_button("Download XLSX", f, file_name="chat.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
