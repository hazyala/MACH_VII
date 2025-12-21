# vision_display.py
# ================================================================================
# MACH VII - Vision Display (RealSense + OpenCV 별도 창)
# ================================================================================

import cv2
import threading
import time
from vision import VisionSystem
from logger import get_logger

logger = get_logger('VISION')

class VisionDisplay:
    """RealSense 실시간 표시 (별도 OpenCV 창)"""
    
    def __init__(self):
        logger.info("VisionDisplay 초기화")
        self.vision = VisionSystem('yolov11s.pt')
        self.running = False
        self.last_frame = None
        self.last_result = None
        self.last_coordinates = None
    
    def run(self):
        """실시간 표시 루프"""
        logger.info("Vision 디스플레이 시작")
        self.running = True
        
        try:
            while self.running:
                # Vision 처리
                frame, text_result, coordinates = self.vision.process_frame()
                
                if frame is not None:
                    self.last_frame = frame
                    self.last_result = text_result
                    self.last_coordinates = coordinates
                    
                    # OpenCV 창에 표시
                    display_frame = frame.copy()
                    
                    # 텍스트 추가
                    cv2.putText(
                        display_frame,
                        f"Detected: {text_result}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )
                    
                    # 좌표 정보 추가
                    y_offset = 60
                    for coord in coordinates:
                        text = f"{coord['name']}: ({coord['x']}, {coord['y']}, {coord['z']}mm)"
                        cv2.putText(
                            display_frame,
                            text,
                            (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 255),
                            1
                        )
                        y_offset += 25
                    
                    # 창에 표시
                    cv2.imshow("🛡️ MACH VII - Vision", display_frame)
                
                # ESC 키로 종료
                if cv2.waitKey(1) & 0xFF == 27:
                    self.running = False
                
                time.sleep(0.067)  # ~15fps
        
        except Exception as e:
            logger.error(f"Vision 디스플레이 오류: {e}")
        
        finally:
            cv2.destroyAllWindows()
            self.vision.release()
            logger.info("Vision 디스플레이 종료")
    
    def start_thread(self):
        """별도 스레드에서 시작"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        logger.info("Vision 디스플레이 스레드 시작")
        return thread
    
    def stop(self):
        """종료"""
        self.running = False
        logger.info("Vision 디스플레이 중지 요청")


# 독립 실행
if __name__ == "__main__":
    try:
        display = VisionDisplay()
        display.run()
    except Exception as e:
        logger.error(f"오류: {e}")
