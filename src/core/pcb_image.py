import cv2
import numpy as np
from typing import Optional

class PCBImage:
    """
    Holds the PCB image data and calculates its physical properties natively via OpenCV.
    Provides functionality for visualization if a display server is available.
    """
    
    def __init__(self, image_data: bytes, filepath: Optional[str] = None):
        """
        Initializes the PCB image container. 
        Decoding is deferred until explicitly requested by a property or method.
        """
        self._image_data: bytes = image_data
        self._filepath: Optional[str] = filepath
        self._height: Optional[int] = None
        self._width: Optional[int] = None
        self._decoded_image: Optional[np.ndarray] = None

    def _calculate_dimensions(self) -> None:
        """
        Decodes the raw byte string using OpenCV to extract dimensional matrices.
        Safeguards against redundant decoding by caching the result internally.
        """
        if self._height is None or self._width is None:
            # Convert raw bytes to a 1D numpy uint8 array
            np_arr = np.frombuffer(self._image_data, np.uint8)
            # Decode array into a multi-dimensional BGR matrix
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is not None:
                self._height, self._width = img.shape[:2]
                self._decoded_image = img
            else:
                self._height = 0
                self._width = 0

    def get_resolution(self) -> str:
        """
        Returns the native image resolution mapped as a formatted string (WxH).
        """
        self._calculate_dimensions()
        return f"{self._width}x{self._height}"

    def get_height(self) -> int:
        """
        Returns the raw pixel matrix height.
        """
        self._calculate_dimensions()
        return self._height

    def get_width(self) -> int:
        """
        Returns the raw pixel matrix width.
        """
        self._calculate_dimensions()
        return self._width

    def get_size_bytes(self) -> int:
        """
        Returns the original physical payload size of the image string in bytes.
        """
        return len(self._image_data)

    def show(self) -> None:
        """
        Displays the image via high-level OpenCV window wrappers. 
        Degrades gracefully by catching context exceptions when in headless setups.
        """
        self._calculate_dimensions()
        
        if self._decoded_image is None:
            print("Warning: Cannot display image. Invalid or empty byte data.")
            return

        try:
            target_name = self._filepath if self._filepath else 'Memory'
            cv2.imshow(f"PCB Preview: {target_name}", self._decoded_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error as e:
            print(f"Warning: Display context not available (Headless environment). Details: {e}")