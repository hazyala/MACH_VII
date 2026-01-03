# code/engine.py

import threading
import time
import cv2
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import MessagesPlaceholder

from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

logger = get_logger('ENGINE')
agent_logger = get_logger('AGENT')

class AgentFileLogger(BaseCallbackHandler):
    """에이전트의 사고 과정을 로그 파일에 실시간으로 기록하는 클래스입니다."""
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
        """비전 시스템과 메모리, 에이전트를 초기화합니다."""
        self.vision = VisionSystem()
        self.last_frame = None
        self.last_vision_result = "nothing"
        self.last_coordinates = []
        
        self.llm = ChatOllama(
            model="gemma3:27b", 
            base_url="http://ollama.aikopo.net", 
            temperature=0.0
        )
        
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=1000, 
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # 클래스 내부의 _init_agent 함수를 올바르게 호출합니다.
        self.agent_executor = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        """마마의 12대 강령을 완벽히 수록하여 에이전트를 초기화합니다."""
        
        system_instruction = (
            "당신은 로봇 조수 '맹칠'입니다. 한국어로 정중히 답변하세요. "
            "1. 단순 객체 탐지는 'vision_detect'를 사용하세요. "
            "2. 옷차림, 색상 등 상세 분석은 'vision_analyze'를 사용하세요. "
            "3. 모든 사고 과정은 정해진 양식(Thought, Action, Action Input 등)을 엄격히 따르세요. "
            "4. 생각 과정에서나 대화 응답 상황에 맞는 감정을 'emotion_set' 도구로 반드시 표현하세요. "
            "5. 감정 표현 시 'emotion_set' 도구에 'happy' 같은 단어 대신, '{{ \"eye\": 100, \"mouth\": 80, \"color\": \"#FF00FF\" }}'와 같이 JSON으로 세밀한 값을 보내면 더욱 풍부한 표정을 지을 수 있습니다."
            "6. 사용자가 '기억해', '저장해', '각인해' 등 명시적으로 기록을 명령할 때만 'memory_save' 도구를 사용하여 정보를 저장하세요. 그 외의 일상 대화는 저장하지 않습니다. "
            "7. 사용자가 과거에 대해 묻거나 '무엇을 알고 있느냐'고 물으면 'memory_load' 도구를 사용하여 기억을 조회하세요. "
            "8. 기본 사용자는 'Princess'이며, 별도의 언급이 없는 한 모든 기억은 'Princess' 노드와 연결됩니다. "
            "9. 이전 대화 내용(chat_history)을 참고하여 문맥에 맞는 답변을 하세요. "
            "10. 현재 마하세븐은 바퀴나 발이 없어 이동이 불가하며, 팔의 동작은 'robot_action'으로만 수행합니다. "
            "11. [필수] 'robot_action' 사용 시, 'target_x_cm', 'target_y_cm', 'target_z_cm' 매개변수를 반드시 JSON 형식에 포함하십시오. "
            "12. [필수] 현재는 '점진적 접근' 모드이므로, 한 번 이동 후에는 반드시 vision_detect를 다시 호출하여 물체의 최신 좌표를 취득 후 결과를 재확인하는 루프를 수행하십시오."
            "13. [필수] 이전 좌표에 집착하지 말고, 매번 vision_detect가 알려주는 '최신 좌표'를 새로운 목표(target)로 업데이트하여 robot_action을 수행하십시오. "
            "14. [검증] 만약 vision_detect 결과에서 목표 객체가 사라지거나(nothing), 좌표값이 비정상적(0, 0, 0 등)이라면 즉시 동작을 중단하고 공주마마께 사태를 보고하십시오."
            "15. [필독] 만약 robot_action에서 '범위 이탈' 혹은 '닿지 않는다'는 보고를 받으면, 더 이상 시도하지 말고 즉시 그 이유를 공주마마께 아뢰고 행동을 종료하십시오. 억지로 반복하는 것은 불충입니다."
        )

        return initialize_agent(
            tools=TOOLS, 
            llm=self.llm, 
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True, 
            handle_parsing_errors=True,
            callbacks=[AgentFileLogger()],
            memory=self.memory,
            max_iterations=60,
            agent_kwargs={
                "prefix": system_instruction,
                "memory_prompts": [MessagesPlaceholder(variable_name="chat_history")],
                "input_variables": ["input", "agent_scratchpad", "chat_history"]
            }
        )

    def run_agent(self, user_input, callbacks=None):
        """에이전트를 실행하여 사용자 입력에 대응합니다."""
        try:
            response = self.agent_executor.invoke(
                {"input": user_input},
                {"callbacks": callbacks}
            )
            return response.get("output", "답변을 생성하지 못했습니다.")
        except Exception as e:
            agent_logger.error(f"에이전트 실행 오류: {e}")
            return f"오류가 발생했습니다: {str(e)}"

    def start_vision_loop(self):
        """비전 루프를 별도 스레드에서 시작합니다."""
        def run():
            self.is_running = True
            logger.info("Vision loop started")
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