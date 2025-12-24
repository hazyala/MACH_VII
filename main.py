import streamlit as st
import os
from logger import setup_terminal_logging

# 시스템 기록 시작
setup_terminal_logging()

from engine import MachEngine
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# 1. 페이지 기본 설정 및 고정 레이아웃을 위한 CSS 주입
st.set_page_config(page_title="MACH VII - 맹칠 관제 센터", layout="wide")

st.markdown("""
    <style>
    /* 전체 화면 스크롤 방지 */
    .main {
        overflow: hidden;
        height: 100vh;
    }
    /* 사이드바 영역 스타일 */
    [data-testid="stVerticalBlock"] > div:has(div.stImage) {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }
    /* 채팅창 영역 고정 높이 및 내부 스크롤 */
    .chat-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [], 
        "current_emotion": "idle", 
        "current_emotion_path": "assets/gif/idle.gif"
    })

@st.cache_resource
def load_engine():
    """엔진 인스턴스 생성 및 비전 루프 시작"""
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

engine = load_engine()
st.session_state.engine = engine 

# 3. 메인 레이아웃 구성 (좌측 1 : 우측 2.5)
col_left, col_right = st.columns([1, 2.5])

# --- 좌측 영역: 맹칠이 상태 및 비전 정보 ---
with col_left:
    st.header("🛡️ MACH VII")
    
    # 맹칠이 표정 (감정 GIF)
    if os.path.exists(st.session_state.current_emotion_path):
        st.image(st.session_state.current_emotion_path, use_container_width=True)
    else:
        st.warning("표정 파일을 찾을 수 없습니다.")
        
    st.subheader(f"상태: {st.session_state.current_emotion.upper()}")
    
    st.divider()
    
    # 실시간 탐지 정보 (가독성 보강)
    st.markdown("### 👁️ 실시간 탐지 정보")
    st.info(f"**현재 탐지된 객체:**\n\n{engine.last_vision_result}")
    
    if engine.last_coordinates:
        with st.expander("상세 좌표 보기", expanded=True):
            for coord in engine.last_coordinates:
                st.write(f"- {coord['name']}: Z={coord['z']}mm")

# --- 우측 영역: 메신저 스타일 채팅창 ---
with col_right:
    chat_box = st.container(height=650) # CSS와 연동되어 내부 스크롤 발생
    
    # 기존 메시지 출력
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자 입력 및 에이전트 대응
    if user_input := st.chat_input("공주마마, 무엇을 도와드릴까요?"):
        # 최신 비전 프레임 캡처
        st.session_state.last_frame = engine.last_frame
        
        # 사용자 메시지 기록
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_box.chat_message("user"):
            st.write(user_input)
        
        # 맹칠이의 답변 생성
        with chat_box.chat_message("assistant"):
            # 추론 과정(Thought/Action)을 보여주기 위한 콜백 핸들러
            st_callback = StreamlitCallbackHandler(st.container())
            
            # 에이전트 실행
            answer = engine.run_agent(user_input, callbacks=[st_callback])
            st.write(answer)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()