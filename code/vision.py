import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
from logger import get_logger
import os

# 'VISION' 이름의 로거를 생성하여 시스템 상태를 기록합니다.
logger = get_logger('VISION')

class VisionSystem:
    def __init__(self, model_path=None):
        """
        비전 시스템을 초기화하고 카메라와 YOLO 모델을 준비합니다.
        실거리 좌표 계산을 위해 카메라의 고유 파라미터(Intrinsics)를 획득합니다.
        """
        try:
            # 모델 경로 설정 (절대 경로 기준)
            if model_path is None:
                base_directory = os.path.dirname(os.path.abspath(__file__))
                model_path = os.path.normpath(os.path.join(base_directory, "..", "data", "models", "yolo11n.pt"))

            # 리얼센스 파이프라인 및 스트림 설정
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
            
            # 파이프라인 시작 및 카메라 고유 정보(Intrinsics) 획득
            self.profile = self.pipeline.start(self.config)
            self.intrinsics = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
            
            # 깊이 데이터 시각화 도구 및 YOLO 모델 로드
            self.colorizer = rs.colorizer()
            self.model = YOLO(model_path)
            
            logger.info("Vision system initialized with RealSense Intrinsics.")
            
        except Exception as error:
            logger.error(f"Camera initialization failed: {error}")
            raise

    def get_real_world_coordinates(self, depth_data, pixel_x, pixel_y):
        """
        픽셀 좌표와 깊이 데이터를 실제 3D 공간 좌표(mm)로 변환합니다.
        Z=0 문제를 방지하기 위해 주변 영역의 중간값을 활용합니다.
        """
        # 중앙점 주변 5x5 영역의 깊이 값을 추출하여 유효성 검사 수행
        roi_size = 2
        y_start, y_end = max(0, pixel_y - roi_size), min(480, pixel_y + roi_size + 1)
        x_start, x_end = max(0, pixel_x - roi_size), min(640, pixel_x + roi_size + 1)
        
        depth_roi = depth_data[y_start:y_end, x_start:x_end]
        valid_depths = depth_roi[depth_roi > 0]
        
        if valid_depths.size > 0:
            # 노이즈를 제거하기 위해 유효한 깊이 값 중 중간값(Median) 선택
            median_depth = np.median(valid_depths)
            
            # 카메라 고유 정보를 바탕으로 픽셀을 3D 포인트로 역투영
            point = rs.rs2_deproject_pixel_to_point(self.intrinsics, [pixel_x, pixel_y], median_depth)
            
            # RealSense 좌표계: x(우측), y(하단), z(전방)
            # 로봇 좌표계에 맞게 변환 (mm 단위 반환)
            return round(point[0], 2), round(point[1], 2), round(point[2], 2)
        
        return 0, 0, 0

    def process_frame(self):
        """
        프레임을 처리하여 물체를 탐지하고 실제 좌표를 산출합니다.
        """
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=5000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                return None, None, "nothing", []

            color_image = np.asanyarray(color_frame.get_data())
            depth_data = np.asanyarray(depth_frame.get_data())
            depth_colormap = np.asanyarray(self.colorizer.colorize(depth_frame).get_data())
            
            # YOLO 탐지 수행
            results = self.model(color_image, verbose=False, conf=0.5)
            annotated_image = color_image.copy()
            detected_items = []
            coordinates = []

            if results:
                detection_result = results[0]
                annotated_image = detection_result.plot()
                
                for box in detection_result.boxes:
                    class_id = int(box.cls[0])
                    name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # 객체 중앙 픽셀 계산
                    box_coords = box.xyxy[0].cpu().numpy()
                    center_x = int((box_coords[0] + box_coords[2]) / 2)
                    center_y = int((box_coords[1] + box_coords[3]) / 2)
                    
                    # 픽셀 좌표를 실제 3D 공간 좌표(mm)로 변환
                    real_x, real_y, real_z = self.get_real_world_coordinates(depth_data, center_x, center_y)
                    
                    detected_items.append(name)
                    coordinates.append({
                        'name': name, 
                        'confidence': round(confidence, 2),
                        'x': real_x, 
                        'y': real_y, 
                        'z': real_z
                    })

            detection_text = ", ".join(set(detected_items)) if detected_items else "nothing"
            combined_display = np.hstack((annotated_image, depth_colormap))
            
            return combined_display, annotated_image, detection_text, coordinates
            
        except Exception as error:
            logger.error(f"Frame processing error: {error}")
            return None, None, "error", []

    def release(self):
        """카메라 파이프라인을 안전하게 중지합니다."""
        self.pipeline.stop()