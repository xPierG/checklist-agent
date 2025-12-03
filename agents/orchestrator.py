from google.adk.agents import LlmAgent, SequentialAgent
from .librarian import create_librarian_agent
from .auditor import create_auditor_agent

def create_orchestrator_agent(model_name: str = "gemini-1.5-flash") -> SequentialAgent:
    """
    Creates the Orchestrator agent (as a Sequential Pipeline for V1).
    
    Structure:
    1. Librarian: Finds info.
    2. Auditor: Evaluates info.
    
    In a more complex V2, this could be a custom agent that decides who to call.
    For the checklist batch process, a sequential flow is often best:
    Get Context -> Evaluate.
    """
    librarian = create_librarian_agent()
    auditor = create_auditor_agent()
    
    # We wrap them in a SequentialAgent to enforce the flow
    # Librarian finds info -> Context is passed to Auditor -> Auditor answers
    return SequentialAgent(
        name="ComplianceOrchestrator",
        sub_agents=[librarian, auditor],
        description="Coordinates the retrieval and evaluation process."
    )
