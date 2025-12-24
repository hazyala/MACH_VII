# engine.py
# ================================================================================
# MACH VII - 실행 엔진 (경량화 및 터미널 로그 최적화 버전)
# ================================================================================

import threading
import time
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType
# 비전 시스템과 도구 모음을 가져옵니다.
from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

# 'ENGINE' 모듈 전용 로거를 생성합니다.
logger = get_logger('ENGINE')

class MachEngine:
    """비전 분석과 에이전트 추론을 담당하는 핵심 엔진 클래스입니다."""
    
    def __init__(self):
        # 1. 모델 경량화: 기존 's' 모델보다 훨씬 빠른 'yolov11n.pt'(나노)를 사용합니다.
        # 이 모델은 정확도는 소폭 낮으나 처리 속도가 비약적으로 빠릅니다.
        self.vision = VisionSystem('yolov11n.pt')
        
        # 2. 에이전트 초기화
        self.agent = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        """터미널 로그에 집중하도록 에이전트를 설정합니다."""
        # 로컬 Ollama 서버와 연결합니다.
        llm = ChatOllama(
            model="gemma3:4b", 
            base_url="http://localhost:11434", 
            temperature=0.0
        )
        
        system_instruction = (
            "당신은 인공지능 로봇 '맹칠'입니다. "
            "주어진 도구를 사용하여 질문에 정중하게 답변하세요. "
            "사고 과정은 상세히 출력하되, 최종 답변은 한국어로 작성하세요."
        )

        # verbose=True 설정을 통해 터미널에 사고 과정을 실시간으로 출력합니다.
        # UI 콜백을 제거하여 시스템 부하를 줄였습니다.
        return initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True, 
            handle_parsing_errors=True,
            agent_kwargs={"prefix": system_instruction}
        )

    def start_vision_loop(self):
        """별도의 스레드에서 비전 분석을 수행하여 메인 화면의 멈춤을 방지합니다."""
        if self.is_running:
            return
            
        def run():
            self.is_running = True
            logger.info("경량 비전 루프 가동 시작")
            while self.is_running:
                try:
                    # 카메라로부터 프레임과 탐지 데이터를 획득합니다.
                    frame, text, coords = self.vision.process_frame()
                    if frame is not None:
                        # 스트림릿 세션 상태에 실시간 데이터를 저장합니다.
                        st.session_state.last_frame = frame
                        st.session_state.last_vision_result = text
                        st.session_state.last_coordinates = coords
                    # 영상의 부드러움을 위해 대기 시간을 최소화(0.01초)합니다.
                    time.sleep(0.01)
                except Exception as e:
                    logger.error(f"비전 루프 오류: {e}")
                    break

        # 스레드를 생성하고 스트림릿 문맥을 부여하여 실행합니다.
        vision_thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(vision_thread)
        vision_thread.start()