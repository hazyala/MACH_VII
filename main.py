# main.py
import streamlit as st
import cv2
import time
from engine import MachEngine, StreamlitThoughtHandler
from logger import get_logger

logger = get_logger('MAIN')

st.set_page_config(page_title="MACH VII 관제 시스템", layout="wide")

# 세션 변수 초기화 (기존 변수 유지)
if "agent_thoughts" not in st.session_state:
    st.session_state.agent_thoughts = ""

@st.cache_resource
def init_engine():
    eng = MachEngine()
    eng.start_vision_loop()
    return eng

engine = init_engine()

# --- 레이아웃 분리 ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("👁️ 실시간 비전 (2.1 FPS)")
    video_area = st.empty()
    # 영상 표시 (영상이 멈추지 않도록 빈 공간을 활용)
    if st.session_state.last_frame is not None:
        img = cv2.cvtColor(st.session_state.last_frame, cv2.COLOR_BGR2RGB)
        video_area.image(img, use_container_width=True)
    st.info(f"감지됨: {st.session_state.last_vision_result}")

with col_right:
    st.image(st.session_state.current_emotion_path, width=150)
    
    # [핵심] 마마께서 원하신 사고 과정 출력창
    st.subheader("🧠 맹칠이의 생각 주머니")
    with st.container(height=250, border=True):
        st.markdown(st.session_state.agent_thoughts)

    # 채팅 시스템
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])

    if prompt := st.chat_input("명을 내리소서..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.agent_thoughts = f"💬 **마마의 명:** {prompt}\n"
        st.rerun()

# 에이전트 실행 로직 (입력이 있을 때만 수행)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    with st.spinner("생각 중이옵니다..."):
        # StreamlitThoughtHandler를 통해 사고 과정을 실시간으로 가로챕니다.
        response = engine.agent(
            {"input": last_user_msg}, 
            callbacks=[StreamlitThoughtHandler()]
        )
        ans = response.get("output", "답변 실패")
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

# ⚠️ 주의: 무한 루프 제거 후 스트림릿이 스스로 돌게 놔둡니다.