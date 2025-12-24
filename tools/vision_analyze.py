# tools/vision_analyze.py
import streamlit as st
import base64
import requests
import cv2
from langchain_core.tools import tool
from logger import get_logger

logger = get_logger('TOOLS')

@tool
def vision_analyze(query: str) -> str:
    """현재 카메라 프레임을 VLM으로 상세 분석합니다."""
    try:
        if "last_frame" not in st.session_state: return "영상을 찾을 수 없습니다."
        frame = st.session_state.last_frame
        
        resized = cv2.resize(frame, (320, 240))
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # [수정] 외부 서버 주소와 27b 모델로 변경하고 타임아웃을 180초로 늘립니다.
        response = requests.post(
            "http://ollama.aikopo.net/api/generate",
            json={
                "model": "gemma3:27b",
                "prompt": query,
                "images": [image_base64],
                "stream": False
            },
            timeout=180
        )
        
        if response.status_code == 200:
            return response.json().get('response', '응답이 없습니다.')
        return f"분석 실패 (코드: {response.status_code})"
    except Exception as e:
        return f"통신 오류 발생: {str(e)}"