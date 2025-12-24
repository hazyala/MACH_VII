import streamlit as st
import os
from engine import MachEngine
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="MACH VII - 통합 관제 센터", layout="wide")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], 
        "current_emotion": "idle", 
        "current_emotion_path": "assets/gif/idle.gif"
    })

@st.cache_resource
def load_engine():
    """엔진을 한 번만 생성하고 비전 루프를 실행합니다."""
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

# 엔진 생성 및 공유 보관함(Session State)에 저장
engine = load_engine()
st.session_state.engine = engine 

st.title("🛡️ MACH VII - 맹칠 관제 센터")
col_info, col_emo = st.columns([2, 1])

with col_info:
    st.info("영상은 별도 창(OpenCV)에서 출력 중입니다.")
    st.write(f"**현재 탐지 중:** {engine.last_vision_result}")

with col_emo:
    if os.path.exists(st.session_state.current_emotion_path):
        st.image(st.session_state.current_emotion_path, width=150)
    st.caption(f"현재 기분: {st.session_state.current_emotion.upper()}")

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
        st.rerun() # 감정 상태 즉시 반영을 위해 재실행