import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
from logger import get_logger
import os

# 비전 시스템의 상태와 오류를 기록하기 위한 로거 설정
logger = get_logger('VISION')

class VisionSystem:
    def __init__(self, model_path=None):
        """
        비전 시스템 초기화 및 리얼센스 카메라 설정.
        RGB와 깊이 영상의 정렬(Align) 기능을 추가하여 좌표 오차를 해결함.
        """
        try:
            # 모델 경로 설정
            if model_path is None:
                base_directory = os.path.dirname(os.path.abspath(__file__))
                model_path = os.path.normpath(os.path.join(base_directory, "..", "data", "models", "yolo11n.pt"))

            # 리얼센스 파이프라인 및 스트림 설정
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
            
            # 파이프라인 시작
            self.profile = self.pipeline.start(self.config)
            
            # [수정] RGB와 깊이 영상을 정렬하기 위한 Align 객체 생성
            # YOLO는 컬러 영상 기준이므로 깊이 영상을 컬러 영상의 시점으로 맞춤
            self.align = rs.align(rs.stream.color)
            
            # [수정] 실제 거리 계산을 위한 깊이 배율(Depth Scale) 획득
            depth_sensor = self.profile.get_device().first_depth_sensor()
            self.depth_scale = depth_sensor.get_depth_scale()
            
            # 카메라 고유 정보(Intrinsics) 획득
            self.intrinsics = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
            
            self.colorizer = rs.colorizer()
            self.model = YOLO(model_path)
            
            logger.info(f"Vision system initialized. Depth scale: {self.depth_scale}")
            
        except Exception as error:
            logger.error(f"Camera initialization failed: {error}")
            raise

    def get_real_world_coordinates(self, depth_frame, pixel_x, pixel_y):
        """
        픽셀 좌표를 실제 3D 공간 좌표(cm)로 변환함.
        정렬된 깊이 데이터를 사용하여 정확도를 높이고 단위를 cm로 변경함.
        """
        # 중앙점 주변 5x5 영역의 깊이 값을 추출하여 유효성 검사 수행
        roi_size = 2
        
        # 유효한 깊이 값을 저장할 리스트
        depth_values = []
        for y in range(max(0, pixel_y - roi_size), min(480, pixel_y + roi_size + 1)):
            for x in range(max(0, pixel_x - roi_size), min(640, pixel_x + roi_size + 1)):
                dist = depth_frame.get_distance(x, y)
                if dist > 0:
                    depth_values.append(dist)
        
        if depth_values:
            # 노이즈 제거를 위해 중간값(Median) 선택 (단위: Meters)
            median_distance = np.median(depth_values)
            
            # 카메라 고유 정보를 바탕으로 픽셀을 3D 포인트로 역투영
            # 결과값 point는 [x, y, z] 형태의 미터(m) 단위 리스트임
            point = rs.rs2_deproject_pixel_to_point(self.intrinsics, [pixel_x, pixel_y], median_distance)
            
            # [수정] 미터(m) 단위를 센티미터(cm)로 변환하여 반환 (1m = 100cm)
            return round(point[0] * 100, 2), round(point[1] * 100, 2), round(point[2] * 100, 2)
        
        return 0.0, 0.0, 0.0

    def process_frame(self):
        """
        프레임을 정렬하고 물체를 탐지하여 실제 좌표(cm)를 산출함.
        """
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=5000)
            
            # [수정] 깊이 영상을 컬러 영상의 시점에 맞게 정렬 (오차 해결의 핵심)
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                return None, None, "nothing", []

            color_image = np.asanyarray(color_frame.get_data())
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
                    
                    # [수정] 정렬된 depth_frame을 사용하여 실값 좌표(cm) 계산
                    real_x, real_y, real_z = self.get_real_world_coordinates(depth_frame, center_x, center_y)
                    
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
        """리소스 안전하게 해제"""
        self.pipeline.stop()