import unittest
import pandas as pd
import os
from unittest.mock import MagicMock, patch, AsyncMock
from services.compliance_service import ComplianceService
from google.genai import Client, types
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService


class TestComplianceServiceIntegration(unittest.TestCase):

    def setUp(self):
        # Patch environment variables for API_KEY auth mode
        self.patcher_env = patch.dict(os.environ, {'AUTH_MODE': 'API_KEY', 'GOOGLE_API_KEY': 'TEST_KEY'})
        self.patcher_env.start()
        
        # Patch google.genai.Client globally
        self.patcher_genai_client = patch('services.compliance_service.Client', autospec=True)
        self.MockGenaiClient = self.patcher_genai_client.start()
        self.mock_genai_client_instance = self.MockGenaiClient.return_value 

        # Mock the agents used by the Orchestrator
        self.mock_librarian_agent = MagicMock(spec=LlmAgent)
        self.mock_auditor_agent = MagicMock(spec=LlmAgent)
        self.mock_librarian_agent.parent_agent = None
        self.mock_auditor_agent.parent_agent = None

        # Patch create_librarian_agent and create_auditor_agent to return our mocks
        self.patcher_create_librarian = patch('agents.orchestrator.create_librarian_agent', return_value=self.mock_librarian_agent)
        self.patcher_create_auditor = patch('agents.orchestrator.create_auditor_agent', return_value=self.mock_auditor_agent)
        self.patcher_create_librarian.start()
        self.patcher_create_auditor.start()

        # Patch InMemoryRunner and InMemorySessionService
        self.patcher_runner = patch('services.compliance_service.InMemoryRunner')
        self.MockInMemoryRunner = self.patcher_runner.start()
        self.mock_runner_instance = self.MockInMemoryRunner.return_value
        
        # Mocking the session_service of the runner
        self.mock_runner_instance.session_service = MagicMock(spec=InMemorySessionService)
        # Mocking async methods for session_service
        self.mock_runner_instance.session_service.get_session = AsyncMock(return_value=None)
        self.mock_runner_instance.session_service.create_session = AsyncMock(return_value=None)


        # Initialize ComplianceService
        self.service = ComplianceService(auth_mode="API_KEY")
        
        # Setup common data
        self.service.checklist_df = pd.DataFrame({
            'ID': ['1', '2'],
            'Question': ['Is X compliant?', 'Is Y compliant?'],
            'Description': ['Details for X', 'Details for Y'],
            'Risposta': ['?', '?'],
            'Confidenza': [0, 0],
            'Giustificazione': ['', ''],
            'Status': ['PENDING', 'PENDING'],
            'Discussion_Log': ['', '']
        })
        self.service.id_column = 'ID'
        self.service.question_column = 'Question'
        self.service.description_column = 'Description'

        # Dummy PDFs
        self.service.context_pdf_uris = [{'filename': 'context.pdf', 'uri': 'files/context_uri'}]
        self.service.target_pdf_uris = [{'filename': 'target.pdf', 'uri': 'files/target_uri'}]

    def tearDown(self):
        self.patcher_env.stop()
        self.patcher_genai_client.stop()
        self.patcher_create_librarian.stop()
        self.patcher_create_auditor.stop()
        self.patcher_runner.stop()

    def _create_mock_event(self, content_text: str, is_final: bool = False, author: str = 'auditor') -> MagicMock:
        """Helper to create a mock event."""
        mock_content = MagicMock(spec=types.Content)
        mock_content.parts = [MagicMock(spec=types.Part)]
        mock_content.parts[0].text = content_text
        
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = is_final
        mock_event.content = mock_content
        mock_event.author = author
        return mock_event

    @patch('services.compliance_service.logger.info')
    @patch('services.compliance_service.logger.success')
    def test_analyze_row_success(self, mock_logger_success, mock_logger_info):
        # Mock the runner's run method to return a list of events
        mock_response_text = """
        **RISPOSTA:** Sì
        **CONFIDENZA:** 90%
        **GIUSTIFICAZIONE:** Compliance found.
        """
        self.mock_runner_instance.run.return_value = [
            self._create_mock_event("Librarian processing...", author='Librarian'),
            self._create_mock_event("Auditor evaluating...", author='Auditor'),
            self._create_mock_event(mock_response_text, is_final=True, author='Auditor')
        ]

        row_index = 0
        question = "Is X compliant?"
        result = self.service.analyze_row(row_index, question)

        self.mock_runner_instance.run.assert_called_once()
        self.assertIn("RISPOSTA", result) # Raw response text is returned

        # Verify DataFrame update
        self.assertEqual(self.service.checklist_df.at[row_index, 'Risposta'], 'Sì')
        self.assertEqual(self.service.checklist_df.at[row_index, 'Confidenza'], 90)
        self.assertEqual(self.service.checklist_df.at[row_index, 'Giustificazione'], 'Compliance found.')
        self.assertEqual(self.service.checklist_df.at[row_index, 'Status'], 'DRAFT')
        
        self.mock_runner_instance.session_service.get_session.assert_called_once()
        self.mock_runner_instance.session_service.create_session.assert_called_once()

    def test_analyze_row_no_target_pdfs(self):
        self.service.target_pdf_uris = [] # Clear target PDFs
        row_index = 0
        question = "Is X compliant?"
        result = self.service.analyze_row(row_index, question)

        self.assertIn("Error: No target documents loaded", result)
        self.mock_runner_instance.run.assert_not_called()

    def test_chat_with_row_success(self):
        mock_response_text = "Yes, the document confirms X."
        self.mock_runner_instance.run.return_value = [
            self._create_mock_event(mock_response_text, is_final=True, author='chat_agent')
        ]

        row_index = 0
        user_message = "Tell me more about X."
        response = self.service.chat_with_row(row_index, user_message)

        self.mock_runner_instance.run.assert_called_once()
        self.assertEqual(response, mock_response_text)
        
        self.mock_runner_instance.session_service.get_session.assert_called_once()
        self.mock_runner_instance.session_service.create_session.assert_called_once()

    def test_chat_with_row_no_target_pdfs(self):
        self.service.target_pdf_uris = [] # Clear target PDFs
        row_index = 0
        user_message = "Tell me more about X."
        response = self.service.chat_with_row(row_index, user_message)

        self.assertIn("No target documents loaded", response)
        self.mock_runner_instance.run.assert_not_called()

    @patch('services.compliance_service.time.sleep')
    @patch('services.compliance_service.ComplianceService.analyze_row')
    def test_batch_analyze_success(self, mock_analyze_row, mock_sleep):
        # Configure mock_analyze_row to return structured response for each call
        mock_analyze_row.side_effect = [
            """
            **RISPOSTA:** Sì
            **CONFIDENZA:** 90%
            **GIUSTIFICAZIONE:** Compliance found for Q1.
            """,
            """
            **RISPOSTA:** No
            **CONFIDENZA:** 50%
            **GIUSTIFICAZIONE:** Non-compliance for Q2.
            """
        ]
        
        # Since analyze_row is mocked, we need to manually simulate df updates
        def mock_analyze_row_side_effect(row_idx, question):
            if row_idx == 0:
                self.service.checklist_df.at[0, 'Risposta'] = 'Sì'
                self.service.checklist_df.at[0, 'Confidenza'] = 90
                self.service.checklist_df.at[0, 'Giustificazione'] = 'Compliance found for Q1.'
                self.service.checklist_df.at[0, 'Status'] = 'DRAFT'
            elif row_idx == 1:
                self.service.checklist_df.at[1, 'Risposta'] = 'No'
                self.service.checklist_df.at[1, 'Confidenza'] = 50
                self.service.checklist_df.at[1, 'Giustificazione'] = 'Non-compliance for Q2.'
                self.service.checklist_df.at[1, 'Status'] = 'DRAFT'
            return "Mocked raw response"

        mock_analyze_row.side_effect = mock_analyze_row_side_effect

        result = self.service.batch_analyze(max_items=2)

        self.assertEqual(result['total_processed'], 2)
        self.assertEqual(mock_analyze_row.call_count, 2)
        # Check if sleep was called between items
        mock_sleep.assert_called_once_with(2) 

        # Verify final DataFrame state
        self.assertEqual(self.service.checklist_df.at[0, 'Risposta'], 'Sì')
        self.assertEqual(self.service.checklist_df.at[1, 'Risposta'], 'No')
        self.assertEqual(self.service.checklist_df.at[0, 'Status'], 'DRAFT')
        self.assertEqual(self.service.checklist_df.at[1, 'Status'], 'DRAFT')

    def test_batch_analyze_no_checklist(self):
        self.service.checklist_df = None
        result = self.service.batch_analyze(max_items=1)
        self.assertIn("No checklist loaded", result['error'])
        self.mock_runner_instance.run.assert_not_called()

    def test_batch_analyze_no_pdf(self):
        self.service.target_pdf_uris = []
        result = self.service.batch_analyze(max_items=1)
        self.assertIn("No PDF loaded", result['error'])
        self.mock_runner_instance.run.assert_not_called()

    @patch('services.compliance_service.time.sleep')
    @patch('services.compliance_service.ComplianceService.analyze_row')
    def test_batch_analyze_skips_processed(self, mock_analyze_row, mock_sleep):
        self.service.checklist_df.at[0, 'Status'] = 'APPROVED' # Mark first item as processed

        def mock_analyze_row_side_effect(row_idx, question):
            self.service.checklist_df.at[row_idx, 'Risposta'] = 'Answer'
            self.service.checklist_df.at[row_idx, 'Status'] = 'DRAFT'
            return "Mocked raw response"
        mock_analyze_row.side_effect = mock_analyze_row_side_effect


        result = self.service.batch_analyze(max_items=2)

        self.assertEqual(result['total_processed'], 1) # Only second item should be processed
        self.assertEqual(mock_analyze_row.call_count, 1) # analyze_row called only once
        # Should be called for row 1
        self.assertEqual(self.service.checklist_df.at[0, 'Status'], 'APPROVED') # First item untouched
        self.assertEqual(self.service.checklist_df.at[1, 'Status'], 'DRAFT') # Second item processed
        mock_analyze_row.assert_called_once_with(1, 'Is Y compliant?')
        mock_sleep.assert_not_called() # Only one item processed, no delay needed


if __name__ == '__main__':
    unittest.main()
