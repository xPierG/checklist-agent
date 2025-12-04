import streamlit as st
import pandas as pd
import os
from services.compliance_service import ComplianceService

# Page Config
st.set_page_config(layout="wide", page_title="ADK Compliance Agent")

# Initialize Service in Session State
if "service" not in st.session_state:
    try:
        st.session_state.service = ComplianceService()
        st.success("✅ Compliance Service Initialized")
    except Exception as e:
        st.error(f"Failed to initialize service: {e}")
        st.stop()

service = st.session_state.service

# Sidebar
with st.sidebar:
    st.title("🔍 Compliance Agent")
    
    st.markdown("---")
    st.subheader("1️⃣ Upload Documents")
    
    # PDF Upload
    uploaded_pdf = st.file_uploader("Policy Document (PDF)", type="pdf")
    if uploaded_pdf:
        # Save to temp file
        temp_path = f"temp_{uploaded_pdf.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        
        if st.button("📤 Process PDF", use_container_width=True):
            with st.spinner("Uploading to Gemini..."):
                uri = service.load_pdf(temp_path)
                st.success(f"✅ PDF Loaded")
                os.remove(temp_path)

    # Checklist Upload
    uploaded_excel = st.file_uploader("Checklist (Excel)", type=["xlsx", "xls", "csv"])
    if uploaded_excel:
        if st.button("📊 Load Checklist", use_container_width=True):
            df = service.load_checklist(uploaded_excel)
            st.session_state.checklist_df = df
            
            # Show detected columns
            if service.id_column:
                st.success(f"✅ ID Column: `{service.id_column}`")
            if service.question_column:
                st.success(f"✅ Question Column: `{service.question_column}`")
            
            if not service.question_column:
                st.warning("⚠️ Could not auto-detect question column. See CHECKLIST_FORMAT.md")
    
    st.markdown("---")
    st.subheader("2️⃣ Processing Mode")
    
    mode = st.radio(
        "Choose mode:",
        ["Single Item", "Batch (First 3)"],
        help="Single: Analyze one item at a time. Batch: Process first 3 pending items."
    )

# Main Area
if "checklist_df" in st.session_state:
    df = st.session_state.checklist_df
    
    if mode == "Batch (First 3)":
        # Batch Mode
        st.header("📦 Batch Processing Mode")
        
        st.info("This will analyze the first 3 PENDING items in your checklist. Processing includes 2-second delays between items to respect API rate limits (~6 seconds total).")
        
        # Show preview
        pending_df = df[df['Status'] == 'PENDING'].head(3)
        if len(pending_df) > 0:
            st.subheader("Items to Process")
            st.dataframe(pending_df, width='stretch')
            
            if st.button("🚀 Start Batch Analysis", type="primary"):
                with st.spinner("Processing batch..."):
                    results = service.batch_analyze(max_items=3)
                    
                    if "error" in results:
                        st.error(f"Error: {results['error']}")
                    else:
                        st.success(f"✅ Processed {results['total_processed']} items")
                        
                        # Show results
                        for result in results['results']:
                            with st.expander(f"Item {result['id']}: {result['question'][:50]}..."):
                                if result['status'] == 'success':
                                    st.markdown("**Response:**")
                                    st.write(result['response'])
                                else:
                                    st.error(f"Error: {result.get('error', 'Unknown error')}")
                        
                        # Refresh dataframe
                        st.session_state.checklist_df = service.get_dataframe()
                        st.rerun()
        else:
            st.info("No pending items to process.")
        
        # Show full checklist
        st.subheader("Full Checklist")
        st.dataframe(df, width='stretch')
    
    else:
        # Single Item Mode
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 Checklist")
            
            # Display Data Grid
            st.dataframe(df, width='stretch')
            
            # Row Selection
            row_indices = df.index.tolist()
            selected_row = st.selectbox("Select Row to Analyze/Discuss", row_indices)
            
            if st.button("🔍 Analyze Selected Row"):
                question = service.get_question_from_row(selected_row)
                with st.spinner("Agent is analyzing..."):
                    response = service.analyze_row(selected_row, question)
                    st.session_state.checklist_df = service.get_dataframe() # Refresh
                    st.rerun()

        with col2:
            st.subheader("💬 Contextual Chat")
            if selected_row is not None:
                st.info(f"Discussing Row {selected_row}")
                
                # Chat History Key per row
                chat_key = f"chat_history_{selected_row}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []
                
                # Display History
                for msg in st.session_state[chat_key]:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
                
                # Chat Input
                if prompt := st.chat_input("Ask about this compliance item..."):
                    # Add user message
                    st.session_state[chat_key].append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    # Get Agent Response
                    with st.spinner("Thinking..."):
                        response = service.chat_with_row(selected_row, prompt)
                    
                    # Add agent message
                    st.session_state[chat_key].append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.write(response)

else:
    st.info("👈 Please upload a checklist to begin.")
    
    # Show format help
    with st.expander("📖 Checklist Format Guide"):
        st.markdown("""
        ### Required Columns
        Your Excel file should have:
        - **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`
        - **Question Column**: `Question`, `Requirement`, `Item`, `Description`, or `Check`
        
        ### Example
        | ID | Question | Status |
        |----|----------|--------|
        | 1  | Is there a DPO appointed? | PENDING |
        | 2  | Are access controls documented? | PENDING |
        
        See `CHECKLIST_FORMAT.md` for full details.
        """)

