import os
from ..core.pcb_image import PCBImage

class Camera:
    """
    Hardware interface mock for the camera.
    Reads from a local file to simulate real-time capture.
    """
    def __init__(self, default_feed_path: str = "media/Muestra_095.jpg"):
        self.default_feed_path = default_feed_path

    def get_real_time_image(self) -> PCBImage:
        """
        Simulates a live frame capture.
        """
        if not os.path.exists(self.default_feed_path):
            raise FileNotFoundError(f"Mock feed image not found: {self.default_feed_path}")
        
        with open(self.default_feed_path, 'rb') as f:
            image_data = f.read()
            
        return PCBImage(image_data=image_data, filepath=self.default_feed_path)

    def get_image_from_file(self, filepath: str) -> PCBImage:
        """
        Reads a specific image from the local filesystem.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Image file not found: {filepath}")
            
        with open(filepath, 'rb') as f:
            image_data = f.read()
            
        return PCBImage(image_data=image_data, filepath=filepath)