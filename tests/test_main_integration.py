"""
tests/test_main_integration.py — Integration tests for the main entry point.

These tests exercise the full ``main()`` function using ``unittest.mock`` to
replace the ``Camera`` and ``Detector`` hardware dependencies, allowing the
complete CLI argument parsing and mode dispatch logic to run without requiring
a physical camera or YOLO model weights.

Patching strategy
-----------------
All patches target the ``src.application`` module namespace (not the hardware
or vision modules directly) because ``Application`` imports ``Camera`` and
``Detector`` at its own module scope. Patching at the import site ensures that
the mock objects are injected into the live ``Application`` class at
instantiation time.
"""
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
    Integration test suite for ``src/main.py`` and the ``Application`` API.

    Validates argument parsing, mode dispatch, and the interaction contract
    between ``main()`` and the ``Application`` façade for both the ``single``
    and ``simulate`` execution modes.
    """

    def setUp(self):
        """
        Creates a temporary directory containing two blank 640×640 JPEG test images.

        The images are used by tests to simulate a real dataset directory without
        depending on any files committed to the repository.
        """
        self.test_dir = tempfile.mkdtemp()

        self.img1_path = os.path.join(self.test_dir, "test1.jpg")
        self.img2_path = os.path.join(self.test_dir, "test2.jpg")

        # Blank 640×640 images — standard PCB input resolution
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.imwrite(self.img1_path, dummy_img)
        cv2.imwrite(self.img2_path, dummy_img)

    def tearDown(self):
        """
        Removes the temporary directory and all generated artefacts after each test.
        """
        shutil.rmtree(self.test_dir)

    @patch('src.application.Detector')
    @patch('src.application.Camera')
    def test_single_mode_with_image(self, mock_camera_class, mock_detector_class):
        """
        Verifies the ``--mode single --image`` path through ``main()``.

        Asserts that:
        - The camera's ``get_image_from_file`` is called exactly once with the
          correct path.
        - The detector's ``detect`` method is invoked with the returned PCBImage.
        - The progress message confirming the image path appears in stdout.
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
    def test_simulate_mode_fast(self, mock_camera_class, mock_detector_class, mock_sleep):
        """
        Verifies the ``--mode simulate`` path at maximum speed (no ``--mean``).

        ``itertools.cycle`` is patched to return a finite iterator so the test
        terminates. Asserts that:
        - Both images in the mocked dataset are processed exactly once.
        - The correct startup messages appear in stdout.
        """
        test_argv = ['src/main.py', '--mode', 'simulate']

        os.makedirs(os.path.join(self.test_dir, "data", "simulate"), exist_ok=True)

        # Replace cycle with a normal iter to prevent the infinite loop
        with patch('src.main.itertools.cycle', side_effect=lambda x: iter(x)), \
             patch('src.main.glob.glob', side_effect=[[self.img1_path, self.img2_path], [], []]), \
             patch('sys.argv', test_argv), \
             patch('sys.stdout', new=StringIO()) as fake_out, \
             patch('src.main.project_root', self.test_dir), \
             patch('src.application.project_root', self.test_dir):

            mock_camera_instance = mock_camera_class.return_value
            from src.core.pcb_image import PCBImage

            # Must be a valid JPEG that cv2 can decode for the augmentation step
            dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
            success, buffer = cv2.imencode('.jpg', dummy_img)
            mock_pcb_image = PCBImage(image_data=buffer.tobytes(), filepath=self.img1_path)
            mock_camera_instance.get_image_from_file.return_value = mock_pcb_image

            mock_detector_instance = mock_detector_class.return_value
            from src.core.detection_result import DetectionResult
            mock_detector_instance.detect.return_value = DetectionResult()

            main()
            output = fake_out.getvalue()

            self.assertIn("Entering Simulation Mode", output)
            self.assertIn("indefinite simulation with 2 base images", output)
            self.assertIn("Maximum speed mode", output)

            # Both images must have been loaded and inspected
            self.assertEqual(mock_camera_instance.get_image_from_file.call_count, 2)
            self.assertEqual(mock_detector_instance.detect.call_count, 2)

    @patch('src.application.time.sleep', return_value=None)
    @patch('src.application.Detector')
    @patch('src.application.Camera')
    def test_simulate_mode_with_cadence(self, mock_camera_class, mock_detector_class, mock_sleep):
        """
        Verifies that ``--sim_time 0`` causes the simulation loop to exit immediately.

        When ``sim_time`` is 0 seconds, the elapsed-time check fires before the
        first image is even loaded. Asserts that the correct Gaussian cadence
        banner and the timeout message appear in stdout.
        """
        test_argv = [
            'src/main.py', '--mode', 'simulate',
            '--mean', '5.0', '--deviation', '2.0', '--sim_time', '0',
        ]
        os.makedirs(os.path.join(self.test_dir, "data", "simulate"), exist_ok=True)

        with patch('src.main.itertools.cycle', side_effect=lambda x: iter(x)), \
             patch('src.main.glob.glob', side_effect=[[self.img1_path, self.img2_path], [], []]), \
             patch('sys.argv', test_argv), \
             patch('sys.stdout', new=StringIO()) as fake_out, \
             patch('src.main.project_root', self.test_dir), \
             patch('src.application.project_root', self.test_dir):

            mock_camera_instance = mock_camera_class.return_value
            from src.core.pcb_image import PCBImage
            dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
            success, buffer = cv2.imencode('.jpg', dummy_img)
            mock_pcb_image = PCBImage(image_data=buffer.tobytes(), filepath=self.img1_path)
            mock_camera_instance.get_image_from_file.return_value = mock_pcb_image

            mock_detector_instance = mock_detector_class.return_value
            from src.core.detection_result import DetectionResult
            mock_detector_instance.detect.return_value = DetectionResult()

            main()
            output = fake_out.getvalue()

            self.assertIn("Entering Simulation Mode", output)
            self.assertIn("Gaussian cadence: mean=5.0s, deviation=2.0s", output)
            # sim_time=0 means the loop exits on the very first iteration check
            self.assertIn("Simulation time (0.0s) reached.", output)


if __name__ == '__main__':
    unittest.main()
