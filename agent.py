# agent.py
# ================================================================================
# MACH VII - 에이전트 시스템 (안정화 버전)
# LangChain 0.1.x 버전에 최적화된 initialize_agent 방식을 사용합니다.
# ================================================================================

# 라이브러리 경로에 맞게 클래스들을 가져옵니다.
from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType
# 프로젝트 내부 도구 모음을 가져옵니다.
from tools import TOOLS
# 로그 기록을 위한 객체를 가져옵니다.
from logger import get_logger

# 'AGENT' 이름으로 로그를 남길 객체를 초기화합니다.
logger = get_logger('AGENT')

def get_agent():
    """
    안정성이 검증된 ZERO_SHOT_REACT_DESCRIPTION 방식으로 에이전트를 생성합니다.
    """
    try:
        # logger.info("안정화 버전의 에이전트 초기화를 시작합니다.")
        
        # # 1. 언어 모델(LLM) 설정
        # # 로컬 Ollama 서버와 통신하는 젬마 모델 객체를 생성합니다.
        # llm = ChatOllama(
        #     model="gemma3:4b",
        #     base_url="http://localhost:11434",
        #     temperature=0.0
        # )

        response = requests.post(
            "http://ollama.aikopo.net/api/generate",
            json={
                "model": "gemma3:27b", # 27b
                "prompt": query,
                "images": [image_base64],
                "stream": False
            },
            timeout=90
        )
        
        # 2. 시스템 지침 설정
        # 에이전트가 자신의 정체성을 잊지 않도록 기본 지침을 작성합니다.
        system_instruction = (
            "당신은 도움을 주는 로봇 조수 '맹칠'입니다. "
            "주어진 도구를 적절히 사용하여 사용자의 질문에 한국어로 정중하게 답변하세요. "
            "도구의 결과를 얻었다면 즉시 최종 답변을 작성하세요."
        )

        # 3. 에이전트 실행기 생성
        # 이전 프로젝트(Proto)에서 성공적으로 구동되었던 설정을 그대로 사용합니다.
        agent_executor = initialize_agent(
            tools=TOOLS, 
            llm=llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,                      # 추론 과정을 터미널에 출력합니다.
            handle_parsing_errors=True,        # 답변 형식이 틀려도 스스로 수정하게 합니다.
            max_iterations=10,                 # 최대 생각 횟수를 제한합니다.
            early_stopping_method="generate",  # 횟수 초과 시 즉시 답변을 생성합니다.
            agent_kwargs={
                "prefix": system_instruction   # 시스템 지침을 주입합니다.
            }
        )
        
        logger.info("에이전트 실행기가 성공적으로 구성되었습니다.")
        return agent_executor
        
    except Exception as e:
        logger.error(f"에이전트 생성 중 오류 발생: {e}")
        raise