# tools/memory_load.py
# ================================================================================
# MACH VII - 도구 7: Memory Load (기억 조회 - Phase 1: Session State)
# Phase 2에서 LAG 쿼리로 업그레이드 예정
# ================================================================================

import streamlit as st
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def memory_load(query: str) -> str:
    """
    저장된 기억 조회
    
    Args:
        query: 조회할 키 또는 키워드 (예: "user_name", "favorite")
    
    Returns:
        조회된 기억 정보
    
    Note:
        Phase 2에서 LAG 지식그래프 쿼리로 업그레이드 예정
    """
    try:
        logger.info(f"memory_load 호출: {query}")
        
        # session_state에 메모리 없으면 생성
        if "memory" not in st.session_state:
            st.session_state.memory = {}
        
        memory = st.session_state.memory
        
        if not memory:
            logger.info("저장된 기억 없음")
            return "저장된 기억이 없습니다."
        
        # 정확한 키 매칭
        if query in memory:
            value = memory[query]['value']
            timestamp = memory[query]['timestamp']
            result = f"✅ 기억: {query} = {value} (저장 시간: {timestamp})"
            logger.info(result)
            return result
        
        # 키워드 매칭 (부분 일치)
        query_lower = query.lower()
        matching_keys = [k for k in memory.keys() if query_lower in k.lower()]
        
        if matching_keys:
            result = "관련 기억:\n"
            for key in matching_keys:
                value = memory[key]['value']
                result += f"  - {key}: {value}\n"
            logger.info(f"부분 일치 기억 찾음: {matching_keys}")
            return result
        
        logger.info(f"기억 찾을 수 없음: {query}")
        return f"'{query}'에 관한 기억을 찾을 수 없습니다."
        
    except Exception as e:
        logger.error(f"memory_load 오류: {e}")
        return f"오류 발생: {str(e)}"
