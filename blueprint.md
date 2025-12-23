# **PROJECT BLUEPRINT V5: ADK Multi-Agent Compliance System**

## **1. Project Overview**

A compliance assistance platform built with Google Agent Development Kit (ADK) that uses a multi-agent architecture to analyze policy documents against security checklists.

**Core Philosophy**: Collaborative Intelligence - The user doesn't just correct AI output, but engages in dialogue with the agent to understand reasoning and refine responses.

**Current Status**: V1 Implementation Complete
- ✅ Multi-agent architecture (Orchestrator → Librarian → Auditor)
- ✅ PDF document grounding via Gemini File API
- ✅ Excel checklist loading and tracking
- ✅ Row-specific conversational interface
- ✅ Session management per checklist item

---

## **2. Tech Stack**

| Component | Technology | Version/Details |
|-----------|-----------|-----------------|
| **Agent Framework** | Google ADK | Python SDK |
| **AI Models** | Google Gemini | 3-flash-preview (Orchestrator/Librarian/Auditor) |
| **Frontend** | Streamlit | Python-native web UI |
| **Document Processing** | Gemini File API | PDF upload & caching |
| **Data Format** | Excel/Pandas | Checklist I/O |
| **Session Management** | ADK InMemorySessionService | Per-row conversation state |

---

## **3. Multi-Agent Architecture**

### **Architecture Pattern**: Hierarchical Sequential Pipeline

```
User Request → Orchestrator → Librarian → Auditor → Response
                    ↓              ↓           ↓
                 (Routes)      (Searches)  (Evaluates)
```

### **🎯 Agent 1: The Orchestrator (ComplianceOrchestrator)**
- **Type**: `SequentialAgent` (ADK)
- **Model**: `gemini-3-flash-preview`
- **Role**: Workflow coordinator
- **Responsibility**: Routes requests through Librarian → Auditor pipeline
- **Implementation**: `agents/orchestrator.py`

### **📚 Agent 2: The Librarian**
- **Type**: `LlmAgent` (ADK)
- **Model**: `gemini-3-flash-preview`
- **Role**: Document retrieval specialist
- **Responsibility**: 
  - Accesses PDF documents via Gemini File API
  - Finds relevant paragraphs (grounding)
  - Extracts evidence with page numbers
  - Does NOT interpret compliance
- **Implementation**: `agents/librarian.py`

### **⚖️ Agent 3: The Auditor**
- **Type**: `LlmAgent` (ADK)
- **Model**: `gemini-3-flash-preview`
- **Role**: Compliance risk specialist
- **Responsibility**:
  - Evaluates compliance based on Librarian's evidence
  - Provides YES/NO/PARTIAL assessments
  - Explains reasoning with citations
  - Handles follow-up Q&A with user
- **Personality**: Cynical, trust-nothing-without-proof approach
- **Implementation**: `agents/auditor.py`

---

## **4. Data Flow & User Journey**

### **Phase 1: Setup & Ingestion**
1. User uploads PDF policy document
2. System uploads to Gemini File API → receives URI
3. User uploads Excel checklist
4. System adds tracking columns: `AI_Proposal`, `Discussion_Log`, `Final_Answer`, `Status`

### **Phase 2: Initial Analysis**
1. User selects a checklist row
2. Clicks "Analyze Selected Row"
3. System creates row-specific session: `session_row_{index}`
4. Orchestrator pipeline executes:
   - Librarian searches PDF for relevant info
   - Auditor evaluates compliance
5. Response stored in `AI_Proposal` column
6. Status set to `DRAFT`

### **Phase 3: Collaborative Dialogue**
1. User opens contextual chat for selected row
2. Chat history is row-specific (isolated conversations)
3. User can:
   - Ask "Why did you say YES?"
   - Request "Check if RSA is mentioned"
   - Challenge "Are you sure about page 12?"
4. Agent (Auditor) responds with reasoning
5. Can update `AI_Proposal` based on new insights

### **Phase 4: Finalization** *(Planned for V2)*
- User confirms answer → Status becomes `VALIDATED`
- Manual override option
- Export to Excel with full audit trail

---

## **5. UI/UX Specification**

### **Layout**: Wide Mode, Two-Column Split

#### **Sidebar (Left)**
- **Project Controls**:
  - 📄 Upload Policy Document (PDF)
  - 📊 Upload Checklist (Excel)
  - 🔄 Process PDF button
  - 📥 Load Checklist button

#### **Main Area: Column 1 (Checklist Grid)**
- Interactive dataframe display with dynamic column management.
- Includes row number, Status, ID, Question, Description, and AI-generated fields.
- Justification Viewer: A dedicated section to view full justification for selected row.
- Row selection dropdown for individual analysis.
- Real-time status indicators:
  - Empty = Not analyzed
  - `DRAFT` = AI proposal ready
  - `VALIDATED` = User confirmed *(V2)*

#### **Main Area: Column 2 (Contextual Chat)**
- **Header**: "Discussing Row {index}"
- **Chat History**: 
  - Persisted per row in `st.session_state[chat_history_{row_index}]`
  - Displays user/assistant messages
- **Input**: `st.chat_input()` for follow-up questions
- **Future Actions** *(V2)*:
  - ✅ Accept Answer
  - ✏️ Manual Override

---

## **6. Session Management Strategy**

### **Session Isolation**
- Each checklist row gets its own ADK session
- Session ID format: `session_row_{row_index}`
- User ID: `user_default` (single-user V1)

### **Session State**
- Stored in `InMemorySessionService`
- Contains: `{"pdf_uri": "gs://..."}`
- Enables conversation continuity per row

### **Session Lifecycle**
1. Created on first `analyze_row()` or `chat_with_row()`
2. Persists for entire Streamlit session
3. Allows multi-turn dialogue without context loss

---

## **7. Excel Output Specification**

### **Original Columns** (User-provided)
- `Domanda` (Question)
- Other domain-specific columns...

### **Added Columns** (System-generated)

| Column | Purpose | Example Value |
|--------|---------|---------------|
| `Risposta AI` | Agent's direct answer | "Sì" |
| `Confidenza Risposta` | Confidence score (0-100%) | 95% |
| `Spiegazione` | Detailed justification with evidence | "Contesto: Art. 37 GDPR... Evidenza: Sezione 3.2..." |
| `Discussion_Log` | Chat history for the item | "User asked why... Agent clarified..." |
| `Status` | Workflow state | `DRAFT` / `VALIDATED` |

---

## **8. Implementation Details**

### **File Structure**
```
checklist-agent/
├── app.py                          # Streamlit UI
├── services/
│   └── compliance_service.py       # Facade for ADK agents
├── agents/
│   ├── orchestrator.py             # Sequential pipeline
│   ├── librarian.py                # Document retrieval
│   └── auditor.py                  # Compliance evaluation
├── utils/
│   └── pdf_loader.py               # Gemini File API wrapper
├── requirements.txt
├── .env.example
└── README.md
```

### **Key Technical Decisions**

#### **Why SequentialAgent?**
- Enforces Librarian → Auditor flow
- Prevents "app name mismatch" errors
- Simplifies V1 implementation

#### **Why Per-Row Sessions?**
- Isolates conversations
- Prevents context bleeding between checklist items
- Enables parallel analysis in future

#### **Why InMemoryRunner?**
- Simplest ADK deployment for V1
- No external database required
- Sufficient for single-user Streamlit app

#### **Pandas PyArrow Fix**
- Force `dtype=str` on Excel read to avoid type inference issues
- Replace "nan" strings with empty strings

---

## **9. Current Limitations & V2 Roadmap**

### **V1 Limitations**
- ❌ No batch analysis (must analyze rows individually)
- ❌ No answer validation workflow
- ❌ No Excel export with updated data
- ❌ No multi-user support
- ❌ Sessions lost on Streamlit restart

### **V2 Planned Features**
1. **Batch Analysis**: "Analyze All Rows" button
2. **Validation Workflow**:
   - ✅ Accept Answer → Status = `VALIDATED`
   - ✏️ Manual Override → User edits `Final_Answer`
3. **Export**: Download Excel with all columns populated
4. **Discussion Log**: Auto-summarize chat history
5. **Persistent Sessions**: Database-backed session storage
6. **Multi-User**: User authentication & isolation

### **V3 Vision**
- Cloud Run deployment
- Real-time collaboration
- Advanced RAG with vector search
- Audit trail & compliance reporting
- Integration with ticketing systems

---

## **10. Running the Application**

### **Prerequisites**
- Python 3.10+
- Google Cloud Project with Gemini API enabled
- `GOOGLE_API_KEY` environment variable

### **Setup**
```bash
# Clone and navigate
cd checklist-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY
```

### **Run**
```bash
streamlit run app.py
```

### **Usage Flow**
1. Upload PDF document → Click "Process PDF"
2. Upload Excel checklist → Click "Load Checklist"
3. Select a row from dropdown
4. Click "Analyze Selected Row"
5. Use chat to discuss the AI's reasoning
6. Repeat for other rows

---

## **11. Model Selection Rationale**

| Agent | Model | Reasoning |
|-------|-------|-----------|
| **Orchestrator** | gemini-3-flash-preview | Fast routing, low cost |
| **Librarian** | gemini-3-flash-preview | Quick document search, grounding |
| **Auditor** | gemini-3-flash-preview | Deep reasoning, compliance evaluation |

**Cost Optimization**: Use Flash for retrieval, Pro for analysis.

---

## **12. Security & Compliance Considerations**

### **Data Handling**
- PDFs uploaded to Gemini File API (Google-managed storage)
- Temporary local files cleaned up after upload
- No persistent storage of sensitive data in V1

### **Access Control** *(V2)*
- User authentication required
- Row-level access control
- Audit logging

### **DORA Compliance** *(Future)*
- Document all architectural decisions
- Maintain change logs
- Implement incident response procedures

---

## **Appendix: Differences from Original Blueprint**

### **Changes from V4 → V5**
1. **Model Updates**: 
   - V4: gemini-1.5-pro/flash
   - V5: gemini-2.5-flash-lite + gemini-3-pro-preview
2. **Session Management**: Added async/await pattern for session creation
3. **Pandas Fix**: Added dtype handling for PyArrow compatibility
4. **Runner API**: Updated to use named parameters (`user_id`, `session_id`, `new_message`)
5. **Simplified V1 Scope**: Removed batch analysis from initial release

### **Preserved from V4**
- ✅ Multi-agent architecture
- ✅ Collaborative dialogue approach
- ✅ Row-specific chat isolation
- ✅ Sequential pipeline pattern
- ✅ Streamlit UI design
