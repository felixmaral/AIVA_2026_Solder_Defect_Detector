class SolderDefect:
    """
    Represents an individual solder defect detection.
    """
    def __init__(self, top_left_x: int, top_left_y: int, width: int, height: int, confidence: float):
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.width = width
        self.height = height
        self.confidence = confidence

    def to_xml_string(self) -> str:
        """
        Converts the defect instance into an XML formatted string.
        """
        return f"""    <defect>
        <x>{self.top_left_x}</x>
        <y>{self.top_left_y}</y>
        <width>{self.width}</width>
        <height>{self.height}</height>
        <confidence>{self.confidence}</confidence>
    </defect>"""