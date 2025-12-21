# tools/vision_analyze.py
# ================================================================================
# MACH VII - 도구 2: Vision Analyze (VLM 세부 분석)
# ================================================================================

import streamlit as st
import base64
import requests
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def vision_analyze(query: str) -> str:
    """
    현재 카메라 프레임을 VLM(Vision Language Model)으로 분석
    
    Args:
        query: 분석 질문 (예: "뭐하고 있어?", "어떤 상황이야?")
    
    Returns:
        VLM 분석 결과 (텍스트)
    """
    try:
        logger.info(f"vision_analyze 호출: {query}")
        
        # session_state에서 현재 프레임 가져오기
        if "current_frame" not in st.session_state:
            logger.warning("현재 프레임 없음")
            return "현재 프레임을 사용할 수 없습니다."
        
        frame = st.session_state.current_frame
        
        if frame is None:
            return "프레임을 캡처할 수 없습니다."
        
        # 이미지를 base64로 인코딩
        import cv2
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Ollama VLM 호출
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:4b",
                    "prompt": query,
                    "images": [image_base64],
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '응답 없음')
                logger.info(f"vision_analyze 결과: {result[:100]}...")
                return result
            else:
                logger.error(f"VLM 응답 오류: {response.status_code}")
                return "VLM 분석 실패"
                
        except requests.exceptions.ConnectionError:
            logger.error("Ollama 서버 연결 실패")
            return "로컬 LLM 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요."
        
    except Exception as e:
        logger.error(f"vision_analyze 오류: {e}")
        return f"오류 발생: {str(e)}"
