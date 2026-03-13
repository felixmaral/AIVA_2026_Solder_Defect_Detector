import unittest
from src._mockup.core.solder_defect import SolderDefect
from src._mockup.core.detection_result import DetectionResult

class TestSolderDefect(unittest.TestCase):
    """
    Suite para validar los modelos de datos de defectos y reportes.
    """

    def test_solder_defect_initialization(self):
        """
        Verifica que los atributos se asignen correctamente en el constructor.
        """
        defect = SolderDefect(
            top_left_x=10, 
            top_left_y=20, 
            width=100, 
            height=50, 
            confidence=0.95
        )
        self.assertEqual(defect.top_left_x, 10)
        self.assertEqual(defect.width, 100)
        self.assertEqual(defect.confidence, 0.95)

    def test_xml_serialization(self):
        """
        Valida que el fragmento XML generado sea correcto.
        """
        defect = SolderDefect(5, 5, 10, 10, 0.8)
        xml_output = defect.to_xml_string()
        self.assertIn("<x>5</x>", xml_output)
        self.assertIn("<confidence>0.8</confidence>", xml_output)

    def test_detection_result_aggregation(self):
        """
        Verifica la acumulación de defectos y el reporte final.
        """
        result = DetectionResult()
        result.add_defect(SolderDefect(0, 0, 1, 1, 0.1))
        result.add_defect(SolderDefect(1, 1, 2, 2, 0.2))
        
        xml_report = result.to_xml()
        self.assertEqual(len(result.defects), 2)
        self.assertIn("<detection_count>2</detection_count>", xml_report)

if __name__ == '__main__':
    unittest.main()