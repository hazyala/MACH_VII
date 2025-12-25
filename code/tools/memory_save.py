# tools/memory_save.py
# ================================================================================
# MACH VII - 도구 6: Memory Save (기억 저장 - 안정화 버전)
# ================================================================================

import streamlit as st
from datetime import datetime
from langchain.tools import tool # 안정화 버전에 맞게 수정
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def memory_save(input_str: str) -> str:
    """
    기억을 저장합니다. 
    입력 형식은 반드시 '키, 값' 형태여야 합니다. (예: '이름, 맹칠이')
    
    Args:
        input_str: 저장할 키와 값을 쉼표(,)로 구분한 문자열
    """
    try:
        logger.info(f"memory_save 호출: {input_str}")
        
        # 1. 입력값 분리: 쉼표를 기준으로 키와 값을 나눕니다.
        if ',' not in input_str:
            return "⚠️ 오류: '키, 값' 형식으로 입력해야 합니다. (예: 사용자이름, 공주마마)"
            
        key, value = input_str.split(',', 1)
        key = key.strip()
        value = value.strip()
        
        # 2. session_state 메모리 초기화
        if "memory" not in st.session_state:
            st.session_state.memory = {}
        
        # 3. 데이터 저장
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