"""Application façade for the PCB solder defect detection pipeline."""
import os
import time
import datetime
import sys
import cv2

# Ensure the project root is in the Python path to allow absolute imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.hardware.camera import Camera
from src.vision.detector import Detector


class Application:
    """
    Primary API façade for the PCB Solder Defect Detection System.

    ``Application`` is the single entry point for any external client — whether
    a Python orchestration script or a native C/C++ robot controller — that
    needs to inspect a PCB for solder defects. It coordinates the full
    inspection lifecycle:

    1. Acquires the image via the ``Camera`` hardware interface.
    2. Runs YOLO inference via the ``Detector`` engine.
    3. Serialises the result to an XML report on disk.
    4. Optionally renders bounding boxes in a live OpenCV window.

    The class is designed to be instantiated **once** per session (heavyweight
    operations such as camera initialisation and model loading happen in
    ``__init__``), after which ``process_from_path`` or ``process_live_camera``
    can be called repeatedly in a tight loop without incurring additional
    startup cost.

    Attributes:
        camera (Camera): Hardware interface used to acquire ``PCBImage`` objects.
        detector (Detector): YOLO inference engine.
        visualize (bool): When ``True``, detection results are rendered in a live
            OpenCV window after each inference cycle.
        output_dir (str): Filesystem directory where XML reports are saved.
            Created automatically if it does not exist.
    """

    def __init__(self, camera_index: int = 0, output_dir: str = None, visualize: bool = False):
        """
        Initialises the camera interface and loads the YOLO model into memory.

        This constructor performs all heavyweight one-time setup. Subsequent
        calls to the process methods are lightweight inference calls.

        Args:
            camera_index (int): OpenCV device index for the physical camera.
                Defaults to 0 (primary Raspberry Pi camera).
            output_dir (str, optional): Path to the directory where XML reports
                will be saved. Defaults to ``<project_root>/reports/xml/``.
            visualize (bool): If ``True``, activates the live detection window.
                Should be ``False`` in headless production deployments.
                Defaults to ``False``.
        """
        print("Initializing hardware camera interface...")
        self.camera = Camera(camera_index=camera_index)
        self.visualize = visualize

        print("Loading YOLO detector...")
        self.detector = Detector()

        self.output_dir = output_dir if output_dir else os.path.join(project_root, "reports", "xml")
        os.makedirs(self.output_dir, exist_ok=True)
        print("Application initialized successfully.")

    def process_from_path(self, image_path: str) -> dict:
        """
        Reads a PCB image from disk, runs inference, and saves an XML report.

        Convenience method for batch processing workflows where images are
        already stored on the filesystem (e.g., simulation or evaluation runs).

        Args:
            image_path (str): Absolute or relative path to the PCB image file.

        Returns:
            dict: Result dictionary with the following keys:

                - ``xml_path`` (str): Absolute path to the saved XML report.
                - ``processing_time_s`` (float): Wall-clock inference time in seconds.
                - ``processing_time_ms`` (float): Same value in milliseconds.
                - ``detection_count`` (int): Number of defects detected.
        """
        print(f"\nProcessing local image: {image_path}")
        pcb_image = self.camera.get_image_from_file(image_path)
        return self._process(pcb_image, source_path=image_path)

    def process_pcb_image(self, pcb_image, custom_name: str = None) -> dict:
        """
        Runs inference on a pre-loaded ``PCBImage`` object.

        Useful for pipelines that construct or augment ``PCBImage`` objects in
        memory before inspection (e.g., the 24-hour stress simulation with
        random data augmentation).

        Args:
            pcb_image (PCBImage): The image object to inspect.
            custom_name (str, optional): Base name for the output XML file,
                without extension. If ``None``, a timestamp-based name is used.

        Returns:
            dict: Same structure as :meth:`process_from_path`.
        """
        return self._process(pcb_image, custom_name=custom_name)

    def process_live_camera(self) -> dict:
        """
        Captures a frame from the physical camera and runs inference on it.

        Intended for real-time production deployments where the robot control
        software triggers an inspection at the moment the PCB reaches the
        calibrated inspection position.

        Returns:
            dict: Same structure as :meth:`process_from_path`.
        """
        print("\nAttempting to capture real-time image from camera hardware...")
        pcb_image = self.camera.get_real_time_image()
        return self._process(pcb_image)

    def _process(self, pcb_image, source_path: str = None, custom_name: str = None) -> dict:
        """
        Core inference pipeline shared by all public process methods.

        Executes the full inspection cycle: measures image properties, runs
        YOLO inference, serialises the result to XML, optionally renders
        detections, and returns a summary dictionary.

        Args:
            pcb_image (PCBImage): The image to inspect.
            source_path (str, optional): Original file path, used to derive
                the XML report filename. Ignored if ``custom_name`` is given.
            custom_name (str, optional): Explicit base name for the XML report.
                Takes precedence over ``source_path``.

        Returns:
            dict: Result dictionary with keys ``xml_path``, ``processing_time_s``,
                ``processing_time_ms``, and ``detection_count``.
        """
        print(f"Image captured: {pcb_image.get_resolution()} — {pcb_image.get_size_bytes()} bytes")

        # Start the stopwatch strictly from image delivery, excluding I/O overhead
        proc_start = time.time()

        print("Running defect detection...")
        detection_result = self.detector.detect(pcb_image)
        xml_report = detection_result.to_xml()

        # Stop the stopwatch immediately after inference completes
        proc_time = time.time() - proc_start

        print("Inspection completed. XML report generated.")

        # Determine the output filename: explicit name → source path → timestamp
        if custom_name:
            base_name = custom_name
        elif source_path:
            base_name = os.path.splitext(os.path.basename(source_path))[0]
        else:
            base_name = f"Capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        xml_filename = os.path.join(self.output_dir, f"{base_name}.xml")
        with open(xml_filename, 'w', encoding='utf-8') as f:
            f.write(xml_report)
        print(f"XML saved to {xml_filename}")

        if self.visualize:
            self._render_detections(pcb_image, detection_result)

        return {
            "xml_path": xml_filename,
            "processing_time_s": proc_time,
            "processing_time_ms": proc_time * 1000,
            "detection_count": len(detection_result.defects),
        }

    def _render_detections(self, pcb_image, detection_result) -> None:
        """
        Overlays bounding boxes on the PCB image and updates the OpenCV window.

        Called automatically after each inference cycle when ``visualize=True``.
        The window is non-blocking (``waitKey(1)``): it updates the display
        immediately and keeps the frame visible until the next call, allowing
        the operator to observe each inspected plate without halting the pipeline.

        Args:
            pcb_image (PCBImage): The inspected image, used as the display canvas.
            detection_result (DetectionResult): The inference output containing
                the bounding boxes to draw.
        """
        pcb_image._calculate_dimensions()
        img = pcb_image._decoded_image
        if img is None:
            return

        # Work on a copy to avoid mutating the cached decoded image
        display_img = img.copy()

        for defect in detection_result.defects:
            x, y, w, h = defect.top_left_x, defect.top_left_y, defect.width, defect.height
            # Draw the bounding box in red (BGR: 0, 0, 255)
            cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            label = f"Defect: {defect.confidence:.2f}"
            cv2.putText(display_img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        try:
            cv2.imshow("Solder Defect Detections", display_img)
            # Non-blocking update: 1 ms is sufficient to pump the UI event loop
            cv2.waitKey(1)
        except cv2.error as e:
            print(f"Visualization error: {e}")

    def wait(self, delay_s: float) -> None:
        """
        Pauses execution for a given duration while keeping the UI responsive.

        When ``visualize=True``, this method uses ``cv2.waitKey`` instead of
        ``time.sleep`` to pump the OpenCV event loop during the inter-plate
        wait. This prevents the detection window from becoming unresponsive
        between inspection cycles. When ``visualize=False``, it falls back to
        a standard ``time.sleep``.

        Args:
            delay_s (float): Duration to wait in seconds.
        """
        if self.visualize:
            # cv2.waitKey expects milliseconds; minimum is 1 ms
            delay_ms = max(1, int(delay_s * 1000))
            cv2.waitKey(delay_ms)
        else:
            time.sleep(delay_s)

    def wait_for_key(self) -> None:
        """
        Blocks indefinitely until the operator presses any key in the OpenCV window.

        Only has an effect when ``visualize=True``. Used in ``single`` mode to
        hold the detection window open until the operator has finished reviewing
        the result before the process exits.
        """
        if self.visualize:
            cv2.waitKey(0)
