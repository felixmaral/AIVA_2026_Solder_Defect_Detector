from typing import List
from .solder_defect import SolderDefect

class DetectionResult:
    """
    Aggregates multiple SolderDefect instances and provides bulk XML serialization.
    """
    
    def __init__(self):
        """
        Initializes an empty registry for the detected structural anomalies.
        """
        self.defects: List[SolderDefect] = []

    def add_defect(self, defect: SolderDefect) -> None:
        """
        Registers a newly discovered defect bounding box into the result map.
        """
        self.defects.append(defect)

    def to_xml(self) -> str:
        """
        Compiles the entire defects registry into a comprehensive XML manifest.
        """
        # Formulate manifest header containing global block metrics
        lines = [
            "<result>", 
            f"    <detection_count>{len(self.defects)}</detection_count>"
        ]
        
        # Append XML serialization of all independent detected boxes
        for defect in self.defects:
            lines.append(defect.to_xml_string())
            
        lines.append("</result>")
        
        # Return merged sequence with trailing carriage return standard
        return "\n".join(lines) + "\n"