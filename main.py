import streamlit as st
import os
from engine import MachEngine
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="MACH VII - 통합 관제 센터", layout="wide")

if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], "current_emotion": "idle", 
        "current_emotion_path": "assets/gif/idle.gif"
    })

@st.cache_resource
def load_engine():
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

engine = load_engine()
# 엔진 객체를 세션에 공유합니다.
st.session_state.engine = engine 

st.title("🛡️ MACH VII - 맹칠 관제 센터")
col_info, col_emo = st.columns([2, 1])

with col_info:
    st.write(f"**현재 탐지:** {engine.last_vision_result}")

with col_emo:
    if os.path.exists(st.session_state.current_emotion_path):
        st.image(st.session_state.current_emotion_path, width=150)
    st.caption(f"상태: {st.session_state.current_emotion.upper()}")

st.divider()
chat_box = st.container(height=450)
for msg in st.session_state.messages:
    with chat_box.chat_message(msg["role"]): st.write(msg["content"])

if user_input := st.chat_input("명을 내리소서..."):
    # [핵심] 채팅 실행 직전, 엔진의 최신 프레임을 도구들이 접근할 수 있는 위치에 복사합니다.
    st.session_state.last_frame = engine.last_frame
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_box.chat_message("user"): st.write(user_input)
    
    with chat_box.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        answer = engine.run_agent(user_input, callbacks=[st_callback])
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()