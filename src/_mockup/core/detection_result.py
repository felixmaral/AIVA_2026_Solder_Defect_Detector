from typing import List
from .solder_defect import SolderDefect

class DetectionResult:
    """
    Aggregates multiple SolderDefect instances and handles XML report generation.
    """
    def __init__(self):
        self.defects: List[SolderDefect] = []

    def add_defect(self, defect: SolderDefect) -> None:
        """
        Appends a new defect to the results list.
        """
        self.defects.append(defect)

    def to_xml(self) -> str:
        """
        Generates the complete XML report containing all stored defects.
        """
        xml_output = "<result>\n"
        xml_output += f"    <detection_count>{len(self.defects)}</detection_count>\n"
        
        for defect in self.defects:
            xml_output += defect.to_xml_string() + "\n"
            
        xml_output += "</result>\n"
        return xml_output