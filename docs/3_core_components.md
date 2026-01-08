# Core Components

This section provides a detailed look into the individual components that make up the Checklist Agent, including the specialized AI agents, the central `ComplianceService`, and the structure of the Streamlit user interface.

## 1. AI Agents

The Checklist Agent leverages Google's Agent Development Kit (ADK) to define and orchestrate three primary agents, each with a distinct role.

### 1.1. ComplianceOrchestrator

*   **File**: `agents/orchestrator.py`
*   **Type**: Custom `SequentialAgent` (subclass of ADK's `SequentialAgent`)
*   **Purpose**: To define the fixed sequence of operations for analyzing a checklist item. It acts as the traffic controller, ensuring the Librarian performs its task before the Auditor begins its evaluation.
*   **Key Logic**:
    *   Instantiates the `Librarian` and `Auditor` agents.
    *   Configures them as `sub_agents` in a sequential flow.
    *   The `ComplianceOrchestrator` is designed as a custom class to avoid potential ADK "app name mismatch" errors when using a library agent as the root of the application's agent tree.
*   **Creation Function**: `create_orchestrator_agent(model_name: str = "gemini-3-flash-preview") -> SequentialAgent`
    *   `model_name`: Specifies the LLM model to be used by the sub-agents (though the orchestrator itself doesn't directly use an LLM for reasoning).

### 1.2. Librarian

*   **File**: `agents/librarian.py`
*   **Type**: `LlmAgent`
*   **Purpose**: To meticulously search through uploaded PDF documents (both Context and Target) and extract relevant text snippets, along with their sources. Its primary function is information retrieval and grounding, without interpretation.
*   **Prompt Philosophy**: "The Archivist." Focuses on objective data extraction and citation.
*   **Key Instructions**:
    *   Clearly distinguishes between `CONTEXT` documents (rules) and `TARGET` documents (content to verify).
    *   Requires actual text snippets (50-200 words each) from both document types.
    *   Strictly enforces citation of source `Filename` and `Page/Section` if available.
    *   **Anti-hallucination Rule**: Absolutely forbidden from inventing file names, pages, or sections. Must state "Fonte non disponibile" if not explicitly provided.
    *   Explicitly instructed *not* to interpret or evaluate compliance.
*   **Output Format**: Structured as `**Context (Rules):**` and `**Target (Compliance):**` sections, each with text snippets and sources.
*   **Creation Function**: `create_librarian_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent`
    *   `model_name`: The LLM model used for document understanding and information extraction.

### 1.3. Auditor

*   **File**: `agents/auditor.py`
*   **Type**: `LlmAgent`
*   **Purpose**: To receive the objective evidence from the Librarian and perform a compliance assessment. It interprets the evidence, forms a judgment, and provides a structured, justified response.
*   **Prompt Philosophy**: "The Cynical Compliance Specialist." Trusts nothing without proof and demands rigorous evidence.
*   **Key Instructions**:
    *   Receives `CONTEXT` rules, `TARGET` content, and a `CHECKLIST QUESTION`.
    *   **Strict Output Format**: MUST adhere to a precise structure including `**RISPOSTA:**`, `**CONFIDENZA:**`, and `**GIUSTIFICAZIONE:**` (with sub-sections for `Spiegazione`, `Context Rule`, `Target Evidence`, `Fonte Context`, `Fonte Target`).
    *   **Concise RISPOSTA**: Emphasizes brevity for the `RISPOSTA` field (e.g., "Sì", "No", specific dates/names). All details go into `GIUSTIFICAZIONE`.
    *   **Descriptive Questions**: Provides specific guidance for questions asking for descriptions (e.g., "descrivere", "spiega") to ensure a summary response rather than a simple Yes/No.
    *   **Confidence Scoring**: Defines clear ranges for confidence percentages based on evidence quality.
    *   **Anti-hallucination Rule**: Similar to the Librarian, strictly forbids inventing sources. Must use *only* sources explicitly provided by the Librarian.
    *   Defines a fallback response if no evidence is found.
*   **Creation Function**: `create_auditor_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent`
    *   `model_name`: The LLM model used for reasoning, interpretation, and response generation.

## 2. Compliance Service

*   **File**: `services/compliance_service.py`
*   **Purpose**: This class acts as a central facade, abstracting the complexities of the ADK agents and Streamlit's session management from the main UI logic. It orchestrates file uploads, checklist processing, and agent interactions.
*   **Key Responsibilities**:
    *   **Initialization**: Sets up the Gemini API client, the `PDFLoader`, and the ADK `InMemoryRunner` with the `ComplianceOrchestrator`. Handles `API_KEY` vs `ADC` authentication.
    *   **PDF Management**: Provides methods (`load_context_pdf`, `load_target_pdf`) to upload PDF files to the Gemini File API and store their URIs.
    *   **Checklist Management**:
        *   `load_checklist`: Reads Excel/CSV files, performs intelligent column detection (for `ID`, `Question`, `Description`), filters invalid rows, and adds required AI result columns (`Risposta`, `Confidenza`, `Giustificazione`, `Status`, `Discussion_Log`).
        *   `get_question_from_row`, `get_description_from_row`: Helper methods to extract text from the checklist based on detected columns.
    *   **Agent Interaction**:
        *   `analyze_row`: Prepares the prompt for a single checklist item, invokes the ADK `runner` with the `ComplianceOrchestrator`, parses the structured response, and updates the `checklist_df`.
        *   `chat_with_row`: Handles interactive follow-up conversations for a specific checklist item, providing conversational context to the agents.
        *   `batch_analyze`: (Planned for V2, currently a placeholder) Orchestrates the analysis of multiple checklist items sequentially.
    *   **Session Management**: Uses `_get_or_create_session` to ensure an ADK session exists for each checklist row, maintaining conversational history and state isolation.
    *   **Response Parsing**: `_parse_response` extracts structured fields (`Risposta`, `Confidenza`, `Giustificazione`) from the raw text output of the `Auditor`.
    *   **State Management**: Holds the `checklist_df`, `context_pdf_uris`, and `target_pdf_uris` in its internal state, which is then typically stored in Streamlit's `st.session_state`.
*   **Dependencies**: `google.genai.Client`, `google.adk.runners.InMemoryRunner`, `utils.pdf_loader.PDFLoader`, `utils.logger.logger`, `pandas`.

## 3. Streamlit User Interface (UI) Structure

*   **File**: `app.py`
*   **Purpose**: Provides the interactive web interface for the Checklist Agent, built using the Streamlit framework. It handles user input (file uploads, selections), displays results, and manages the overall application flow.
*   **Key Sections**:
    *   **Page Configuration**: Sets `st.set_page_config` for a wide layout and page title.
    *   **CSS Loading**: Integrates custom CSS (`assets/style.css`) for styling, including font (Inter) and Ant Design components.
    *   **Service Initialization**: Creates and stores an instance of `ComplianceService` in `st.session_state`, ensuring it persists across reruns.
    *   **Wizard Mode (`mostra_wizard`)**: A step-by-step setup guide for initial file uploads (checklist, context PDFs, target PDFs). This is the default entry point.
    *   **Main Interface (`mostra_interfaccia_principal`)**:
        *   **Sidebar**: Contains upload widgets for all document types, quick stats, and action buttons (New Analysis, Export Results).
        *   **Tabbed Layout**: Uses `streamlit_antd_components` for a professional tabbed interface, separating different functionalities:
            *   **Dashboard**: Overview of checklist progress and interactive data editor for checklist items.
            *   **Analyze & Discuss**: Dedicated area for single-item analysis, displaying AI results, and providing a chat interface for follow-up questions.
            *   **Batch Analysis**: Interface for initiating and monitoring batch processing of checklist items.
            *   **Activity Logs**: Displays recent actions logged by the system, offering transparency into agent operations.
    *   **State Management**: Extensively uses `st.session_state` to maintain the application's state across user interactions and Streamlit reruns, including the `ComplianceService` instance, the `checklist_df`, selected rows, and chat histories.
    *   **File Handling**: Manages the upload of `st.file_uploader` objects, writing them to temporary files before passing to `ComplianceService`, and then cleaning up.
*   **Dependencies**: `streamlit`, `pandas`, `os`, `time`, `streamlit_antd_components`, `services.compliance_service`.
