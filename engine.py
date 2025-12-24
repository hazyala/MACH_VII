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

# 'ENGINE'과 'AGENT' 로거를 각각 준비합니다.
logger = get_logger('ENGINE')
agent_logger = get_logger('AGENT')

class AgentFileLogger(BaseCallbackHandler):
    """
    에이전트의 사고 과정(Chain, Thought, Action, Observation)을 
    실시간으로 가로채어 로그 파일에 기록하는 사관 클래스입니다.
    """
    def on_chain_start(self, serialized, inputs, **kwargs):
        agent_logger.info("\n> Entering new AgentExecutor chain...")

    def on_text(self, text, **kwargs):
        # 에이전트의 Thought(생각) 부분을 기록합니다.
        if text:
            # 불필요한 공백을 제거하고 기록합니다.
            clean_text = text.strip()
            if clean_text:
                agent_logger.info(f"{clean_text}")

    def on_agent_action(self, action, **kwargs):
        # 실행할 도구와 입력값을 기록합니다.
        agent_logger.info(f"Action: {action.tool}")
        agent_logger.info(f"Action Input: {action.tool_input}")
        
    def on_tool_end(self, output, **kwargs):
        # 도구 실행 결과(Observation)를 기록합니다.
        agent_logger.info(f"Observation: {output}")

    def on_agent_finish(self, finish, **kwargs):
        # 최종 답변과 체인 종료를 기록합니다.
        agent_logger.info(f"Final Answer: {finish.return_values['output']}")
        agent_logger.info("> Finished chain.\n")

class MachEngine:
    def __init__(self):
        self.vision = VisionSystem('yolo11n.pt')
        self.last_frame = None
        self.last_vision_result = "nothing"
        self.last_coordinates = []
        
        # 에이전트 초기화 시 기록용 사관(Callback)을 임명합니다.
        self.agent_executor = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        llm = ChatOllama(model="gemma3:27b", base_url="http://ollama.aikopo.net", temperature=0.0)
        
        system_instruction = (
            "당신은 로봇 조수 '맹칠'입니다. 한국어로 정중히 답변하세요. "
            "1. 단순 객체 탐지는 'vision_detect'를 사용하세요. "
            "2. 옷차림, 색상 등 상세 분석은 'vision_analyze'를 사용하세요. "
            "3. 모든 사고 과정은 정해진 양식(Thought, Action, Action Input 등)을 엄격히 따르세요."
        )

        return initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True, 
            handle_parsing_errors=True,
            # [핵심] 에이전트가 생성될 때 기록용 콜백을 기본으로 장착합니다.
            callbacks=[AgentFileLogger()],
            agent_kwargs={"prefix": system_instruction}
        )

    def run_agent(self, user_input, callbacks=None):
        try:
            # 실행 시에도 콜백이 누락되지 않도록 처리합니다.
            response = self.agent_executor.invoke(
                {"input": user_input},
                {"callbacks": callbacks}
            )
            return response.get("output", "답변 생성 실패")
        except Exception as e:
            agent_logger.error(f"에이전트 실행 중 오류: {e}")
            return f"오류 발생: {str(e)}"

    def start_vision_loop(self):
        def run():
            self.is_running = True
            logger.info("비전 루프 가동 시작")
            try:
                while self.is_running:
                    combined, color, text, coords = self.vision.process_frame()
                    if combined is not None:
                        self.last_frame = color
                        self.last_vision_result = text
                        self.last_coordinates = coords
                        cv2.imshow("MACH VII - Live Vision", combined)
                        if cv2.waitKey(1) & 0xFF == ord('q'): break
                    time.sleep(0.01)
            finally:
                cv2.destroyAllWindows()
                self.vision.release()
        
        thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(thread)
        thread.start()