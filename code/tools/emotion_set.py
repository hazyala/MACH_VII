# code/tools/emotion_set.py

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
    2. A custom parameter string (e.g., 'eye: 50, mouth: -30, color: #FFA500')
       - eye: 0 (closed) to 100 (open)
       - mouth: -100 (sad) to 100 (happy)
    """
    try:
        clean_input = emotion_input.strip()
        new_params = {}

        # [핵심 수정] 입력값에 중괄호가 있거나 콜론(:)이 있으면 JSON 파싱 시도
        # 에이전트가 중괄호를 빼고 보내도, 혹시 넣어서 보내도 처리할 수 있게 유연성 확보
        if clean_input.startswith('{') or ':' in clean_input:
            try:
                # 중괄호가 없으면 양쪽에 붙여서 유효한 JSON 문자열로 변환
                json_str = clean_input if clean_input.startswith('{') else f"{{{clean_input}}}"
                
                # 작은따옴표(')를 큰따옴표(")로 변환 (JSON 표준 맞춤)
                json_str = json_str.replace("'", '"')
                
                custom_params = json.loads(json_str)
                
                # 기존 값 유지하면서 업데이트 (Partial Update)
                current = st.session_state.get('face_params', EMOTION_PRESETS['idle'].copy())
                current.update(custom_params)
                new_params = current
                logger.info(f"Custom Expression Set: {new_params}")
            except json.JSONDecodeError:
                # 파싱 실패 시 로그만 남기고 아래 프리셋 로직으로 넘어감 (혹시 'happy' 같은 단어일 수 있음)
                logger.warning(f"JSON parsing failed for input: {clean_input}")
                pass
        
        # 위에서 파싱되지 않았다면 프리셋 단어로 간주
        if not new_params:
            key = clean_input.lower().replace('"', '').replace("'", "") # 따옴표 제거
            if key in EMOTION_PRESETS:
                new_params = EMOTION_PRESETS[key]
                logger.info(f"Preset Expression Set: {key}")
            else:
                # 알 수 없는 입력이면 idle로 설정하되 메시지 반환
                new_params = EMOTION_PRESETS['idle']
                return f"Unknown emotion '{clean_input}'. Set to idle."

        # 세션 상태에 'face_params'라는 딕셔너리로 저장 -> main.py에서 렌더링에 사용
        st.session_state.face_params = new_params
        
        # 변경된 상태를 반환 (생각의 흐름에 기록됨)
        return f"Face updated: Eye={new_params.get('eye')}, Mouth={new_params.get('mouth')}"

    except Exception as error:
        logger.error(f"Error in emotion_set: {error}")
        return f"Failed to set emotion: {str(error)}"