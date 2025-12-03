import os
import pandas as pd
from typing import Dict, Any, List
from dotenv import load_dotenv
from google.genai import Client
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator import create_orchestrator_agent
from utils.pdf_loader import PDFLoader

# Load environment variables
load_dotenv()

class ComplianceService:
    """
    Facade for the Compliance Agent system.
    Handles session management, file loading, and agent execution.
    """
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = Client(api_key=api_key)
        self.pdf_loader = PDFLoader(self.client)
        
        # ADK Setup
        self.agent = create_orchestrator_agent()
        self.session_service = InMemorySessionService()
        self.runner = InMemoryRunner(self.agent, app_name="compliance_app", session_service=self.session_service)
        
        # State
        self.checklist_df = None
        self.pdf_uri = None
        self.current_session_id = None

    def load_pdf(self, file_path: str) -> str:
        """Uploads PDF and returns URI."""
        self.pdf_uri = self.pdf_loader.upload_and_cache(file_path)
        return self.pdf_uri

    def load_checklist(self, file_path: str) -> pd.DataFrame:
        """Loads Excel checklist."""
        self.checklist_df = pd.read_excel(file_path)
        # Add status columns if missing
        required_cols = ['AI_Proposal', 'Discussion_Log', 'Final_Answer', 'Status']
        for col in required_cols:
            if col not in self.checklist_df.columns:
                self.checklist_df[col] = ""
        return self.checklist_df

    def analyze_row(self, row_index: int, question: str) -> str:
        """
        Runs the agent on a specific row.
        """
        if not self.pdf_uri:
            return "Error: No PDF loaded."

        user_id = "user_default"
        session_id = f"session_row_{row_index}"
        
        # Ensure session exists
        try:
            self.session_service.get_session("compliance_app", user_id, session_id).blocking_get()
        except:
             self.session_service.create_session(
                "compliance_app", 
                user_id, 
                session_id,
                state={"pdf_uri": self.pdf_uri} # Pass PDF context to agents via state if needed
            ).blocking_get()

        # Construct prompt
        # We need to explicitly tell the Librarian to look at the PDF URI
        # For V1, we might just inject the URI into the prompt or rely on the agent having access to the client
        # Ideally, we attach the file to the request.
        
        prompt = f"""
        Context Document URI: {self.pdf_uri}
        
        Checklist Question: {question}
        
        Please analyze the document and determine compliance.
        """
        
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        
        # Run Synchronously for V1 simplicity (or async if Streamlit supports it well)
        # ADK runner.run returns an iterator of events
        events = self.runner.run(user_id, session_id, content)
        
        final_response = ""
        for event in events:
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text
        
        # Update DataFrame
        self.checklist_df.at[row_index, 'AI_Proposal'] = final_response
        self.checklist_df.at[row_index, 'Status'] = 'DRAFT'
        
        return final_response

    def chat_with_row(self, row_index: int, message: str) -> str:
        """
        Continues the conversation for a specific row.
        """
        user_id = "user_default"
        session_id = f"session_row_{row_index}"
        
        content = types.Content(role='user', parts=[types.Part(text=message)])
        events = self.runner.run(user_id, session_id, content)
        
        final_response = ""
        for event in events:
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text
                
        return final_response

    def get_dataframe(self) -> pd.DataFrame:
        return self.checklist_df
