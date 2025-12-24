# tools/emotion_set.py
# ================================================================================
# MACH VII - 도구 5: Emotion Set (감정 상태 변경 시스템)
# 로봇의 감정 상태를 변경하고, 화면에 표시될 GIF 경로와 이모지를 관리합니다.
# ================================================================================

import streamlit as st
import os
from langchain_core.tools import tool
# 실행 과정을 기록하기 위해 로깅 시스템을 가져옵니다.
from logger import get_logger

# 'TOOLS'라는 이름으로 로그를 기록할 로거 객체를 생성합니다.
logger = get_logger('TOOLS')

# 감정 이름과 실제 GIF 파일 경로를 연결한 딕셔너리(Dictionary)입니다.
# 딕셔너리는 키(Key)를 사용해 값(Value)을 찾는 저장 구조입니다.
EMOTION_MAP = {
    'idle': 'assets/gif/idle.gif',
    'thinking': 'assets/gif/thinking.gif',
    'happy': 'assets/gif/happy.gif',
    'sad': 'assets/gif/sad.gif',
    'angry': 'assets/gif/angry.gif',
    'confused': 'assets/gif/confused.gif'
}

# 감정 이름에 대응하는 이모지 문자열을 담은 딕셔너리입니다.
# 이 프로젝트에서는 예외적으로 코드 내 이모지 사용이 허용됩니다.
EMOTION_EMOJI = {
    'idle': '😐',
    'thinking': '🤔',
    'happy': '😊',
    'sad': '😢',
    'angry': '😠',
    'confused': '😕'
}

@tool
def emotion_set(emotion: str) -> str:
    """
    맹칠의 감정 상태를 설정하고 화면에 표시될 GIF 파일과 이모지를 업데이트합니다.
    
    매개변수(Args):
        emotion: 설정할 감정의 이름입니다. (예: 'happy', 'sad' 등)
    
    반환값(Returns):
        성공 시 이모지가 포함된 결과 메시지를 반환하고, 실패 시 오류 메시지를 반환합니다.
    """
    try:
        # 어떤 감정 변경 요청이 들어왔는지 로그에 남깁니다.
        logger.info(f"emotion_set 호출: {emotion}")
        
        # 세션 상태(st.session_state)에 감정 변수가 없다면 기본값인 'idle'로 생성합니다.
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = "idle"
        
        # 입력된 감정 이름을 소문자로 통일하여 비교 오류를 방지합니다.
        emotion_lower = emotion.lower()
        
        # 1. 감정 이름 유효성 검사: 정의된 감정 목록(EMOTION_MAP)에 있는지 확인합니다.
        if emotion_lower not in EMOTION_MAP:
            logger.warning(f"정의되지 않은 감정 요청: {emotion}")
            valid_emotions = ", ".join(EMOTION_MAP.keys())
            return f"유효하지 않은 감정입니다. 가능한 목록: {valid_emotions}"
        
        # 2. 파일 존재 여부 검사: 해당 경로에 GIF 파일이 실제로 있는지 os 모듈로 확인합니다.
        gif_path = EMOTION_MAP[emotion_lower]
        if not os.path.exists(gif_path):
            logger.error(f"파일 경로 오류: {gif_path}")
            return f"이미지를 찾을 수 없습니다: {gif_path}"
        
        # 3. 데이터 업데이트: 세션 상태에 감정 이름과 파일 경로를 저장합니다.
        # main.py는 이 변수를 실시간으로 읽어 화면의 이미지를 교체합니다.
        st.session_state.current_emotion = emotion_lower
        st.session_state.current_emotion_path = gif_path
        
        # 4. 결과 메시지 구성: 해당 감정에 맞는 이모지를 찾아 결과에 포함합니다.
        # 이모지 딕셔너리에서 값을 가져오며, 없을 경우 기본 이모지(😐)를 사용합니다.
        emoji = EMOTION_EMOJI.get(emotion_lower, '😐')
        result_message = f"{emoji} 감정을 '{emotion_lower}' 상태로 변경했습니다."
        
        logger.info(result_message)
        return result_message
        
    except Exception as e:
        # 처리 도중 예외(오류)가 발생하면 로그에 기록하고 사용자에게 알립니다.
        error_msg = f"감정 설정 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return error_msg