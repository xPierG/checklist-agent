import asyncio
import os
import time
import pandas as pd
from typing import Dict, Any, List
from dotenv import load_dotenv
from google.genai import Client
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator import create_orchestrator_agent
from utils.pdf_loader import PDFLoader
from utils.logger import logger

# Load environment variables
load_dotenv()

class ComplianceService:
    """
    Facade for the Compliance Agent system.
    Handles session management, file loading, and agent execution.
    """
    def __init__(self):
        logger.info("Initializing ComplianceService")
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment")
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = Client(api_key=api_key)
        self.pdf_loader = PDFLoader(self.client)
        
        # ADK Setup
        logger.info("Setting up ADK agents")
        self.agent = create_orchestrator_agent()
        self.runner = InMemoryRunner(self.agent, app_name="agents")
        self.session_service = self.runner.session_service
        
        # State
        self.checklist_df = None
        self.pdf_uri = None
        self.current_session_id = None
        
        logger.success("ComplianceService initialized successfully")

    def load_pdf(self, file_path: str) -> str:
        """Uploads PDF and returns URI."""
        logger.info(f"Loading PDF: {os.path.basename(file_path)}")
        try:
            self.pdf_uri = self.pdf_loader.upload_and_cache(file_path)
            logger.success(f"PDF uploaded successfully", f"URI: {self.pdf_uri}")
            return self.pdf_uri
        except Exception as e:
            logger.error(f"Failed to upload PDF", str(e))
            raise

    def load_checklist(self, file_path: str) -> pd.DataFrame:
        """
        Loads Excel checklist with flexible column detection.
        Looks for ID and Question columns using common naming patterns.
        """
        # Force all columns to be strings to avoid PyArrow inference issues
        self.checklist_df = pd.read_excel(file_path, dtype=str)
        # Replace "nan" strings with empty string if any
        self.checklist_df = self.checklist_df.replace("nan", "")
        
        # Detect ID column (case-insensitive)
        id_patterns = ['id', 'item_id', 'item id', 'number', 'no', '#']
        id_col = None
        for col in self.checklist_df.columns:
            if col.lower().strip() in id_patterns:
                id_col = col
                break
        
        # Detect Question column (case-insensitive)
        question_patterns = ['question', 'requirement', 'item', 'description', 'check']
        question_col = None
        for col in self.checklist_df.columns:
            if col.lower().strip() in question_patterns:
                question_col = col
                break
        
        # Store column mappings
        self.id_column = id_col
        self.question_column = question_col
        
        # Add status columns if missing
        required_cols = ['AI_Proposal', 'Discussion_Log', 'Final_Answer', 'Status']
        for col in required_cols:
            if col not in self.checklist_df.columns:
                self.checklist_df[col] = ""
        
        # Initialize Status to PENDING if empty
        if 'Status' in self.checklist_df.columns:
            self.checklist_df['Status'] = self.checklist_df['Status'].replace('', 'PENDING')
        
        return self.checklist_df
    
    def get_question_from_row(self, row_index: int) -> str:
        """Extract question text from a row using detected column."""
        if self.question_column and self.question_column in self.checklist_df.columns:
            return str(self.checklist_df.at[row_index, self.question_column])
        # Fallback: try to find any column that looks like a question
        for col in self.checklist_df.columns:
            if col not in ['AI_Proposal', 'Discussion_Log', 'Final_Answer', 'Status', self.id_column]:
                return str(self.checklist_df.at[row_index, col])
        return "No question found"
    
    def batch_analyze(self, max_items: int = 3) -> Dict[str, Any]:
        """
        Analyzes the first N items in the checklist in batch.
        Returns a summary of results.
        """
        logger.info(f"Starting batch analysis", f"Max items: {max_items}")
        
        if self.checklist_df is None:
            logger.error("Batch analysis failed: No checklist loaded")
            return {"error": "No checklist loaded"}
        
        if not self.pdf_uri:
            logger.error("Batch analysis failed: No PDF loaded")
            return {"error": "No PDF loaded"}
        
        results = []
        total_items = min(max_items, len(self.checklist_df))
        logger.info(f"Processing {total_items} items")
        
        for idx in range(total_items):
            # Skip if already processed
            if self.checklist_df.at[idx, 'Status'] not in ['PENDING', '']:
                logger.info(f"Skipping item {idx}", "Already processed")
                continue
                
            question = self.get_question_from_row(idx)
            item_id = self.checklist_df.at[idx, self.id_column] if self.id_column else str(idx)
            
            logger.info(f"Analyzing item {item_id}", question[:100])
            
            try:
                response = self.analyze_row(idx, question)
                results.append({
                    "index": idx,
                    "id": item_id,
                    "question": question,
                    "response": response,
                    "status": "success"
                })
                logger.success(f"Item {item_id} analyzed successfully")
                
                # Add delay between items to avoid rate limiting
                if idx < total_items - 1:  # Don't delay after last item
                    logger.info("Waiting 2s to avoid rate limiting")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to analyze item {item_id}", str(e))
                results.append({
                    "index": idx,
                    "id": item_id,
                    "question": question,
                    "error": str(e),
                    "status": "error"
                })
        
        logger.success(f"Batch analysis complete", f"Processed {len(results)} items")
        return {
            "total_processed": len(results),
            "results": results
        }

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
