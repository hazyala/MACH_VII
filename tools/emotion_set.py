# tools/emotion_set.py (수정)
# ================================================================================
# MACH VII - 도구 5: Emotion Set (감정 상태 변경)
# ================================================================================

import streamlit as st
import os
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

# 유효한 감정 상태 + GIF 경로
EMOTION_MAP = {
    'idle': 'assets/gif/idle.jpg',
    'thinking': 'assets/gif/thinking.jpg',
    'happy': 'assets/gif/happy.jpg',
    'sad': 'assets/gif/sad.jpg',
    'angry': 'assets/gif/angry.jpg',
    'confused': 'assets/gif/confused.jpg'
}

@tool
def emotion_set(emotion: str) -> str:
    """
    맹칠의 감정 상태 설정
    
    Args:
        emotion: 감정 상태 (idle, thinking, happy, sad, angry, confused)
    
    Returns:
        설정 결과 메시지
    """
    try:
        logger.info(f"emotion_set 호출: {emotion}")
        
        # session_state에 감정 상태 초기화
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = "idle"
        
        emotion_lower = emotion.lower()
        
        # 감정 검증
        if emotion_lower not in EMOTION_MAP:
            logger.warning(f"유효하지 않은 감정: {emotion}")
            valid_list = ", ".join(EMOTION_MAP.keys())
            return f"⚠️ 유효하지 않은 감정입니다. 가능한 감정: {valid_list}"
        
        # GIF 파일 존재 확인
        gif_path = EMOTION_MAP[emotion_lower]
        if not os.path.exists(gif_path):
            logger.warning(f"GIF 파일 없음: {gif_path}")
            return f"⚠️ GIF 파일을 찾을 수 없습니다: {gif_path}"
        
        # 감정 상태 업데이트
        st.session_state.current_emotion = emotion_lower
        st.session_state.current_emotion_path = gif_path
        
        # 감정 이모지 매핑
        emotion_emoji = {
            'idle': '😐',
            'thinking': '🤔',
            'happy': '😊',
            'sad': '😢',
            'angry': '😠',
            'confused': '😕'
        }
        
        emoji = emotion_emoji.get(emotion_lower, '😐')
        result = f"{emoji} 감정을 '{emotion_lower}'로 변경했습니다."
        
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"emotion_set 오류: {e}")
        return f"오류 발생: {str(e)}"
