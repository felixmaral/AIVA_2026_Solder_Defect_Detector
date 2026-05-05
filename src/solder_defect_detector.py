import os
import time
import datetime
import sys
import cv2

# Ensure the project root is in the python path to allow absolute imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.hardware.camera import Camera
from src.vision.detector import Detector

class SolderDefectDetector:
    """
    Main API Facade for the PCB Solder Defect Detection System.
    Encapsulates camera hardware and the YOLO vision model to provide
    a simple interface for external clients.
    """
    def __init__(self, camera_index=0, output_dir=None, visualize=False):
        print("Initializing hardware camera interface...")
        self.camera = Camera(camera_index=camera_index)
        self.visualize = visualize
        
        print("Loading YOLO detector...")
        self.detector = Detector()
        
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(project_root, "reports", "xml")
            
        os.makedirs(self.output_dir, exist_ok=True)
        print("SolderDefectDetector initialized successfully.")

    def process_from_path(self, image_path):
        """
        Reads an image from the given path, performs detection, saves the XML report,
        and returns the processing details.
        
        Args:
            image_path (str): The absolute or relative path to the PCB image.
            
        Returns:
            dict: Contains 'xml_path', 'processing_time_ms', and 'detection_count'.
        """
        print(f"\nProcessing local image: {image_path}")
        pcb_image = self.camera.get_image_from_file(image_path)
        return self._process(pcb_image, source_path=image_path)

    def process_pcb_image(self, pcb_image, custom_name=None):
        """
        Processes a pre-loaded PCBImage object directly. Useful for data augmentation 
        or live camera feeds without saving the image to disk first.
        
        Args:
            pcb_image (PCBImage): The image object to process.
            custom_name (str): Optional name for the output XML file.
            
        Returns:
            dict: Contains 'xml_path', 'processing_time_ms', and 'detection_count'.
        """
        return self._process(pcb_image, custom_name=custom_name)
        
    def process_live_camera(self):
        """
        Captures an image directly from the physical hardware camera and processes it.
        """
        print("\nAttempting to capture real-time image from camera hardware...")
        pcb_image = self.camera.get_real_time_image()
        return self._process(pcb_image)

    def _process(self, pcb_image, source_path=None, custom_name=None):
        """
        Internal method to execute the inference and save the result.
        """
        print(f"Image captured: {pcb_image.get_resolution()} - {pcb_image.get_size_bytes()} bytes")
        
        # Inicio estricto del cronómetro "desde que nos entregan la imagen"
        proc_start = time.time()
        
        print("Running defect detection...")
        detection_result = self.detector.detect(pcb_image)
        xml_report = detection_result.to_xml()
        
        # Fin del cronómetro (Inferencia completada)
        proc_time = time.time() - proc_start
        
        print("Inspection Completed. XML Report generated.")
        
        if custom_name:
            base_name = custom_name
        elif source_path:
            base_name = os.path.splitext(os.path.basename(source_path))[0]
        else:
            base_name = f"Capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        xml_filename = os.path.join(self.output_dir, f"{base_name}.xml")
        with open(xml_filename, 'w') as f:
            f.write(xml_report)
        print(f"XML saved to {xml_filename}")
        
        if self.visualize:
            self._render_detections(pcb_image, detection_result)
        
        return {
            "xml_path": xml_filename,
            "processing_time_s": proc_time,
            "processing_time_ms": proc_time * 1000,
            "detection_count": len(detection_result.defects)
        }

    def _render_detections(self, pcb_image, detection_result):
        """
        Draws bounding boxes on the PCB image and displays it.
        The window is updated but does not block indefinitely.
        """
        pcb_image._calculate_dimensions()
        img = pcb_image._decoded_image
        if img is None:
            return
            
        display_img = img.copy()
        
        for defect in detection_result.defects:
            x, y, w, h = defect.top_left_x, defect.top_left_y, defect.width, defect.height
            cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            label = f"Defect: {defect.confidence:.2f}"
            cv2.putText(display_img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
        try:
            cv2.imshow("Solder Defect Detections", display_img)
            cv2.waitKey(1)
        except cv2.error as e:
            print(f"Visualization error: {e}")

    def wait(self, delay_s):
        """
        Waits for a specified amount of time. If visualization is enabled, 
        pumps OpenCV UI events to prevent the window from freezing.
        """
        if self.visualize:
            delay_ms = max(1, int(delay_s * 1000))
            cv2.waitKey(delay_ms)
        else:
            time.sleep(delay_s)

    def wait_for_key(self):
        """
        Blocks until a key is pressed in the OpenCV window (only if visualization is enabled).
        """
        if self.visualize:
            cv2.waitKey(0)

