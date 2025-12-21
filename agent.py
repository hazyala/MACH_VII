# agent.py
# ================================================================================
# MACH VII - ReAct Agent (langchain 1.2.0)
# ================================================================================

from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from tools import TOOLS
from logger import get_logger

logger = get_logger('AGENT')

def get_agent():
    """ReAct Agent 초기화 및 반환"""
    
    try:
        logger.info("ReAct Agent 초기화 시작")
        
        # ===== LLM 초기화 =====
        llm = ChatOllama(
            model="gemma3:4b",
            base_url="http://localhost:11434",
            temperature=0.0,
            timeout=60.0
        )
        logger.info("✅ LLM 초기화 완료")
        
        # ===== 도구 로드 =====
        logger.info(f"도구 {len(TOOLS)}개 로드")
        for tool in TOOLS:
            logger.debug(f"  - {tool.name}")
        
        # ===== 시스템 프롬프트 =====
        system_prompt = """당신은 도움이 되는 AI 어시스턴트입니다.
사용자의 요청에 따라 적절한 도구를 사용하여 작업을 수행하세요.

다음 형식으로 응답하세요:
Thought: 다음에 할 일
Action: 도구명
Action Input: 입력값
Observation: 결과
...
Final Answer: 최종 답변"""
        
        logger.info("✅ 시스템 프롬프트 생성 완료")
        
        # ===== Agent 생성 =====
        agent = create_agent(
            model=llm,
            tools=TOOLS,
            system_prompt=system_prompt
        )
        logger.info("✅ ReAct Agent 생성 완료")
        logger.info("ReAct Agent 초기화 완료!")
        
        return agent
        
    except Exception as e:
        logger.error(f"Agent 초기화 오류: {e}")
        logger.error(f"오류 타입: {type(e).__name__}")
        raise


# 테스트
if __name__ == "__main__":
    try:
        logger.info("ReAct Agent 테스트 시작")
        agent = get_agent()
        logger.info("✅ ReAct Agent 초기화 성공!")
        
    except Exception as e:
        logger.error(f"ReAct Agent 테스트 실패: {e}")
