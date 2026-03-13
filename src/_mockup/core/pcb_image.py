import cv2
import numpy as np

class PCBImage:
    """
    Holds the PCB image data and calculates its physical properties using OpenCV.
    Provides functionality for visualization if a display server is available.
    """
    def __init__(self, image_data: bytes, filepath: str = None):
        self._image_data = image_data
        self._filepath = filepath
        self._height = None
        self._width = None
        self._decoded_image = None

    def _calculate_dimensions(self) -> None:
        """
        Decodes the image from bytes using OpenCV to extract real dimensions.
        Avoids redundant decoding if dimensions are already calculated.
        """
        if self._height is None or self._width is None:
            np_arr = np.frombuffer(self._image_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is not None:
                self._height, self._width = img.shape[:2]
                self._decoded_image = img
            else:
                self._height = 0
                self._width = 0

    def get_resolution(self) -> str:
        """
        Returns the image resolution as a formatted string.
        """
        self._calculate_dimensions()
        return f"{self._width}x{self._height}"

    def get_height(self) -> int:
        """
        Returns the image height in pixels.
        """
        self._calculate_dimensions()
        return self._height

    def get_width(self) -> int:
        """
        Returns the image width in pixels.
        """
        self._calculate_dimensions()
        return self._width

    def get_size_bytes(self) -> int:
        """
        Returns the image file size in bytes.
        """
        return len(self._image_data)

    def show(self) -> None:
        """
        Displays the image using OpenCV. 
        Fails gracefully if no windowing system (GUI) is available.
        """
        self._calculate_dimensions()
        
        if self._decoded_image is None:
            print("Warning: Cannot display image. Invalid or empty byte data.")
            return

        try:
            cv2.imshow(f"PCB Preview: {self._filepath or 'Memory'}", self._decoded_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error as e:
            print(f"Warning: Display not available (Headless environment). Details: {e}")