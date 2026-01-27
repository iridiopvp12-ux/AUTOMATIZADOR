import unittest
from unittest.mock import MagicMock, patch
import os
import xml.etree.ElementTree as ET
from src.utils.xml_to_excel_logic import XmlToExcelLogic

class TestXmlLogic(unittest.TestCase):
    def setUp(self):
        self.logic = XmlToExcelLogic()

    @patch('pandas.ExcelWriter')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('xml.etree.ElementTree.parse')
    @patch('pandas.DataFrame.to_excel')
    def test_xml_conversion_success(self, mock_to_excel, mock_parse, mock_listdir, mock_exists, mock_writer):
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ['nota.xml']

        # Mock writer context manager
        mock_writer.return_value.__enter__.return_value = MagicMock()

        # Mock XML content
        xml_content = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe35123456789012345678901234567890123456789012"><ide><nNF>100</nNF><serie>1</serie><dhEmi>2023-10-25T10:00:00-03:00</dhEmi></ide><emit><xNome>Empresa A</xNome><CNPJ>12345678000199</CNPJ></emit><dest><xNome>Cliente B</xNome><CNPJ>98765432000100</CNPJ></dest><total><ICMSTot><vNF>150.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree

        # Run
        success, msg = self.logic.xml_folder_to_excel("dummy_folder", "output.xlsx")

        if not success:
            print(f"\nFAILURE MSG: {msg}")

        # Assert
        self.assertTrue(success)
        self.assertIn("Sucesso", msg)
        self.assertIn("1 XMLs processados", msg)

    @patch('os.path.exists')
    def test_invalid_folder(self, mock_exists):
        mock_exists.return_value = False
        success, msg = self.logic.xml_folder_to_excel("invalid", "out.xlsx")
        self.assertFalse(success)
        self.assertEqual(msg, "Pasta de origem inválida.")

if __name__ == '__main__':
    unittest.main()
