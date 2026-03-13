from ..core.pcb_image import PCBImage
from ..core.solder_defect import SolderDefect
from ..core.detection_result import DetectionResult

class Detector:
    """
    Mock inference engine used to simulate image processing and defect localization.
    """
    def detect(self, image: PCBImage) -> DetectionResult:
        """
        Simulates image analysis and returns a DetectionResult with hardcoded anomalies.
        """
        result = DetectionResult()
        
        result.add_defect(SolderDefect(15, 30, 45, 45, 0.98))
        result.add_defect(SolderDefect(120, 210, 25, 35, 0.82))
        
        return result