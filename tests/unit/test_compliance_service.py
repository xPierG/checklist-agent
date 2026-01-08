import unittest
import pandas as pd
import os
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO
from services.compliance_service import ComplianceService
from google.genai import Client

class TestComplianceService(unittest.TestCase):

    def setUp(self):
        self.patcher_env = patch.dict(os.environ, {'AUTH_MODE': 'API_KEY', 'GOOGLE_API_KEY': 'TEST_KEY'})
        self.patcher_env.start()
        
        # Patch google.genai.Client globally for the test class to control its instantiation
        self.patcher_genai_client = patch('services.compliance_service.Client', autospec=True)
        self.MockGenaiClient = self.patcher_genai_client.start()
        # Mock the instance returned by Client()
        self.mock_genai_client_instance = self.MockGenaiClient.return_value 
        
        # Initialize ComplianceService
        with patch('services.compliance_service.create_orchestrator_agent'), \
             patch('services.compliance_service.InMemoryRunner'):
            self.service = ComplianceService(auth_mode="API_KEY")
        
        # Reset any state that might persist across tests
        self.service.checklist_df = None
        self.service.context_pdf_uris = []
        self.service.target_pdf_uris = []
        self.service.id_column = None
        self.service.question_column = None
        self.service.description_column = None

    def tearDown(self):
        self.patcher_env.stop()
        self.patcher_genai_client.stop()

    def test_init_api_key_mode(self):
        # The setUp already runs with API_KEY mode, just verify
        self.assertIsNotNone(self.service.client)
        self.MockGenaiClient.assert_called_with(api_key='TEST_KEY')
        self.assertIsNotNone(self.service.pdf_loader)
        self.assertIsNotNone(self.service.agent)
        self.assertIsNotNone(self.service.runner)
        self.assertIsNotNone(self.service.session_service)

    def test_init_adc_mode(self):
        with patch.dict(os.environ, {'AUTH_MODE': 'ADC', 'GOOGLE_API_KEY': 'DUMMY'}, clear=True):
            # We need to restart the ComplianceService to pick up the new env var
            with patch('services.compliance_service.create_orchestrator_agent'), \
                 patch('services.compliance_service.InMemoryRunner'):
                service_adc = ComplianceService(auth_mode="ADC")
                self.assertIsNotNone(service_adc.client)
                self.MockGenaiClient.assert_called_with() # Should be called without api_key for ADC
                self.assertIsNotNone(service_adc.pdf_loader)

    def test_init_unsupported_auth_mode(self):
        with self.assertRaisesRegex(ValueError, "Unsupported authentication mode: UNSUPPORTED"):
            with patch.dict(os.environ, {'AUTH_MODE': 'UNSUPPORTED', 'GOOGLE_API_KEY': 'DUMMY'}, clear=True):
                with patch('services.compliance_service.create_orchestrator_agent'), \
                     patch('services.compliance_service.InMemoryRunner'):
                    ComplianceService(auth_mode="UNSUPPORTED")

    @patch('services.compliance_service.PDFLoader.upload_and_cache')
    def test_load_context_pdf(self, mock_upload_and_cache):
        mock_upload_and_cache.return_value = "files/context_uri_1"
        file_path = "test_context.pdf"
        # Create a dummy file for os.path.basename
        with open(file_path, "w") as f:
            f.write("dummy content")
        
        uri = self.service.load_context_pdf(file_path)
        
        self.assertEqual(uri, "files/context_uri_1")
        self.assertEqual(len(self.service.context_pdf_uris), 1)
        self.assertEqual(self.service.context_pdf_uris[0]['filename'], "test_context.pdf")
        self.assertEqual(self.service.context_pdf_uris[0]['uri'], "files/context_uri_1")
        mock_upload_and_cache.assert_called_once_with(file_path)
        os.remove(file_path)

    @patch('services.compliance_service.PDFLoader.upload_and_cache')
    def test_load_target_pdf(self, mock_upload_and_cache):
        mock_upload_and_cache.return_value = "files/target_uri_1"
        file_path = "test_target.pdf"
        # Create a dummy file for os.path.basename
        with open(file_path, "w") as f:
            f.write("dummy content")

        uri = self.service.load_target_pdf(file_path)
        
        self.assertEqual(uri, "files/target_uri_1")
        self.assertEqual(len(self.service.target_pdf_uris), 1)
        self.assertEqual(self.service.target_pdf_uris[0]['filename'], "test_target.pdf")
        self.assertEqual(self.service.target_pdf_uris[0]['uri'], "files/target_uri_1")
        mock_upload_and_cache.assert_called_once_with(file_path)
        os.remove(file_path)

    @patch('pandas.read_excel')
    def test_load_checklist_excel_default_cols(self, mock_read_excel):
        # Create a dummy Excel file data
        df_input = pd.DataFrame({
            'ID': ['1', '2'],
            'Question': ['Q1', 'Q2'],
            'Description': ['Desc1', 'Desc2'],
            'Other': ['O1', 'O2']
        })
        mock_read_excel.return_value = df_input.copy()

        # Mock the UploadedFile object passed to load_checklist
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "checklist.xlsx"
        
        df = self.service.load_checklist(mock_uploaded_file)
        
        mock_read_excel.assert_called_once_with(mock_uploaded_file, dtype=str)

        self.assertIsNotNone(df)
        self.assertEqual(len(df), 2)
        self.assertEqual(self.service.id_column, 'ID')
        self.assertEqual(self.service.question_column, 'Question')
        self.assertEqual(self.service.description_column, 'Description')
        self.assertIn('Status', df.columns)
        self.assertIn('Risposta', df.columns)
        self.assertIn('Confidenza', df.columns)
        self.assertIn('Giustificazione', df.columns)
        self.assertIn('Discussion_Log', df.columns)
        self.assertEqual(df['Status'].iloc[0], 'PENDING')

    @patch('pandas.read_excel') # Mock read_excel which is called by service.load_checklist
    @patch('pandas.read_csv')   # Directly mock read_csv for when it's the actual underlying call
    def test_load_checklist_csv_alt_cols(self, mock_read_csv, mock_read_excel):
        # Mocking read_excel because service.load_checklist always tries read_excel first
        # For CSV testing, we assume read_excel would delegate or fail, and then read_csv is used.
        # Here, we'll make read_excel return a specific DataFrame directly, acting as if it read a CSV
        # Or, more realistically, we can make read_excel raise an error, and then patch the *logic* inside load_checklist
        # The service's load_checklist method only calls pd.read_excel. To test CSV, we need to mock that it can handle it.
        # A simpler way is to ensure read_excel correctly simulates reading a CSV for our test case.
        
        df_input = pd.DataFrame({
            'Item_No': ['1', '2'],
            'Requirement': ['Req1', 'Req2'],
            'Details': ['Detail1', 'Detail2']
        })
        mock_read_excel.return_value = df_input.copy() # Simulate pandas reading CSV via excel path

        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "checklist.csv" # The file extension determines pandas internal logic
        
        df = self.service.load_checklist(mock_uploaded_file)
        
        mock_read_excel.assert_called_once_with(mock_uploaded_file, dtype=str) # service calls read_excel

        self.assertIsNotNone(df)
        self.assertEqual(len(df), 2)
        self.assertEqual(self.service.id_column, 'Item_No')
        self.assertEqual(self.service.question_column, 'Requirement')
        self.assertEqual(self.service.description_column, 'Details')

    @patch('pandas.read_excel')
    def test_load_checklist_empty_rows(self, mock_read_excel):
        df_input = pd.DataFrame({
            'ID': ['1', '2', '3'],
            'Question': ['Q1', '', 'Q3'],
            'Description': ['Desc1', 'Desc2', 'Desc3']
        })
        mock_read_excel.return_value = df_input.copy()

        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "checklist.xlsx"

        df = self.service.load_checklist(mock_uploaded_file)
        self.assertEqual(len(df), 2) # Row with empty question should be dropped
        self.assertListEqual(df['ID'].tolist(), ['1', '3'])
    
    @patch('pandas.read_excel')
    def test_load_checklist_nan_rows(self, mock_read_excel):
        df_input = pd.DataFrame({
            'ID': ['1', '2', '3'],
            'Question': ['Q1', float('nan'), 'Q3'],
            'Description': ['Desc1', 'Desc2', 'Desc3']
        })
        mock_read_excel.return_value = df_input.copy()

        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "checklist.xlsx"

        df = self.service.load_checklist(mock_uploaded_file)
        self.assertEqual(len(df), 2) # Row with 'nan' question should be dropped
        self.assertListEqual(df['ID'].tolist(), ['1', '3'])
    
    def test_get_question_from_row(self):
        self.service.checklist_df = pd.DataFrame({
            'ID': ['1'],
            'Question': ['Test Question'],
            'Description': ['Test Desc']
        })
        self.service.question_column = 'Question'
        self.assertEqual(self.service.get_question_from_row(0), 'Test Question')

    def test_get_description_from_row(self):
        self.service.checklist_df = pd.DataFrame({
            'ID': ['1'],
            'Question': ['Test Question'],
            'Description': ['Test Desc']
        })
        self.service.description_column = 'Description'
        self.assertEqual(self.service.get_description_from_row(0), 'Test Desc')

    def test_parse_response_full(self):
        response_text = """
        **RISPOSTA:** Sì
        **CONFIDENZA:** 95%
        **GIUSTIFICAZIONE:**
        - Spiegazione: The document explicitly states compliance.
        - Context Rule: "Rule A states..."
        - Target Evidence: "Doc X says..."
        - Fonte Context: rule.pdf, p.5
        - Fonte Target: doc.pdf, p.10
        """
        parsed = self.service._parse_response(response_text)
        self.assertEqual(parsed['risposta'], 'Sì')
        self.assertEqual(parsed['confidenza'], 95)
        self.assertIn('The document explicitly states compliance.', parsed['giustificazione'])

    def test_parse_response_no_confidence(self):
        response_text = """
        **RISPOSTA:** No
        **GIUSTIFICAZIONE:**
        - Spiegazione: No evidence found.
        """
        parsed = self.service._parse_response(response_text)
        self.assertEqual(parsed['risposta'], 'No')
        self.assertEqual(parsed['confidenza'], 0) # Default
        self.assertIn('No evidence found.', parsed['giustificazione'])

    def test_parse_response_only_justification(self):
        response_text = "This is just a justification without structured headers."
        parsed = self.service._parse_response(response_text)
        self.assertEqual(parsed['risposta'], '?') # Default
        self.assertEqual(parsed['confidenza'], 0) # Default
        self.assertEqual(parsed['giustificazione'], response_text.strip())

    def test_parse_response_empty(self):
        response_text = ""
        parsed = self.service._parse_response(response_text)
        self.assertEqual(parsed['risposta'], '?')
        self.assertEqual(parsed['confidenza'], 0)
        self.assertEqual(parsed['giustificazione'], '')

if __name__ == '__main__':
    unittest.main()
