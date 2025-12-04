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
1. The exact text snippet (50-200 words) that answers the question
2. The document name
3. The page number or section if available

Format your response as:
**Snippet:**
"[Exact text from document - 50-200 words that directly answer the question]"

**Fonte:** [Document name, Page/Section]

IMPORTANT:
- Include the ACTUAL TEXT from the document, not just a reference
- The snippet should be long enough to understand the context
- If multiple relevant sections exist, provide the most relevant one
- If the information is not found, state clearly:
  "Nessuna informazione trovata nel documento relativa a questa domanda."

Do NOT interpret or evaluate compliance - just report what the document says with the actual text.
"""
    )

