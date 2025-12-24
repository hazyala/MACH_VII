# tools/emotion_set.py
# ================================================================================
# MACH VII - 도구 5: Emotion Set (감정 상태 변경)
# ================================================================================

import streamlit as st
import os
from langchain.tools import tool # 안정화 버전에 맞게 수정
from logger import get_logger

logger = get_logger('TOOLS')

# 실제 존재하는 .gif 확장자로 경로를 수정하였사옵니다.
EMOTION_MAP = {
    'idle': 'assets/gif/idle.gif',
    'thinking': 'assets/gif/thinking.gif',
    'happy': 'assets/gif/happy.gif',
    'sad': 'assets/gif/sad.gif',
    'angry': 'assets/gif/angry.gif',
    'confused': 'assets/gif/confused.gif'
}

@tool
def emotion_set(emotion: str) -> str:
    """
    로봇의 감정 상태(표정)를 변경합니다.
    사용 가능: idle, thinking, happy, sad, angry, confused
    """
    try:
        logger.info(f"emotion_set 호출: {emotion}")
        
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = "idle"
        
        emotion_lower = emotion.lower().strip()
        
        if emotion_lower not in EMOTION_MAP:
            valid_list = ", ".join(EMOTION_MAP.keys())
            return f"⚠️ 유효하지 않은 감정입니다. 가능한 감정: {valid_list}"
        
        gif_path = EMOTION_MAP[emotion_lower]
        # 파일이 실제로 존재하는지 확인합니다.
        if not os.path.exists(gif_path):
            return f"⚠️ 파일을 찾을 수 없습니다: {gif_path}"
        
        st.session_state.current_emotion = emotion_lower
        st.session_state.current_emotion_path = gif_path
        
        emotion_emoji = {
            'idle': '😐', 'thinking': '🤔', 'happy': '😊', 
            'sad': '😢', 'angry': '😠', 'confused': '😕'
        }
        
        emoji = emotion_emoji.get(emotion_lower, '😐')
        result = f"{emoji} 감정을 '{emotion_lower}'로 변경했습니다."
        
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"emotion_set 오류: {e}")
        return f"오류 발생: {str(e)}"