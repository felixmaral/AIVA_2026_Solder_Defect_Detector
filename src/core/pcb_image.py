import cv2
import numpy as np
from typing import Optional


class PCBImage:
    """
    Intelligent container for raw PCB image data captured from the hardware pipeline.

    This class encapsulates the raw byte payload of a captured image and exposes
    controlled access to its physical properties (width, height). Image decoding
    is deferred via lazy evaluation: the raw byte buffer is only decoded into a
    NumPy matrix when a property or method explicitly requires it. This avoids
    unnecessary computational overhead when, for example, only the file size is
    needed without inspecting the image content.

    Attributes:
        _image_data (bytes): The raw JPEG-encoded byte payload of the image.
        _filepath (Optional[str]): The original filesystem path, used as a display
            label and for naming output artefacts. May be None for in-memory images.
        _height (Optional[int]): Cached pixel height, populated on first decode.
        _width (Optional[int]): Cached pixel width, populated on first decode.
        _decoded_image (Optional[np.ndarray]): Cached BGR matrix, populated on
            first decode and retained to avoid redundant decoding.
    """

    def __init__(self, image_data: bytes, filepath: Optional[str] = None):
        """
        Initialises the PCB image container without performing any decoding.

        Args:
            image_data (bytes): Raw JPEG byte payload of the captured image.
            filepath (Optional[str]): Original filesystem path of the image.
                Used for display labels and output file naming. Defaults to None.
        """
        self._image_data: bytes = image_data
        self._filepath: Optional[str] = filepath
        self._height: Optional[int] = None
        self._width: Optional[int] = None
        self._decoded_image: Optional[np.ndarray] = None

    def _calculate_dimensions(self) -> None:
        """
        Decodes the raw byte buffer into a BGR NumPy matrix and caches dimensions.

        This is the single decode point for the class. After the first call, both
        the matrix and its dimensions are cached internally, making subsequent
        calls a no-op. If decoding fails (e.g., malformed data), dimensions are
        set to 0 and the decoded image remains None.
        """
        if self._height is None or self._width is None:
            # Convert the raw byte string to a flat uint8 NumPy array
            np_arr = np.frombuffer(self._image_data, np.uint8)
            # Decode the 1-D array into a multi-dimensional BGR matrix
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is not None:
                self._height, self._width = img.shape[:2]
                self._decoded_image = img
            else:
                # Graceful degradation: mark dimensions as invalid
                self._height = 0
                self._width = 0

    def get_resolution(self) -> str:
        """
        Returns the native image resolution as a formatted string.

        Returns:
            str: Resolution in 'WxH' format (e.g., '1920x1080').
        """
        self._calculate_dimensions()
        return f"{self._width}x{self._height}"

    def get_height(self) -> int:
        """
        Returns the raw pixel height of the image matrix.

        Returns:
            int: Image height in pixels, or 0 if decoding failed.
        """
        self._calculate_dimensions()
        return self._height

    def get_width(self) -> int:
        """
        Returns the raw pixel width of the image matrix.

        Returns:
            int: Image width in pixels, or 0 if decoding failed.
        """
        self._calculate_dimensions()
        return self._width

    def get_size_bytes(self) -> int:
        """
        Returns the size of the original compressed image payload in bytes.

        Note: This reflects the size of the raw JPEG byte string, not the
        size of the uncompressed decoded matrix.

        Returns:
            int: Size of the raw image byte payload in bytes.
        """
        return len(self._image_data)

    def show(self) -> None:
        """
        Displays the image in an OpenCV window and waits for a keypress to close it.

        Degrades gracefully in headless environments (e.g., SSH sessions or
        CI runners) by catching the OpenCV display context exception instead of
        crashing the process.
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