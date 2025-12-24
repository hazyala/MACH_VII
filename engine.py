import threading
import time
import cv2
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType

from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

logger = get_logger('ENGINE')

class MachEngine:
    """
    비전 시스템과 AI 에이전트를 통합 관리하는 핵심 클래스입니다.
    """
    def __init__(self):
        # YOLO 모델 및 카메라 초기화
        self.vision = VisionSystem('yolo11n.pt')
        
        # 실시간 공유 데이터 (도구들이 참조할 데이터)
        self.last_frame = None
        self.last_vision_result = "nothing"
        self.last_coordinates = []
        
        # 에이전트 초기화
        self.agent_executor = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        """
        외부 서버의 Gemma3 27b 모델을 사용하여 에이전트를 설정합니다.
        """
        llm = ChatOllama(
            model="gemma3:27b", 
            base_url="http://ollama.aikopo.net", 
            temperature=0.0
        )
        
        system_instruction = (
            "당신은 인공지능 로봇 '맹칠'입니다. 한국어로 정중하게 답변하세요. "
            "1. 반드시 도구가 필요한 상황에서만 도구를 사용하세요. "
            "2. 카메라에 보이지 않는 물체는 없다고 정직하게 답변하세요."
        )

        return initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={"prefix": system_instruction}
        )

    def run_agent(self, user_input, callbacks=None):
        """에이전트에게 명령을 전달하고 결과를 반환합니다."""
        try:
            response = self.agent_executor.invoke(
                {"input": user_input},
                {"callbacks": callbacks}
            )
            return response.get("output", "답변을 생성하지 못했습니다.")
        except Exception as e:
            logger.error(f"에이전트 실행 중 오류: {e}")
            return f"오류가 발생했습니다: {str(e)}"

    def start_vision_loop(self):
        """백그라운드에서 실시간 영상을 분석하는 루프를 시작합니다."""
        def run():
            self.is_running = True
            logger.info("비전 루프 가동 시작")
            try:
                while self.is_running:
                    combined, color, text, coords = self.vision.process_frame()
                    if combined is not None:
                        # 엔진 내부에 실시간 데이터 업데이트
                        self.last_frame = color
                        self.last_vision_result = text
                        self.last_coordinates = coords
                        
                        cv2.imshow("MACH VII - Live Vision", combined)
                        if cv2.waitKey(1) & 0xFF == ord('q'): break
                    time.sleep(0.01)
            finally:
                cv2.destroyAllWindows()
                self.vision.release()
                logger.info("비전 루프 종료")

        thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(thread)
        thread.start()