import unittest
from src._mockup.vision.detector import Detector
from src._mockup.core.pcb_image import PCBImage

class TestDetector(unittest.TestCase):
    """
    Suite para validar la lógica de detección simulada.
    """

    def test_inference_output(self):
        """
        Verifica que el detector devuelva resultados válidos.
        """
        detector = Detector()
        image = PCBImage(b"dummy")
        result = detector.detect(image)
        
        self.assertTrue(len(result.defects) > 0)
        self.assertGreaterEqual(result.defects[0].confidence, 0.0)

if __name__ == '__main__':
    unittest.main()