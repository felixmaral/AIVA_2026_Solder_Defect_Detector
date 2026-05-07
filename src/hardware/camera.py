import os
import cv2
from ..core.pcb_image import PCBImage


class Camera:
    """
    Hardware abstraction layer for the Raspberry Pi 5 camera module.

    Provides a unified interface for acquiring PCB images regardless of
    whether the source is a live hardware feed (CSI/USB) or a local file
    on disk. Both acquisition paths return a ``PCBImage`` object, ensuring
    that downstream components are completely decoupled from the image source.

    Attributes:
        camera_index (int): OpenCV device index mapped to the physical camera.
            On the Raspberry Pi 5, index 0 typically corresponds to the
            primary CSI camera module.
    """

    def __init__(self, camera_index: int = 0):
        """
        Initialises the camera interface with the target hardware device index.

        Args:
            camera_index (int): The OpenCV ``VideoCapture`` device index.
                Defaults to 0, which maps to the primary camera on
                Raspberry Pi 5 deployments.
        """
        self.camera_index = camera_index

    def get_real_time_image(self) -> PCBImage:
        """
        Captures a single live frame from the physical camera hardware.

        Opens the camera device identified by ``camera_index``, reads one
        frame, immediately releases the device, and encodes the raw BGR
        matrix into a JPEG byte payload wrapped in a ``PCBImage`` object.

        Returns:
            PCBImage: A container holding the captured frame as a JPEG-encoded
                byte payload, with filepath set to 'Raspberry_Pi_Live_Feed.jpg'.

        Raises:
            ConnectionError: If the camera device cannot be opened (e.g.,
                disconnected CSI ribbon or missing USB device).
            ConnectionError: If the device is opened but fails to deliver a
                valid frame (e.g., hardware initialisation error).
            RuntimeError: If the captured BGR matrix cannot be JPEG-encoded
                into a byte buffer.
        """
        cap = cv2.VideoCapture(self.camera_index)

        # Verify that the OS-level video device descriptor was acquired successfully
        if not cap.isOpened():
            cap.release()
            raise ConnectionError(
                "No camera detected. Please verify the CSI/USB connection "
                "on the Raspberry Pi 5."
            )

        ret, frame = cap.read()
        cap.release()

        # Verify that the hardware delivered a valid pixel matrix
        if not ret or frame is None:
            raise ConnectionError(
                "Camera is connected but failed to deliver a valid frame. "
                "Check hardware initialisation."
            )

        # PCBImage expects a raw JPEG byte stream; encode the BGR matrix accordingly
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            raise RuntimeError(
                "Internal error: failed to encode the captured frame to a JPEG byte buffer."
            )

        return PCBImage(image_data=buffer.tobytes(), filepath='Raspberry_Pi_Live_Feed.jpg')

    def get_image_from_file(self, filepath: str) -> PCBImage:
        """
        Reads a PCB image from the local filesystem.

        Intended for development, simulation, and testing workflows where a
        physical camera is not available or required. The raw byte payload is
        read directly without re-encoding, preserving the original file format.

        Args:
            filepath (str): Absolute or relative path to the image file
                (JPEG or PNG).

        Returns:
            PCBImage: A container holding the file's raw byte payload.

        Raises:
            FileNotFoundError: If no file exists at the given path.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Image file not found: {filepath}")

        with open(filepath, 'rb') as f:
            image_data = f.read()

        return PCBImage(image_data=image_data, filepath=filepath)
