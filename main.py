# main.py (간소화)
# ================================================================================
# MACH VII - Streamlit UI (텍스트 정보만)
# ================================================================================

import streamlit as st
from PIL import Image
import os

from logger import get_logger
from vision import VisionSystem
from agent import get_agent

logger = get_logger('MAIN')

# ===== Streamlit 페이지 설정 =====
st.set_page_config(
    page_title="🛡️ MACH VII - 맹칠",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== Session State 초기화 =====
def init_session_state():
    if "vision_system" not in st.session_state:
        st.session_state.vision_system = None
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "last_vision_result" not in st.session_state:
        st.session_state.last_vision_result = "nothing"
    if "last_coordinates" not in st.session_state:
        st.session_state.last_coordinates = []
    if "current_emotion" not in st.session_state:
        st.session_state.current_emotion = "idle"
    if "current_emotion_path" not in st.session_state:
        st.session_state.current_emotion_path = "assets/gif/idle.jpg"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory" not in st.session_state:
        st.session_state.memory = {}

init_session_state()

# ===== Vision 시스템 =====
@st.cache_resource
def load_vision_system():
    try:
        logger.info("Vision 시스템 초기화")
        vision = VisionSystem('yolov11s.pt')
        logger.info("✅ Vision 로드")
        return vision
    except Exception as e:
        logger.error(f"Vision 오류: {e}")
        st.error(f"❌ Vision: {e}")
        return None

# ===== Agent =====
@st.cache_resource
def load_agent():
    try:
        logger.info("Agent 초기화")
        agent = get_agent()
        logger.info("✅ Agent 로드")
        return agent
    except Exception as e:
        logger.error(f"Agent 오류: {e}")
        st.warning(f"⚠️ Agent: {e}")
        return None

# ===== 메인 =====
def main():
    st.title("🛡️ MACH VII - 맹칠")
    
    st.info("💡 **RealSense 창을 별도로 띄워주세요!**\n`python3 vision_display.py`")
    
    st.markdown("---")
    
    vision = load_vision_system()
    agent = load_agent()
    
    # ===== 2열 레이아웃 =====
    col_info, col_chat = st.columns([1, 1])
    
    # ===== 왼쪽: Vision 정보 =====
    with col_info:
        st.subheader("📊 Vision 정보")
        
        if st.button("📸 현재 프레임 분석"):
            with st.spinner("🔄 분석 중..."):
                try:
                    if vision is None:
                        st.error("Vision 시스템이 없습니다.")
                        return
                    
                    frame, text_result, coordinates = vision.process_frame()
                    
                    st.session_state.last_vision_result = text_result
                    st.session_state.last_coordinates = coordinates
                    
                    logger.info(f"분석: {text_result}")
                    
                    # 결과 표시
                    st.success(f"✅ 감지: **{text_result}**")
                    
                    if coordinates:
                        st.markdown("**감지된 객체:**")
                        for coord in coordinates:
                            st.write(
                                f"- **{coord['name']}** "
                                f"(신뢰도: {coord['confidence']}) "
                                f"위치: ({coord['x']}, {coord['y']}) "
                                f"거리: {coord['z']}mm"
                            )
                    else:
                        st.info("감지된 객체 없음")
                
                except Exception as e:
                    logger.error(f"분석 오류: {e}")
                    st.error(f"❌ {e}")
    
    # ===== 오른쪽: 감정 & 채팅 =====
    with col_chat:
        st.subheader("😊 감정 & 채팅")
        
        # 감정 GIF
        try:
            emotion_path = st.session_state.current_emotion_path
            if os.path.exists(emotion_path):
                emotion_image = Image.open(emotion_path)
                st.image(
                    emotion_image,
                    use_column_width=True,
                    caption=f"현재 감정: {st.session_state.current_emotion}"
                )
            else:
                st.warning(f"⚠️ GIF 없음")
        except Exception as e:
            logger.error(f"감정 오류: {e}")
        
        st.markdown("---")
        
        # 채팅
        st.subheader("💬 채팅")
        
        # 메시지 표시
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.write(f"👤 **사용자:** {msg['content']}")
            else:
                st.write(f"🤖 **맹칠:** {msg['content']}")
        
        # 입력
        user_input = st.text_input("명령어 입력")
        
        if user_input:
            logger.info(f"입력: {user_input}")
            
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            with st.spinner("🤖 생각 중..."):
                try:
                    if agent is not None:
                        result = agent.invoke({"input": user_input})
                        response = result.get("output", "응답 없음")
                    else:
                        response = "Agent를 사용할 수 없습니다."
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    logger.info(f"응답: {response[:100]}...")
                
                except Exception as e:
                    logger.error(f"Agent 오류: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ {str(e)}"
                    })
            
            st.rerun()

if __name__ == "__main__":
    try:
        logger.info("MACH VII 시작")
        main()
    except Exception as e:
        logger.error(f"오류: {e}")
        st.error(f"❌ {e}")

