import unittest
import cv2
import numpy as np
from src.core.pcb_image import PCBImage

class TestPCBImage(unittest.TestCase):
    """
    Suite to validate processing of image structs using OpenCV.
    """

    def setUp(self):
        """
        Prepares a real image buffer (100x200) natively for tests.
        """
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        self.image_bytes = buffer.tobytes()

    def test_metadata_extraction(self):
        """
        Verifies correct raw extraction of internal dimensions.
        """
        image = PCBImage(image_data=self.image_bytes, filepath="test.jpg")
        self.assertEqual(image.get_width(), 200)
        self.assertEqual(image.get_height(), 100)
        self.assertEqual(image.get_resolution(), "200x100")

    def test_invalid_image_data(self):
        """
        Verifies handling of explicitly corrupted data streams.
        """
        image = PCBImage(image_data=b"corrupted")
        self.assertEqual(image.get_width(), 0)
        self.assertEqual(image.get_height(), 0)

if __name__ == '__main__':
    unittest.main()
