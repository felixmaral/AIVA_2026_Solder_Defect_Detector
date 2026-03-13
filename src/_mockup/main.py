from .hardware.camera import Camera
from .vision.detector import Detector

def main():
    """
    Main execution flow for the mocked PCB inspection system.
    Orchestrates camera capture, detection, and XML reporting.
    """
    camera = Camera(default_feed_path="media/Muestra_095.jpg")
    detector = Detector()

    try:
        pcb_image = camera.get_real_time_image()
        print(f"Image captured: {pcb_image.get_resolution()} - {pcb_image.get_size_bytes()} bytes")
        
        # Opcional: Visualización si hay interfaz gráfica
        pcb_image.show()
        
        detection_result = detector.detect(pcb_image)
        xml_report = detection_result.to_xml()
        
        print("\nMock Inspection Completed. XML Report:")
        print(xml_report)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()