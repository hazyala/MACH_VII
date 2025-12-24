# tools/vision_detect.py
import streamlit as st
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def vision_detect(query: str) -> str:
    """실시간 카메라에서 감지된 객체와 좌표 정보 반환"""
    try:
        if "last_vision_result" not in st.session_state:
            st.session_state.last_vision_result = "nothing"
        if "last_coordinates" not in st.session_state:
            st.session_state.last_coordinates = []
            
        result_text = st.session_state.last_vision_result
        coordinates = st.session_state.last_coordinates
        
        if coordinates:
            response = f"감지된 객체: {result_text}\n좌표 정보:\n"
            for coord in coordinates:
                # [수정] .get()을 사용하여 'confidence'가 없어도 오류가 나지 않게 합니다.
                conf = coord.get('confidence', 'N/A')
                response += f"  - {coord['name']}: (x={coord['x']}, y={coord['y']}, z={coord['z']}mm) 신뢰도={conf}\n"
            return response
        return f"감지된 객체: {result_text}"
    except Exception as e:
        logger.error(f"vision_detect 오류: {e}")
        return f"오류 발생: {str(e)}"