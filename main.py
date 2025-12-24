# main.py
# ================================================================================
# MACH VII - 통합 관제 시스템 (실시간 자동 갱신 버전)
# engine.py의 데이터를 streamlit-autorefresh를 통해 실시간으로 화면에 출력합니다.
# ================================================================================

import streamlit as st
import cv2
from streamlit_autorefresh import st_autorefresh
from engine import MachEngine
from logger import get_logger

# 'MAIN' 모듈의 로그 기록을 위한 객체를 생성합니다.
logger = get_logger('MAIN')

# 페이지 레이아웃을 넓게 설정하고 제목을 지정합니다.
st.set_page_config(page_title="MACH VII - 통합 관제 센터", layout="wide")

# 세션 상태(st.session_state) 변수들을 초기화합니다.
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], 
        "last_frame": None, 
        "last_vision_result": "nothing",
        "current_emotion": "idle", 
        "current_emotion_path": "assets/gif/idle.gif"
    })

# [핵심] 실시간 화면 갱신 설정: 200ms(0.2초)마다 화면을 강제로 다시 그립니다.
# 이 위젯은 화면에 보이지 않으며, 배경에서 Rerun을 트리거하는 역할을 수행합니다.
st_autorefresh(interval=200, key="framer_refresh")

# 엔진 객체를 캐시를 사용하여 1회만 생성하고 비전 루프를 시작합니다.
@st.cache_resource
def load_maengchil_engine():
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

engine = load_maengchil_engine()

# --- 레이아웃 구성 ---
st.title("🛡️ MACH VII - 맹칠 실시간 제어")
col_vid, col_chat = st.columns([2, 1])

with col_vid:
    st.subheader("👁️ 실시간 비전 스트림 (Autorefresh On)")
    # 영상이 표시될 공간을 지정합니다.
    video_placeholder = st.empty()
    
    # 세션 상태에 저장된 최신 프레임이 있다면 화면에 출력합니다.
    if st.session_state.last_frame is not None:
        # OpenCV의 BGR 형식을 Streamlit이 인식하는 RGB 형식으로 변환합니다.
        rgb_image = cv2.cvtColor(st.session_state.last_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(rgb_image, use_container_width=True)
    
    # 현재 탐지된 객체 정보를 출력합니다.
    st.info(f"실시간 분석 결과: {st.session_state.last_vision_result}")

with col_chat:
    # 맹칠의 현재 감정 이미지를 출력합니다.
    st.image(st.session_state.current_emotion_path, width=180)
    st.caption(f"상태: {st.session_state.current_emotion.upper()}")
    
    st.divider()
    st.subheader("💬 대화 시스템")
    # 대화 기록을 표시하는 컨테이너입니다.
    chat_box = st.container(height=450)
    
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자로부터 명령을 입력받습니다.
    if user_command := st.chat_input("명을 내리소서..."):
        # 사용자의 질문을 세션 상태에 저장합니다.
        st.session_state.messages.append({"role": "user", "content": user_command})
        
        with st.spinner("생각 중이옵니다..."):
            try:
                # 에이전트에게 명령을 전달하고 답변을 받습니다.
                # 사고 과정(Thought)은 터미널 로그에 실시간으로 출력됩니다.
                result = engine.agent({"input": user_command})
                final_answer = result.get("output", "답변을 생성할 수 없습니다.")
                
                # 에이전트의 답변을 세션 상태에 저장하고 화면을 갱신합니다.
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                st.rerun()
            except Exception as e:
                st.error(f"실행 중 오류가 발생했습니다: {e}")
                logger.error(f"에이전트 실행 오류: {e}")