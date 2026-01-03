import streamlit as st
import json
from langchain.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

# 1. 기본 감정 프리셋 (에이전트가 단어로 말할 때를 대비한 기본값)
# 값 범위 -> eye: 0~100, mouth: -100~100, color: Hex Code
EMOTION_PRESETS = {
    'idle':     {'eye': 100, 'mouth': 0,   'color': '#00FFFF'}, # 기본 시안색
    'happy':    {'eye': 90,  'mouth': 60,  'color': '#00FF00'}, # 기쁨의 녹색
    'joy':      {'eye': 85,  'mouth': 80,  'color': '#00FF00'},
    'sad':      {'eye': 40,  'mouth': -60, 'color': '#0000FF'}, # 슬픔의 파랑
    'angry':    {'eye': 70,  'mouth': -40, 'color': '#FF0000'}, # 분노의 빨강
    'thinking': {'eye': 60,  'mouth': 10,  'color': '#FFD700'}, # 생각의 노랑
    'confused': {'eye': 100, 'mouth': -10, 'color': '#FF00FF'}, # 혼란의 보라
    'sleepy':   {'eye': 10,  'mouth': 0,   'color': '#555555'}
}

@tool
def emotion_set(emotion_input: str) -> str:
    """
    Sets the robot's facial expression.
    Inputs can be:
    1. A preset name (e.g., 'happy', 'angry', 'thinking')
    2. A JSON string for custom control (e.g., '{"eye": 50, "mouth": -30, "color": "#FFA500"}')
       - eye: 0 (closed) to 100 (open)
       - mouth: -100 (sad) to 100 (happy)
    """
    try:
        clean_input = emotion_input.strip()
        new_params = {}

        # 경우 1: 입력이 JSON 형식인 경우 (에이전트가 섬세하게 조절할 때)
        if clean_input.startswith('{'):
            try:
                custom_params = json.loads(clean_input)
                # 기존 값 유지하면서 업데이트 (Partial Update)
                current = st.session_state.get('face_params', EMOTION_PRESETS['idle'])
                current.update(custom_params)
                new_params = current
                logger.info(f"Custom Expression Set: {new_params}")
            except json.JSONDecodeError:
                return "Error: Invalid JSON format for expression."
        
        # 경우 2: 입력이 프리셋 단어인 경우
        else:
            key = clean_input.lower()
            if key in EMOTION_PRESETS:
                new_params = EMOTION_PRESETS[key]
                logger.info(f"Preset Expression Set: {key}")
            else:
                # 없는 단어면 기본 idle로 설정하되 경고 반환
                new_params = EMOTION_PRESETS['idle']
                return f"Unknown emotion '{clean_input}'. Set to idle."

        # 세션 상태에 'face_params'라는 딕셔너리로 저장
        st.session_state.face_params = new_params
        
        return f"Face updated: Eye={new_params.get('eye')}, Mouth={new_params.get('mouth')}"

    except Exception as error:
        logger.error(f"Error in emotion_set: {error}")
        return f"Failed to set emotion: {str(error)}"