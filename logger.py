import logging
import sys
import os
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """
    로그 메시지에 색상과 이모지를 추가하여 가독성을 높이는 클래스입니다.
    """
    COLORS = {
        'DEBUG': '\033[36m', 'INFO': '\033[92m', 'WARNING': '\033[93m',
        'ERROR': '\033[91m', 'CRITICAL': '\033[95m'
    }
    RESET = '\033[0m'
    EMOJIS = {
        'VISION': '👁️ ', 'AGENT': '🧠', 'MAIN': '📱', 
        'ROBOT': '🤖', 'EMOTION': '😊', 'TOOLS': '🛠️', 'ENGINE': '⚙️'
    }
    
    def format(self, record):
        module_name = record.name.upper()
        emoji = self.EMOJIS.get(module_name, '📌')
        log_color = self.COLORS.get(record.levelname, '')
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"{log_color}[{current_time}] [{emoji} {module_name}] {record.getMessage()}{self.RESET}"

def get_logger(name):
    """
    터미널 출력과 날짜별 파일 저장을 동시에 수행하는 로거를 생성합니다.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        logger.handlers.clear()
    
    # 1. 터미널 출력 설정
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColoredFormatter())
    logger.addHandler(stream_handler)
    
    # 2. 파일 저장 설정 (날짜별 하나의 파일)
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    file_path = os.path.join(log_dir, f"maengchil_{date_str}.log")
    
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    file_fmt = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s', '%H:%M:%S')
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    return logger