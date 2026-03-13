import unittest
import cv2
import numpy as np
from src._mockup.core.pcb_image import PCBImage

class TestPCBImage(unittest.TestCase):
    """
    Suite para validar el procesamiento de imágenes con OpenCV.
    """

    def setUp(self):
        """
        Prepara un buffer de imagen real (100x200) para las pruebas.
        """
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        self.image_bytes = buffer.tobytes()

    def test_metadata_extraction(self):
        """
        Verifica la extracción de dimensiones desde los bytes.
        """
        image = PCBImage(image_data=self.image_bytes, filepath="test.jpg")
        self.assertEqual(image.get_width(), 200)
        self.assertEqual(image.get_height(), 100)

    def test_invalid_image_data(self):
        """
        Verifica el manejo de datos corruptos.
        """
        image = PCBImage(image_data=b"corrupted")
        self.assertEqual(image.get_width(), 0)
        self.assertEqual(image.get_height(), 0)

if __name__ == '__main__':
    unittest.main()