import streamlit as st
import streamlit.components.v1 as components
import os
from logger import setup_terminal_logging
from engine import MachEngine
from face_renderer import render_face_svg 
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# 1. 시스템 기록 설정
setup_terminal_logging()

# 경로 설정
base_directory = os.path.dirname(os.path.abspath(__file__))
data_directory = os.path.join(base_directory, "..", "data")

# 2. 페이지 기본 설정
st.set_page_config(page_title="MACH VII - Control Center", layout="wide")

# CSS 스타일 정의
st.markdown("""
    <style>
    .main { overflow: hidden; height: 100vh; }
    [data-testid="stVerticalBlock"] > div:has(div.stImage) {
        background-color: #f0f2f6; border-radius: 15px; padding: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }
    .chat-container { height: calc(100vh - 200px); overflow-y: auto; padding-right: 10px; }
    
    /* 얼굴 액자 스타일 */
    .face-card {
        width: 100%; max-width: 400px; height: 400px;
        margin: 0 auto; background-color: #050505;
        border-radius: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        overflow: hidden; display: flex; justify-content: center; align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [],
        "face_params": {"eye": 100, "mouth": 0, "color": "#FFFFFF"},
        "current_user": "Princess",
        "current_emotion": "IDLE"
    })

@st.cache_resource
def load_engine():
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

engine = load_engine()
st.session_state.engine = engine 

# 4. 화면 레이아웃
col_left, col_right = st.columns([1, 2.5])

# [좌측 패널]
with col_left:
    st.header("MACH VII")
    
    # [핵심] 얼굴을 그릴 '빈 공간(Placeholder)'을 미리 확보하고 세션에 공유합니다.
    # 이렇게 하면 engine/tools에서 이 공간에 직접 접근해 얼굴을 실시간으로 바꿀 수 있습니다.
    face_container = st.empty()
    st.session_state.face_container = face_container
    
    # 초기 얼굴 그리기 함수 (재사용을 위해 분리하지 않고 즉시 실행)
    def draw_face():
        params = st.session_state.get("face_params", {"eye": 100, "mouth": 0, "color": "#FFFFFF"})
        raw_svg = render_face_svg(
            eye_openness=params.get("eye", 100),
            mouth_curve=params.get("mouth", 0),
            eye_color=params.get("color", "#FFFFFF")
        )
        clean_svg = " ".join(raw_svg.split())
        # 확보해둔 컨테이너에 HTML을 씁니다.
        face_container.markdown(f'<div class="face-card">{clean_svg}</div>', unsafe_allow_html=True)

    # 최초 1회 실행
    draw_face()
    
    status_text = st.session_state.get("current_emotion", "IDLE").upper()
    st.subheader(f"Status: {status_text}")
    
    st.divider()
    st.markdown("### Vision Information")
    st.info(f"Detected: {engine.last_vision_result}")
    
    if engine.last_coordinates:
        with st.expander("Details", expanded=True):
            for coord in engine.last_coordinates:
                st.write(f"- {coord['name']}: Z={coord['z']}cm")

# [우측 패널]
with col_right:
    chat_box = st.container(height=650)
    
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("Input your command here..."):
        st.session_state.last_frame = engine.last_frame
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_box.chat_message("user"):
            st.write(user_input)
        
        with chat_box.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            answer = engine.run_agent(user_input, callbacks=[st_callback])
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()