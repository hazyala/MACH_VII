# main.py
# ================================================================================
# MACH VII - 통합 UI/UX 제어 시스템
# 사이드바 상태창, 사고 과정 콘솔, 실시간 비전 스트림이 결합된 메인 인터페이스입니다.
# ================================================================================

import streamlit as st
import threading
import time
import cv2
import requests
from PIL import Image
import numpy as np

# 프로젝트 내부 모듈들을 가져옵니다.
from logger import get_logger
from vision import VisionSystem
from agent import get_agent

# 'MAIN' 전용 로거를 초기화합니다.
logger = get_logger('MAIN')

# 화면을 넓게 사용하기 위해 와이드 레이아웃을 설정합니다.
st.set_page_config(
    page_title="MACH VII - 통합 관제 시스템",
    page_icon="🛡️",
    layout="wide"
)

def init_session_state():
    """
    시스템 운영에 필요한 모든 세션 변수를 초기화합니다.
    """
    if "vision_running" not in st.session_state:
        st.session_state.vision_running = False
    if "last_frame" not in st.session_state:
        st.session_state.last_frame = None
    if "last_vision_result" not in st.session_state:
        st.session_state.last_vision_result = "nothing"
    if "last_coordinates" not in st.session_state:
        st.session_state.last_coordinates = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_emotion" not in st.session_state:
        st.session_state.current_emotion = "idle"
    if "current_emotion_path" not in st.session_state:
        st.session_state.current_emotion_path = "assets/gif/idle.gif"
    # 에이전트의 사고 과정(Thought)을 저장할 변수입니다.
    if "agent_thoughts" not in st.session_state:
        st.session_state.agent_thoughts = ""

def check_system_status():
    """
    외부 서비스(Ollama 등)의 연결 상태를 확인합니다.
    """
    status = {"Ollama": "🔴 연결 안 됨", "RealSense": "🔴 미연결"}
    
    # 1. Ollama 연결 확인
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        if response.status_code == 200:
            status["Ollama"] = "🟢 정상"
    except:
        pass
        
    # 2. RealSense 상태 확인 (세션 상태 기준)
    if st.session_state.vision_running:
        status["RealSense"] = "🟢 작동 중"
        
    return status

def vision_thread_loop(vision_system):
    """
    비전 시스템을 별도의 실행 단위(Thread)로 구동하여 실시간성을 확보합니다.
    """
    while st.session_state.vision_running:
        try:
            frame, text, coords = vision_system.process_frame()
            if frame is not None:
                st.session_state.last_frame = frame
                st.session_state.last_vision_result = text
                st.session_state.last_coordinates = coords
            time.sleep(0.01)
        except Exception as e:
            logger.error(f"비전 루프 오류: {e}")
            break

def main():
    init_session_state()
    
    # 시스템 자원을 로드합니다.
    @st.cache_resource
    def load_systems():
        vision = VisionSystem('yolov11s.pt')
        agent = get_agent()
        return vision, agent

    vision, agent = load_systems()

    # 비전 스레드 자동 시작
    if not st.session_state.vision_running:
        st.session_state.vision_running = True
        t = threading.Thread(target=vision_thread_loop, args=(vision,), daemon=True)
        t.start()

    # ================================================================================
    # [비책 A & C] 사이드바 및 상태 지표
    # ================================================================================
    with st.sidebar:
        st.header("⚙️ 시스템 설정 및 상태")
        
        # 실시간 상태 지표 표시
        status = check_system_status()
        st.subheader("연결 상태")
        st.info(f"🤖 **Ollama:** {status['Ollama']}")
        st.info(f"👁️ **RealSense:** {status['RealSense']}")
        st.info(f"💾 **FalkorDB:** 🟡 준비 중") # Phase 2 예정
        
        st.divider()
        st.subheader("모델 정보")
        st.text("Vision: YOLOv11s")
        st.text("Brain: Gemma3:4b")
        
        if st.button("🔴 시스템 종료"):
            st.session_state.vision_running = False
            st.rerun()

    # ================================================================================
    # 메인 레이아웃 구성
    # ================================================================================
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # 실시간 영상 출력 구역
        st.subheader("👁️ 실시간 비전 모니터링")
        video_area = st.empty()
        
        # 탐지 정보 구역
        st.divider()
        info_area = st.empty()

    with col_right:
        # 감정 표현 구역
        st.subheader("😊 로봇 페르소나")
        emotion_area = st.empty()
        
        st.divider()
        # 채팅 및 사고 과정 구역
        st.subheader("💬 대화 시스템")
        chat_history = st.container(height=400)
        
        # [비책 B] 사고 과정 콘솔 (Expander 활용)
        with st.expander("🧠 맹칠이의 사고 과정 (ReAct Thought)", expanded=False):
            thought_area = st.empty()
            thought_area.code(st.session_state.agent_thoughts if st.session_state.agent_thoughts else "대기 중...")

        user_input = st.chat_input("명령을 하사하소서...")

    # ================================================================================
    # 실시간 렌더링 루프
    # ================================================================================
    while True:
        # 1. 영상 업데이트
        if st.session_state.last_frame is not None:
            rgb_frame = cv2.cvtColor(st.session_state.last_frame, cv2.COLOR_BGR2RGB)
            video_area.image(rgb_frame, channels="RGB", use_container_width=True)
            
            # 탐지 텍스트 업데이트
            info_text = f"**현재 감지:** {st.session_state.last_vision_result}\n\n"
            for c in st.session_state.last_coordinates:
                info_text += f"`{c['name']}`: ({c['x']}, {c['y']}, {c['z']}mm) | "
            info_area.write(info_text)

        # 2. 감정 GIF 업데이트
        with emotion_area:
            st.image(st.session_state.current_emotion_path, 
                     caption=f"상태: {st.session_state.current_emotion.upper()}")

        # 3. 채팅 메시지 출력
        with chat_history:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        # 4. 사용자 입력 처리
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("생각 중..."):
                try:
                    # 실제 에이전트 실행 및 사고 과정 기록
                    # (참고: agent_thoughts는 에이전트 실행 시 업데이트되도록 agent.py와 연동 필요)
                    response = agent.invoke({"input": user_input})
                    answer = response.get("output", "응답을 생성하지 못했습니다.")
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    # 테스트용 사고 과정 기록 (실제로는 에이전트 로그를 캡처해야 합니다)
                    st.session_state.agent_thoughts = f"입력: {user_input}\n결과: {answer[:50]}..."
                except Exception as e:
                    st.error(f"오정 발생: {e}")
            st.rerun()

        time.sleep(0.033) # 약 30fps 유지

if __name__ == "__main__":
    main()