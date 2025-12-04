import streamlit as st
import pandas as pd
import os
from services.compliance_service import ComplianceService
from utils.logger import logger

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

# Initialize selected row
if "selected_row" not in st.session_state:
    st.session_state.selected_row = 0

# Sidebar
with st.sidebar:
    st.title("🔍 Compliance Agent")
    
    st.markdown("---")
    st.subheader("1️⃣ Upload Documents")
    
    # PDF Upload - Multiple files
    uploaded_pdfs = st.file_uploader(
        "Policy Documents (PDF)", 
        type="pdf",
        accept_multiple_files=True,
        help="Upload one or more PDF documents"
    )
    
    if uploaded_pdfs:
        if st.button("📤 Process PDFs", use_container_width=True):
            with st.spinner(f"Uploading {len(uploaded_pdfs)} PDF(s)..."):
                for uploaded_pdf in uploaded_pdfs:
                    temp_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    
                    uri = service.load_pdf(temp_path)
                    os.remove(temp_path)
                
                st.success(f"✅ {len(uploaded_pdfs)} PDF(s) Loaded")
    
    # Show loaded PDFs
    if service.pdf_uris:
        with st.expander(f"📚 Loaded PDFs ({len(service.pdf_uris)})", expanded=False):
            for i, uri in enumerate(service.pdf_uris, 1):
                st.caption(f"{i}. {uri}")

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
    
    # Activity Monitor
    st.markdown("---")
    st.subheader("📊 Activity Log")
    
    with st.expander("Recent Activity", expanded=False):
        activities = logger.get_recent_activities(limit=10)
        if activities:
            for activity in activities:
                level = activity['level']
                emoji = {
                    "INFO": "ℹ️",
                    "SUCCESS": "✅",
                    "WARNING": "⚠️",
                    "ERROR": "❌"
                }.get(level, "•")
                
                st.markdown(f"{emoji} **{activity['timestamp']}** - {activity['message']}")
                if activity.get('details'):
                    st.caption(activity['details'])
        else:
            st.info("No recent activity")
    
    if st.button("Clear Activity Log", use_container_width=True):
        logger.clear_activities()
        st.rerun()

# Main Area - 3 Column Layout
if "checklist_df" in st.session_state:
    df = st.session_state.checklist_df
    
    if mode == "Batch (First 3)":
        # Batch Mode (full width)
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
        # Single Item Mode - 3 Column Layout
        col_left, col_center, col_right = st.columns([1, 2, 2])
        
        with col_left:
            st.subheader("🎯 Row Selection")
            
            # Row selector
            row_indices = df.index.tolist()
            selected_row = st.selectbox(
                "Select Row:",
                row_indices,
                index=st.session_state.selected_row if st.session_state.selected_row < len(row_indices) else 0,
                key="row_selector"
            )
            st.session_state.selected_row = selected_row
            
            # Show selected row details
            if selected_row is not None:
                st.markdown("---")
                st.markdown("**Selected Item:**")
                if service.id_column:
                    st.caption(f"ID: {df.at[selected_row, service.id_column]}")
                st.caption(f"Status: {df.at[selected_row, 'Status']}")
                
                question = service.get_question_from_row(selected_row)
                st.markdown(f"**Question:**")
                st.info(question)
                
                if st.button("🔍 Analyze This Row", use_container_width=True, type="primary"):
                    logger.info(f"User requested analysis for row {selected_row}")
                    with st.spinner("Agent is analyzing..."):
                        response = service.analyze_row(selected_row, question)
                        st.session_state.checklist_df = service.get_dataframe()
                        st.rerun()
        
        with col_center:
            st.subheader("📋 Checklist")
            
            # Display Data Grid
            st.dataframe(df, width='stretch', height=600)
        
        with col_right:
            st.subheader("💬 Chat")
            
            if selected_row is not None:
                st.caption(f"Discussing Row {selected_row}")
                
                # Chat History Key per row
                chat_key = f"chat_history_{selected_row}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []
                
                # Chat container with fixed height
                chat_container = st.container(height=500)
                
                with chat_container:
                    # Display History
                    for msg in st.session_state[chat_key]:
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])
                
                # Chat Input (always visible at bottom)
                if prompt := st.chat_input("Ask about this compliance item..."):
                    logger.info(f"User chat for row {selected_row}", prompt[:100])
                    
                    # Add user message
                    st.session_state[chat_key].append({"role": "user", "content": prompt})
                    
                    # Get Agent Response
                    with st.spinner("Thinking..."):
                        response = service.chat_with_row(selected_row, prompt)
                    
                    # Add agent message
                    st.session_state[chat_key].append({"role": "assistant", "content": response})
                    st.rerun()

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
