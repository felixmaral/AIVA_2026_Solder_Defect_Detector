import unittest
import os
import cv2
import numpy as np
import tempfile
import shutil
import time
from io import StringIO
from unittest.mock import patch, MagicMock
from src.main import main

class TestMainIntegration(unittest.TestCase):
    """
    Test suite for the main entry point (src/main.py) and the new API class.
    Validates operational modes: single, simulate, and simulate_24h.
    """

    def setUp(self):
        """
        Creates a temporary directory with test images to simulate the execution.
        """
        self.test_dir = tempfile.mkdtemp()
        
        # Create dummy images
        self.img1_path = os.path.join(self.test_dir, "test1.jpg")
        self.img2_path = os.path.join(self.test_dir, "test2.jpg")
        
        # 640x640 blank images representing the input format
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.imwrite(self.img1_path, dummy_img)
        cv2.imwrite(self.img2_path, dummy_img)

    def tearDown(self):
        """
        Cleans up the temporary directory.
        """
        shutil.rmtree(self.test_dir)

    @patch('src.application.Detector')
    @patch('src.application.Camera')
    def test_single_mode_with_image(self, mock_camera_class, mock_detector_class):
        """
        Verifies that passing --mode single --image <path> correctly captures the image,
        runs detection, and saves the XML report.
        """
        test_argv = ['src/main.py', '--mode', 'single', '--image', self.img1_path]
        
        mock_camera_instance = mock_camera_class.return_value
        from src.core.pcb_image import PCBImage
        
        with open(self.img1_path, 'rb') as f:
            dummy_bytes = f.read()
        mock_pcb_image = PCBImage(image_data=dummy_bytes, filepath=self.img1_path)
        mock_camera_instance.get_image_from_file.return_value = mock_pcb_image
        
        mock_detector_instance = mock_detector_class.return_value
        from src.core.detection_result import DetectionResult
        mock_detector_instance.detect.return_value = DetectionResult()
        
        with patch('sys.argv', test_argv), patch('sys.stdout', new=StringIO()) as fake_out, \
             patch('src.main.project_root', self.test_dir), \
             patch('src.application.project_root', self.test_dir):
            main()
            output = fake_out.getvalue()
            
            self.assertIn(f"Processing local image: {self.img1_path}", output)
            
            mock_camera_instance.get_image_from_file.assert_called_once_with(self.img1_path)
            mock_detector_instance.detect.assert_called_once_with(mock_pcb_image)

    @patch('src.application.time.sleep', return_value=None)
    @patch('src.application.Detector')
    @patch('src.application.Camera')
    def test_simulate_mode(self, mock_camera_class, mock_detector_class, mock_sleep):
        """
        Verifies the simulate mode reads all images from the simulated directory
        and iterates through them correctly using Application.
        """
        test_argv = ['src/main.py', '--mode', 'simulate']
        
        os.makedirs(os.path.join(self.test_dir, "data", "simulate"), exist_ok=True)
        # We override the glob.glob call in main.py to return our temp images
        with patch('src.main.glob.glob', side_effect=[[self.img1_path, self.img2_path], [], []]), \
             patch('sys.argv', test_argv), \
             patch('sys.stdout', new=StringIO()) as fake_out, \
             patch('src.main.project_root', self.test_dir), \
             patch('src.application.project_root', self.test_dir):
             
            mock_camera_instance = mock_camera_class.return_value
            from src.core.pcb_image import PCBImage
            mock_pcb_image = PCBImage(image_data=b'dummy', filepath=self.img1_path)
            mock_camera_instance.get_image_from_file.return_value = mock_pcb_image
            
            mock_detector_instance = mock_detector_class.return_value
            from src.core.detection_result import DetectionResult
            mock_detector_instance.detect.return_value = DetectionResult()
            
            main()
            output = fake_out.getvalue()
            
            self.assertIn("Entering Simulation Mode", output)
            self.assertIn("Found 2 images", output)
            
            self.assertEqual(mock_camera_instance.get_image_from_file.call_count, 2)
            self.assertEqual(mock_detector_instance.detect.call_count, 2)

    @patch('src.application.time.sleep', return_value=None)
    @patch('src.application.Detector')
    @patch('src.application.Camera')
    def test_simulate_24h_mode(self, mock_camera_class, mock_detector_class, mock_sleep):
        """
        Verifies the simulate_24h mode loops correctly, applies augmentations,
        and uses Gaussian wait times via the new API.
        """
        test_argv = ['src/main.py', '--mode', 'simulate_24h']
        os.makedirs(os.path.join(self.test_dir, "data", "simulate"), exist_ok=True)
        
        # Override itertools.cycle to just return a normal iterator to avoid infinite loops
        with patch('src.main.itertools.cycle', side_effect=lambda x: iter(x)), \
             patch('src.main.glob.glob', side_effect=[[self.img1_path, self.img2_path], [], []]), \
             patch('sys.argv', test_argv), \
             patch('sys.stdout', new=StringIO()) as fake_out, \
             patch('src.main.project_root', self.test_dir), \
             patch('src.application.project_root', self.test_dir):
             
            mock_camera_instance = mock_camera_class.return_value
            from src.core.pcb_image import PCBImage
            # We must use a valid image that can be decoded by cv2 for augmentation
            dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
            success, buffer = cv2.imencode('.jpg', dummy_img)
            mock_pcb_image = PCBImage(image_data=buffer.tobytes(), filepath=self.img1_path)
            mock_camera_instance.get_image_from_file.return_value = mock_pcb_image
            
            mock_detector_instance = mock_detector_class.return_value
            from src.core.detection_result import DetectionResult
            mock_detector_instance.detect.return_value = DetectionResult()
            
            main()
            output = fake_out.getvalue()
            
            self.assertIn("Entering 24H Simulation Mode", output)
            self.assertIn("Gaussian cadence: mu=5.0s, sigma=2.0s", output)
            self.assertIn("[24H Sim] Processing augmented image from", output)

if __name__ == '__main__':
    unittest.main()
