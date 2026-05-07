class SolderDefect:
    """
    Represents a single solder defect detected by the inference engine.

    Each instance encodes the spatial location and confidence score of one
    anomaly found on the PCB surface. The bounding box is expressed in the
    top-left origin convention, consistent with standard computer vision
    coordinate systems (x increases rightward, y increases downward).

    Attributes:
        top_left_x (int): Horizontal pixel coordinate of the bounding box origin.
        top_left_y (int): Vertical pixel coordinate of the bounding box origin.
        width (int): Bounding box width in pixels.
        height (int): Bounding box height in pixels.
        confidence (float): Model confidence score in the range [0.0, 1.0].
    """

    def __init__(
        self,
        top_left_x: int,
        top_left_y: int,
        width: int,
        height: int,
        confidence: float,
    ):
        """
        Initialises the defect with its spatial bounding box and confidence score.

        Args:
            top_left_x (int): X-coordinate of the top-left corner of the bounding box.
            top_left_y (int): Y-coordinate of the top-left corner of the bounding box.
            width (int): Width of the bounding box in pixels.
            height (int): Height of the bounding box in pixels.
            confidence (float): Prediction confidence in the range [0.0, 1.0].
        """
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.width = width
        self.height = height
        self.confidence = confidence

    def to_xml_string(self) -> str:
        """
        Serialises the defect properties into a standardised XML fragment.

        The produced fragment is designed to be embedded directly within the
        ``<result>`` root element of a full DetectionResult XML manifest.

        Returns:
            str: A well-formed XML block representing this defect, including
                 bounding box coordinates and confidence score (4 decimal places).

        Example::

            <defect>
                <x>120</x>
                <y>45</y>
                <width>60</width>
                <height>30</height>
                <confidence>0.9372</confidence>
            </defect>
        """
        return (
            f"    <defect>\n"
            f"        <x>{self.top_left_x}</x>\n"
            f"        <y>{self.top_left_y}</y>\n"
            f"        <width>{self.width}</width>\n"
            f"        <height>{self.height}</height>\n"
            f"        <confidence>{self.confidence:.4f}</confidence>\n"
            f"    </defect>"
        )