# vision.py
import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
from logger import get_logger

logger = get_logger('VISION')

class VisionSystem:
    def __init__(self, model_path='yolo11n.pt'):
        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
            self.pipeline.start(self.config)
            self.colorizer = rs.colorizer()
            self.model = YOLO(model_path)
            logger.info(f"비전 시스템 가동 성공: {model_path}")
        except Exception as e:
            logger.error(f"카메라 초기화 실패: {e}")
            raise

    def process_frame(self):
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=5000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            if not color_frame or not depth_frame: return None, None, "nothing", []

            color_image = np.asanyarray(color_frame.get_data())
            depth_colormap = np.asanyarray(self.colorizer.colorize(depth_frame).get_data())
            
            results = self.model(color_image, verbose=False, conf=0.5)
            annotated = color_image.copy()
            detected_items = []
            coordinates = []

            if results:
                res = results[0]
                annotated = res.plot()
                depth_array = np.asanyarray(depth_frame.get_data())
                for box in res.boxes:
                    name = self.model.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    cx, cy = int((xyxy[0]+xyxy[2])/2), int((xyxy[1]+xyxy[3])/2)
                    z_val = int(depth_array[cy, cx])
                    
                    detected_items.append(name)
                    # [핵심] 'confidence' 키를 포함하여 저장합니다.
                    coordinates.append({
                        'name': name, 'confidence': round(conf, 2),
                        'x': cx, 'y': cy, 'z': z_val
                    })

            text = ", ".join(set(detected_items)) if detected_items else "nothing"
            combined = np.hstack((annotated, depth_colormap))
            return combined, annotated, text, coordinates
        except Exception as e:
            logger.error(f"처리 오류: {e}")
            return None, None, "error", []

    def release(self):
        self.pipeline.stop()