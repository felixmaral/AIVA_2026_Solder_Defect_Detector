import unittest
import numpy as np
import cv2
from src.vision.detector import Detector
from src.core.pcb_image import PCBImage

class TestDetector(unittest.TestCase):
    """
    Test suite for validating the real YOLO-based Detector inference.
    """

    def setUp(self):
        """
        Initializes an empty image block simulating a valid OpenCV frame to test hardware pipeline tolerance.
        """
        # Create a blank 100x100 RGB image
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        # Encode strictly to PNG bytes as expected by the PCBImage integration
        _, buffer = cv2.imencode('.png', img_array)
        self.image = PCBImage(image_data=buffer.tobytes())

    def test_detector_initialization(self):
        """
        Ensures the YOLO engine correctly initializes assuming weights/best.pt is reachable natively.
        """
        detector = Detector()
        self.assertIsNotNone(detector.model)

    def test_inference_output(self):
        """
        Verifies that the inference model can digest a structural image matrix natively without exploding.
        A blank matrix organically should result in zero defects cleanly mapped as a logical zero.
        """
        detector = Detector()
        result = detector.detect(self.image)
        
        self.assertIsNotNone(result)
        # The defect count will properly equal 0 theoretically inside this artificial blank matrix constraint.
        self.assertEqual(len(result.defects), 0)

if __name__ == '__main__':
    unittest.main()
