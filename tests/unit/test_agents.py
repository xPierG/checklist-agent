import unittest
from unittest.mock import MagicMock, patch
from agents.orchestrator import create_orchestrator_agent
from agents.librarian import create_librarian_agent
from agents.auditor import create_auditor_agent
from google.adk.agents import LlmAgent, SequentialAgent

class TestAgentCreation(unittest.TestCase):

    def test_create_librarian_agent(self):
        agent = create_librarian_agent(model_name="test-model-librarian")
        self.assertIsInstance(agent, LlmAgent)
        self.assertEqual(agent.name, "Librarian")
        self.assertEqual(agent.model, "test-model-librarian")
        self.assertIn("Finds relevant paragraphs and information", agent.description)
        self.assertIn("You are The Librarian.", agent.instruction)

    def test_create_auditor_agent(self):
        agent = create_auditor_agent(model_name="test-model-auditor")
        self.assertIsInstance(agent, LlmAgent)
        self.assertEqual(agent.name, "Auditor")
        self.assertEqual(agent.model, "test-model-auditor")
        self.assertIn("Evaluates compliance risks and answers questions based on evidence.", agent.description)
        self.assertIn("You are The Auditor, a cynical risk compliance specialist.", agent.instruction)

    @patch('agents.orchestrator.create_librarian_agent')
    @patch('agents.orchestrator.create_auditor_agent')
    def test_create_orchestrator_agent(self, mock_create_auditor, mock_create_librarian):
        mock_librarian_agent = MagicMock(spec=LlmAgent)
        mock_auditor_agent = MagicMock(spec=LlmAgent)
        
        # Mock parent_agent attribute which SequentialAgent tries to access
        mock_librarian_agent.parent_agent = None
        mock_auditor_agent.parent_agent = None
        
        mock_create_librarian.return_value = mock_librarian_agent
        mock_create_auditor.return_value = mock_auditor_agent

        orchestrator = create_orchestrator_agent(model_name="test-model-orchestrator")
        
        self.assertIsInstance(orchestrator, SequentialAgent)
        self.assertEqual(orchestrator.name, "ComplianceOrchestrator")
        self.assertEqual(orchestrator.description, "Coordinates the retrieval and evaluation process.")
        
        mock_create_librarian.assert_called_once()
        mock_create_auditor.assert_called_once()

        self.assertEqual(len(orchestrator.sub_agents), 2)
        self.assertIs(orchestrator.sub_agents[0], mock_librarian_agent)
        self.assertIs(orchestrator.sub_agents[1], mock_auditor_agent)

if __name__ == '__main__':
    unittest.main()
