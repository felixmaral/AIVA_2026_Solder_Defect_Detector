import unittest
import os
import ctypes
import sys
import tempfile
import shutil
import numpy as np
import cv2
from unittest.mock import patch


def _find_library():
    """Locate the compiled C shared library relative to the project root."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("libsolder_defect.so", "libsolder_defect.dylib"):
        path = os.path.join(base, "src", "c_bindings", name)
        if os.path.exists(path):
            return path
    return None


LIB_PATH = _find_library()
SKIP_REASON = (
    "C binding library not compiled. "
    "Run 'make' inside src/c_bindings/ first."
)


class DetectionResultInfo(ctypes.Structure):
    """Mirror of DetectionResultInfo from solder_defect.h."""
    _fields_ = [
        ("xml_path",           ctypes.c_char * 512),
        ("processing_time_ms", ctypes.c_double),
        ("detection_count",    ctypes.c_int),
        ("success",            ctypes.c_int),
    ]


@unittest.skipIf(LIB_PATH is None, SKIP_REASON)
class TestCBindingsSafety(unittest.TestCase):
    """
    Tests that the C API is safe to call even with bad inputs.
    These tests require NO compiled model or real hardware.
    """

    @classmethod
    def setUpClass(cls):
        cls.lib = ctypes.CDLL(LIB_PATH)

        # Define function signatures matching solder_defect.h
        cls.lib.application_create.restype = ctypes.c_void_p
        cls.lib.application_create.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int
        ]
        cls.lib.application_process_from_path.restype = DetectionResultInfo
        cls.lib.application_process_from_path.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p
        ]
        cls.lib.application_process_live_camera.restype = DetectionResultInfo
        cls.lib.application_process_live_camera.argtypes = [ctypes.c_void_p]
        cls.lib.application_destroy.restype = None
        cls.lib.application_destroy.argtypes = [ctypes.c_void_p]

    def test_null_handle_process_from_path_returns_failure(self):
        """
        Passing a NULL handle to process_from_path must return success=0
        without crashing (no segfault).
        """
        result = self.lib.application_process_from_path(None, b"any_path.jpg")
        self.assertEqual(result.success, 0)

    def test_null_handle_process_live_camera_returns_failure(self):
        """
        Passing a NULL handle to process_live_camera must return success=0
        without crashing.
        """
        result = self.lib.application_process_live_camera(None)
        self.assertEqual(result.success, 0)

    def test_null_handle_destroy_does_not_crash(self):
        """application_destroy(NULL) must be a safe no-op."""
        try:
            self.lib.application_destroy(None)
        except Exception as e:
            self.fail(f"application_destroy(NULL) raised an exception: {e}")


@unittest.skipIf(LIB_PATH is None, SKIP_REASON)
class TestCBindingsWithMocks(unittest.TestCase):
    """
    Tests the C API end-to-end using Python mocks for Camera and Detector,
    so no physical hardware or YOLO model weights are required.

    This works because the C library embeds the same Python interpreter
    already running here, meaning unittest.mock patches are visible to
    the C code when it calls into Python.
    """

    @classmethod
    def setUpClass(cls):
        cls.lib = ctypes.CDLL(LIB_PATH)
        cls.lib.application_create.restype = ctypes.c_void_p
        cls.lib.application_create.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int
        ]
        cls.lib.application_process_from_path.restype = DetectionResultInfo
        cls.lib.application_process_from_path.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p
        ]
        cls.lib.application_destroy.restype = None
        cls.lib.application_destroy.argtypes = [ctypes.c_void_p]

    def _make_mock_pcb_image(self, filepath="/fake/path.jpg"):
        """Helper: build a real PCBImage backed by a tiny blank JPEG."""
        from src.core.pcb_image import PCBImage
        dummy = np.zeros((10, 10, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", dummy)
        return PCBImage(image_data=buf.tobytes(), filepath=filepath)

    def _make_mock_detection_result(self, num_defects=0):
        """Helper: build a DetectionResult with a given number of fake defects."""
        from src.core.detection_result import DetectionResult
        from src.core.solder_defect import SolderDefect
        dr = DetectionResult()
        for _ in range(num_defects):
            dr.add_defect(SolderDefect(10, 20, 50, 50, 0.95))
        return dr

    def test_create_returns_valid_handle(self):
        """application_create returns a non-NULL handle when Application loads correctly."""
        tmp = tempfile.mkdtemp()
        try:
            with patch("src.application.Camera"), patch("src.application.Detector"):
                handle = self.lib.application_create(0, tmp.encode(), 0)
                self.assertIsNotNone(handle, "Expected a non-NULL ApplicationHandle.")
                self.lib.application_destroy(handle)
        finally:
            shutil.rmtree(tmp)

    def test_process_from_path_success_no_defects(self):
        """
        process_from_path returns success=1 and detection_count=0
        when the model finds no defects.
        """
        tmp = tempfile.mkdtemp()
        try:
            mock_pcb = self._make_mock_pcb_image()
            mock_det = self._make_mock_detection_result(num_defects=0)

            with patch("src.application.Camera") as MockCam, \
                 patch("src.application.Detector") as MockDet:
                MockCam.return_value.get_image_from_file.return_value = mock_pcb
                MockDet.return_value.detect.return_value = mock_det

                handle = self.lib.application_create(0, tmp.encode(), 0)
                result = self.lib.application_process_from_path(
                    handle, b"/fake/path.jpg"
                )
                self.lib.application_destroy(handle)

            self.assertEqual(result.success, 1)
            self.assertEqual(result.detection_count, 0)
            self.assertGreaterEqual(result.processing_time_ms, 0.0)
            self.assertGreater(len(result.xml_path), 0)
        finally:
            shutil.rmtree(tmp)

    def test_process_from_path_success_with_defects(self):
        """
        process_from_path returns success=1 and detection_count=2
        when the model detects 2 defects.
        """
        tmp = tempfile.mkdtemp()
        try:
            mock_pcb = self._make_mock_pcb_image()
            mock_det = self._make_mock_detection_result(num_defects=2)

            with patch("src.application.Camera") as MockCam, \
                 patch("src.application.Detector") as MockDet:
                MockCam.return_value.get_image_from_file.return_value = mock_pcb
                MockDet.return_value.detect.return_value = mock_det

                handle = self.lib.application_create(0, tmp.encode(), 0)
                result = self.lib.application_process_from_path(
                    handle, b"/fake/path.jpg"
                )
                self.lib.application_destroy(handle)

            self.assertEqual(result.success, 1)
            self.assertEqual(result.detection_count, 2)
        finally:
            shutil.rmtree(tmp)

    def test_xml_report_is_saved_to_disk(self):
        """
        After process_from_path, the XML file reported in xml_path must
        actually exist on disk.
        """
        tmp = tempfile.mkdtemp()
        try:
            mock_pcb = self._make_mock_pcb_image()
            mock_det = self._make_mock_detection_result(num_defects=1)

            with patch("src.application.Camera") as MockCam, \
                 patch("src.application.Detector") as MockDet:
                MockCam.return_value.get_image_from_file.return_value = mock_pcb
                MockDet.return_value.detect.return_value = mock_det

                handle = self.lib.application_create(0, tmp.encode(), 0)
                result = self.lib.application_process_from_path(
                    handle, b"/fake/path.jpg"
                )
                self.lib.application_destroy(handle)

            xml_path = result.xml_path.decode("utf-8")
            self.assertTrue(
                os.path.isfile(xml_path),
                f"XML report not found at: {xml_path}"
            )
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
