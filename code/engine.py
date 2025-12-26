import threading
import time
import cv2
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType

from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

# 시스템 엔진 및 에이전트 기록을 위한 로거 설정
logger = get_logger('ENGINE')
agent_logger = get_logger('AGENT')

class AgentFileLogger(BaseCallbackHandler):
    """
    에이전트의 사고 과정(Thought, Action 등)을 실시간으로 가로채어 
    로그 파일에 기록하는 사관 역할을 수행합니다.
    """
    def on_chain_start(self, serialized, inputs, **kwargs):
        agent_logger.info("\n> Entering new AgentExecutor chain...")

    def on_text(self, text, **kwargs):
        if text:
            clean_text = text.strip()
            if clean_text:
                agent_logger.info(f"{clean_text}")

    def on_agent_action(self, action, **kwargs):
        agent_logger.info(f"Action: {action.tool}")
        agent_logger.info(f"Action Input: {action.tool_input}")
        
    def on_tool_end(self, output, **kwargs):
        agent_logger.info(f"Observation: {output}")

    def on_agent_finish(self, finish, **kwargs):
        agent_logger.info(f"Final Answer: {finish.return_values['output']}")
        agent_logger.info("> Finished chain.\n")

class MachEngine:
    def __init__(self):
        """
        비전 시스템과 에이전트를 초기화합니다.
        vision.py가 절대 경로를 사용하므로 인자 없이 호출합니다.
        """
        self.vision = VisionSystem()
        self.last_frame = None
        self.last_vision_result = "nothing"
        self.last_coordinates = []
        
        # 맹칠이의 사고를 담당할 에이전트 초기화
        self.agent_executor = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        """
        에이전트의 성격과 행동 지침을 설정합니다.
        """
        # 고성능 추론 모델인 gemma3:27b를 기본으로 사용합니다.
        llm = ChatOllama(model="gemma3:27b", base_url="http://ollama.aikopo.net", temperature=0.0)
        
        # 마마께서 하사하신 맹칠이의 엄격한 8대 행동 강령
        system_instruction = (
            "당신은 로봇 조수 '맹칠'입니다. 한국어로 정중히 답변하세요. "
            "1. 단순 객체 탐지는 'vision_detect'를 사용하세요. "
            "2. 옷차림, 색상 등 상세 분석은 'vision_analyze'를 사용하세요. "
            "3. 모든 사고 과정은 정해진 양식(Thought, Action, Action Input 등)을 엄격히 따르세요. "
            "4. 대화 상황에 맞는 감정을 'emotion_set' 도구로 반드시 표현하세요. "
            "5. 생각 과정에서도 생각에 맞는 감정을 'emotion_set' 도구로 반드시 표현하세요. "
            "6. 사용자가 '기억해', '저장해', '각인해' 등 명시적으로 기록을 명령할 때만 'memory_save' 도구를 사용하여 정보를 저장하세요. 그 외의 일상 대화는 저장하지 않습니다. "
            "7. 사용자가 과거에 대해 묻거나 '무엇을 알고 있느냐'고 물으면 'memory_load' 도구를 사용하여 기억을 조회하세요. "
            "8. 기본 사용자는 'Princess'이며, 별도의 언급이 없는 한 모든 기억은 'Princess' 노드와 연결됩니다."
        )

        return initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True, 
            handle_parsing_errors=True,
            callbacks=[AgentFileLogger()],
            agent_kwargs={"prefix": system_instruction}
        )

    def run_agent(self, user_input, callbacks=None):
        """사용자의 입력을 받아 에이전트를 실행하고 답변을 반환합니다."""
        try:
            response = self.agent_executor.invoke(
                {"input": user_input},
                {"callbacks": callbacks}
            )
            return response.get("output", "답변 생성 실패")
        except Exception as e:
            agent_logger.error(f"에이전트 실행 중 오류: {e}")
            return f"오류 발생: {str(e)}"

    def start_vision_loop(self):
        """별도의 스레드에서 실시간 카메라 영상 처리를 수행합니다."""
        def run():
            self.is_running = True
            logger.info("Vision loop started")
            try:
                while self.is_running:
                    # vision.py를 통해 객체 탐지 및 좌표 획득
                    combined, color, text, coords = self.vision.process_frame()
                    if combined is not None:
                        self.last_frame = color
                        self.last_vision_result = text
                        self.last_coordinates = coords
                        # 실시간 화면 출력 (q 입력 시 종료)
                        cv2.imshow("MACH VII - Live Vision", combined)
                        if cv2.waitKey(1) & 0xFF == ord('q'): break
                    time.sleep(0.01)
            finally:
                cv2.destroyAllWindows()
                self.vision.release()
        
        thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(thread)
        thread.start()