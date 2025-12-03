import asyncio
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
        self.runner = InMemoryRunner(self.agent, app_name="agents")
        self.session_service = self.runner.session_service
        
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
        # Force all columns to be strings to avoid PyArrow inference issues
        self.checklist_df = pd.read_excel(file_path, dtype=str)
        # Replace "nan" strings with empty string if any
        self.checklist_df = self.checklist_df.replace("nan", "")
        
        # Add status columns if missing
        required_cols = ['AI_Proposal', 'Discussion_Log', 'Final_Answer', 'Status']
        for col in required_cols:
            if col not in self.checklist_df.columns:
                self.checklist_df[col] = ""
        return self.checklist_df

    def _get_or_create_session(self, user_id: str, session_id: str):
        """Helper to ensure session exists."""
        session = None
        try:
            # Check if session exists
            session = asyncio.run(self.session_service.get_session(
                app_name="agents", 
                user_id=user_id, 
                session_id=session_id
            ))
        except Exception:
            pass
            
        if session is None:
             # Create new session
             asyncio.run(self.session_service.create_session(
                app_name="agents", 
                user_id=user_id, 
                session_id=session_id,
                state={"pdf_uri": self.pdf_uri}
            ))

    def analyze_row(self, row_index: int, question: str) -> str:
        """
        Runs the agent on a specific row.
        """
        if not self.pdf_uri:
            return "Error: No PDF loaded."

        user_id = "user_default"
        session_id = f"session_row_{row_index}"
        
        self._get_or_create_session(user_id, session_id)

        # Construct prompt
        prompt = f"""
        Context Document URI: {self.pdf_uri}
        
        Checklist Question: {question}
        
        Please analyze the document and determine compliance.
        """
        
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        
        # Run Synchronously
        events = self.runner.run(
            user_id=user_id, 
            session_id=session_id, 
            new_message=content
        )
        
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
        
        self._get_or_create_session(user_id, session_id)
        
        content = types.Content(role='user', parts=[types.Part(text=message)])
        events = self.runner.run(
            user_id=user_id, 
            session_id=session_id, 
            new_message=content
        )
        
        final_response = ""
        for event in events:
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text
                
        return final_response

    def get_dataframe(self) -> pd.DataFrame:
        return self.checklist_df
