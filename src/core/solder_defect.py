class SolderDefect:
    """
    Represents an individual solder defect detected by the model.
    """
    
    def __init__(self, top_left_x: int, top_left_y: int, width: int, height: int, confidence: float):
        """
        Initializes the bounding box constraints and confidence threshold.
        """
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.width = width
        self.height = height
        self.confidence = confidence

    def to_xml_string(self) -> str:
        """
        Serializes the primary defect properties into a standardized XML format block.
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