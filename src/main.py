import os
import sys

# Ensure the project root is in the python path to allow absolute imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.hardware.camera import Camera
from src.vision.detector import Detector

def main():
    """
    Main execution flow for the PCB inspection system.
    Orchestrates camera capture, detection, and XML reporting.
    """
    print("Initializing hardware camera interface...")
    camera = Camera(camera_index=0)
    
    print("Loading YOLO detector...")
    try:
        detector = Detector()
    except FileNotFoundError as e:
        print(f"Error loading model: {e}")
        return

    try:
        print("Attempting to capture real-time image from Raspberry Pi 5...")
        try:
            pcb_image = camera.get_real_time_image()
        except ConnectionError as e:
            # Fallback for development environments (like Mac) where the Pi camera isn't available
            print(f"Camera connection failed: {e}")
            fallback_image = "media/Muestra_095.jpg"
            print(f"Falling back to local test image: {fallback_image}")
            pcb_image = camera.get_image_from_file(fallback_image)

        print(f"Image captured: {pcb_image.get_resolution()} - {pcb_image.get_size_bytes()} bytes")
        
        # Optional
        # pcb_image.show()
        
        print("Running defect detection...")
        detection_result = detector.detect(pcb_image)
        xml_report = detection_result.to_xml()
        
        print("\nInspection Completed. XML Report:")
        print(xml_report)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
