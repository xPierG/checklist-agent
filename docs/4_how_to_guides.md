# How-To Guides

This section provides practical guides for developers looking to extend or customize the Checklist Agent.

## 1. Modify Agent Prompts

The behavior of the `Librarian` and `Auditor` agents is primarily controlled by their system instructions (prompts). Modifying these prompts allows you to fine-tune their responses, reasoning, and adherence to specific output formats.

### Locate the Agent Definition

1.  **Librarian Agent**: Open `agents/librarian.py`. The prompt is defined within the `instruction` parameter of the `LlmAgent` constructor.
2.  **Auditor Agent**: Open `agents/auditor.py`. The prompt is defined within the `instruction` parameter of the `LlmAgent` constructor.

### Best Practices for Prompt Modification

*   **Clarity and Specificity**: Be extremely clear and specific in your instructions. Avoid ambiguity.
*   **Structured Output**: If you require a specific output format (like the Auditor's `**RISPOSTA:**`, `**CONFIDENZA:**`, `**GIUSTIFICAZIONE:**`), provide examples and explicitly state that the agent *MUST* adhere to this format.
*   **Role-Playing**: Start with a clear role definition (e.g., "You are The Librarian, an archivist...").
*   **Constraints**: Clearly define what the agent should *not* do (e.g., "Do NOT interpret or evaluate compliance").
*   **Anti-Hallucination**: Emphasize rules for source citation and what to do if information is not found (as already present in the current prompts).
*   **Testing**: After modifying a prompt, thoroughly test the agent's behavior with various inputs to ensure it performs as expected and that no unintended side effects are introduced.

### Example: Adjusting Auditor's Tone

Suppose you want the Auditor to be less "cynical" and more "supportive."

**Original (`agents/auditor.py` excerpt):**
```python
def create_auditor_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent:
    """
    Creates the Auditor agent.
    Role: The Compliance Specialist.
    Task: Evaluates compliance based on the information provided.
    """
    return LlmAgent(
        name="Auditor",
        model=model_name,
        description="Evaluates compliance risks and answers questions based on evidence.",
        instruction="""You are The Auditor, a cynical risk compliance specialist.
... 
Trust nothing without proof. Be precise and professional.
"""
    )
```

**Modified:**
```python
def create_auditor_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent:
    """
    Creates the Auditor agent.
    Role: The Compliance Specialist.
    Task: Evaluates compliance based on the information provided.
    """
    return LlmAgent(
        name="Auditor",
        model=model_name,
        description="Evaluates compliance and provides helpful feedback based on evidence.",
        instruction="""You are The Auditor, a helpful and objective compliance specialist.
Your goal is to verify if TARGET documents comply with CONTEXT rules.
... 
Base your assessments strictly on the evidence. Be precise and professional.
"""
    )
```
In this example, changing "cynical" to "helpful and objective" and "Trust nothing without proof" to "Base your assessments strictly on the evidence" will subtly shift the agent's persona.

## 2. Add a New Agent

The `SequentialAgent` structure in the `Orchestrator` makes it straightforward to introduce new agents into the processing pipeline.

### Scenario: Adding a "Summarizer" Agent

Let's say you want to add a `Summarizer` agent that takes the Auditor's justification and condenses it into a short, executive summary before the final response is returned to the user.

1.  **Create the New Agent File**:
    Create a new file, `agents/summarizer.py`:
    ```python
    from google.adk.agents import LlmAgent

    def create_summarizer_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent:
        """
        Creates a Summarizer agent.
        Role: Condenses detailed justifications into concise summaries.
        """
        return LlmAgent(
            name="Summarizer",
            model=model_name,
            description="Summarizes detailed compliance justifications.",
            instruction="""You are a professional Summarizer.
The user will provide a detailed compliance justification.
Your task is to condense this justification into a concise, executive summary of no more than 3 sentences.
Focus on the key finding, the compliance status, and the primary evidence.
Output ONLY the summary.
""",
            output_key="executive_summary" # This will be the key in the session state
        )
    ```

2.  **Integrate into the Orchestrator**:
    Open `agents/orchestrator.py` and modify the `create_orchestrator_agent` function:

    *   Import the new agent: `from .summarizer import create_summarizer_agent`
    *   Instantiate the new agent.
    *   Add it to the `sub_agents` list in the desired position.

    **Original (`agents/orchestrator.py` excerpt):**
    ```python
    from google.adk.agents import LlmAgent, SequentialAgent
    from .librarian import create_librarian_agent
    from .auditor import create_auditor_agent

    class ComplianceOrchestrator(SequentialAgent):
        """Custom Orchestrator Agent."""
        pass

    def create_orchestrator_agent(model_name: str = "gemini-3-flash-preview") -> SequentialAgent:
        librarian = create_librarian_agent()
        auditor = create_auditor_agent()
        
        return ComplianceOrchestrator(
            name="ComplianceOrchestrator",
            sub_agents=[librarian, auditor],
            description="Coordinates the retrieval and evaluation process."
        )
    ```

    **Modified (`agents/orchestrator.py`):**
    ```python
    from google.adk.agents import LlmAgent, SequentialAgent
    from .librarian import create_librarian_agent
    from .auditor import create_auditor_agent
    from .summarizer import create_summarizer_agent # <--- New Import

    class ComplianceOrchestrator(SequentialAgent):
        """Custom Orchestrator Agent."""
        pass

    def create_orchestrator_agent(model_name: str = "gemini-3-flash-preview") -> SequentialAgent:
        librarian = create_librarian_agent()
        auditor = create_auditor_agent()
        summarizer = create_summarizer_agent() # <--- New Agent Instance
        
        return ComplianceOrchestrator(
            name="ComplianceOrchestrator",
            sub_agents=[librarian, auditor, summarizer], # <--- Added Summarizer here
            description="Coordinates the retrieval, evaluation, and summarization process."
        )
    ```

3.  **Update the `ComplianceService` (if needed)**:
    If the new agent produces an output that you want to display in the UI or store in the checklist DataFrame, you'll need to modify `services/compliance_service.py`:
    *   The `analyze_row` method currently expects the final response from the last agent in the pipeline to be a structured string that `_parse_response` can handle.
    *   If your `Summarizer` agent produces `executive_summary` in the session state, you would access it from `event.session.state.get("executive_summary")` and update the DataFrame accordingly. You might introduce a new column in your checklist, e.g., `Executive Summary`.

    This involves adapting the `_parse_response` function or adding new logic in `analyze_row` to handle the `executive_summary` output key from the `Summarizer` agent.

## 3. Extend the Streamlit UI

Adding new features or modifying the layout of the Streamlit application is done primarily in `app.py`.

### Basic Principles

*   **`st.session_state`**: Use `st.session_state` for any data that needs to persist across Streamlit reruns (e.g., `checklist_df`, `service` instance, chat history).
*   **Reruns**: Streamlit reruns the entire script from top to bottom on every user interaction. Design your code to be idempotent and efficient.
*   **Widgets**: Use Streamlit widgets (`st.button`, `st.selectbox`, `st.text_input`, etc.) for user interaction.
*   **Layout**: Use `st.sidebar`, `st.columns`, `st.expander`, `st.container` to structure your layout.
*   **`streamlit_antd_components`**: For a more polished look, use components from this library (e.g., `sac.tabs`, `sac.segmented`).

### Scenario: Adding a "Configuration" Tab

Let's add a new tab to the main interface where users can view (and potentially edit) some application settings.

1.  **Modify Tab Definition**:
    Open `app.py`. Locate the `sac.tabs` definition within `mostra_interfaccia_principal()`.

    **Original (`app.py` excerpt):**
    ```python
    with st.container():
        selected_tab = sac.tabs([
            sac.TabsItem(label='DASHBOARD', icon='clipboard-data'),
            sac.TabsItem(label='ANALYZE & DISCUSS', icon='robot'),
            sac.TabsItem(label='BATCH ANALYSIS', icon='box-seam'),
            sac.TabsItem(label='ACTIVITY LOGS', icon='terminal'),
        ], format_func='title', align='center', variant='outline')
    ```

    **Modified (`app.py`):**
    ```python
    with st.container():
        selected_tab = sac.tabs([
            sac.TabsItem(label='DASHBOARD', icon='clipboard-data'),
            sac.TabsItem(label='ANALYZE & DISCUSS', icon='robot'),
            sac.TabsItem(label='BATCH ANALYSIS', icon='box-seam'),
            sac.TabsItem(label='ACTIVITY LOGS', icon='terminal'),
            sac.TabsItem(label='CONFIGURATION', icon='gear'), # <--- New Tab
        ], format_func='title', align='center', variant='outline')
    ```

2.  **Add Tab Content Logic**:
    Add a new `elif` block for the new tab's content.

    **Original (`app.py` excerpt):**
    ```python
    # ... other tabs ...

    # --- TAB 4: ACTIVITY LOGS ---
    elif selected_tab == 'ACTIVITY LOGS':
        st.subheader("📝 Activity Logs")
        # ... content ...
    ```

    **Modified (`app.py`):**
    ```python
    # ... other tabs ...

    # --- TAB 4: ACTIVITY LOGS ---
    elif selected_tab == 'ACTIVITY LOGS':
        st.subheader("📝 Activity Logs")
        # ... content ...

    # --- TAB 5: CONFIGURATION ---
    elif selected_tab == 'CONFIGURATION':
        st.subheader("⚙️ Application Configuration")
        st.write("Here you can view and modify application settings.")

        with st.container(border=True):
            st.markdown("##### Current Environment Variables (Example)")
            st.code(f"GOOGLE_API_KEY = {'Set' if os.environ.get('GOOGLE_API_KEY') else 'Not Set'}\nAUTH_MODE = {os.environ.get('AUTH_MODE', 'API_KEY')}")

            st.markdown("##### Model Settings (Future Feature)")
            st.info("Dynamic model selection for agents could be implemented here in a future version.")
            # Example for future dynamic model selection
            # new_model = st.selectbox("Select Auditor Model", ["gemini-3-flash-preview", "gemini-3-pro-preview"])
            # if st.button("Apply Model Change"):
            #     st.session_state.service.set_auditor_model(new_model)
            #     st.toast("Model updated! Restart analysis for changes to take effect.")
    ```

3.  **Advanced UI Integration**:
    For more complex interactions (e.g., dynamically changing agent models), you might need to add methods to the `ComplianceService` to handle those changes and propagate them to the ADK agents.

## 4. Change AI Models

The models used by the `Librarian` and `Auditor` agents are configured in their respective `create_*_agent` functions.

### How to Change Models

1.  **Locate Model Definitions**:
    *   `agents/librarian.py`: `create_librarian_agent` function.
    *   `agents/auditor.py`: `create_auditor_agent` function.
    *   `agents/orchestrator.py`: `create_orchestrator_agent` (it passes the model name to sub-agents, or sub-agents define their own).

2.  **Modify `model_name`**:
    Simply change the `model` parameter in the `LlmAgent` constructor or the `model_name` argument in the agent creation function.

    **Example: Changing Librarian to a different model**
    ```python
    # agents/librarian.py
    from google.adk.agents import LlmAgent

    def create_librarian_agent(model_name: str = "gemini-3-flash-preview") -> LlmAgent: # <-- can change default here
        """
        Creates the Librarian agent.
        """
        return LlmAgent(
            name="Librarian",
            model="gemini-3-pro-preview", # <--- Directly specify a different model
            description="Has access to the documents. Finds relevant paragraphs and information.",
            # ... rest of instruction ...
        )
    ```

3.  **Considerations**:
    *   **Cost**: Different models have different pricing.
    *   **Performance**: Larger models might be slower but potentially more accurate.
    *   **Availability**: Ensure the model you select is available in your region and project.
    *   **System Prompt Length**: Some models have limits on instruction length.
    *   **Output Consistency**: Changes in models might require adjustments to prompts or parsing logic if the output format changes slightly.

This allows for easy experimentation and optimization of the agent's performance by swapping out the underlying LLM.
