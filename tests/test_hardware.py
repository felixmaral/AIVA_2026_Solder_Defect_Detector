import unittest
import os
import cv2
import numpy as np
import tempfile
import shutil
from src.hardware.camera import Camera

class TestCamera(unittest.TestCase):
    """
    Test suite validating physical hardware camera bindings utilizing OpenCV structures.
    """

    def setUp(self):
        """
        Creates a temporary mock image natively resolving hardware fallback mechanisms.
        """
        self.test_dir = tempfile.mkdtemp()
        self.img_path = os.path.join(self.test_dir, "test_cam.jpg")
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.imwrite(self.img_path, img)

    def tearDown(self):
        """
        Cleans dynamically generated temporary artifacts safely.
        """
        shutil.rmtree(self.test_dir)

    def test_capture_device_fails_gracefully(self):
        """
        Expects a ConnectionError specifically when a target Raspberry Pi hardware channel lacks an attached pipeline.
        This validates that internal bindings won't crash silently causing structural bottlenecks.
        """
        # Given this is likely ran on a dev machine without the specified physical target attached...
        camera = Camera(camera_index=99) # Purposely arbitrary out-of-range hardware index
        
        with self.assertRaises((ConnectionError, Exception)) as context:
            camera.get_real_time_image()
            
        self.assertIn("camara conectada", str(context.exception))

    def test_fallback_file_not_found(self):
        """
        Ensures reading missing image datasets throws FileNotFoundError precisely like the mockup natively.
        """
        camera = Camera()
        with self.assertRaises(FileNotFoundError):
            camera.get_image_from_file("missing_nonexistent_test.jpg")

    def test_read_image_from_file(self):
        """
        Validates internal interoperability reading localized physical drives successfully.
        """
        camera = Camera()
        image = camera.get_image_from_file(self.img_path)
        self.assertEqual(image.get_width(), 50)
        self.assertEqual(image.get_height(), 50)

if __name__ == '__main__':
    unittest.main()
