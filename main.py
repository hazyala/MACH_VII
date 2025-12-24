# main.py
import streamlit as st
import os
from engine import MachEngine
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="MACH VII - 통합 관제 센터", layout="wide")

if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], "last_vision_result": "대기 중",
        "current_emotion": "idle", "current_emotion_path": "assets/gif/idle.gif"
    })

@st.cache_resource
def load_engine():
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

engine = load_engine()

st.title("🛡️ MACH VII - 맹칠 관제 센터")
col_info, col_emo = st.columns([2, 1])

with col_info:
    st.info("영상은 별도 창에서 출력 중입니다. (RGB + Depth Map)")
    st.write(f"**탐지 정보:** {st.session_state.last_vision_result}")

with col_emo:
    # [수정] GIF 파일 경로 확인 및 출력
    if os.path.exists(st.session_state.current_emotion_path):
        st.image(st.session_state.current_emotion_path, width=150)
    else:
        st.error("표정 파일을 찾을 수 없습니다.")
    st.caption(f"상태: {st.session_state.current_emotion.upper()}")

st.divider()
chat_box = st.container(height=450)
for msg in st.session_state.messages:
    with chat_box.chat_message(msg["role"]): st.write(msg["content"])

if user_input := st.chat_input("명을 내리소서..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_box.chat_message("user"): st.write(user_input)
    
    with chat_box.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        answer = engine.run_agent(user_input, callbacks=[st_callback])
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun() # 표정 및 상태 즉시 반영