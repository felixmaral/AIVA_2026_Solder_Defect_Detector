import unittest
from src.core.solder_defect import SolderDefect
from src.core.detection_result import DetectionResult

class TestDetectionResult(unittest.TestCase):
    """
    Validates structural aggregations and final batch reports correctly interpolate sequences.
    """
    def test_add_and_batch_xml(self):
        result = DetectionResult()
        defect1 = SolderDefect(10, 20, 50, 60, 0.88)
        defect2 = SolderDefect(100, 200, 500, 600, 0.99)
        
        result.add_defect(defect1)
        result.add_defect(defect2)
        
        xml = result.to_xml()
        self.assertEqual(len(result.defects), 2)
        self.assertIn("<detection_count>2</detection_count>", xml)
        self.assertIn("<x>10</x>", xml)
        self.assertIn("<y>200</y>", xml)
        self.assertIn("</result>", xml)

if __name__ == '__main__':
    unittest.main()
