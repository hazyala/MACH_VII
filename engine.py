# engine.py
# ================================================================================
# MACH VII - 실행 엔진 (고급 로깅 및 엄격한 지침 적용 버전)
# ================================================================================

import threading
import time
import cv2
import numpy as np
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType

# 프로젝트 내부 모듈을 가져옵니다.
from vision import VisionSystem
from tools import TOOLS
from logger import get_logger

# 'ENGINE' 모듈 전용 로거를 생성합니다. (터미널 출력 및 파일 저장 겸용)
logger = get_logger('ENGINE')

class AgentFileLogger(BaseCallbackHandler):
    """
    에이전트의 사고 과정(Thought, Action)을 실시간으로 가로채어 
    logger.py를 통해 logs 폴더의 파일에 저장하는 클래스입니다.
    """
    def on_agent_action(self, action, **kwargs):
        # 에이전트가 도구를 사용하기로 결정했을 때 호출됩니다.
        logger.info(f"[도구 실행] 도구명: {action.tool}, 입력값: {action.tool_input}")
        
    def on_agent_finish(self, finish, **kwargs):
        # 에이전트가 최종 답변을 내놓았을 때 호출됩니다.
        logger.info(f"[최종 답변] {finish.return_values['output']}")

class MachEngine:
    """비전 분석과 에이전트 추론을 총괄하는 핵심 엔진 클래스입니다."""
    
    def __init__(self):
        # 1. 비전 시스템 초기화 (모델 파일명을 yolo11n.pt로 수정함)
        # 카메라 연결에 실패해도 엔진이 멈추지 않도록 설계되었습니다.
        self.vision = VisionSystem('yolo11n.pt')
        
        # 2. 에이전트 실행기 초기화
        self.agent_executor = self._init_agent()
        self.is_running = False

    # def _init_agent(self):
    #     """에이전트에게 정체성과 엄격한 행동 지침을 부여합니다."""
    #     # 로컬 Ollama 서버의 Gemma3 모델을 연결합니다.
    #     llm = ChatOllama(
    #         model="gemma3:4b", 
    #         base_url="http://localhost:11434", 
    #         temperature=0.0
    #     )

    def _init_agent(self):
        """에이전트의 지능을 외부 서버의 27b 모델로 업그레이드합니다."""
        # 로컬이 아닌 외부 Ollama 서버 주소와 27b 모델을 설정합니다.
        llm = ChatOllama(
            model="gemma3:27b", 
            base_url="http://ollama.aikopo.net", 
            temperature=0.0
        )
        
        # [핵심] 맹칠이의 정신 개조를 위한 엄격한 시스템 지침
        # 불필요한 도구 사용을 금지하고, 없는 물체를 상상하지 않도록 명시합니다.
        system_instruction = (
            "당신은 인공지능 로봇 조수 '맹칠'입니다. 질문에 한국어로 정중하게 답변하세요. "
            "1. 반드시 도구가 필요하다고 판단되는 상황(예: 주변 확인, 로봇 팔 작동)에서만 도구를 사용하세요. "
            "2. 단순한 인사나 일상적인 대화에는 도구를 절대 사용하지 말고 즉시 답변하세요. "
            "3. 현재 화면에 보이지 않는 물체(예: 컵)를 상상해서 조작하려 하지 마세요. "
            "4. 답변은 간결하고 명확하게 하세요."
        )

        # 에이전트 실행기를 생성합니다.
        return initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,                      # 터미널에 사고 과정 출력
            handle_parsing_errors=True,        # 답변 형식 오류 자가 수정
            max_iterations=10,                 # 최대 사고 횟수를 10회로 유지
            early_stopping_method="generate",  # 시간 초과 시 즉시 답변 생성
            agent_kwargs={
                "prefix": system_instruction   # 수정된 시스템 지침 주입
            }
        )

    def run_agent(self, user_input, callbacks=None):
        """
        사용자의 명령을 받아 에이전트를 실행합니다.
        UI 콜백과 파일 로깅 콜백을 동시에 처리합니다.
        """
        # 파일 저장용 핸들러를 생성합니다.
        file_handler = AgentFileLogger()
        
        # 기존 콜백(UI 표시용)과 파일 저장용 핸들러를 합칩니다.
        all_callbacks = []
        if callbacks:
            all_callbacks.extend(callbacks)
        all_callbacks.append(file_handler)
        
        try:
            # 에이전트에게 명령을 전달하고 실행합니다.
            response = self.agent_executor.invoke(
                {"input": user_input},
                {"callbacks": all_callbacks}
            )
            return response.get("output", "죄송합니다. 답변을 생성하지 못했습니다.")
        except Exception as e:
            logger.error(f"에이전트 추론 중 오류 발생: {e}")
            return f"오류가 발생했습니다: {str(e)}"

    def start_vision_loop(self):
        """별도의 배경 스레드에서 카메라 영상을 획득하고 전시합니다."""
        if self.is_running:
            return
            
        def run():
            self.is_running = True
            logger.info("실시간 비전 루프 가동 시작")
            
            try:
                while self.is_running:
                    # vision.py를 통해 RGB 영상과 뎁스 컬러맵, 탐지 데이터를 가져옵니다.
                    # combined: RGB와 Depth가 합쳐진 영상, color: 순수 RGB 영상
                    combined, color, text, coords = self.vision.process_frame()
                    
                    if combined is not None:
                        # 1. 스트림릿 세션 상태 업데이트 (분석 도구가 최신 화면을 보도록 함)
                        st.session_state.last_frame = color
                        st.session_state.last_vision_result = text
                        st.session_state.last_coordinates = coords
                        
                        # 2. OpenCV 별도 창에 RGB + Depth Map 실시간 전시
                        # 이 창은 스트림릿과 별개로 작동하여 화면 깜빡임이 없습니다.
                        cv2.imshow("MACH VII - Live Vision (RGB & Depth Map)", combined)
                        
                        # 'q' 키를 누르면 루프를 종료합니다.
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self.is_running = False
                            break
                    
                    # CPU 부하를 줄이기 위해 아주 짧게 대기합니다.
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"비전 루프 중 오류 발생: {e}")
            finally:
                # 종료 시 모든 창을 닫고 카메라 자원을 해제합니다.
                cv2.destroyAllWindows()
                self.vision.release()
                logger.info("비전 루프 종료 및 자원 해제 완료")

        # 스레드를 생성하고 스트림릿 문맥을 부여하여 실행합니다.
        vision_thread = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(vision_thread)
        vision_thread.start()