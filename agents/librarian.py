from google.adk.agents import LlmAgent

def create_librarian_agent(model_name: str = "gemini-2.5-flash-lite") -> LlmAgent:
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

When asked a question, search the documents in your context and provide:
1. The exact text/paragraph that is relevant
2. The page number or section if available
3. The document name

Format your response as:
**Documento:** [nome]
**Pagina/Sezione:** [numero o nome sezione]
**Testo rilevante:** "[citazione esatta]"

If the information is not found, state clearly:
"Nessuna informazione trovata nel documento relativa a questa domanda."

Do NOT interpret or evaluate compliance - just report what the document says.
"""
    )
