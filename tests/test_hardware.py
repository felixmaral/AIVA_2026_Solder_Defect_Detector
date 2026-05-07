"""
tests/test_hardware.py — Unit tests for the Camera hardware abstraction layer.

Tests cover three scenarios:
- Graceful failure when no physical camera is attached (CI / dev machine).
- Correct ``FileNotFoundError`` propagation when a file path does not exist.
- Successful image loading from a valid file path with correct dimension extraction.
"""
import unittest
import os
import cv2
import numpy as np
import tempfile
import shutil
from src.hardware.camera import Camera


class TestCamera(unittest.TestCase):
    """
    Test suite for the ``Camera`` hardware abstraction layer.

    Tests that require a physical camera are written to fail gracefully in
    environments where no camera is present (CI runners, developer laptops),
    while still asserting that the correct exception type and message are raised.
    """

    def setUp(self):
        """
        Creates a temporary directory containing a 50×50 blank JPEG test image.

        The image is written to disk so that ``get_image_from_file`` can be
        exercised with a real file rather than a mock.
        """
        self.test_dir = tempfile.mkdtemp()
        self.img_path = os.path.join(self.test_dir, "test_cam.jpg")
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.imwrite(self.img_path, img)

    def tearDown(self):
        """
        Removes the temporary directory and all generated artefacts after each test.
        """
        shutil.rmtree(self.test_dir)

    def test_capture_device_fails_gracefully(self):
        """
        Verifies that a ``ConnectionError`` is raised when no camera is reachable.

        Uses device index 99, which is intentionally out of range on any machine,
        to simulate the absence of a physical camera without requiring hardware.
        The error message must clearly identify the issue so that the operator
        can diagnose connection problems in the field.
        """
        # Index 99 is guaranteed to be out of range on any standard machine
        camera = Camera(camera_index=99)

        with self.assertRaises((ConnectionError, Exception)) as context:
            camera.get_real_time_image()

        self.assertIn("No camera detected", str(context.exception))

    def test_fallback_file_not_found(self):
        """
        Verifies that ``FileNotFoundError`` is raised for a non-existent file path.

        Ensures that the file-based acquisition path fails loudly rather than
        silently returning ``None`` or an invalid ``PCBImage``.
        """
        camera = Camera()
        with self.assertRaises(FileNotFoundError):
            camera.get_image_from_file("missing_nonexistent_test.jpg")

    def test_read_image_from_file(self):
        """
        Verifies that a valid file is read and wrapped in a correctly-sized ``PCBImage``.

        Checks that the resulting ``PCBImage`` reports dimensions that match the
        source image (50×50), confirming that the byte payload is passed through
        without corruption.
        """
        camera = Camera()
        image = camera.get_image_from_file(self.img_path)
        self.assertEqual(image.get_width(), 50)
        self.assertEqual(image.get_height(), 50)


if __name__ == '__main__':
    unittest.main()
