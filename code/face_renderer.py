# code/face_renderer.py

def render_face_svg(eye_openness=100, mouth_curve=0, eye_color="#00FFFF", glow_intensity=0.7):
    """
    맹칠이의 얼굴(눈과 입)을 SVG 코드로 그려내는 화공 모듈이옵니다.
    """
    # 1. 캔버스 설정 (입이 잘리지 않도록 넉넉하게 400x400)
    canvas_width, canvas_height = 400, 400
    
    # 2. 눈의 기하학적 계산
    base_eye_w, base_eye_h = 100, 110
    center_y = 160 
    
    # 눈 높이 조절 (눈 깜빡임 및 표정)
    curr_eye_h = base_eye_h * (eye_openness / 100.0)
    eye_y = center_y - (curr_eye_h / 2)
    radius = 20 if eye_openness > 20 else 5

    # 3. 입의 기하학적 계산
    mouth_base_y = 280
    mouth_sx, mouth_sy = 160, mouth_base_y
    mouth_ex, mouth_ey = 240, mouth_base_y
    
    # 입꼬리 제어 (양수=웃음, 음수=슬픔)
    control_y = mouth_base_y + (mouth_curve * 1.8)
    mouth_opacity = 0 if abs(mouth_curve) < 5 else 1.0

    # 4. SVG 조립
    svg_code = f"""
    <svg width="100%" height="100%" viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{canvas_width}" height="{canvas_height}" fill="#050505" rx="40" ry="40"/>
        <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
                <feComponentTransfer in="coloredBlur" result="glow_adjusted">
                    <feFuncA type="linear" slope="{glow_intensity + 0.5}"/>
                </feComponentTransfer>
                <feMerge><feMergeNode in="glow_adjusted"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
        </defs>
        <g filter="url(#glow)" fill="{eye_color}" stroke="{eye_color}">
            <rect x="60" y="{eye_y}" width="{base_eye_w}" height="{curr_eye_h}" rx="{radius}" ry="{radius}" stroke="none" />
            <rect x="240" y="{eye_y}" width="{base_eye_w}" height="{curr_eye_h}" rx="{radius}" ry="{radius}" stroke="none" />
            <path d="M {mouth_sx} {mouth_sy} Q 200 {control_y} {mouth_ex} {mouth_ey}"
                  stroke-width="8" fill="transparent" stroke-linecap="round" opacity="{mouth_opacity}" />
        </g>
    </svg>
    """
    return svg_code