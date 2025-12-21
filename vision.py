# vision.py
# ================================================================================
# MACH VII - Vision 모듈 (RealSense + YOLO + XYZ 좌표)
# ================================================================================

import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
import time
from logger import get_logger

logger = get_logger('VISION')

class VisionSystem:
    """RealSense + YOLO 객체 감지 시스템"""
    
    def __init__(self, model_path='yolov11s.pt'):
        """초기화"""
        logger.info(f"Vision 시스템 초기화 시작: {model_path}")
        
        # ===== RealSense 파이프라인 초기화 =====
        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # RGB 스트림 설정
            self.config.enable_stream(
                rs.stream.color,
                640, 480,
                rs.format.bgr8,
                15
            )
            logger.info("✅ RGB 스트림 설정 완료 (640x480, 15fps, BGR8)")
            
            # Depth 스트림 설정
            self.config.enable_stream(
                rs.stream.depth,
                640, 480,
                rs.format.z16,
                15
            )
            logger.info("✅ Depth 스트림 설정 완료 (640x480, 15fps, Z16)")
            
            # 파이프라인 시작
            profile = self.pipeline.start(self.config)
            logger.info("✅ RealSense 파이프라인 시작")
            
            # Intrinsic 파라미터 로드 (깊이→거리 변환)
            depth_profile = profile.get_stream(rs.stream.depth)
            self.intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()
            logger.debug(f"Intrinsics: fx={self.intrinsics.fx}, fy={self.intrinsics.fy}, ppx={self.intrinsics.ppx}, ppy={self.intrinsics.ppy}")
            
            # Colorizer (깊이값 시각화용)
            self.colorizer = rs.colorizer()
            
        except Exception as e:
            logger.error(f"RealSense 초기화 실패: {e}")
            raise
        
        # ===== YOLO 모델 로드 =====
        try:
            self.model = YOLO(model_path)
            logger.info(f"✅ YOLO 모델 로드 성공: {model_path}")
        except Exception as e:
            logger.error(f"YOLO 모델 로드 실패: {e}")
            self.model = YOLO('yolov8n.pt')
            logger.warning("⚠️ 폴백 모델 사용: yolov8n.pt")
    
    def process_frame(self):
        """프레임 처리 (RGB + Depth + YOLO + XYZ)"""
        start_time = time.time()
        
        try:
            # RGB + Depth 프레임 획득
            frames = self.pipeline.wait_for_frames(timeout_ms=10000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                logger.warning("프레임 없음")
                return None, "No frame", []
            
            # Numpy 배열로 변환
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # YOLO 추론
            results = self.model(color_image, verbose=False, conf=0.5)
            
            detected_items = []
            coordinates = []
            annotated_frame = color_image.copy()
            
            # 결과 처리
            if results and len(results) > 0:
                result = results[0]
                annotated_frame = result.plot()
                
                # 각 감지된 객체 처리
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    item_name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # 바운딩박스 중심점
                    xyxy = box.xyxy[0].cpu().numpy()
                    x_center = int((xyxy[0] + xyxy[2]) / 2)
                    y_center = int((xyxy[1] + xyxy[3]) / 2)
                    
                    # 깊이값 추출 (중심점)
                    depth_value = depth_image[y_center, x_center]
                    
                    # 깊이값이 유효한지 확인
                    if depth_value > 0:
                        # 픽셀→세계 좌표 변환
                        # Z = depth_value / 1000 (mm → m)
                        z_mm = depth_value  # mm 단위
                        
                        detected_items.append(item_name)
                        coordinates.append({
                            'name': item_name,
                            'confidence': round(confidence, 2),
                            'x': x_center,
                            'y': y_center,
                            'z': z_mm
                        })
                        
                        logger.debug(
                            f"탐지: {item_name} (신뢰도: {confidence:.2f}) "
                            f"@ ({x_center}, {y_center}, {z_mm}mm)"
                        )
            
            # 텍스트 결과
            if detected_items:
                text_result = ", ".join(set(detected_items))
            else:
                text_result = "nothing"
            
            # 처리 시간 계산
            elapsed = time.time() - start_time
            fps = 1 / elapsed if elapsed > 0 else 0
            
            logger.info(
                f"프레임 처리 완료: {text_result} "
                f"[{elapsed*1000:.1f}ms, {fps:.1f}fps]"
            )
            
            return annotated_frame, text_result, coordinates
            
        except Exception as e:
            logger.error(f"프레임 처리 오류: {e}")
            return None, "error", []
    
    def release(self):
        """파이프라인 종료"""
        try:
            self.pipeline.stop()
            logger.info("✅ RealSense 파이프라인 종료")
        except Exception as e:
            logger.error(f"파이프라인 종료 오류: {e}")


# 테스트
if __name__ == "__main__":
    logger.info("Vision 시스템 테스트 시작")
    
    try:
        vision = VisionSystem('yolov11s.pt')
        
        for i in range(5):
            frame, text, coords = vision.process_frame()
            if frame is not None:
                logger.info(f"테스트 {i+1}: {text}")
                logger.debug(f"좌표: {coords}")
            time.sleep(0.1)
        
        vision.release()
        logger.info("✅ Vision 시스템 테스트 완료")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
