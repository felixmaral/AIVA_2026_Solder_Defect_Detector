import os
from pathlib import Path

import cv2
from ultralytics import YOLO

from ..core.pcb_image import PCBImage
from ..core.solder_defect import SolderDefect
from ..core.detection_result import DetectionResult


class Detector:
    """
    YOLO-based inference engine for solder defect detection on PCB images.

    Loads a fine-tuned YOLO model at initialisation time and exposes a single
    ``detect`` method that accepts a ``PCBImage`` and returns a ``DetectionResult``
    containing all discovered defect bounding boxes.

    The class applies a mandatory pre-processing step before inference: the input
    BGR image is converted to grayscale and then back to a 3-channel BGR tensor.
    This matches the input distribution of the training dataset, which was
    captured under controlled monochromatic LED lighting.

    Attributes:
        model (YOLO): The loaded Ultralytics YOLO model instance.
        conf_threshold (float): Minimum confidence score [0.0, 1.0] required for
            a detection to be included in the result. Predictions below this
            threshold are discarded by the model automatically.
    """

    def __init__(self, weights_path: str = None, conf_threshold: float = 0.25):
        """
        Loads the YOLO model weights into memory.

        Args:
            weights_path (str, optional): Absolute path to the ``best.pt``
                weights file. If None, defaults to
                ``<project_root>/model_dev/weights/best.pt``.
            conf_threshold (float): Confidence threshold for filtering
                predictions. Defaults to 0.25.

        Raises:
            FileNotFoundError: If the weights file is not found at the
                resolved path.
        """
        # Resolve the default weights path relative to the project root
        if weights_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            weights_path = str(base_dir / "model_dev" / "weights" / "best.pt")

        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found at: {weights_path}")

        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold

    def detect(self, image: PCBImage) -> DetectionResult:
        """
        Runs YOLO inference on a PCB image and returns all detected defects.

        The method follows a four-step pipeline:

        1. **Decode** — Ensure the ``PCBImage`` byte payload has been decoded
           into a BGR NumPy matrix.
        2. **Pre-process** — Convert to grayscale and back to 3-channel BGR to
           match the training data distribution.
        3. **Infer** — Run the YOLO model and collect bounding box predictions.
        4. **Aggregate** — Wrap each predicted box in a ``SolderDefect`` instance
           and collect them into a ``DetectionResult``.

        Args:
            image (PCBImage): The PCB image to inspect.

        Returns:
            DetectionResult: Container with all detected defects. Returns an
                empty ``DetectionResult`` if no defects are found.

        Raises:
            ValueError: If the ``PCBImage`` byte payload is empty or cannot
                be decoded into a valid image matrix.
        """
        # Step 1 — Decode the raw byte payload into a BGR matrix
        image._calculate_dimensions()
        img = image._decoded_image

        if img is None:
            raise ValueError("PCBImage data is empty or cannot be decoded.")

        # Step 2 — Convert to grayscale and back to 3-channel BGR.
        # The model was trained on monochromatic illumination data; this step
        # normalises the colour distribution of any input regardless of source.
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_input = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

        # Step 3 — Run YOLO inference with suppressed console output
        predictions = self.model.predict(
            source=img_input,
            conf=self.conf_threshold,
            verbose=False,
        )

        # Step 4 — Aggregate predictions into the result container
        final_result = DetectionResult()

        # Guard: YOLO may return an empty list if the image is unprocessable
        if not predictions:
            return final_result

        # YOLO returns one Boxes object per input image; since we send one image,
        # the result is always at index 0
        detected_boxes = predictions[0].boxes

        for box in detected_boxes:
            # box.xyxy[0] contains [x_min, y_min, x_max, y_max] in pixel coordinates
            x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
            confidence = float(box.conf[0].item())

            # Derive width and height from the absolute corner coordinates
            width = int(x_max - x_min)
            height = int(y_max - y_min)

            defect = SolderDefect(
                top_left_x=int(x_min),
                top_left_y=int(y_min),
                width=width,
                height=height,
                confidence=confidence,
            )
            final_result.add_defect(defect)

        return final_result
