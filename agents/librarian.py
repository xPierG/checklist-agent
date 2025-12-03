from google.adk.agents import LlmAgent

def create_librarian_agent(model_name: str = "gemini-2.0-flash-lite") -> LlmAgent:
    """
    Creates the Librarian agent.
    
    Role: The Archivist.
    Task: Has access to the PDF files. Finds relevant paragraphs ("Grounding").
    """
    return LlmAgent(
        name="Librarian",
        model=model_name,
        description="Has access to the documents. Finds relevant paragraphs and information.",
        instruction="""You are The Librarian.
Your goal is to find information in the provided documents.
When asked a question, search the documents in your context and provide the relevant excerpts and page numbers if available.
Do not interpret compliance; just report what the document says.
If the information is not found, state clearly that it is missing.
"""
    )
