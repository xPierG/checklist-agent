# Checklist Agent - ADK Compliance Assistant

An AI-powered compliance verification tool that analyzes documents against regulatory requirements using Google's Agent Development Kit (ADK).

## Overview

The Checklist Agent helps verify compliance by analyzing **target documents** against **regulatory requirements** (context documents) and answering structured checklist questions.

### 3-Document Architecture

The system works with three distinct document categories:

1.  **📚 Context Documents** (Regulations/Policies)
    -   Define the rules and compliance requirements
    -   Examples: GDPR regulation, ISO standards, company policies
    -   Optional but recommended for accurate verification

2.  **📋 Checklist** (Excel/CSV)
    -   Contains the questions to verify
    -   Structured format with ID, Question, Category columns
    -   Auto-generates AI response columns

3.  **📄 Target Documents** (Documents to Analyze)
    -   The actual content being verified for compliance
    -   Examples: Privacy manual, security documentation, procedures
    -   These are checked against the context rules

### How It Works

```
Context Documents (Rules) + Target Documents (Content) 
    ↓
Multi-Agent Analysis (Librarian + Auditor)
    ↓
Structured Responses (Answer + Confidence + Justification)
    ↓
Updated Checklist with AI Insights
```

## Features

-   **3-Document Workflow**: Separate context (rules), checklist (questions), and target (content to verify)
-   **Multi-Agent System**: Librarian finds evidence, Auditor evaluates compliance
-   **Structured Responses**: Each answer includes:
    -   Direct answer to the question
    -   Confidence score (0-100%)
    -   Justification with text snippets from both context and target documents
-   **Flexible Column Detection**: Auto-detects ID and Question columns
-   **Batch Processing**: Analyze multiple items at once
-   **Interactive Chat**: Discuss specific checklist items with the AI
-   **Real-time Logging**: Activity monitor shows what the agent is doing
-   **Multi-PDF Support**: Upload multiple context and target documents

## Prerequisites

-   Python 3.8+
-   Google API Key (for Gemini models)
-   Virtual environment (recommended)

## Installation

```bash
# Clone the repository
cd checklist-agent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

### Authentication Mode

The application supports two authentication modes:

-   **`API_KEY` (Default)**: Uses a Google API Key set in the `GOOGLE_API_KEY` environment variable. This is suitable for local development.
-   **`ADC` (Application Default Credentials)**: Uses Google Cloud's Application Default Credentials. This is the recommended method for deploying to Google Cloud environments like Cloud Run, as it leverages the service account attached to the environment.

To set the authentication mode, set the `AUTH_MODE` environment variable:

```bash
# For API Key authentication (default)
export AUTH_MODE=API_KEY
# Or simply omit it, as API_KEY is the default behavior if GOOGLE_API_KEY is present

# For Application Default Credentials
export AUTH_MODE=ADC
```
```

## Usage

### 1. Start the Application

```bash
source .venv/bin/activate
streamlit run app.py
```

### 2. Upload Documents

**Context Documents (Optional but Recommended)**:
-   Upload regulations, policies, or standards that define the rules
-   Example: GDPR regulation PDF, ISO 27001 standard

**Target Documents (Required)**:
-   Upload the documents you want to verify
-   Example: Company privacy manual, security procedures

**Checklist (Required)**:
-   Upload Excel/CSV file with your questions
-   See `CHECKLIST_FORMAT.md` for format details

### 3. Processing Modes

**Single Item Mode**:
-   Analyze individual checklist items
-   Interactive chat for each item
-   Full control over which items to process

**Batch Mode**:
-   Process first 3 pending items automatically
-   Includes rate limiting delays
-   Shows results for all processed items

### 4. Review Results

The AI generates for each question:
-   **🤖 Risposta**: Direct answer based on evidence
-   **🤖 Confidenza**: Confidence score (0-100%)
-   **🤖 Giustificazione**: 
    -   Context Rule: Text from regulations
    -   Target Evidence: Text from your documents
    -   Sources for both
    -   Explanation of compliance status

## Architecture

### Multi-Agent System

**Orchestrator**: Coordinates the workflow
**Librarian**: Searches documents for relevant information
-   Distinguishes context (rules) from target (content)
-   Provides text snippets from both document types

**Auditor**: Evaluates compliance
-   Verifies target documents against context rules
-   Provides structured responses with confidence scores

### Technology Stack

-   **Frontend**: Streamlit
-   **AI Framework**: Google ADK (Agent Development Kit)
-   **LLM**: Gemini 2.5 Flash Lite / Gemini 3 Pro Preview
-   **Data**: Pandas for checklist management
-   **Logging**: Custom logger with file and activity tracking

## Project Structure

```
checklist-agent/
├── agents/
│   ├── orchestrator.py    # Main coordinator
│   ├── librarian.py       # Document search (context + target)
│   └── auditor.py         # Compliance evaluation
├── services/
│   └── compliance_service.py  # Core business logic
├── utils/
│   ├── pdf_loader.py      # PDF upload handling
│   └── logger.py          # Logging system
├── app.py                 # Streamlit UI
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Example Workflow

1.  **Upload Context**: GDPR regulation PDF
2.  **Upload Target**: Company's data processing manual
3.  **Upload Checklist**: Privacy compliance questions
4.  **Analyze**: "Is there a DPO appointed?"
5.  **Result**:
    -   **Risposta**: "Yes, John Doe is appointed as DPO"
    -   **Confidenza**: 95%
    -   **Giustificazione**:
        -   Context Rule: "Article 37 GDPR requires a DPO for..."
        -   Target Evidence: "Section 3.2 states: John Doe, DPO..."
        -   Explanation: Manual explicitly names DPO as required by GDPR

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Your License Here]
