# tools/robot_action.py
# ================================================================================
# MACH VII - 도구 4: Robot Action (로봇 시뮬레이션 - Phase 1)
# Phase 2에서 실제 DOFBOT 연결 예정
# ================================================================================

import streamlit as st
import time
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def robot_action(command: str) -> str:
    """
    로봇팔에 명령 실행 (Phase 1: 시뮬레이션만)
    
    Args:
        command: 명령어 (wave, grab, push, home 등)
    
    Returns:
        실행 결과 메시지
    """
    try:
        logger.info(f"robot_action 호출: {command}")
        
        # session_state에 로봇 상태 초기화
        if "robot_state" not in st.session_state:
            st.session_state.robot_state = "idle"
        
        command_lower = command.lower()
        
        # 명령어 처리
        if "wave" in command_lower:
            st.session_state.robot_state = "waving"
            result = "🤖 로봇이 손을 흔듭니다! (wave)"
            
        elif "grab" in command_lower or "잡" in command_lower:
            st.session_state.robot_state = "grabbing"
            result = "🤖 로봇이 물건을 잡습니다! (grab)"
            
        elif "push" in command_lower or "밀" in command_lower:
            st.session_state.robot_state = "pushing"
            result = "🤖 로봇이 물건을 밉니다! (push)"
            
        elif "home" in command_lower or "돌아가" in command_lower:
            st.session_state.robot_state = "home"
            result = "🤖 로봇이 홈 위치로 돌아갑니다! (home)"
            
        else:
            st.session_state.robot_state = "idle"
            result = f"⚠️ 알 수 없는 명령어: {command} (wave, grab, push, home)"
        
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"robot_action 오류: {e}")
        return f"오류 발생: {str(e)}"
