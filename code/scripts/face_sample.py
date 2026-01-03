# 파일명: code/scripts/face_sample.py (또는 face_sample.py)
import streamlit as st
import streamlit.components.v1 as components

def render_face_svg(eye_openness=100, mouth_curve=0, eye_color="#00FFFF", glow_intensity=0.6):
    """
    EMO 스타일의 얼굴을 그리는 SVG 생성기 (화면 확장판)
    """
    
    # [수정 1] 화면 전체 크기 설정 (높이를 300 -> 400으로 확장)
    canvas_width = 400
    canvas_height = 400  # 웃을 때 입이 내려갈 공간 확보
    
    # 1. 눈의 기하학적 계산
    base_eye_width = 100
    base_eye_height = 110
    
    # 눈 위치: 화면이 길어졌으니 중앙(200)보다 조금 위쪽(150)에 눈을 배치해야 귀여움
    center_y_axis = 160 
    
    current_eye_height = base_eye_height * (eye_openness / 100.0)
    eye_y_pos = center_y_axis - (current_eye_height / 2)
    corner_radius = 20 if eye_openness > 20 else 5

    # 2. 입의 기하학적 계산
    # 입 위치도 눈에 맞춰서 살짝 조정
    mouth_base_y = 280  # 기본 입 위치
    mouth_start_x, mouth_start_y = 160, mouth_base_y
    mouth_end_x, mouth_end_y = 240, mouth_base_y
    
    # 제어점 계산: 웃을 때(양수) Y값이 증가하여 아래로 볼록해짐
    # 입이 화면 밖으로 나가지 않도록 최대치 고려 (최대 400)
    control_y = mouth_base_y + (mouth_curve * 1.8) 
    
    mouth_opacity = 0 if abs(mouth_curve) < 5 else 1.0

    # 3. SVG 코드 조립
    svg_html = f"""
    <svg width="100%" height="100%" viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{canvas_width}" height="{canvas_height}" fill="#050505" rx="40" ry="40"/>
        
        <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
                <feComponentTransfer in="coloredBlur" result="glow_adjusted">
                    <feFuncA type="linear" slope="{glow_intensity + 0.5}"/>
                </feComponentTransfer>
                <feMerge>
                    <feMergeNode in="glow_adjusted"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <g filter="url(#glow)" fill="{eye_color}" stroke="{eye_color}">
            <rect x="60" y="{eye_y_pos}" width="{base_eye_width}" height="{current_eye_height}" 
                  rx="{corner_radius}" ry="{corner_radius}" stroke="none" />
            <rect x="240" y="{eye_y_pos}" width="{base_eye_width}" height="{current_eye_height}" 
                  rx="{corner_radius}" ry="{corner_radius}" stroke="none" />
            
            <path d="M {mouth_start_x} {mouth_start_y} Q 200 {control_y} {mouth_end_x} {mouth_end_y}"
                  stroke-width="8" fill="transparent" stroke-linecap="round"
                  opacity="{mouth_opacity}" />
        </g>
    </svg>
    """
    return svg_html

def main():
    st.set_page_config(page_title="EMO Face Generator", layout="centered")
    st.title("🤖 맹칠이 표정 연구소 v2")
    st.divider()

    col_ctrl, col_view = st.columns([1, 1.5])
    
    with col_ctrl:
        st.subheader("🎛️ 파라미터 조절")
        eye_open = st.slider("눈 크기", 0, 100, 100)
        # 입꼬리 범위를 조금 더 늘려서 테스트
        mouth_val = st.slider("입꼬리 (감정)", -80, 80, 0) 
        color_val = st.color_picker("색상", "#00FFFF")
        glow_val = st.slider("광원 세기", 0.0, 1.0, 0.7)

    with col_view:
        st.subheader("📺 실시간 미리보기")
        face_svg = render_face_svg(eye_open, mouth_val, color_val, glow_val)
        
        # [수정 2] HTML 컴포넌트 높이도 SVG에 맞춰 420px로 증가
        container_style = """
        <div style="
            border: 4px solid #333; 
            border-radius: 20px; 
            padding: 10px; 
            background-color: #000;
            display: flex; justify-content: center;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);">
        """
        st.markdown(container_style, unsafe_allow_html=True)
        # 높이(height)를 넉넉하게 420으로 설정
        components.html(face_svg, height=420, scrolling=False)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()