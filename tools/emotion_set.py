import streamlit as st
import os
from langchain.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

EMOTION_MAP = {
    'idle': 'assets/gif/idle.gif', 'thinking': 'assets/gif/thinking.gif',
    'happy': 'assets/gif/happy.gif', 'sad': 'assets/gif/sad.gif',
    'angry': 'assets/gif/angry.gif', 'confused': 'assets/gif/confused.gif'
}

@tool
def emotion_set(emotion: str) -> str:
    """로봇의 감정 상태를 변경합니다. (이모지 포함)"""
    try:
        emo_key = emotion.lower().strip()
        if emo_key not in EMOTION_MAP: return "알 수 없는 감정입니다."
        
        st.session_state.current_emotion = emo_key
        st.session_state.current_emotion_path = EMOTION_MAP[emo_key]
        
        emojis = {'idle':'😐','thinking':'🤔','happy':'😊','sad':'😢','angry':'😠','confused':'😕'}
        emoji = emojis.get(emo_key, '😐')
        
        logger.info(f"감정 변경: {emo_key}")
        return f"{emoji} 로봇의 표정이 '{emo_key}'(으)로 변경되었습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"