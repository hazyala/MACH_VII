# logger.py
# ================================================================================
# MACH VII - 로깅 시스템
# ColoredFormatter + 파일 + 터미널 이중 핸들러
# ================================================================================

import logging
import sys
import os
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """이모지와 컬러를 지원하는 포매터"""
    
    # ANSI 컬러 코드
    COLORS = {
        'DEBUG': '\033[36m',      # 청록색
        'INFO': '\033[92m',       # 초록색
        'WARNING': '\033[93m',    # 노란색
        'ERROR': '\033[91m',      # 빨간색
        'CRITICAL': '\033[95m'    # 보라색
    }
    RESET = '\033[0m'
    
    # 이모지 매핑
    EMOJIS = {
        'VISION': '👁️ ',
        'AGENT': '🧠',
        'MAIN': '📱',
        'ROBOT': '🤖',
        'EMOTION': '😊',
        'ERROR': '❌',
        'SUCCESS': '✅',
        'DEBUG': '🔍',
        'STREAM': '📹',
        'LLM': '💬',
        'TOOLS': '🛠️',
        'CONFIG': '⚙️'
    }
    
    def format(self, record):
        # 모듈명 추출
        module_name = record.name.upper()
        
        # 이모지 선택 (모듈명 기반)
        emoji = self.EMOJIS.get(module_name, '📌')
        
        # 로그 레벨 컬러
        levelname = record.levelname
        color = self.COLORS.get(levelname, '')
        
        # 타임스탬프
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 포매팅
        formatted_msg = (
            f"{color}[{timestamp}] [{emoji} {module_name}] "
            f"{record.getMessage()}{self.RESET}"
        )
        return formatted_msg


def get_logger(name):
    """로거 인스턴스 생성"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # ===== 터미널 핸들러 =====
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(ColoredFormatter())
    
    # ===== 파일 핸들러 =====
    # logs/ 디렉토리 자동 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 파일명 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"maengchil_{timestamp}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 핸들러 추가
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    return logger


# 테스트
if __name__ == "__main__":
    logger = get_logger('MAIN')
    logger.info("✅ 로거 초기화 성공")
    logger.debug("🔍 디버그 메시지")
    logger.warning("⚠️ 경고 메시지")
    logger.error("❌ 오류 메시지")
