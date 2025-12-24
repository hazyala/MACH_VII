# agent.py
# ================================================================================
# MACH VII - ReAct Agent (LangChain 기반 지능형 엔진)
# 사용자의 의도를 분석하고 등록된 도구(Tools)를 사용하여 임무를 수행합니다.
# ================================================================================

from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
# 도구 모음 리스트를 가져옵니다.
from tools import TOOLS
# 로그 기록을 위한 로거 객체를 가져옵니다.
from logger import get_logger

# 'AGENT'라는 이름으로 로그를 남길 로거 객체를 초기화합니다.
logger = get_logger('AGENT')

def get_agent():
    """
    맹칠의 두뇌 역할을 하는 ReAct 에이전트를 초기화하여 반환하는 함수입니다.
    
    반환값(Returns):
        AgentExecutor: 도구 사용과 추론 루프가 포함된 에이전트 실행 객체입니다.
    """
    try:
        logger.info("에이전트 두뇌 초기화 작업을 시작합니다.")
        
        # 1. LLM(대규모 언어 모델) 설정
        # 로컬 환경에서 실행 중인 Ollama의 gemma3:4b 모델을 사용합니다.
        llm = ChatOllama(
            model="gemma3:4b",
            base_url="http://localhost:11434",
            temperature=0.0,  # 일관된 답변을 위해 창의성을 0으로 설정합니다.
            timeout=60.0
        )
        logger.info("언어 모델(LLM) 연결에 성공하였습니다.")
        
        # 2. ReAct 프롬프트 템플릿 구성
        # 에이전트가 생각(Thought), 행동(Action), 관찰(Observation) 단계를 거치도록 유도하는 지침서입니다.
        template = """당신은 인공지능 로봇 '맹칠'입니다. 
항상 사용자에게 예의를 갖추고, 주어진 도구들을 사용하여 질문에 답변하세요.

사용 가능한 도구 목록:
{tools}

도구 이름 목록:
{tool_names}

응답 형식(반드시 이 형식을 지키세요):
Thought: 사용자의 질문에 답변하기 위해 무엇을 해야 할지 생각합니다.
Action: 사용할 도구의 이름을 적습니다. ({tool_names} 중 하나)
Action Input: 도구에 전달할 입력값을 적습니다.
Observation: 도구를 실행한 결과가 여기에 나타납니다.
... (이 과정은 필요하면 여러 번 반복될 수 있습니다)
Thought: 이제 최종 답변을 알고 있습니다.
Final Answer: 사용자의 질문에 대한 최종 답변을 한국어로 정중하게 작성합니다.

사용자의 질문: {input}
Thought: {agent_scratchpad}"""

        # 프롬프트 템플릿 객체를 생성합니다.
        prompt = PromptTemplate.from_template(template)
        logger.info("프롬프트 템플릿 작성을 완료하였습니다.")
        
        # 3. 에이전트 객체 생성
        # 모델, 도구 목록, 프롬프트를 결합하여 추론 능력을 가진 에이전트를 만듭니다.
        agent = create_react_agent(llm, TOOLS, prompt)
        
        # 4. 에이전트 실행기(Executor) 설정
        # 생성된 에이전트가 실제로 도구를 호출하고 루프를 돌 수 있도록 관리하는 실행 주체입니다.
        agent_executor = AgentExecutor(
            agent=agent,
            tools=TOOLS,
            verbose=True,            # 터미널에 에이전트의 생각 과정을 상세히 출력합니다.
            handle_parsing_errors=True, # 모델의 응답 형식이 틀렸을 때 스스로 수정하게 합니다.
            max_iterations=10        # 무한 루프 방지를 위해 최대 시도 횟수를 제한합니다.
        )
        
        logger.info("에이전트 실행기(Executor) 구성을 완료하였습니다.")
        return agent_executor
        
    except Exception as e:
        # 에이전트 생성 도중 오류가 발생하면 로그를 남기고 예외를 전달합니다.
        logger.error(f"에이전트 초기화 중 오류가 발생했습니다: {e}")
        raise

# 파일이 직접 실행될 때 테스트를 수행합니다.
if __name__ == "__main__":
    try:
        executor = get_agent()
        logger.info("에이전트 엔진 테스트 성공!")
    except Exception as e:
        logger.error(f"에이전트 엔진 테스트 실패: {e}")