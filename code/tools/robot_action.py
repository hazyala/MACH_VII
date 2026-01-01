import streamlit as st
import math
from langchain_core.tools import tool
from logger import get_logger

# 도구의 동작 상태를 기록하기 위한 로거 설정
logger = get_logger('TOOLS')

# [로봇 물리 제원 설정 - 단위: Meters]
LINK_L1 = 0.08  # 두 번째 관절 길이
LINK_L2 = 0.08  # 세 번째 관절 길이
LINK_D_MAX = 0.11  # 집게까지의 최대 길이
BASE_HEIGHT = 0.09  # 바닥에서 첫 관절까지 높이

# [안정 작업공간 설정 - 단위: Meters]
WORKSPACE_R_MIN = 0.06  # 최소 도달 반경
WORKSPACE_R_MAX = 0.22  # 최대 도달 반경
WORKSPACE_Z_MIN = 0.02  # 최소 작업 높이
WORKSPACE_Z_MAX = 0.18  # 최대 작업 높이

# [점진적 접근 및 오프셋 설정]
STEP_RATIO = 0.4  # 목표 거리의 40%씩 신중하게 이동
ARRIVAL_THRESHOLD_CM = 1.0  # 1cm 이내 접근 시 도착으로 간주
CAM_TO_ROBOT_OFFSET_X = 0.0
CAM_TO_ROBOT_OFFSET_Y = 0.0
CAM_TO_ROBOT_OFFSET_Z = 0.05  # 카메라와 로봇 베이스 사이 거리 보정

def is_within_workspace(x_m, y_m, z_m):
    """
    입력된 로봇 기준 좌표(m)가 물리적인 안전 작업 범위 내에 있는지 검증합니다.
    """
    # 수평 거리(R) 계산
    distance_r = math.sqrt(x_m**2 + y_m**2)
    
    # 반경 범위 검사
    if not (WORKSPACE_R_MIN <= distance_r <= WORKSPACE_R_MAX):
        return False, f"반경(R) 이탈: {distance_r*100:.1f}cm (허용: {WORKSPACE_R_MIN*100}~{WORKSPACE_R_MAX*100}cm)"
    
    # 높이 범위 검사
    if not (WORKSPACE_Z_MIN <= z_m <= WORKSPACE_Z_MAX):
        return False, f"높이(Z) 이탈: {z_m*100:.1f}cm (허용: {WORKSPACE_Z_MIN*100}~{WORKSPACE_Z_MAX*100}cm)"
    
    return True, "정상 범위"

@tool
def robot_action(command: str, target_x_cm: float = None, target_y_cm: float = None, target_z_cm: float = None) -> str:
    """
    로봇 팔에 동작 명령을 내리는 도구입니다.
    최종 목적지가 안전 범위 내인지 먼저 확인한 후, 점진적으로 접근합니다.
    
    Args:
        command: 수행할 동작 명칭 (예: grab, push, wave, home)
        target_x_cm: 목표 X 좌표 (cm)
        target_y_cm: 목표 Y 좌표 (cm)
        target_z_cm: 목표 Z 좌표 (cm)
    """
    try:
        # 1. 좌표가 필요 없는 단순 동작 처리
        if target_x_cm is None:
            logger.info(f"단순 동작 수행: {command}")
            return f"[{command}] 명령을 안전하게 수행하였나이다."

        # 2. [공주마마 지침] 최종 목적지 안전 검증 (1차 수행)
        # 비전에서 넘어온 cm 단위를 내부 연산을 위해 m로 변환
        target_x_m = (target_x_cm / 100.0) + CAM_TO_ROBOT_OFFSET_X
        target_y_m = (target_y_cm / 100.0) + CAM_TO_ROBOT_OFFSET_Y
        target_z_m = (target_z_cm / 100.0) + CAM_TO_ROBOT_OFFSET_Z
        
        is_safe, message = is_within_workspace(target_x_m, target_y_m, target_z_m)
        
        if not is_safe:
            # 범위 밖일 경우 에이전트가 단념하도록 명확히 보고
            logger.warning(f"작업 영역 이탈 보고: {message}")
            return f"결정적 오류: 목표 위치가 로봇의 물리적 한계를 벗어났나이다. ({message}) 더 이상의 접근 시도는 불가하오니 마마께 보고 후 종료하십시오."

        # 3. [공주마마 지침] 안전 확인 시 점진적 접근 수행 (2차 수행)
        if "current_arm_pos" not in st.session_state:
            # 현재 위치 정보가 없으면 초기 위치로 설정
            st.session_state.current_arm_pos = {"x": 0.0, "y": 0.0, "z": 15.0}

        curr = st.session_state.current_arm_pos
        
        # 현재 위치와 최종 목표 사이의 차이 계산
        diff_x = target_x_cm - curr['x']
        diff_y = target_y_cm - curr['y']
        diff_z = target_z_cm - curr['z']
        
        total_distance = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)

        # 이미 목표 지점에 도달했는지 확인
        if total_distance < ARRIVAL_THRESHOLD_CM:
            return f"마마, 이미 최종 목적지({target_x_cm}, {target_y_cm}, {target_z_cm}cm)에 안착하였나이다!"

        # 점진적 이동량 계산 (비율 적용)
        step_x = diff_x * STEP_RATIO
        step_y = diff_y * STEP_RATIO
        step_z = diff_z * STEP_RATIO
        
        # 새로운 중간 위치 업데이트
        new_pos = {
            "x": curr['x'] + step_x,
            "y": curr['y'] + step_y,
            "z": curr['z'] + step_z
        }
        st.session_state.current_arm_pos = new_pos

        # 로그 기록 및 결과 반환
        logger.info(f"[STEP_MOVE] To ({new_pos['x']:.1f}, {new_pos['y']:.1f}, {new_pos['z']:.1f}cm)")
        
        return (f"최종 목적지가 안전함을 확인하여, 목표를 향해 {STEP_RATIO*100:.0f}%만큼 신중히 다가갔나이다. "
                f"현재 위치는 ({new_pos['x']:.1f}, {new_pos['y']:.1f}, {new_pos['z']:.1f}cm)이오니, "
                f"마마, 비전(vision_detect)으로 다시 한번 살펴 주시옵소서.")

    except Exception as error:
        logger.error(f"robot_action 실행 중 오류: {error}")
        return f"작업 중 예상치 못한 불충이 발생하였나이다: {str(error)}"