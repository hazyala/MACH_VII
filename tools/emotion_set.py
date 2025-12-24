import streamlit as st
import os
from langchain.tools import tool
from logger import get_logger

# 'TOOLS' 로거를 가져옵니다.
logger = get_logger('TOOLS')

# 감정 키와 실제 GIF 파일 경로를 연결하는 딕셔너리(Dictionary)입니다.
EMOTION_MAP = {
    'idle': 'assets/gif/idle.gif',
    'thinking': 'assets/gif/thinking.gif',
    'happy': 'assets/gif/happy.gif',
    'sad': 'assets/gif/sad.gif',
    'angry': 'assets/gif/angry.gif',
    'confused': 'assets/gif/confused.gif'
}

# 사용자가 입력한 다양한 단어를 표준 감정 키로 변환하는 매핑 테이블입니다.
INPUT_KEY_MAP = {
    # 행복/기쁨 계열
    'happy': 'happy', '행복': 'happy', '기쁨': 'happy', '즐거움': 'happy', '😊': 'happy',
    # 생각/고민 계열
    'thinking': 'thinking', '생각': 'thinking', '고민': 'thinking', '추론': 'thinking', '🤔': 'thinking',
    # 슬픔/우울 계열
    'sad': 'sad', '슬픔': 'sad', '우울': 'sad', '서운': 'sad', '😢': 'sad',
    # 화남/분노 계열
    'angry': 'angry', '화남': 'angry', '분노': 'angry', '짜증': 'angry', '😠': 'angry',
    # 당황/혼란 계열
    'confused': 'confused', '당황': 'confused', '혼란': 'confused', '😕': 'confused',
    # 대기/보통 계열
    'idle': 'idle', '대기': 'idle', '보통': 'idle', '😐': 'idle'
}

@tool
def emotion_set(emotion_input: str) -> str:
    """
    로봇의 감정 상태(표정)를 변경하는 도구입니다.
    한글 감정 표현이나 이모티콘을 입력해도 적절한 표정으로 변경됩니다.
    """
    try:
        # 입력된 문자열의 공백을 제거하고 소문자로 변환합니다.
        clean_input = emotion_input.lower().strip()
        
        # 입력된 단어를 표준 감정 키(Standard Key)로 변환합니다. 
        # 매핑되지 않은 단어라면 입력값을 그대로 사용합니다.
        target_emotion = INPUT_KEY_MAP.get(clean_input, clean_input)
        
        # 유효한 감정 키인지 확인합니다.
        if target_emotion not in EMOTION_MAP:
            logger.warning(f"지원하지 않는 감정 입력: {emotion_input}")
            return f"'{emotion_input}'은(는) 맹칠이가 아직 배우지 못한 표정입니다."
        
        # 세션 상태(st.session_state)에 현재 감정과 이미지 경로를 저장합니다.
        st.session_state.current_emotion = target_emotion
        st.session_state.current_emotion_path = EMOTION_MAP[target_emotion]
        
        # 화면에 표시될 이모티콘을 결정합니다.
        emoji_icons = {
            'idle': '😐', 'thinking': '🤔', 'happy': '😊', 
            'sad': '😢', 'angry': '😠', 'confused': '😕'
        }
        selected_emoji = emoji_icons.get(target_emotion, '😐')
        
        logger.info(f"감정 변경 성공: {target_emotion}")
        return f"{selected_emoji} 맹칠이의 표정이 '{target_emotion}'(으)로 바뀌었습니다!"
        
    except Exception as error:
        logger.error(f"emotion_set 실행 중 오류 발생: {error}")
        return f"표정을 바꾸는 중에 오류가 발생했습니다: {str(error)}"