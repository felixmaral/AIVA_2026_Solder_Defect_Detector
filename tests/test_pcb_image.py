"""
tests/test_pcb_image.py — Unit tests for the PCBImage data container.

Verifies that the lazy-evaluation decoding strategy works correctly for valid
JPEG payloads and degrades gracefully when the byte data is malformed.
"""
import unittest
import cv2
import numpy as np
from src.core.pcb_image import PCBImage


class TestPCBImage(unittest.TestCase):
    """
    Test suite for the ``PCBImage`` lazy-evaluation image container.

    All tests operate on synthetic in-memory JPEG payloads to avoid any
    filesystem dependency.
    """

    def setUp(self):
        """
        Creates a 200×100 blank JPEG byte payload shared across all tests.

        The image dimensions are intentionally non-square (width ≠ height) to
        make width/height assertion errors immediately distinguishable.
        """
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        self.image_bytes = buffer.tobytes()

    def test_metadata_extraction(self):
        """
        Verifies that width, height, and resolution string are decoded correctly.

        Ensures the lazy-evaluation trigger (``_calculate_dimensions``) fires on
        the first property access and returns the correct values for the test image.
        """
        image = PCBImage(image_data=self.image_bytes, filepath="test.jpg")
        self.assertEqual(image.get_width(), 200)
        self.assertEqual(image.get_height(), 100)
        self.assertEqual(image.get_resolution(), "200x100")

    def test_invalid_image_data(self):
        """
        Verifies graceful degradation when the byte payload is not a valid image.

        Width and height must be 0 rather than raising an exception, so that the
        pipeline can log and continue rather than crashing on a bad camera frame.
        """
        image = PCBImage(image_data=b"corrupted")
        self.assertEqual(image.get_width(), 0)
        self.assertEqual(image.get_height(), 0)


if __name__ == '__main__':
    unittest.main()
