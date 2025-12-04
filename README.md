# ADK Compliance Agent

A multi-agent compliance platform built with Google's Agent Development Kit (ADK), Gemini 2.5/3.0, and Streamlit. This tool assists auditors by analyzing documents against a checklist using a "Collaborative Intelligence" approach.

## Features
*   **Multi-Agent Architecture**: Uses an Orchestrator, Librarian, and Auditor agent team.
*   **Document Grounding**: Uploads PDFs to Gemini and retrieves relevant context for every answer.
*   **Interactive Chat**: Discuss specific checklist items with the agent to refine the assessment.
*   **Draft & Validate**: Workflow to propose answers and validate them manually.

## Prerequisites
*   Python 3.10+
*   Google Cloud Project with Gemini API enabled.
*   `GOOGLE_API_KEY` environment variable.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd checklist-agent
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Copy the example file and add your API key:
    ```bash
    cp .env.example .env
    # Edit .env and set GOOGLE_API_KEY
    ```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

### Processing Modes

#### Single Item Mode
1.  **Upload PDF**: Upload the policy or technical document you want to audit.
2.  **Upload Checklist**: Upload an Excel file containing the audit questions.
3.  **Analyze**: Select a row and click "Analyze" to get an initial AI assessment.
4.  **Chat**: Use the chat interface to ask follow-up questions or request more evidence.

#### Batch Mode (First 3 Items)
1.  **Upload PDF and Checklist**: Same as above.
2.  **Select Batch Mode**: Choose "Batch (First 3)" in the sidebar.
3.  **Start Batch**: Click "Start Batch Analysis" to process the first 3 pending items automatically.
4.  **Review Results**: Expand each item to see the AI's assessment.

### Checklist Format

Your Excel file should contain:
- **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`
- **Question Column**: `Question`, `Requirement`, `Item`, `Description`, or `Check`

The system will auto-detect these columns. See `CHECKLIST_FORMAT.md` for full details and `example_checklist.csv` for a sample.

## Architecture

*   **Frontend**: Streamlit (Python-native UI).
*   **Backend**: `ComplianceService` facade managing ADK agents.
*   **Agents**:
    *   `Orchestrator`: Manages the workflow.
    *   `Librarian`: Finds information in the PDF.
    *   `Auditor`: Evaluates compliance based on evidence.

## Features

*   **Flexible Column Detection**: Automatically detects ID and Question columns using common naming patterns
*   **Batch Processing**: Process multiple checklist items at once
*   **Dual-Mode Interface**: Switch between single-item and batch processing
*   **Contextual Chat**: Discuss specific items with the AI agent
*   **Status Tracking**: Track progress with PENDING/DRAFT/APPROVED states
