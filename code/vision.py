import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
from logger import get_logger
import os

# 'VISION' 이름의 로거를 생성합니다.
logger = get_logger('VISION')

class VisionSystem:
    def __init__(self, model_path=None):
        """
        비전 시스템을 초기화하고 YOLO 모델을 로드합니다.
        """
        try:
            # 모델 경로가 제공되지 않은 경우 절대 경로를 기반으로 기본 모델을 설정합니다.
            if model_path is None:
                base_directory = os.path.dirname(os.path.abspath(__file__))
                model_path = os.path.normpath(os.path.join(base_directory, "..", "data", "models", "yolo11n.pt"))

            # 리얼센스 카메라 스트림 설정을 시작합니다.
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
            self.pipeline.start(self.config)
            
            # 깊이 정보를 시각화하기 위한 도구를 준비합니다.
            self.colorizer = rs.colorizer()
            
            # 지정된 경로의 YOLO 모델을 로드합니다.
            self.model = YOLO(model_path)
            logger.info(f"Vision system initialized with model: {model_path}")
            
        except Exception as error:
            logger.error(f"Camera initialization failed: {error}")
            raise

    def process_frame(self):
        """
        카메라 프레임을 획득하여 물체를 탐지하고 좌표를 계산합니다.
        """
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=5000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                return None, None, "nothing", []

            color_image = np.asanyarray(color_frame.get_data())
            depth_colormap = np.asanyarray(self.colorizer.colorize(depth_frame).get_data())
            
            # YOLO 모델로 물체를 탐지합니다.
            results = self.model(color_image, verbose=False, conf=0.5)
            annotated_image = color_image.copy()
            detected_items = []
            coordinates = []

            if results:
                detection_result = results[0]
                annotated_image = detection_result.plot()
                depth_data = np.asanyarray(depth_frame.get_data())
                
                for box in detection_result.boxes:
                    class_id = int(box.cls[0])
                    name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # 객체의 중앙 좌표를 계산합니다.
                    box_coords = box.xyxy[0].cpu().numpy()
                    center_x = int((box_coords[0] + box_coords[2]) / 2)
                    center_y = int((box_coords[1] + box_coords[3]) / 2)
                    
                    # 중앙 좌표의 깊이(Z) 값을 가져옵니다.
                    distance_z = int(depth_data[center_y, center_x])
                    
                    detected_items.append(name)
                    coordinates.append({
                        'name': name, 
                        'confidence': round(confidence, 2),
                        'x': center_x, 
                        'y': center_y, 
                        'z': distance_z
                    })

            # 탐지된 물체들을 쉼표로 구분한 텍스트로 변환합니다.
            detection_text = ", ".join(set(detected_items)) if detected_items else "nothing"
            
            # 컬러 영상과 깊이 영상을 가로로 결합하여 반환합니다.
            combined_display = np.hstack((annotated_image, depth_colormap))
            return combined_display, annotated_image, detection_text, coordinates
            
        except Exception as error:
            logger.error(f"Frame processing error: {error}")
            return None, None, "error", []

    def release(self):
        """카메라 파이프라인을 안전하게 중지합니다."""
        self.pipeline.stop()