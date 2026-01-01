import streamlit as st
import math
from langchain_core.tools import tool
from logger import get_logger

# 시스템 동작 기록을 위한 로거 설정
logger = get_logger('TOOLS')

# [물리 제원 설정 - 단위: Meters]
# 로봇 팔의 각 링크 길이 및 최대 작업 가능 범위
LINK_L1 = 0.08  # J2 ~ J3 길이
LINK_L2 = 0.08  # J3 ~ J4 길이
LINK_D_MAX = 0.11  # J4 ~ 그리퍼 끝 최대 길이
BASE_HEIGHT = 0.09  # 지면 ~ J1 높이

# [안정 작업공간 (Stable Workspace) - 단위: Meters]
# 로봇이 안전하게 움직일 수 있는 물리적 한계 범위
WORKSPACE_R_MIN = 0.06
WORKSPACE_R_MAX = 0.22
WORKSPACE_Z_MIN = 0.02
WORKSPACE_Z_MAX = 0.18

# [관절 각도 제한 - 단위: Degrees]
LIMIT_J1 = (0, 180)
LIMIT_J2 = (25, 155)
LIMIT_J3 = (0, 180)
LIMIT_J4 = (0, 180)
LIMIT_J5 = (0, 180)

# [카메라-로봇 좌표 변환 오프셋 - 단위: Meters]
# 카메라의 원점과 로봇 베이스의 위치 차이를 보정
CAM_TO_ROBOT_OFFSET_X = 0.0
CAM_TO_ROBOT_OFFSET_Y = 0.0
CAM_TO_ROBOT_OFFSET_Z = 0.05 

def is_within_workspace(x_m, y_m, z_m):
    """
    입력된 로봇 기준 좌표(미터)가 안전 작업 범위 내에 있는지 검증함.
    """
    # 1. 수평 거리 r 계산 (피타고라스 정리 적용)
    distance_r = math.sqrt(x_m**2 + y_m**2)
    
    # 2. 작업 반경 검사
    if not (WORKSPACE_R_MIN <= distance_r <= WORKSPACE_R_MAX):
        return False, f"작업 반경(R) 초과: 현재 {distance_r*100:.2f}cm (범위: {WORKSPACE_R_MIN*100}~{WORKSPACE_R_MAX*100}cm)"
    
    # 3. 작업 높이 검사
    if not (WORKSPACE_Z_MIN <= z_m <= WORKSPACE_Z_MAX):
        return False, f"작업 높이(Z) 초과: 현재 {z_m*100:.2f}cm (범위: {WORKSPACE_Z_MIN*100}~{WORKSPACE_Z_MAX*100}cm)"

    return True, "성공"

@tool
def robot_action(command: str, target_x_cm: float = None, target_y_cm: float = None, target_z_cm: float = None) -> str:
    """
    로봇 팔에 동작 명령을 내립니다. 비전 시스템에서 받은 cm 단위 좌표를 검증함.
    
    Args:
        command: 명령어 (wave, grab, push, home 등)
        target_x_cm: 목표 X 좌표 (센티미터 단위)
        target_y_cm: 목표 Y 좌표 (센티미터 단위)
        target_z_cm: 목표 Z 좌표 (센티미터 단위)
    """
    try:
        logger.info(f"robot_action 호출: {command} (Coords: {target_x_cm}, {target_y_cm}, {target_z_cm} cm)")
        
        # 1. 좌표 데이터가 있는 경우 작업 공간 검증 수행
        if target_x_cm is not None and target_y_cm is not None and target_z_cm is not None:
            # [수정] cm 단위를 내부 연산을 위한 m 단위로 변환하고 오프셋 적용
            robot_x = (target_x_cm / 100.0) + CAM_TO_ROBOT_OFFSET_X
            robot_y = (target_y_cm / 100.0) + CAM_TO_ROBOT_OFFSET_Y
            robot_z = (target_z_cm / 100.0) + CAM_TO_ROBOT_OFFSET_Z
            
            # 검증 함수 호출
            valid, message = is_within_workspace(robot_x, robot_y, robot_z)
            
            if not valid:
                logger.warning(f"작업 범위 이탈: {message}")
                return f"송구하오나 마마, 명령하신 위치는 제 팔이 닿지 않사옵니다. ({message})"

        # 2. 명령어 처리 (로직 수행)
        cmd_lower = command.lower()
        if "wave" in cmd_lower:
            result = "로봇이 지정된 범위 내에서 정중히 손을 흔듭니다."
        elif "grab" in cmd_lower or "잡" in cmd_lower:
            result = "로봇이 정밀하게 물건을 포착하여 잡았습니다."
        elif "push" in cmd_lower or "밀" in cmd_lower:
            result = "로봇이 부드럽게 물건을 밀어 이동시켰습니다."
        elif "home" in cmd_lower or "돌아가" in cmd_lower:
            result = "로봇이 안전하게 홈 위치로 복귀하였습니다."
        else:
            result = f"알 수 없는 명령어이나, 범위 내에서 대기합니다: {command}"
            
        return result
        
    except Exception as e:
        logger.error(f"robot_action 오류 발생: {str(e)}")
        return f"작업 수행 중 문제가 발생하였나이다: {str(e)}"