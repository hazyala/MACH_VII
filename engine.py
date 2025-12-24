# engine.py
import streamlit as st
import threading
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.base import BaseCallbackHandler # 로그 가로채기용
from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

logger = get_logger('ENGINE')

class StreamlitThoughtHandler(BaseCallbackHandler):
    """에이전트의 생각을 실시간으로 UI 변수에 기록하는 전령입니다."""
    def on_agent_action(self, action, **kwargs):
        # 에이전트가 도구를 사용하기로 했을 때의 생각을 기록합니다.
        thought = f"\n🤔 **생각:** {action.log}\n"
        st.session_state.agent_thoughts += thought
        # 화면을 즉시 갱신하기 위해 강제 트리거를 줄 수 있으나, 여기서는 변수 저장에 집중합니다.

class MachEngine:
    def __init__(self):
        self.vision = VisionSystem('yolov11s.pt')
        self.agent = self._init_agent()
        self.is_running = False

    def _init_agent(self):
        # 마마의 Proto 프로젝트에서 검증된 설정을 유지합니다.
        llm = ChatOllama(model="gemma3:4b", base_url="http://localhost:11434", temperature=0.0)
        return initialize_agent(
            tools=TOOLS,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )

    def start_vision_loop(self):
        if self.is_running: return
        def run():
            self.is_running = True
            while self.is_running:
                frame, text, coords = self.vision.process_frame()
                if frame is not None:
                    st.session_state.last_frame = frame
                    st.session_state.last_vision_result = text
                    st.session_state.last_coordinates = coords
                time.sleep(0.01) # UI 응답성을 위해 대기 시간 최소화
        
        thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(thread)
        thread.start()