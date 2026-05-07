"""
tests/test_solder_defect.py — Unit tests for the SolderDefect data class.

Verifies that defect properties are correctly serialised into the XML fragment
format expected by the downstream report generation pipeline.
"""
import unittest
from src.core.solder_defect import SolderDefect


class TestSolderDefect(unittest.TestCase):
    """
    Test suite for the ``SolderDefect`` atomic defect container.
    """

    def test_defect_xml_serialization(self):
        """
        Verifies that all bounding box fields are correctly embedded in the XML fragment.

        Confidence is expected to be formatted to 4 decimal places, matching the
        ``to_xml_string`` implementation contract.
        """
        defect = SolderDefect(top_left_x=10, top_left_y=20, width=50, height=60, confidence=0.88)
        xml = defect.to_xml_string()

        # Assert each field appears as a properly-tagged XML element
        self.assertIn("<x>10</x>", xml)
        self.assertIn("<y>20</y>", xml)
        self.assertIn("<width>50</width>", xml)
        self.assertIn("<height>60</height>", xml)
        # Confidence must be formatted to exactly 4 decimal places
        self.assertIn("<confidence>0.8800</confidence>", xml)


if __name__ == '__main__':
    unittest.main()
