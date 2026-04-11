import os
import cv2
import numpy as np
from ultralytics import YOLO

from ..core.pcb_image import PCBImage
from ..core.solder_defect import SolderDefect
from ..core.detection_result import DetectionResult

class Detector:
    """
    Inference engine using ultralytics YOLO to process images and detect solder defects.
    """
    def __init__(self, weights_path: str = None, conf_threshold: float = 0.25):
        """
        Initializes the YOLO model with the given weights.
        """
        if weights_path is None:
            # Default path relative to this file assuming execution from repo
            current_dir = os.path.dirname(os.path.abspath(__file__))
            weights_path = os.path.join(current_dir, "..", "..", "model_dev", "weights", "best.pt")
            weights_path = os.path.abspath(weights_path)
            
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found at {weights_path}")
            
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold

    def detect(self, image: PCBImage) -> DetectionResult:
        """
        Analyzes the PCBImage using the YOLO model and returns a DetectionResult.
        """
        # Ensure image is decoded by invoking the internal method
        image._calculate_dimensions()
        
        if image._decoded_image is None:
            raise ValueError("Invalid PCBImage: Cannot decode image data.")
            
        img = image._decoded_image
        
        # Preprocessing: Convert to Grayson and then to 3 channels as expected by this YOLO model
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_input = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        
        # Run inference
        results = self.model.predict(source=img_input, conf=self.conf_threshold, verbose=False)
        
        detection_result = DetectionResult()
        
        if len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            for box in boxes:
                # box.xyxy returns x1, y1, x2, y2 (top-left, bottom-right)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                
                width = int(x2 - x1)
                height = int(y2 - y1)
                top_left_x = int(x1)
                top_left_y = int(y1)
                
                defect = SolderDefect(
                    top_left_x=top_left_x,
                    top_left_y=top_left_y,
                    width=width,
                    height=height,
                    confidence=float(conf)
                )
                detection_result.add_defect(defect)
                
        return detection_result
