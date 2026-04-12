import unittest
from src.core.solder_defect import SolderDefect

class TestSolderDefect(unittest.TestCase):
    """
    Test suite for the standard solder defect container variables.
    """
    def test_defect_xml_serialization(self):
        """
        Validates the properties correctly interpolate into the XML chunk natively.
        """
        defect = SolderDefect(top_left_x=10, top_left_y=20, width=50, height=60, confidence=0.88)
        xml = defect.to_xml_string()
        
        self.assertIn("<x>10</x>", xml)
        self.assertIn("<y>20</y>", xml)
        self.assertIn("<width>50</width>", xml)
        self.assertIn("<height>60</height>", xml)
        self.assertIn("<confidence>0.8800</confidence>", xml)

if __name__ == '__main__':
    unittest.main()
