import os
import cv2
from ..core.pcb_image import PCBImage

class Camera:
    """
    Hardware interface for the Raspberry Pi 5 camera module.
    Captures live frames directly from the local CSI or USB hardware slot.
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initializes the hardware configuration. Parameters are tailored for Raspberry Pi deployments.
        camera_index: The OpenCV video device index (defaults to 0).
        """
        self.camera_index = camera_index

    def get_real_time_image(self) -> PCBImage:
        """
        Captures a live frame from the hardware device and returns a PCBImage object.
        Raises an explicit error if the camera is disconnected or malfunctioning.
        """
        cap = cv2.VideoCapture(self.camera_index)
        
        # Verify if Raspberry Pi device descriptor mapped efficiently to OpenCV
        if not cap.isOpened():
            cap.release()
            raise ConnectionError("No hay camara conectada. Por favor, compruebe la conexion (CSI/USB) de la camara en la Raspberry Pi 5.")
            
        ret, frame = cap.read()
        cap.release()
        
        # Verify if the hardware yielded a valid visual matrix
        if not ret or frame is None:
            raise ConnectionError("Error al capturar la imagen. La camara parece estar conectada pero no devuelve frames.")
            
        # PCBImage natively expects raw byte streams, so we encode the spatial BGR matrix
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            raise RuntimeError("Fallo interno: No se pudo codificar el frame local a buffer de bytes.")
            
        return PCBImage(image_data=buffer.tobytes(), filepath='Raspberry_Pi_Live_Feed.jpg')

    def get_image_from_file(self, filepath: str) -> PCBImage:
        """
        Reads a specific image from the local filesystem (Preserved for interoperability and testing).
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Image file not found: {filepath}")
            
        with open(filepath, 'rb') as f:
            image_data = f.read()
            
        return PCBImage(image_data=image_data, filepath=filepath)
