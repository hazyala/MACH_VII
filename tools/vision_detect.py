# tools/vision_detect.py
# ================================================================================
# MACH VII - 도구 1: Vision Detect (YOLO 감지 + XYZ 좌표)
# ================================================================================

import streamlit as st
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def vision_detect(query: str) -> str:
    """
    실시간 카메라에서 감지된 객체와 좌표 정보 반환
    
    Args:
        query: 사용자 질문 (예: "뭐가 보여?", "무엇을 감지했어?")
    
    Returns:
        감지된 객체명과 좌표 정보 (텍스트)
    """
    try:
        logger.info(f"vision_detect 호출: {query}")
        
        # session_state에서 마지막 비전 결과 가져오기
        if "last_vision_result" not in st.session_state:
            st.session_state.last_vision_result = "nothing"
        
        if "last_coordinates" not in st.session_state:
            st.session_state.last_coordinates = []
        
        result_text = st.session_state.last_vision_result
        coordinates = st.session_state.last_coordinates
        
        # 응답 구성
        if coordinates:
            response = f"감지된 객체: {result_text}\n"
            response += "좌표 정보:\n"
            for coord in coordinates:
                response += (
                    f"  - {coord['name']}: "
                    f"(x={coord['x']}, y={coord['y']}, z={coord['z']}mm) "
                    f"신뢰도={coord['confidence']}\n"
                )
        else:
            response = f"감지된 객체: {result_text}"
        
        logger.info(f"vision_detect 결과: {response}")
        return response
        
    except Exception as e:
        logger.error(f"vision_detect 오류: {e}")
        return f"오류 발생: {str(e)}"
