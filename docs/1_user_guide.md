# User Guide

This guide will walk you through the process of setting up and using the Checklist Agent application.

## Installation and Setup

### Prerequisites

*   Python 3.8+
*   Google API Key (for Gemini models) or Google Cloud Application Default Credentials (ADC)
*   Virtual environment (recommended)

### Steps

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-repo/checklist-agent.git
    cd checklist-agent
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and add your `GOOGLE_API_KEY`.

    ### Authentication Mode

    The application supports two authentication modes, configured via the `AUTH_MODE` environment variable in your `.env` file:

    *   **`API_KEY` (Default)**: Uses a Google API Key. Set `GOOGLE_API_KEY=YOUR_API_KEY_HERE` in your `.env` file. This is suitable for local development.
    *   **`ADC` (Application Default Credentials)**: Uses Google Cloud's Application Default Credentials. This is recommended for deploying to Google Cloud environments (e.g., Cloud Run), as it leverages the service account attached to the environment. To use this, ensure your environment is configured for ADC (e.g., `gcloud auth application-default login`).

    Example `.env` for API Key:
    ```
    GOOGLE_API_KEY=YOUR_API_KEY_HERE
    AUTH_MODE=API_KEY
    ```
    Example `.env` for ADC:
    ```
    AUTH_MODE=ADC
    ```

## Running the Application

Once the setup is complete, you can start the application:

```bash
streamlit run app.py
```

This will open the application in your web browser.

## Application Walkthrough

The Checklist Agent guides you through a wizard for initial document setup and then presents a tabbed interface for analysis.

### Setup Wizard

Upon first launch, you'll be guided through three steps:

1.  **Upload Checklist**: Upload your Excel or CSV file containing the questions/requirements. Refer to the [Checklist Format Specification](#checklist-format-specification) for details on required columns.
2.  **Upload Context (Rules)**: Upload PDF documents containing regulations, policies, or standards that define the rules. These are optional but highly recommended for accurate compliance verification.
3.  **Upload Target (Content)**: Upload PDF documents that contain the actual content you want to verify against the rules. These are required.

After completing the wizard, you will be redirected to the main application interface.

### Main Interface

The main interface is divided into several tabs:

#### 1. DASHBOARD

*   **Progress Overview**: Shows the overall completion rate and counts of items by status (Pending, Draft, Approved, Rejected).
*   **Checklist Table**: Displays your loaded checklist. You can filter items by their status.

#### 2. ANALYZE & DISCUSS

This tab is for focusing on individual checklist items.

*   **Select Row for Analysis**: Choose a specific row from your checklist to analyze.
*   **Analyze Row Button**: Triggers the AI to analyze the selected row using the loaded context and target documents. The AI will provide an answer, confidence score, and detailed justification.
*   **Analysis Result**: Displays the AI's generated answer, confidence, and justification for the selected row.
*   **Chat about this Row**: An interactive chat interface to discuss the analysis with the AI. You can ask follow-up questions, request clarifications, or challenge the AI's reasoning. The chat history is specific to each checklist item.

#### 3. BATCH ANALYSIS

This tab allows you to process multiple checklist items automatically.

*   **Batch Processing Options**:
    *   **All Pending**: Processes all items with a "PENDING" status.
    *   **Range**: Processes items within a specified row range (e.g., rows 1 to 5).
    *   **Specific Rows**: Processes a comma-separated list of specific row numbers.
*   **Start Batch Button**: Initiates the batch analysis. A progress bar will show the status, and a small delay is introduced between items to prevent rate limiting issues.

#### 4. ACTIVITY LOGS

*   Displays a real-time log of the activities performed by the agents, providing transparency into their operations.

## Sidebar Controls

The sidebar (left panel) provides global controls and status information:

*   **Quick Stats**: Summary of loaded rules, content documents, and pending checklist items.
*   **Setup**: Sections for uploading Context PDFs, Target PDFs, and the Checklist.
*   **Actions**:
    *   **New Analysis**: Clears all loaded data and restarts the application (back to the wizard).
    *   **Export Results**: Downloads the current checklist DataFrame, including all AI-generated results and updated statuses, as an Excel file.

## Checklist Format Specification

The Checklist Agent is designed to work with standard Excel (`.xlsx`, `.xls`) or CSV (`.csv`) files.

### Required Columns (Case-Insensitive Detection)

The system automatically detects the following columns based on common naming patterns:

*   **ID Column**: Must contain unique identifiers for each checklist item.
    *   **Recognized Names**: `ID`, `Item_ID`, `Item ID`, `Number`, `No`, `#`
*   **Question Column**: Contains the actual question or requirement to be verified.
    *   **Recognized Names**: `Question`, `Requirement`, `Item`, `Description`, `Check`, `Domanda`
*   **Description Column** (Optional): Provides additional context or details for the AI to better understand the question. This helps the AI to give more specific answers and justifications.
    *   **Recognized Names**: `Description`, `Descrizione`, `Details`, `Dettagli`, `Note`, `Context`

### Auto-Generated Columns (Added by the System)

Upon loading, the system adds or populates the following columns to track the analysis results and workflow status:

*   `**Risposta**`: The AI's direct answer to the question (e.g., "Sì", "No", "Non trovato", or a concise summary).
*   `**Confidenza**`: A confidence score (0-100%) indicating how certain the AI is about its answer based on the evidence.
*   `**Giustificazione**`: A detailed explanation of the AI's reasoning, including text snippets from both context and target documents, and their sources.
*   `**Status**`: The workflow status of the checklist item.
    *   `PENDING`: Item awaiting analysis.
    *   `DRAFT`: Item has been analyzed by AI; review is needed.
    *   `APPROVED`: User has accepted the AI's analysis or manually validated it.
    *   `REJECTED`: User has rejected the AI's analysis.
*   `**Discussion_Log**`: (Planned for V2) Stores the chat history for each checklist item, allowing for an audit trail of the interactive dialogue.

### Best Practices for Checklist Creation

*   **Clear and Specific Questions**: Formulate questions unambiguously.
*   **Unique IDs**: Ensure your ID column has unique values for each row.
*   **One Question Per Row**: Avoid combining multiple questions in a single cell.
*   **No Merged Cells**: Ensure the checklist data is tabular.
*   **First Row as Headers**: The first row of your Excel/CSV file should contain the column headers.

## Interpreting Results

The AI provides a structured output for each checklist item:

*   **`Risposta`**: The concise answer to the question. Pay attention to "Non trovato" or "?" which indicate insufficient evidence.
*   **`Confidenza`**: A higher percentage indicates stronger evidence. Lower confidence suggests ambiguity or lack of direct proof.
*   **`Giustificazione`**: This is the most crucial part. It explains *why* the AI arrived at its answer, citing specific text from your uploaded documents (both context and target). Always review the justification to validate the AI's reasoning. Pay attention to the "Fonte" (Source) information to trace back the evidence.

By reviewing the `Risposta`, `Confidenza`, and `Giustificazione`, you can make informed decisions about the compliance status of each item.
