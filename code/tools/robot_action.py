import streamlit as st
import math
from langchain_core.tools import tool
from logger import get_logger

# 로거 설정
logger = get_logger('TOOLS')

# [물리 제원 설정 - 단위: Meters]
LINK_L1 = 0.08  # J2 ~ J3 길이
LINK_L2 = 0.08  # J3 ~ J4 길이
LINK_D_MAX = 0.11  # J4 ~ 그리퍼 끝 최대 길이
BASE_HEIGHT = 0.09  # 지면 ~ J1 높이

# [안정 작업공간 (Stable Workspace) - 단위: Meters]
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
# 실제 로봇 설치 후 이 값을 실측하여 수정하십시오.
CAM_TO_ROBOT_OFFSET_X = 0.0  # 가로 방향 차이
CAM_TO_ROBOT_OFFSET_Y = 0.0  # 세로 방향 차이
CAM_TO_ROBOT_OFFSET_Z = 0.05 # 카메라와 로봇 베이스 사이의 거리

def is_within_workspace(x_m, y_m, z_m):
    """
    입력된 로봇 기준 좌표가 안전 작업 범위 내에 있는지 확인합니다.
    """
    # 1. 수평 거리 r 계산 (피타고라스 정리)
    distance_r = math.sqrt(x_m**2 + y_m**2)
    
    # 2. 작업 반경 검사
    if not (WORKSPACE_R_MIN <= distance_r <= WORKSPACE_R_MAX):
        return False, f"작업 반경(R) 초과: 현재 {distance_r:.2f}m (범위: {WORKSPACE_R_MIN}~{WORKSPACE_R_MAX}m)"
    
    # 3. 작업 높이 검사
    if not (WORKSPACE_Z_MIN <= z_m <= WORKSPACE_Z_MAX):
        return False, f"작업 높이(Z) 초과: 현재 {z_m:.2f}m (범위: {WORKSPACE_Z_MIN}~{WORKSPACE_Z_MAX}m)"
    
    # 4. 베이스 회전각(Theta) 검사
    theta_deg = math.degrees(math.atan2(y_m, x_m))
    # atan2 결과는 -180~180이므로 0~180 범위로 조정 필요 (필요시)
    if not (LIMIT_J1[0] <= theta_deg <= LIMIT_J1[1]):
        # 실제 로봇 설치 방향에 따라 보정 로직이 추가될 수 있음
        pass

    return True, "성공"

@tool
def robot_action(command: str, target_x_mm: float = None, target_y_mm: float = None, target_z_mm: float = None) -> str:
    """
    로봇 팔에 동작 명령을 내립니다. 좌표값이 입력되면 작업 공간 검증을 수행합니다.
    
    Args:
        command: 명령어 (wave, grab, push, home 등)
        target_x_mm: 목표 X 좌표 (미리미터 단위)
        target_y_mm: 목표 Y 좌표 (미리미터 단위)
        target_z_mm: 목표 Z 좌표 (미리미터 단위)
    """
    try:
        logger.info(f"robot_action 호출: {command} (Coords: {target_x_mm}, {target_y_mm}, {target_z_mm})")
        
        # 1. 좌표 데이터가 있는 경우 작업 공간 검증 수행
        if target_x_mm is not None and target_y_mm is not None and target_z_mm is not None:
            # mm 단위를 m 단위로 변환하고 오프셋 적용
            robot_x = (target_x_mm / 1000.0) + CAM_TO_ROBOT_OFFSET_X
            robot_y = (target_y_mm / 1000.0) + CAM_TO_ROBOT_OFFSET_Y
            robot_z = (target_z_mm / 1000.0) + CAM_TO_ROBOT_OFFSET_Z
            
            # 검증 함수 호출
            valid, message = is_within_workspace(robot_x, robot_y, robot_z)
            
            if not valid:
                logger.warning(f"작업 범위 이탈: {message}")
                return f"송구하오나 마마, 명령하신 위치는 제 팔이 닿지 않사옵니다. ({message})"

        # 2. 명령어 처리 (시뮬레이션 단계)
        cmd_lower = command.lower()
        if "wave" in cmd_lower:
            result = "🤖 로봇이 지정된 범위 내에서 정중히 손을 흔듭니다."
        elif "grab" in cmd_lower or "잡" in cmd_lower:
            result = "🤖 로봇이 정밀하게 물건을 포착하여 잡았습니다."
        elif "push" in cmd_lower or "밀" in cmd_lower:
            result = "🤖 로봇이 부드럽게 물건을 밀어 이동시켰습니다."
        elif "home" in cmd_lower or "돌아가" in cmd_lower:
            result = "🤖 로봇이 안전하게 홈 위치로 복귀하였습니다."
        else:
            result = f"⚠️ 알 수 없는 명령어이나, 범위 내에서 대기합니다: {command}"
            
        return result
        
    except Exception as e:
        logger.error(f"robot_action 오류 발생: {str(e)}")
        return f"작업 수행 중 문제가 발생하였나이다: {str(e)}"