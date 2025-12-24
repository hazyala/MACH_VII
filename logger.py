import logging
import sys
import os
from datetime import datetime

class TerminalTee:
    """
    터미널 출력(stdout)을 가로채어 파일에도 동시에 기록하는 클래스입니다.
    """
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "a", encoding="utf-8")

    def write(self, message):
        """터미널과 파일 양쪽에 메시지를 씁니다."""
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        """출력 버퍼를 비웁니다."""
        self.terminal.flush()
        self.log_file.flush()

def setup_terminal_logging():
    """
    프로그램의 모든 터미널 출력을 파일로 저장하도록 설정하는 함수입니다.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    date_str = datetime.now().strftime("%Y%m%d")
    full_log_path = os.path.join(log_dir, f"terminal_full_{date_str}.log")
    
    # 표준 출력을 가로챕니다.
    sys.stdout = TerminalTee(full_log_path)
    print(f"\n[SYSTEM] 모든 터미널 기록이 {full_log_path}에 저장됩니다.\n")

def get_logger(name):
    """
    기존의 모듈별 로깅 기능을 수행하는 로거를 생성합니다.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        logger.handlers.clear()
    
    # 터미널 출력 설정 (이미 sys.stdout이 Tee로 교체되어 파일에도 같이 적힙니다.)
    stream_handler = logging.StreamHandler(sys.stdout)
    
    # 이모지 매핑 (마마의 교지에 따라 로깅에는 이모지를 사용합니다.)
    emojis = {'VISION': '👁️ ', 'ENGINE': '⚙️ ', 'AGENT': '🧠', 'TOOLS': '🛠️ '}
    emoji = emojis.get(name.upper(), '📌')
    
    class EmojiFormatter(logging.Formatter):
        def format(self, record):
            t = datetime.now().strftime("%H:%M:%S")
            return f"[{t}] [{emoji} {record.name.upper()}] {record.getMessage()}"
            
    stream_handler.setFormatter(EmojiFormatter())
    logger.addHandler(stream_handler)
    return logger