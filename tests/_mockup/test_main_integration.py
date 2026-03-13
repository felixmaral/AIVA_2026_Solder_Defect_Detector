import unittest
import os
import cv2
import numpy as np
import tempfile
import shutil
from io import StringIO
from unittest.mock import patch
from src._mockup.main import main

class TestMainIntegration(unittest.TestCase):
    """
    Prueba el flujo completo del sistema.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.img_path = os.path.join(self.test_dir, "Muestra_095.jpg")
        cv2.imwrite(self.img_path, np.zeros((10, 10, 3), dtype=np.uint8))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('src._mockup.hardware.camera.Camera.__init__', autospec=True)
    def test_main_execution(self, mock_init):
        """
        Ejecuta main() capturando la salida de consola y parcheando la cámara.
        """
        def mocked_init(self, default_feed_path=self.img_path):
            self.default_feed_path = default_feed_path
        mock_init.side_effect = mocked_init

        with patch('sys.stdout', new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()
            self.assertIn("Mock Inspection Completed", output)
            self.assertIn("<result>", output)

if __name__ == '__main__':
    unittest.main()