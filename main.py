# main.py
# ================================================================================
# MACH VII - 통합 UI/UX 제어 시스템 (안정화 버전)
# 이전 프로젝트(Proto)의 에이전트 구동 방식과 현재의 실시간 UI를 통합한 코드입니다.
# ================================================================================

import streamlit as st
import threading
import time
import cv2
import requests
from PIL import Image
import numpy as np

# 로그 기록, 비전 처리, 에이전트 생성을 위한 내부 모듈을 가져옵니다.
from logger import get_logger
from vision import VisionSystem
from agent import get_agent

# 'MAIN' 모듈 전용 로거 객체를 생성하여 초기화합니다.
logger = get_logger('MAIN')

# 웹 화면의 레이아웃을 넓게 설정하고 브라우저 탭의 제목을 지정합니다.
st.set_page_config(
    page_title="MACH VII - 통합 관제 시스템",
    page_icon="🛡️",
    layout="wide"
)

def init_session_state():
    """
    프로그램 실행 중 데이터를 유지하기 위한 스트림릿 세션 상태 변수들을 초기화합니다.
    """
    # 비전 시스템의 실행 여부를 판단하는 논리형(Boolean) 변수입니다.
    if "vision_running" not in st.session_state:
        st.session_state.vision_running = False
    
    # 마지막으로 획득한 카메라 프레임 데이터를 저장하는 변수입니다.
    if "last_frame" not in st.session_state:
        st.session_state.last_frame = None
        
    # YOLO 모델이 분석한 결과 텍스트 정보를 저장하는 문자열 변수입니다.
    if "last_vision_result" not in st.session_state:
        st.session_state.last_vision_result = "nothing"
        
    # 탐지된 객체의 좌표 정보가 담긴 리스트 자료구조입니다.
    if "last_coordinates" not in st.session_state:
        st.session_state.last_coordinates = []
        
    # 사용자와 로봇 간의 대화 내역을 저장하는 리스트입니다.
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # 현재 로봇의 감정 상태 이름과 GIF 파일 경로를 관리하는 변수입니다.
    if "current_emotion" not in st.session_state:
        st.session_state.current_emotion = "idle"
    if "current_emotion_path" not in st.session_state:
        st.session_state.current_emotion_path = "assets/gif/idle.gif"
        
    # 에이전트가 추론하는 사고 과정(Thought)을 저장하여 화면에 표시할 변수입니다.
    if "agent_thoughts" not in st.session_state:
        st.session_state.agent_thoughts = ""

def check_system_status():
    """
    외부 인공지능 서버(Ollama) 및 카메라 장치의 연결 상태를 점검하는 함수입니다.
    """
    # 기본 상태를 '연결 안 됨'으로 설정한 딕셔너리 객체입니다.
    status = {"Ollama": "🔴 연결 안 됨", "RealSense": "🔴 미연결"}
    
    # 1. Ollama 서버에 태그 목록을 요청하여 연결 여부를 확인합니다.
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        if response.status_code == 200:
            status["Ollama"] = "🟢 정상"
    except Exception:
        pass
        
    # 2. 비전 스레드가 실행 중인지 확인하여 카메라 상태를 표시합니다.
    if st.session_state.vision_running:
        status["RealSense"] = "🟢 작동 중"
        
    return status

def vision_thread_loop(vision_system):
    """
    메인 UI와 별개로 백그라운드에서 끊임없이 영상을 분석하는 스레드 함수입니다.
    """
    while st.session_state.vision_running:
        try:
            # 비전 클래스의 process_frame 메서드를 호출하여 프레임과 분석 결과를 가져옵니다.
            frame, text, coords = vision_system.process_frame()
            if frame is not None:
                # 분석된 데이터를 세션 상태 변수에 실시간으로 저장합니다.
                st.session_state.last_frame = frame
                st.session_state.last_vision_result = text
                st.session_state.last_coordinates = coords
            
            # CPU 과부하 방지를 위해 0.01초 동안 대기합니다.
            time.sleep(0.01)
        except Exception as e:
            logger.error(f"비전 루프 실행 중 오류 발생: {e}")
            break

def main():
    """
    스트림릿 앱의 메인 UI 레이아웃을 구성하고 이벤트를 처리하는 핵심 함수입니다.
    """
    init_session_state()
    
    # 시스템 자원을 로드하며, cache_resource 데코레이터를 통해 한 번만 실행되도록 설정합니다.
    @st.cache_resource
    def load_systems():
        # YOLO 모델 파일을 로드하여 비전 시스템 객체를 생성합니다.
        vision = VisionSystem('yolov11s.pt')
        # 에이전트 생성 함수를 호출하여 두뇌 객체를 가져옵니다.
        agent_obj = get_agent()
        return vision, agent_obj

    vision_sys, agent_executor = load_systems()

    # 비전 분석을 담당할 백그라운드 스레드가 없다면 새로 시작합니다.
    if not st.session_state.vision_running:
        st.session_state.vision_running = True
        t = threading.Thread(target=vision_thread_loop, args=(vision_sys,), daemon=True)
        t.start()

    # 사이드바 영역: 시스템 설정 및 상태 정보 표시
    with st.sidebar:
        st.header("⚙️ 시스템 설정 및 상태")
        
        system_status = check_system_status()
        st.subheader("연결 상태")
        st.info(f"🤖 **Ollama:** {system_status['Ollama']}")
        st.info(f"👁️ **RealSense:** {system_status['RealSense']}")
        st.info(f"💾 **FalkorDB:** 🟡 준비 중")
        
        st.divider()
        st.subheader("모델 정보")
        st.text("Vision: YOLOv11s")
        st.text("Brain: Gemma3:4b")
        
        # 시스템 종료 버튼 클릭 시 실행 플래그를 거짓으로 변경합니다.
        if st.button("🔴 시스템 종료"):
            st.session_state.vision_running = False
            st.rerun()

    # 메인 화면 레이아웃 구성: 왼쪽은 영상 모니터링, 오른쪽은 대화창
    col_video, col_chat = st.columns([2, 1])

    with col_video:
        st.subheader("👁️ 실시간 비전 모니터링")
        # 영상이 표시될 빈 공간(Placeholder) 객체를 생성합니다.
        video_placeholder = st.empty()
        st.divider()
        info_placeholder = st.empty()

    with col_chat:
        st.subheader("😊 로봇 페르소나")
        emotion_placeholder = st.empty()
        st.divider()
        st.subheader("💬 대화 시스템")
        chat_container = st.container(height=400)
        
        # 에이전트의 사고 과정을 보여주는 확장 영역입니다.
        with st.expander("🧠 맹칠이의 사고 과정 (ReAct Thought)", expanded=False):
            thought_placeholder = st.empty()
            thought_placeholder.code(st.session_state.agent_thoughts if st.session_state.agent_thoughts else "대기 중...")

        # 사용자의 채팅 입력을 받는 구성 요소입니다.
        user_input = st.chat_input("명령을 하사하소서...")

    # 화면을 실시간으로 갱신하는 무한 루프입니다.
    while True:
        # 1. 비전 영상 업데이트: 세션에 저장된 최신 프레임을 RGB로 변환하여 출력합니다.
        if st.session_state.last_frame is not None:
            rgb_img = cv2.cvtColor(st.session_state.last_frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(rgb_img, channels="RGB", use_container_width=True)
            
            # 탐지된 객체 정보 텍스트를 업데이트합니다.
            summary_text = f"**현재 감지:** {st.session_state.last_vision_result}\n\n"
            for item in st.session_state.last_coordinates:
                summary_text += f"`{item['name']}`: ({item['x']}, {item['y']}, {item['z']}mm) | "
            info_placeholder.write(summary_text)

        # 2. 감정 GIF 이미지 업데이트
        with emotion_placeholder:
            st.image(st.session_state.current_emotion_path, 
                     caption=f"상태: {st.session_state.current_emotion.upper()}")

        # 3. 이전 채팅 메시지들을 화면에 출력합니다.
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # 4. 사용자 입력 처리 로직
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("생각 중..."):
                try:
                    # [중요] 이전 프로젝트(Proto) 방식인 딕셔너리 호출 형식을 사용합니다.
                    # langchain < 0.2.0 버전에서는 invoke 대신 이 방식을 주로 사용합니다.
                    agent_response = agent_executor({"input": user_input})
                    
                    # 응답 딕셔너리에서 'output' 키에 저장된 최종 답변을 추출합니다.
                    final_answer = agent_response.get("output", "응답을 생성하지 못했습니다.")
                    
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                    # 사고 과정을 세션 변수에 기록합니다.
                    st.session_state.agent_thoughts = f"입력된 명령: {user_input}\n최종 답변 요약: {final_answer[:50]}..."
                except Exception as err:
                    st.error(f"에이전트 실행 중 오류가 발생하였습니다: {err}")
                    logger.error(f"에이전트 오류 상세: {err}")
            
            # 입력 처리 후 화면을 즉시 새로고침합니다.
            st.rerun()

        # 약 30fps 수준으로 화면을 갱신하기 위해 짧게 대기합니다.
        time.sleep(0.033)

if __name__ == "__main__":
    main()