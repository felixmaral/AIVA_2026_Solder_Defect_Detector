"""
tests/test_vision.py — Integration tests for the YOLO-based Detector engine.

These tests exercise the real model weights (``model_dev/weights/best.pt``)
against synthetic blank images to validate that the inference pipeline
initialises correctly and produces structurally valid output without crashing.
No ground-truth defects are expected on a blank canvas, so the assertion is
always ``detection_count == 0``.
"""
import unittest
import numpy as np
import cv2
from src.vision.detector import Detector
from src.core.pcb_image import PCBImage


class TestDetector(unittest.TestCase):
    """
    Integration test suite for the ``Detector`` YOLO inference engine.

    Uses real model weights. Tests pass as long as the weights file is present
    at ``model_dev/weights/best.pt``.
    """

    def setUp(self):
        """
        Prepares a 100×100 blank PNG ``PCBImage`` used as a benign test input.

        PNG encoding is used here (instead of JPEG) because JPEG's lossy
        compression can introduce artefacts on synthetic blank images that
        might confuse assertions about pixel values. The detector handles
        both formats transparently.
        """
        # Blank black image — simulates a controlled zero-signal input
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.png', img_array)
        self.image = PCBImage(image_data=buffer.tobytes())

    def test_detector_initialization(self):
        """
        Verifies that the YOLO model loads without error and produces a valid model object.

        This test guards against missing or corrupted weight files and ensures
        that the ``Detector.__init__`` path completes successfully in CI.
        """
        detector = Detector()
        self.assertIsNotNone(detector.model)

    def test_inference_output(self):
        """
        Verifies that the inference pipeline returns a valid ``DetectionResult`` for a blank image.

        A structurally blank image should produce zero detections. This test
        confirms that the pipeline does not raise exceptions on edge-case
        (zero-content) inputs and that the result object is well-formed.
        """
        detector = Detector()
        result = detector.detect(self.image)

        self.assertIsNotNone(result)
        # A blank image must yield zero detections under any reasonable confidence threshold
        self.assertEqual(len(result.defects), 0)


if __name__ == '__main__':
    unittest.main()
