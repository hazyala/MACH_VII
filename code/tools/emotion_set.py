import streamlit as st
import os
from langchain.tools import tool
from logger import get_logger

# 도구 로그 기록을 위한 로거 생성
logger = get_logger('TOOLS')

# 현재 파일(emotion_set.py)의 절대 경로를 획득
current_file_path = os.path.abspath(__file__)
# code/tools 폴더의 위치
tools_directory = os.path.dirname(current_file_path)
# 상위의 상위 폴더로 이동하여 data 폴더의 절대 경로 산출
data_directory = os.path.normpath(os.path.join(tools_directory, "..", "..", "data"))

# 감정 상태별 GIF 파일의 절대 경로 지도(Dictionary)
EMOTION_MAP = {
    'idle': os.path.join(data_directory, 'assets/gif/idle.gif'),
    'thinking': os.path.join(data_directory, 'assets/gif/thinking.gif'),
    'happy': os.path.join(data_directory, 'assets/gif/happy.gif'),
    'sad': os.path.join(data_directory, 'assets/gif/sad.gif'),
    'angry': os.path.join(data_directory, 'assets/gif/angry.gif'),
    'confused': os.path.join(data_directory, 'assets/gif/confused.gif')
}

# 사용자 입력 단어를 표준 감정 키값으로 변환해주는 매핑 테이블
INPUT_KEY_MAP = {
    'happy': 'happy', '행복': 'happy', '기쁨': 'happy', '즐거움': 'happy',
    'thinking': 'thinking', '생각': 'thinking', '고민': 'thinking', '추론': 'thinking',
    'sad': 'sad', '슬픔': 'sad', '우울': 'sad', '서운': 'sad',
    'angry': 'angry', '화남': 'angry', '분노': 'angry', '짜증': 'angry',
    'confused': 'confused', '당황': 'confused', '혼란': 'confused',
    'idle': 'idle', '대기': 'idle', '보통': 'idle'
}

@tool
def emotion_set(emotion_input: str) -> str:
    """
    로봇의 감정 상태를 변경하는 도구입니다. 
    입력된 단어에 맞춰 맹칠이의 표정(GIF)을 전환합니다.
    """
    try:
        # 입력값 정제 (공백 제거 및 소문자 변환)
        clean_input = emotion_input.lower().strip()
        
        # 매핑 테이블을 확인하여 표준 감정 키 획득
        target_emotion = INPUT_KEY_MAP.get(clean_input, clean_input)
        
        # 유효하지 않은 감정일 경우 경고 반환
        if target_emotion not in EMOTION_MAP:
            logger.warning(f"Invalid emotion input: {emotion_input}")
            return f"{emotion_input} is not a supported emotion."
        
        # 세션 상태(st.session_state)에 감정 정보와 이미지의 절대 경로 저장
        st.session_state.current_emotion = target_emotion
        st.session_state.current_emotion_path = EMOTION_MAP[target_emotion]
        
        logger.info(f"Emotion changed successfully: {target_emotion}")
        return f"Maengchil's expression has been changed to {target_emotion}."
        
    except Exception as error:
        # 오류 발생 시 로그 기록 및 메시지 반환
        logger.error(f"Error in emotion_set: {error}")
        return f"Failed to change expression: {str(error)}"