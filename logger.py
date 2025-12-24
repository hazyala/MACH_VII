import logging
import sys
import os
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """터미널 출력용: 색상과 이모지 포함"""
    COLORS = {'DEBUG': '\033[36m', 'INFO': '\033[92m', 'WARNING': '\033[93m', 'ERROR': '\033[91m'}
    RESET = '\033[0m'
    EMOJIS = {'VISION': '👁️ ', 'ENGINE': '⚙️ ', 'AGENT': '🧠', 'TOOLS': '🛠️ ', 'MAIN': '📱'}
    
    def format(self, record):
        module_name = record.name.upper()
        emoji = self.EMOJIS.get(module_name, '📌')
        log_color = self.COLORS.get(record.levelname, '')
        t = datetime.now().strftime("%H:%M:%S")
        return f"{log_color}[{t}] [{emoji} {module_name}] {record.getMessage()}{self.RESET}"

def get_logger(name):
    """터미널과 파일에 동시에 이모지 로그를 남깁니다."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers: logger.handlers.clear()
    
    # 1. 터미널 핸들러
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColoredFormatter())
    logger.addHandler(stream_handler)
    
    # 2. 파일 핸들러 (이모지 포함 포맷)
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, f"maengchil_{datetime.now().strftime('%Y%m%d')}.log")
    
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    # 파일 전용 포매터: 색상 코드는 빼고 이모지만 넣습니다.
    class FileEmojiFormatter(logging.Formatter):
        def format(self, record):
            emoji = ColoredFormatter.EMOJIS.get(record.name.upper(), '📌')
            t = datetime.now().strftime("%H:%M:%S")
            return f"[{t}] [{emoji} {record.name.upper()}] {record.getMessage()}"
            
    file_handler.setFormatter(FileEmojiFormatter())
    logger.addHandler(file_handler)
    return logger