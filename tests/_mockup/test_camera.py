import unittest
import os
import cv2
import numpy as np
import tempfile
import shutil
from src._mockup.hardware.camera import Camera

class TestCamera(unittest.TestCase):
    """
    Suite para validar la simulación del hardware de cámara.
    """

    def setUp(self):
        """
        Crea un archivo de imagen temporal.
        """
        self.test_dir = tempfile.mkdtemp()
        self.img_path = os.path.join(self.test_dir, "test_cam.jpg")
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.imwrite(self.img_path, img)

    def tearDown(self):
        """
        Limpia el directorio temporal.
        """
        shutil.rmtree(self.test_dir)

    def test_capture_simulation(self):
        """
        Verifica la lectura de la imagen desde el disco.
        """
        camera = Camera(default_feed_path=self.img_path)
        image = camera.get_real_time_image()
        self.assertEqual(image.get_width(), 50)

    def test_file_not_found(self):
        """
        Verifica que se lance la excepción correcta si no hay archivo.
        """
        camera = Camera(default_feed_path="missing.jpg")
        with self.assertRaises(FileNotFoundError):
            camera.get_real_time_image()

if __name__ == '__main__':
    unittest.main()