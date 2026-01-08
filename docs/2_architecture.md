# Architecture Overview

The Checklist Agent is built upon a robust multi-agent architecture powered by Google's Agent Development Kit (ADK). This design allows for a clear separation of concerns, enabling each agent to specialize in a specific task, leading to more modular, scalable, and understandable AI workflows.

## Multi-Agent System Design

The core of the application utilizes a **Hierarchical Sequential Pipeline** pattern. This means that tasks are broken down into a series of steps, and each step is handled by a specialized agent. The flow is deterministic, ensuring that information is processed in a structured manner from retrieval to evaluation.

### Architecture Diagram

```
User Request
      ↓
+-----------------------+
| ComplianceOrchestrator| (SequentialAgent)
|   - Coordinates workflow|
+-----------------------+
      ↓
+-----------------------+
|       Librarian       | (LlmAgent)
|   - Document Retrieval|
|   - Extracts Evidence |
+-----------------------+
      ↓
+-----------------------+
|        Auditor        | (LlmAgent)
|   - Compliance Eval   |
|   - Generates Response|
+-----------------------+
      ↓
Structured Response to User
```

## Workflow: Orchestrator, Librarian, Auditor

The system's intelligence is distributed across three primary agents: the **Orchestrator**, the **Librarian**, and the **Auditor**.

### 1. ComplianceOrchestrator

*   **Type**: `SequentialAgent` (custom subclass `ComplianceOrchestrator`)
*   **Role**: The primary workflow coordinator.
*   **Responsibility**: The Orchestrator is the entry point for the agentic workflow. It ensures that user requests (e.g., "analyze this checklist item") are routed through the correct sequence of specialized sub-agents. For V1, this means a fixed sequence: first, the Librarian, then the Auditor. This prevents "app name mismatch" errors and simplifies the initial implementation.
*   **Key Function**: `agents/orchestrator.py` (`create_orchestrator_agent` function)

### 2. Librarian

*   **Type**: `LlmAgent`
*   **Role**: The Document Retrieval Specialist / Archivist.
*   **Responsibility**: The Librarian's sole purpose is to access the uploaded PDF documents (both Context and Target) and find information relevant to the checklist question. It *does not* interpret compliance or make judgments. Its task is to:
    *   Identify relevant paragraphs or sections.
    *   Extract direct text snippets (grounding).
    *   Provide source information (filename, page/section) for each snippet.
    *   Distinguish between information from "CONTEXT" documents (rules) and "TARGET" documents (content being checked).
*   **Personality**: Factual, meticulous, unbiased.
*   **Key Function**: `agents/librarian.py` (`create_librarian_agent` function)

### 3. Auditor

*   **Type**: `LlmAgent`
*   **Role**: The Compliance Risk Specialist.
*   **Responsibility**: The Auditor receives the raw, sourced information from the Librarian. Its task is to evaluate this evidence against the checklist question and provide a structured compliance assessment. The Auditor:
    *   Analyzes the provided text snippets from both Context and Target documents.
    *   Determines if the Target documents comply with the Context rules based on the evidence.
    *   Generates a concise answer (`RISPOSTA`).
    *   Assigns a confidence score (`CONFIDENZA`).
    *   Provides a detailed justification (`GIUSTIFICAZIONE`), which includes its reasoning, quotes from the documents, and their sources.
    *   It is designed with a "cynical, trust-nothing-without-proof" personality to encourage rigorous evaluation.
*   **Personality**: Cynical, rigorous, evidence-driven.
*   **Key Function**: `agents/auditor.py` (`create_auditor_agent` function)

## Data Flow and Processing

The interaction between the user, the Streamlit UI, the `ComplianceService`, and the agents follows a defined flow:

1.  **User Input**:
    *   User uploads PDF documents (Context and Target) via the Streamlit UI. These are temporarily stored locally, uploaded to the Gemini File API, and their URIs are stored in the `ComplianceService` session state.
    *   User uploads a checklist (Excel/CSV). The `ComplianceService` parses it, detects columns, and initializes new columns for AI results (`Risposta`, `Confidenza`, `Giustificazione`, `Status`).

2.  **Request Initiation**:
    *   When the user clicks "Analyze Row" or "Start Batch," the Streamlit UI calls a method on the `ComplianceService` (e.g., `analyze_row`).
    *   A unique ADK session is created or retrieved for each checklist item (`session_row_{index}`), ensuring isolated conversations and state.

3.  **Agent Orchestration**:
    *   The `ComplianceService` constructs a prompt containing the checklist question, description, and the URIs of the loaded Context and Target documents.
    *   This prompt is sent to the `ComplianceOrchestrator` agent via the `InMemoryRunner`.
    *   The `ComplianceOrchestrator` first invokes the `Librarian`. The Librarian accesses the documents (via the Gemini File API using the provided URIs) and extracts relevant, sourced snippets.
    *   The output from the `Librarian` (the sourced snippets) is then passed as input to the `Auditor`.
    *   The `Auditor` processes this information, applies its compliance evaluation logic, and generates a structured response (`RISPOSTA`, `CONFIDENZA`, `GIUSTIFICAZIONE`).

4.  **Result Processing**:
    *   The structured response from the `Auditor` is returned to the `ComplianceService`.
    *   The `ComplianceService` parses this response and updates the corresponding row in the checklist DataFrame with the AI's answer, confidence, and justification.
    *   The item's `Status` is updated to `DRAFT`.

5.  **User Interaction (Chat)**:
    *   If the user engages in a chat for a specific row, the `chat_with_row` method in `ComplianceService` is called.
    *   A context-rich prompt (including the original question, document URIs, and previous AI analysis) along with the user's new question is sent to the Orchestrator (which, in this case, will likely route directly to the Auditor for conversational follow-ups).
    *   The Auditor responds, and the conversation is maintained in a row-specific chat history in the Streamlit session state.

This robust pipeline ensures that document retrieval, evidence gathering, and compliance evaluation are handled systematically and transparently.
