# import streamlit as st
# import requests
# from langchain_core.tools import tool
# from logger import get_logger

# # 도구 로그 기록을 위한 로거 설정
# logger = get_logger('TOOLS')

# # [물리 제원 설정 - 수정됨]
# LINK_L1 = 0.08  # J2 ~ J3 길이 (0.08m)
# LINK_L2 = 0.08  # J3 ~ J4 길이 (0.08m)
# LINK_D_MAX = 0.19  # J4 ~ 그리퍼 끝 길이 (0.19m)
# BASE_HEIGHT = 0.12  # 지면 ~ J2 높이 (0.12m)

# # [관절 각도 제한 정보 - 로봇 담당자 참고용]
# # J1: 0~180, J2: 35~145, J3: 25~155, J4: 0~180, J5: 0~180
# # 특이사항: J2, J3, J4는 동작 시 90도를 감산해야 할 수 있음

# # [원격 로봇 서버 설정]
# # 담당자에게 받은 라즈베리 파이의 IP 주소를 아래에 적어주셔야 합니다.
# ROBOT_IP = "100.127.161.127" 
# ROBOT_SERVER_URL = f"http://{ROBOT_IP}:8000/robot/action"

# @tool
# def robot_action(command: str, target_x_mm: float = None, target_y_mm: float = None, target_z_mm: float = None) -> str:
#     """
#     로봇 팔에 동작 명령을 내리고 원격 서버로 전송합니다.
    
#     Args:
#         command: 명령어 (wave, grab, push, home 등)
#         target_x_mm: 목표 X 좌표 (mm)
#         target_y_mm: 목표 Y 좌표 (mm)
#         target_z_mm: 목표 Z 좌표 (mm)
#     """
#     try:
#         logger.info(f"robot_action 원격 호출: {command} (좌표: {target_x_mm}, {target_y_mm}, {target_z_mm})")
        
#         # 1. 원격 서버로 보낼 데이터 구성
#         payload = {
#             "command": command,
#             "target": {
#                 "x": target_x_mm,
#                 "y": target_y_mm,
#                 "z": target_z_mm
#             } if target_x_mm is not None else None,
#             "speed": 50
#         }

#         # 2. 라즈베리 파이 서버로 명령 전송
#         # 작업 공간 검증 없이 즉시 전송합니다.
#         response = requests.post(ROBOT_SERVER_URL, json=payload, timeout=5)
        
#         if response.status_code == 200:
#             result = response.json()
#             msg = result.get("message", "명령이 전달되었습니다.")
#             return f"✅ 팔(라즈베리 파이)이 응답하였나이다: {msg} (ID: {result.get('task_id')})"
#         else:
#             return f"❌ 팔과의 통신에 실패하였나이다. (코드: {response.status_code})"
            
#     except Exception as e:
#         logger.error(f"robot_action 통신 오류: {e}")
#         return f"송구하오나 마마, 팔과 연결이 닿지 않사옵니다: {str(e)}"