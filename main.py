import streamlit as st
import os
from logger import setup_terminal_logging

# 에이전트의 사고 과정을 포함한 모든 터미널 내용을 파일로 저장합니다.
setup_terminal_logging()

from engine import MachEngine
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="MACH VII - 통합 관제 센터", layout="wide")

# 세션 상태(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], 
        "current_emotion": "idle", 
        "current_emotion_path": "assets/gif/idle.gif"
    })

@st.cache_resource
def load_engine():
    """엔진 클래스 인스턴스를 생성하고 비전 루프 스레드를 시작합니다."""
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

# 엔진 로드 및 세션 공유
engine = load_engine()
st.session_state.engine = engine 

st.title("🛡️ MACH VII - 맹칠 관제 센터")
col_info, col_emo = st.columns([2, 1])

with col_info:
    st.info("실시간 영상과 에이전트의 사고 과정이 터미널 및 로그 파일에 기록 중입니다.")
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
    # 비전 분석 도구가 참조할 최신 프레임을 세션에 복사합니다.
    st.session_state.last_frame = engine.last_frame
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_box.chat_message("user"): st.write(user_input)
    
    with chat_box.chat_message("assistant"):
        # 스트림릿 화면에 사고 과정을 보여주는 콜백 핸들러입니다.
        st_callback = StreamlitCallbackHandler(st.container())
        # 에이전트 실행 (verbose=True에 의해 모든 과정이 터미널과 파일에 찍힙니다.)
        answer = engine.run_agent(user_input, callbacks=[st_callback])
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()