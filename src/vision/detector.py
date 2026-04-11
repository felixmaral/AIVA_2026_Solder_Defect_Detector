import os
from pathlib import Path

import cv2
from ultralytics import YOLO

from ..core.pcb_image import PCBImage
from ..core.solder_defect import SolderDefect
from ..core.detection_result import DetectionResult

class Detector:
    """
    Inference engine using YOLO to process images and detect solder defects.
    """
    
    def __init__(self, weights_path: str = None, conf_threshold: float = 0.25):
        """
        Initializes the detector by loading the YOLO model into memory.
        """
        # If no weights path is provided, default to the one in "model_dev"
        if weights_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            weights_path = str(base_dir / "model_dev" / "weights" / "best.pt")
            
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found at: {weights_path}")
            
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold

    def detect(self, image: PCBImage) -> DetectionResult:
        """
        Analyzes a PCBImage with YOLO and returns the detected defects.
        """
        # 1. Ensure the image is decoded (cv2 format)
        image._calculate_dimensions()
        img = image._decoded_image
        
        if img is None:
            raise ValueError("Error: PCBImage data is empty or cannot be read.")
        
        # 2. Preprocessing: Convert to grayscale and then to 3 channels (required by our model)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_input = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        
        # 3. Run YOLO inference
        predictions = self.model.predict(source=img_input, conf=self.conf_threshold, verbose=False)
        
        # 4. Prepare the final result object
        final_result = DetectionResult()
        
        # If no predictions were generated in this run, return the empty result
        if not predictions:
            return final_result
            
        # YOLO returns a list per input image. Since we only process one, we take the first element
        detected_boxes = predictions[0].boxes
        
        # 5. Iterate over each defect that YOLO found in the image
        for box in detected_boxes:
            # box.xyxy provides the bounding box coordinates: [x_min, y_min, x_max, y_max]
            x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
            confidence = float(box.conf[0].item())
            
            # Calculate width and height of the bounding box
            width = int(x_max - x_min)
            height = int(y_max - y_min)
            
            # Construct the defect object with its properties and add it to the result
            defect = SolderDefect(
                top_left_x=int(x_min),
                top_left_y=int(y_min),
                width=width,
                height=height,
                confidence=confidence
            )
            final_result.add_defect(defect)
                
        return final_result
