# tools/memory_save.py
# ================================================================================
# MACH VII - 도구 6: Memory Save (기억 저장 - Phase 1: Session State)
# Phase 2에서 LAG(지식그래프) 통합 예정
# ================================================================================

import streamlit as st
from datetime import datetime
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def memory_save(key: str, value: str) -> str:
    """
    기억 저장 (Session State 기반)
    
    Args:
        key: 저장할 키 (예: "user_name", "favorite_color")
        value: 저장할 값
    
    Returns:
        저장 결과 메시지
    
    Note:
        Phase 2에서 LAG 지식그래프로 업그레이드 예정
    """
    try:
        logger.info(f"memory_save 호출: {key}={value}")
        
        # session_state에 메모리 딕셔너리 초기화
        if "memory" not in st.session_state:
            st.session_state.memory = {}
        
        # 타임스탬프와 함께 저장
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.memory[key] = {
            'value': value,
            'timestamp': timestamp
        }
        
        result = f"✅ 기억 저장 완료: {key} = {value}"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"memory_save 오류: {e}")
        return f"오류 발생: {str(e)}"
