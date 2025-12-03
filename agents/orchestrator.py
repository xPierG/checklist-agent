from google.adk.agents import LlmAgent, SequentialAgent
from .librarian import create_librarian_agent
from .auditor import create_auditor_agent

class ComplianceOrchestrator(SequentialAgent):
    """
    Custom Orchestrator Agent.
    Subclassing SequentialAgent to ensure the agent is defined in the user's codebase,
    avoiding ADK's 'app name mismatch' error when using library agents as root.
    """
    pass

def create_orchestrator_agent(model_name: str = "gemini-2.5-flash-lite") -> SequentialAgent:
    """
    Creates the Orchestrator agent (as a Sequential Pipeline for V1).
    
    Structure:
    1. Librarian: Finds info.
    2. Auditor: Evaluates info.
    """
    librarian = create_librarian_agent()
    auditor = create_auditor_agent()
    
    # We wrap them in a SequentialAgent to enforce the flow
    # Librarian finds info -> Context is passed to Auditor -> Auditor answers
    return ComplianceOrchestrator(
        name="ComplianceOrchestrator",
        sub_agents=[librarian, auditor],
        description="Coordinates the retrieval and evaluation process."
    )
