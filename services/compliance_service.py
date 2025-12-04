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
        self.context_pdf_uris = []  # Regulations, policies (the rules)
        self.target_pdf_uris = []   # Documents to analyze (content to verify)
        self.current_session_id = None
        
        logger.success("ComplianceService initialized successfully")

    def load_context_pdf(self, file_path: str) -> str:
        """
        Uploads a CONTEXT PDF (regulation/policy) and returns URI.
        These are the documents that define the rules.
        """
        logger.info(f"Loading CONTEXT PDF: {os.path.basename(file_path)}")
        try:
            pdf_uri = self.pdf_loader.upload_and_cache(file_path)
            self.context_pdf_uris.append(pdf_uri)
            logger.success(f"Context PDF uploaded", f"URI: {pdf_uri} (Total context: {len(self.context_pdf_uris)})")
            return pdf_uri
        except Exception as e:
            logger.error(f"Failed to upload context PDF", str(e))
            raise
    
    def load_target_pdf(self, file_path: str) -> str:
        """
        Uploads a TARGET PDF (document to analyze) and returns URI.
        These are the documents to verify against the rules.
        """
        logger.info(f"Loading TARGET PDF: {os.path.basename(file_path)}")
        try:
            pdf_uri = self.pdf_loader.upload_and_cache(file_path)
            self.target_pdf_uris.append(pdf_uri)
            logger.success(f"Target PDF uploaded", f"URI: {pdf_uri} (Total target: {len(self.target_pdf_uris)})")
            return pdf_uri
        except Exception as e:
            logger.error(f"Failed to upload target PDF", str(e))
            raise
    
    @property
    def pdf_uri(self):
        """Backward compatibility: return first target PDF URI or None."""
        return self.target_pdf_uris[0] if self.target_pdf_uris else None
    
    @property
    def pdf_uris(self):
        """Backward compatibility: return all PDFs (context + target)."""
        return self.context_pdf_uris + self.target_pdf_uris

    def load_checklist(self, file_path: str) -> pd.DataFrame:
        """
        Loads Excel checklist with flexible column detection.
        Looks for ID and Question columns using common naming patterns.
        """
        # Handle both file paths and UploadedFile objects
        filename = getattr(file_path, 'name', str(file_path))
        if hasattr(filename, 'split'):
            filename = filename.split('/')[-1]  # Get basename
        
        logger.info(f"Loading checklist: {filename}")
        
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
        question_patterns = ['question', 'requirement', 'item', 'description', 'check', 'domanda']
        question_col = None
        for col in self.checklist_df.columns:
            if col.lower().strip() in question_patterns:
                question_col = col
                break
        
        # Store column mappings
        self.id_column = id_col
        self.question_column = question_col
        
        logger.info(f"Detected columns", f"ID: {id_col}, Question: {question_col}")
        
        # Add status columns if missing - UPDATED for structured responses
        required_cols = {
            'Risposta': '',           # Sì/No/Parziale/?
            'Confidenza': '',         # 0-100%
            'Giustificazione': '',    # Full justification
            'Status': 'PENDING',      # PENDING/DRAFT/APPROVED
            'Discussion_Log': ''      # Chat history
        }
        
        for col, default_value in required_cols.items():
            if col not in self.checklist_df.columns:
                self.checklist_df[col] = default_value
        
        # Initialize Status to PENDING if empty
        if 'Status' in self.checklist_df.columns:
            self.checklist_df['Status'] = self.checklist_df['Status'].replace('', 'PENDING')
        
        logger.success(f"Checklist loaded", f"{len(self.checklist_df)} rows")
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
        
        processed_count = len(results)
        logger.success(f"Batch analysis complete", f"Processed {processed_count} items")
        return {
            "total_processed": processed_count,
            "results": results
        }
    
    def chat_with_row(self, row_index: int, user_message: str) -> str:
        """
        Chat about a specific checklist row.
        Provides context about the question, what context documents say, and what target documents contain.
        """
        logger.info(f"Chat for row {row_index}", user_message[:100])
        
        if not self.target_pdf_uris:
            return "⚠️ No target documents loaded. Please upload documents to analyze."
        
        question = self.get_question_from_row(row_index)
        
        # Build context for chat
        context_docs = "\n".join([f"  - {uri}" for uri in self.context_pdf_uris]) if self.context_pdf_uris else "  (None)"
        target_docs = "\n".join([f"  - {uri}" for uri in self.target_pdf_uris])
        
        # Get current analysis if available
        current_analysis = ""
        if 'Risposta' in self.checklist_df.columns:
            risposta = self.checklist_df.at[row_index, 'Risposta']
            confidenza = self.checklist_df.at[row_index, 'Confidenza']
            giustificazione = self.checklist_df.at[row_index, 'Giustificazione']
            
            if pd.notna(risposta):
                current_analysis = f"""
Current AI Analysis:
- Answer: {risposta}
- Confidence: {confidenza}
- Justification: {giustificazione}
"""
        
        chat_prompt = f"""
You are a helpful compliance assistant. The user is asking about a specific checklist item.

CONTEXT DOCUMENTS (Regulations/Rules):
{context_docs}

TARGET DOCUMENTS (Being Analyzed):
{target_docs}

CHECKLIST QUESTION: {question}

{current_analysis}

USER QUESTION: {user_message}

Provide a helpful answer that:
1. Explains what the CONTEXT documents say about this topic (if available)
2. Explains what the TARGET documents contain related to this topic
3. Answers the user's specific question
4. Uses actual text snippets when possible

Be conversational and helpful. If you need to search the documents, do so and provide specific quotes.
"""
        
        user_id = "user_default"
        session_id = f"chat_row_{row_index}"
        
        self._get_or_create_session(user_id, session_id)
        
        content = types.Content(role='user', parts=[types.Part(text=chat_prompt)])
        
        try:
            response = asyncio.run(
                self.orchestrator.send_message(
                    user_id=user_id,
                    session_id=session_id,
                    content=content
                )
            )
            
            response_text = response.parts[0].text if response.parts else "No response"
            logger.success(f"Chat response for row {row_index}", response_text[:100])
            return response_text
            
        except Exception as e:
            logger.error(f"Chat failed for row {row_index}", str(e))
            return f"Error: {str(e)}"

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
             # Create new session with context and target PDF URIs
             asyncio.run(self.session_service.create_session(
                app_name="agents", 
                user_id=user_id, 
                session_id=session_id,
                state={
                    "context_pdf_uris": self.context_pdf_uris,
                    "target_pdf_uris": self.target_pdf_uris
                }
            ))

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse structured response from agent.
        Extracts: Risposta, Confidenza, Giustificazione
        """
        import re
        
        result = {
            'risposta': '?',
            'confidenza': '0%',
            'giustificazione': response_text  # Fallback to full text
        }
        
        # Extract RISPOSTA
        risposta_match = re.search(r'\*\*RISPOSTA:\*\*\s*([^\n]+)', response_text, re.IGNORECASE)
        if risposta_match:
            result['risposta'] = risposta_match.group(1).strip()
        
        # Extract CONFIDENZA
        conf_match = re.search(r'\*\*CONFIDENZA:\*\*\s*([0-9]+)%?', response_text, re.IGNORECASE)
        if conf_match:
            result['confidenza'] = f"{conf_match.group(1)}%"
        
        # Extract GIUSTIFICAZIONE (everything after the keyword)
        giust_match = re.search(r'\*\*GIUSTIFICAZIONE:\*\*\s*(.+)', response_text, re.IGNORECASE | re.DOTALL)
        if giust_match:
            result['giustificazione'] = giust_match.group(1).strip()
        
        return result

    def analyze_row(self, row_index: int, question: str) -> str:
        """
        Runs the agent on a specific row.
        """
        logger.info(f"Analyzing row {row_index}", question[:100])
        
        if not self.target_pdf_uris:
            logger.error("Analysis failed: No target PDFs loaded")
            return "Error: No target documents loaded. Please upload documents to analyze."

        user_id = "user_default"
        session_id = f"session_row_{row_index}"
        
        self._get_or_create_session(user_id, session_id)

        # Construct prompt with context and target documents
        context_docs = "\n".join([f"  - {uri}" for uri in self.context_pdf_uris]) if self.context_pdf_uris else "  (None - analyzing without regulatory context)"
        target_docs = "\n".join([f"  - {uri}" for uri in self.target_pdf_uris])
        
        prompt = f"""
        You are analyzing TARGET documents for compliance.
        
        CONTEXT DOCUMENTS (Regulations/Policies - The Rules):
        {context_docs}
        
        TARGET DOCUMENTS (Documents to Verify):
        {target_docs}
        
        CHECKLIST QUESTION: {question}
        
        TASK: Verify if the TARGET documents comply with the requirements.
        If CONTEXT documents are provided, use them to understand the rules.
        Otherwise, answer based on general best practices.
        
        Provide a structured response with answer, confidence, and justification including text snippets.
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
        
        # Parse structured response
        parsed = self._parse_response(final_response)
        
        # Update DataFrame with structured fields
        self.checklist_df.at[row_index, 'Risposta'] = parsed['risposta']
        self.checklist_df.at[row_index, 'Confidenza'] = parsed['confidenza']
        self.checklist_df.at[row_index, 'Giustificazione'] = parsed['giustificazione']
        self.checklist_df.at[row_index, 'Status'] = 'DRAFT'
        
        logger.success(f"Row {row_index} analyzed", f"Answer: {parsed['risposta']}, Confidence: {parsed['confidenza']}")
        
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
