# API Reference

This section provides a detailed API reference for the `ComplianceService` class, which serves as the primary interface for interacting with the Checklist Agent's backend logic.

## `ComplianceService` Class

*   **File**: `services/compliance_service.py`
*   **Purpose**: Manages document loading, checklist processing, and orchestrates interactions with the ADK multi-agent system. It acts as a facade between the Streamlit UI and the core AI logic.

### Constructor

`__init__(self, auth_mode: str = "API_KEY")`

*   **Description**: Initializes the `ComplianceService`. Sets up the Gemini API client, the PDF loader, and the ADK runner with the `ComplianceOrchestrator`.
*   **Parameters**:
    *   `auth_mode` (`str`, optional): The authentication mode for accessing Google APIs.
        *   `"API_KEY"` (default): Uses `GOOGLE_API_KEY` from environment variables.
        *   `"ADC"`: Uses Application Default Credentials, recommended for Google Cloud deployments.
*   **Raises**: `ValueError` if `GOOGLE_API_KEY` is not set when `auth_mode="API_KEY"` or if an unsupported `auth_mode` is provided.

### Properties

`pdf_uri` (`str` or `None`)

*   **Description**: (Backward compatibility) Returns the URI of the *first* uploaded target PDF, or `None` if no target PDFs are loaded.
*   **Type**: Read-only property.

`pdf_uris` (`List[Dict[str, str]]`)

*   **Description**: (Backward compatibility) Returns a list of dictionaries, where each dictionary contains `filename` and `uri` for all loaded context and target PDFs.
*   **Type**: Read-only property.

`id_column` (`str` or `None`)

*   **Description**: The detected column name for the ID field in the loaded checklist.
*   **Type**: Read-only property.

`question_column` (`str` or `None`)

*   **Description**: The detected column name for the question field in the loaded checklist.
*   **Type**: Read-only property.

`description_column` (`str` or `None`)

*   **Description**: The detected column name for the description field in the loaded checklist.
*   **Type**: Read-only property.

### Methods

`load_context_pdf(self, file_path: str) -> str`

*   **Description**: Uploads a PDF file as a CONTEXT document (e.g., regulation, policy). These documents define the rules.
*   **Parameters**:
    *   `file_path` (`str`): The local path to the PDF file to upload.
*   **Returns**: (`str`) The Gemini File API URI of the uploaded PDF.
*   **Raises**: `Exception` if the upload fails.

`load_target_pdf(self, file_path: str) -> str`

*   **Description**: Uploads a PDF file as a TARGET document (e.g., document to be analyzed). These documents are verified against the rules.
*   **Parameters**:
    *   `file_path` (`str`): The local path to the PDF file to upload.
*   **Returns**: (`str`) The Gemini File API URI of the uploaded PDF.
*   **Raises**: `Exception` if the upload fails.

`load_checklist(self, file_path: Any) -> pd.DataFrame`

*   **Description**: Loads an Excel (`.xlsx`, `.xls`) or CSV (`.csv`) checklist file. It intelligently detects ID, Question, and Description columns based on common naming patterns. Adds or initializes standard columns for AI results (`Risposta`, `Confidenza`, `Giustificazione`, `Status`, `Discussion_Log`). Filters out rows with empty questions.
*   **Parameters**:
    *   `file_path` (`Any`): The path to the checklist file (`str`) or a Streamlit `UploadedFile` object.
*   **Returns**: (`pd.DataFrame`) The processed checklist DataFrame.

`get_question_from_row(self, row_index: int) -> str`

*   **Description**: Extracts the question text for a given row index from the loaded checklist DataFrame using the detected question column.
*   **Parameters**:
    *   `row_index` (`int`): The 0-based index of the row in the DataFrame.
*   **Returns**: (`str`) The question text.

`get_description_from_row(self, row_index: int) -> str`

*   **Description**: Extracts the description text for a given row index from the loaded checklist DataFrame using the detected description column.
*   **Parameters**:
    *   `row_index` (`int`): The 0-based index of the row in the DataFrame.
*   **Returns**: (`str`) The description text, or an empty string if not available.

`batch_analyze(self, max_items: int = 3) -> Dict[str, Any]`

*   **Description**: Analyzes a batch of checklist items. Currently processes up to `max_items` and only 'PENDING' items. Includes a delay between items to avoid rate limiting.
*   **Parameters**:
    *   `max_items` (`int`, optional): The maximum number of items to process in the batch. Defaults to 3.
*   **Returns**: (`Dict[str, Any]`) A dictionary summarizing the batch processing results, including `total_processed` and a list of `results` for each item.
*   **Note**: This method is designed for internal use within the Streamlit UI's batch processing tab.

`chat_with_row(self, row_index: int, user_message: str) -> str`

*   **Description**: Allows for an interactive chat with the AI about a specific checklist item. Provides context from the question, description, and the current AI analysis (if any).
*   **Parameters**:
    *   `row_index` (`int`): The 0-based index of the row being discussed.
    *   `user_message` (`str`): The user's message or question for the AI.
*   **Returns**: (`str`) The AI's response to the user's message.

`analyze_row(self, row_index: int, question: str) -> str`

*   **Description**: Initiates the AI analysis for a single checklist item. This method constructs the prompt, invokes the `ComplianceOrchestrator` agent, parses the structured response, and updates the checklist DataFrame.
*   **Parameters**:
    *   `row_index` (`int`): The 0-based index of the row to analyze.
    *   `question` (`str`): The question text for the current row.
*   **Returns**: (`str`) The raw final response text from the Auditor agent.

`get_dataframe(self) -> pd.DataFrame`

*   **Description**: Returns the current state of the checklist DataFrame, including all original and AI-generated columns.
*   **Returns**: (`pd.DataFrame`) The checklist DataFrame.

### Internal Methods (Not for Direct External Use)

`_get_or_create_session(self, user_id: str, session_id: str)`

*   **Description**: Helper method to ensure an ADK session exists for a given `user_id` and `session_id`. Creates a new session if one does not exist, initializing it with context and target PDF information.
*   **Parameters**:
    *   `user_id` (`str`): The ID of the user (e.g., "user_default").
    *   `session_id` (`str`): A unique ID for the session (typically `session_row_{index}` or `chat_row_{index}`).

`_parse_response(self, response_text: str) -> dict`

*   **Description**: Parses the raw string response from the Auditor agent, extracting structured fields like `risposta`, `confidenza`, and `giustificazione`.
*   **Parameters**:
    *   `response_text` (`str`): The raw text output from the Auditor.
*   **Returns**: (`dict`) A dictionary containing the parsed fields.
