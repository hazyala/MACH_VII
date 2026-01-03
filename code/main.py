import streamlit as st
import streamlit.components.v1 as components
import os
from logger import setup_terminal_logging
from engine import MachEngine
from face_renderer import render_face_svg 
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# 시스템 기록 시작 (터미널 출력을 로그 파일로 저장하는 설정)
setup_terminal_logging()

# 현재 실행 중인 파일(main.py)의 절대 경로를 획득
# os.path.abspath(__file__)는 파일의 전체 경로를 의미함
base_directory = os.path.dirname(os.path.abspath(__file__))

# 데이터가 보관된 data 폴더의 절대 경로를 설정
# code 폴더와 같은 층에 있으므로 한 단계 상위로 이동(..) 후 data 폴더 선택
data_directory = os.path.join(base_directory, "..", "data")

# 1. 페이지 기본 설정 및 레이아웃 구성을 위한 CSS 적용
st.set_page_config(page_title="MACH VII - Control Center", layout="wide")

st.markdown("""
    <style>
    .main {
        overflow: hidden;
        height: 100vh;
    }
    [data-testid="stVerticalBlock"] > div:has(div.stImage) {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }
    .chat-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 세션 상태(st.session_state) 초기화
if "messages" not in st.session_state:
    st.session_state.update({
        "messages": [],
        # 기본 표정 파라미터 초기화 (idle 상태)
        "face_params": {"eye": 100, "mouth": 0, "color": "#00FFFF"},
        "current_user": "Princess"
    })

@st.cache_resource
def load_engine():
    """로봇의 핵심 두뇌인 엔진 인스턴스를 생성하고 비전 루프를 구동함"""
    engine_instance = MachEngine()
    engine_instance.start_vision_loop()
    return engine_instance

# 엔진 로드 및 세션 상태에 저장
engine = load_engine()
st.session_state.engine = engine 

# 3. 화면 레이아웃 구성 (좌측 상태창 : 우측 채팅창)
col_left, col_right = st.columns([1, 2.5])

# 좌측 영역: 로봇의 표정 및 실시간 비전 정보 표시
# code/main.py (이미지 출력 부분)

with col_left:
    st.header("MACH VII")
    
    # 1. 표정 파라미터 가져오기
    params = st.session_state.get("face_params", {"eye": 100, "mouth": 0, "color": "#00FFFF"})
    
    # 2. SVG 생성
    face_svg = render_face_svg(
        eye_openness=params.get("eye", 100),
        mouth_curve=params.get("mouth", 0),
        eye_color=params.get("color", "#00FFFF")
    )
    
    # 3. [수정] 불필요한 st.markdown 껍데기를 제거하고 바로 출력합니다.
    # SVG 내부에 이미 검은 배경(rect)이 있으므로 깔끔하게 나옵니다.
    components.html(face_svg, height=400, scrolling=False)
    
    # 상태 텍스트
    status_text = st.session_state.get("current_emotion", "IDLE").upper()
    st.subheader(f"Status: {status_text}")
    
    # (이하 비전 정보 코드는 그대로 두시면 됩니다)
    st.divider()
    st.markdown("### Vision Information")
    st.info(f"Detected: {engine.last_vision_result}")
    
    if engine.last_coordinates:
        with st.expander("Details", expanded=True):
            for coord in engine.last_coordinates:
                st.write(f"- {coord['name']}: Z={coord['z']}cm")

# 우측 영역: 대화형 인터페이스
with col_right:
    chat_box = st.container(height=650)
    
    # 이전 대화 내용 출력
    for msg in st.session_state.messages:
        with chat_box.chat_message(msg["role"]):
            st.write(msg["content"])

    # 사용자 입력 처리 및 에이전트 답변 생성
    if user_input := st.chat_input("Input your command here..."):
        # 최신 카메라 프레임 저장
        st.session_state.last_frame = engine.last_frame
        
        # 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_box.chat_message("user"):
            st.write(user_input)
        
        # 에이전트 답변 생성 루프
        with chat_box.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            # engine.py의 run_agent를 호출하여 답변 획득
            answer = engine.run_agent(user_input, callbacks=[st_callback])
            st.write(answer)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()