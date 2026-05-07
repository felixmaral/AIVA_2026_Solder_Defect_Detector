"""
tests/test_c_bindings.py — Unit tests for the C binding shared library.

These tests exercise the public C API (``libsolder_defect.so`` / ``.dylib``)
via Python's ``ctypes`` module. They are automatically skipped if the shared
library has not been compiled yet, so they integrate cleanly into the standard
``python -m unittest discover tests`` pipeline without requiring manual setup.

Why ctypes instead of a pure C test runner?
--------------------------------------------
The C library embeds the CPython interpreter. When it is loaded via ``ctypes``
inside an already-running Python process, the two share the **same** interpreter
instance. This means ``unittest.mock`` patches applied in Python are immediately
visible to the C code when it calls back into Python, making it possible to
replace ``Camera`` and ``Detector`` with lightweight mocks without needing
hardware or model weights.

Build the library before running these tests::

    make -C src/c_bindings
    python -m unittest tests.test_c_bindings -v
"""
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
    """
    Searches for the compiled C shared library relative to the project root.

    Returns:
        str: Absolute path to the ``.so`` or ``.dylib`` file, or ``None`` if
             the library has not been compiled yet.
    """
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
    """
    Python-side mirror of the ``DetectionResultInfo`` C struct (from ``solder_defect.h``).

    Must be kept in sync with the field order and types in the header file.
    """
    _fields_ = [
        ("xml_path",           ctypes.c_char * 512),
        ("processing_time_ms", ctypes.c_double),
        ("detection_count",    ctypes.c_int),
        ("success",            ctypes.c_int),
    ]


@unittest.skipIf(LIB_PATH is None, SKIP_REASON)
class TestCBindingsSafety(unittest.TestCase):
    """
    Tests that the C API is safe to call with invalid inputs (NULL handles).

    These tests require no Python mocks, model weights, or physical hardware.
    They only verify that the C boundary conditions are handled correctly
    (no segfaults, correct ``success=0`` return values).
    """

    @classmethod
    def setUpClass(cls):
        """
        Loads the shared library and registers function signatures once for the suite.

        Registering ``argtypes`` and ``restype`` is essential for ctypes to pass
        arguments and interpret return values correctly on all platforms.
        """
        cls.lib = ctypes.CDLL(LIB_PATH)

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
        Verifies that passing NULL to ``process_from_path`` returns ``success=0`` without crashing.

        Guards against null-pointer dereferences at the C boundary.
        """
        result = self.lib.application_process_from_path(None, b"any_path.jpg")
        self.assertEqual(result.success, 0)

    def test_null_handle_process_live_camera_returns_failure(self):
        """
        Verifies that passing NULL to ``process_live_camera`` returns ``success=0`` without crashing.
        """
        result = self.lib.application_process_live_camera(None)
        self.assertEqual(result.success, 0)

    def test_null_handle_destroy_does_not_crash(self):
        """
        Verifies that ``application_destroy(NULL)`` is a documented safe no-op.

        Mirrors the behaviour of POSIX ``free(NULL)``, which must not crash.
        """
        try:
            self.lib.application_destroy(None)
        except Exception as e:
            self.fail(f"application_destroy(NULL) raised an unexpected exception: {e}")


@unittest.skipIf(LIB_PATH is None, SKIP_REASON)
class TestCBindingsWithMocks(unittest.TestCase):
    """
    End-to-end tests for the C API using Python mocks for Camera and Detector.

    Because the C library and the test runner share the same CPython interpreter,
    ``unittest.mock`` patches applied here are visible to the C code when it
    calls back into Python, enabling full pipeline testing without hardware.
    """

    @classmethod
    def setUpClass(cls):
        """
        Loads the shared library and registers the function signatures used in this suite.
        """
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
        """
        Builds a valid ``PCBImage`` backed by a tiny blank JPEG payload.

        Args:
            filepath (str): Filepath label to embed in the PCBImage instance.

        Returns:
            PCBImage: A real (non-mocked) PCBImage with a decodable byte payload.
        """
        from src.core.pcb_image import PCBImage
        dummy = np.zeros((10, 10, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", dummy)
        return PCBImage(image_data=buf.tobytes(), filepath=filepath)

    def _make_mock_detection_result(self, num_defects: int = 0):
        """
        Builds a ``DetectionResult`` pre-populated with a given number of dummy defects.

        Args:
            num_defects (int): Number of ``SolderDefect`` instances to add.
                               Defaults to 0 (clean plate).

        Returns:
            DetectionResult: Result object with ``num_defects`` dummy entries.
        """
        from src.core.detection_result import DetectionResult
        from src.core.solder_defect import SolderDefect
        dr = DetectionResult()
        for _ in range(num_defects):
            dr.add_defect(SolderDefect(10, 20, 50, 50, 0.95))
        return dr

    def test_create_returns_valid_handle(self):
        """
        Verifies that ``application_create`` returns a non-NULL handle when ``Application`` loads correctly.
        """
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
        Verifies that a clean plate inspection returns ``success=1`` and ``detection_count=0``.
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
                result = self.lib.application_process_from_path(handle, b"/fake/path.jpg")
                self.lib.application_destroy(handle)

            self.assertEqual(result.success, 1)
            self.assertEqual(result.detection_count, 0)
            self.assertGreaterEqual(result.processing_time_ms, 0.0)
            self.assertGreater(len(result.xml_path), 0)
        finally:
            shutil.rmtree(tmp)

    def test_process_from_path_success_with_defects(self):
        """
        Verifies that a defective plate inspection returns ``success=1`` and ``detection_count=2``.
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
                result = self.lib.application_process_from_path(handle, b"/fake/path.jpg")
                self.lib.application_destroy(handle)

            self.assertEqual(result.success, 1)
            self.assertEqual(result.detection_count, 2)
        finally:
            shutil.rmtree(tmp)

    def test_xml_report_is_saved_to_disk(self):
        """
        Verifies that the XML report referenced in ``result.xml_path`` is written to disk.

        Confirms that the Python ``Application._process`` method completes the
        full pipeline (inference + file write) when called through the C API.
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
                result = self.lib.application_process_from_path(handle, b"/fake/path.jpg")
                self.lib.application_destroy(handle)

            xml_path = result.xml_path.decode("utf-8")
            self.assertTrue(
                os.path.isfile(xml_path),
                f"XML report was not written to disk at: {xml_path}",
            )
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
