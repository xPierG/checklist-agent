import streamlit as st
import pandas as pd
import os
import time
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
    
    # Quick Stats at top
    if service.checklist_df is not None or service.context_pdf_uris or service.target_pdf_uris:
        col1, col2, col3 = st.columns(3)
        col1.metric("📚", len(service.context_pdf_uris), label_visibility="collapsed")
        col2.metric("📄", len(service.target_pdf_uris), label_visibility="collapsed")
        if service.checklist_df is not None:
            pending = len(service.checklist_df[service.checklist_df['Status'] == 'PENDING'])
            col3.metric("⏳", pending, label_visibility="collapsed")
        else:
            col3.metric("📋", 0, label_visibility="collapsed")
    
    st.markdown("---")
    
    # CONTEXT PDFs - Regulations/Policies
    st.markdown("### 🏛️ Rules & Regulations")
    st.caption("Upload policies, standards, regulations")
    
    uploaded_context_pdfs = st.file_uploader(
        "Drop PDFs",
        type="pdf",
        accept_multiple_files=True,
        key="context_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_context_pdfs:
        if st.button("📤 Process Rules", width="stretch", key="process_context"):
            with st.spinner(f"Processing {len(uploaded_context_pdfs)} file(s)..."):
                for uploaded_pdf in uploaded_context_pdfs:
                    temp_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    service.load_context_pdf(temp_path)
                    os.remove(temp_path)
                st.success(f"✅ {len(uploaded_context_pdfs)} rules loaded")
    
    # Compact file list
    if service.context_pdf_uris:
        st.caption(f"**Active:** {len(service.context_pdf_uris)} files")
        for uri in service.context_pdf_uris[:3]:  # Show max 3
            filename = uri.split('/')[-1][:20] if '/' in uri else uri[:20]
            st.caption(f"🟢 {filename}")
        if len(service.context_pdf_uris) > 3:
            st.caption(f"... +{len(service.context_pdf_uris) - 3} more")
    
    st.markdown("---")
    
    # TARGET PDFs - Documents to Analyze
    st.markdown("### 📄 Content to Analyze")
    st.caption("Documents to verify for compliance")
    
    uploaded_target_pdfs = st.file_uploader(
        "Drop PDFs",
        type="pdf",
        accept_multiple_files=True,
        key="target_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_target_pdfs:
        if st.button("📤 Process Content", width="stretch", key="process_target"):
            with st.spinner(f"Processing {len(uploaded_target_pdfs)} file(s)..."):
                for uploaded_pdf in uploaded_target_pdfs:
                    temp_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    service.load_target_pdf(temp_path)
                    os.remove(temp_path)
                st.success(f"✅ {len(uploaded_target_pdfs)} docs loaded")
    
    # Compact file list
    if service.target_pdf_uris:
        st.caption(f"**Active:** {len(service.target_pdf_uris)} files")
        for uri in service.target_pdf_uris[:3]:  # Show max 3
            filename = uri.split('/')[-1][:20] if '/' in uri else uri[:20]
            st.caption(f"🟢 {filename}")
        if len(service.target_pdf_uris) > 3:
            st.caption(f"... +{len(service.target_pdf_uris) - 3} more")
    
    st.markdown("---")
    
    # CHECKLIST
    st.markdown("### 📋 Checklist")
    st.caption("Excel/CSV with questions")
    
    uploaded_excel = st.file_uploader(
        "Upload file",
        type=["xlsx", "xls", "csv"],
        key="checklist_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_excel:
        if st.button("📊 Load Checklist", width="stretch"):
            df = service.load_checklist(uploaded_excel)
            st.session_state.checklist_df = df
            
            if service.question_column:
                st.success(f"✅ Loaded: {len(df)} items")
            else:
                st.error("⚠️ Column detection failed")
    
    if service.checklist_df is not None:
        pending = len(service.checklist_df[service.checklist_df['Status'] == 'PENDING'])
        st.caption(f"**Active:** {len(service.checklist_df)} items ({pending} pending)")

    st.markdown("---")
    st.caption("💡 Click Status cells to change DRAFT → APPROVED")

# Main Area
if "checklist_df" in st.session_state:
    df = st.session_state.checklist_df
    
    # Progress Bar - UX Feature #2
    total_items = len(df)
    pending = len(df[df['Status'] == 'PENDING'])
    draft = len(df[df['Status'] == 'DRAFT'])
    approved = len(df[df['Status'] == 'APPROVED'])
    rejected = len(df[df['Status'] == 'REJECTED'])
    
    completed = approved + rejected
    completion_rate = (completed / total_items * 100) if total_items > 0 else 0
    
    st.markdown("### 📊 Progress")
    st.progress(completion_rate / 100)
    
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    col_p1.metric("Total", total_items)
    col_p2.metric("⏳ Pending", pending, delta=None, delta_color="off")
    col_p3.metric("📝 Draft", draft, delta=None, delta_color="off")
    col_p4.metric("✅ Approved", approved, delta=None, delta_color="normal")
    col_p5.metric("❌ Rejected", rejected, delta=None, delta_color="inverse")
    
    st.caption(f"**Completion:** {completion_rate:.1f}% ({completed}/{total_items} items)")
    st.markdown("---")
    
    # Action buttons above checklist
    st.markdown("### 🎯 Actions")
    
    # Row 1: Main actions
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        # Batch Analysis with dialog
        if st.button("📦 Batch Analysis", width="stretch", type="primary"):
            st.session_state.show_batch_dialog = True
    
    with col_btn2:
        if st.button("💾 Export Results", width="stretch"):
            # Export to Excel
            output_file = "checklist_results.xlsx"
            df.to_excel(output_file, index=False)
            st.success(f"Exported to {output_file}")
    
    with col_btn3:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()
    
    # Batch Analysis Dialog
    if st.session_state.get('show_batch_dialog', False):
        with st.expander("📦 Batch Analysis Options", expanded=True):
            st.markdown("**Select rows to analyze:**")
            
            batch_mode = st.radio(
                "Mode:",
                ["All Pending", "Range", "Specific Rows"],
                horizontal=True
            )
            
            rows_to_process = []
            
            if batch_mode == "All Pending":
                pending_rows = df[df['Status'] == 'PENDING'].index.tolist()
                st.info(f"Will analyze {len(pending_rows)} pending rows")
                rows_to_process = pending_rows
            
            elif batch_mode == "Range":
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    start_row = st.number_input("From row:", min_value=0, max_value=len(df)-1, value=0)
                with col_r2:
                    end_row = st.number_input("To row:", min_value=0, max_value=len(df)-1, value=min(2, len(df)-1))
                
                if start_row <= end_row:
                    rows_to_process = list(range(start_row, end_row + 1))
                    st.info(f"Will analyze rows {start_row} to {end_row} ({len(rows_to_process)} rows)")
                else:
                    st.error("Start row must be <= End row")
            
            else:  # Specific Rows
                row_input = st.text_input(
                    "Enter row numbers (comma-separated):",
                    placeholder="e.g., 0,2,5,7"
                )
                if row_input:
                    try:
                        rows_to_process = [int(r.strip()) for r in row_input.split(',')]
                        # Validate
                        rows_to_process = [r for r in rows_to_process if 0 <= r < len(df)]
                        st.info(f"Will analyze {len(rows_to_process)} rows: {rows_to_process}")
                    except:
                        st.error("Invalid format. Use comma-separated numbers.")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("▶️ Start Batch", width="stretch", disabled=len(rows_to_process)==0):
                    # Use st.status for better progress visualization
                    with st.status("🚀 Starting batch analysis...", expanded=True) as status:
                        progress_bar = st.progress(0)
                        total = len(rows_to_process)
                        
                        for i, idx in enumerate(rows_to_process, 1):
                            question = service.get_question_from_row(idx)
                            question_preview = question[:50] + "..." if len(question) > 50 else question
                            
                            # Update status label
                            status.update(label=f"🔄 Analyzing row {idx}/{len(df)}: {question_preview}")
                            st.write(f"**Row {idx}**: {question}")
                            
                            # Analyze
                            service.analyze_row(idx, question)
                            st.write("✅ Analysis complete")
                            
                            # Update progress
                            progress_bar.progress(i / total)
                            
                            # Add delay to avoid rate limiting (except for last item)
                            if i < total:
                                st.write(f"⏳ Waiting 2s for rate limit...")
                                time.sleep(2)
                        
                        status.update(label=f"✅ Batch Complete! Analyzed {total} rows", state="complete", expanded=False)
                    
                    st.session_state.checklist_df = service.get_dataframe()
                    st.session_state.show_batch_dialog = False
                    time.sleep(1)
                    st.rerun()
            
            with col_b2:
                if st.button("❌ Cancel", width="stretch"):
                    st.session_state.show_batch_dialog = False
                    st.rerun()
    
    # Row 2: Individual row analysis
    st.markdown("**🔍 Analyze Individual Row**")
    col_row1, col_row2 = st.columns([3, 1])
    
    with col_row1:
        row_to_analyze = st.selectbox(
            "Select row:",
            df.index.tolist(),
            format_func=lambda x: f"Row {x}: {service.get_question_from_row(x)[:50]}...",
            key="individual_row_selector"
        )
    
    with col_row2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("🔍 Analyze", width="stretch", type="secondary", key="analyze_individual"):
            logger.info(f"User requested analysis for row {row_to_analyze}")
            question = service.get_question_from_row(row_to_analyze)
            
            # Use st.status for single row too
            with st.status(f"🔄 Analyzing Row {row_to_analyze}...", expanded=True) as status:
                st.write(f"**Question**: {question}")
                st.write("🤖 Agents are consulting documents...")
                service.analyze_row(row_to_analyze, question)
                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
            
            st.session_state.checklist_df = service.get_dataframe()
            st.rerun()
    
    st.markdown("---")
    
    # Main 2-column layout
    col_checklist, col_chat = st.columns([7, 3])
    
    with col_checklist:
        # Display Checklist Table
        st.markdown("### 📋 Checklist")
        
        # UX Feature #4: Filter in main panel
        filter_selection = st.radio(
            "Show:",
            ["All", "Pending Only", "Draft Only", "Approved", "Rejected"],
            horizontal=True,
            key="status_filter"
        )
        
        # Apply Filter
        display_df = df.copy()
        
        if filter_selection == "Pending Only":
            display_df = display_df[display_df['Status'] == 'PENDING']
        elif filter_selection == "Draft Only":
            display_df = display_df[display_df['Status'] == 'DRAFT']
        elif filter_selection == "Approved":
            display_df = display_df[display_df['Status'] == 'APPROVED']
        elif filter_selection == "Rejected":
            display_df = display_df[display_df['Status'] == 'REJECTED']
        
        if len(display_df) == 0:
            st.info(f"No items match filter: {filter_selection}")
        else:
            st.caption(f"Showing {len(display_df)} of {len(df)} items")
            
            # UX Feature #1: Color-Coded Status Column + #5 Rich justification
            edited_df = st.data_editor(
                display_df,
                width="stretch",
                num_rows="fixed",
                hide_index=False,
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["PENDING", "DRAFT", "APPROVED", "REJECTED"],
                        required=True,
                        help="Click to change status"
                    ),
                    "Confidenza": st.column_config.ProgressColumn(
                        "Confidence",
                        min_value=0,
                        max_value=100,
                        format="%d%%"
                    ),
                    "Risposta": st.column_config.TextColumn(
                        "Answer",
                        width="medium"
                    ),
                    "Giustificazione": st.column_config.TextColumn(
                        "Justification",
                        width="large"
                    )
                },
                height=500,
                key="checklist_editor"
            )
            
            # Update the original dataframe with edits
            if edited_df is not None:
                # Map edited rows back to original df
                for idx in edited_df.index:
                    if idx in df.index:
                        df.loc[idx] = edited_df.loc[idx]
                st.session_state.checklist_df = df
                service.checklist_df = df
    
    with col_chat:
        st.subheader("💬 Ask Questions")
        
        # Row selector for chat
        chat_row = st.selectbox(
            "About row:",
            df.index.tolist(),
            format_func=lambda x: f"Row {x}",
            key="chat_row_selector"
        )
        
        st.caption(f"**Question:** {service.get_question_from_row(chat_row)[:100]}...")
        st.caption("💡 Ask about: the checklist question, what context docs say, what target docs contain")
        
        # Chat History Key per row
        chat_key = f"chat_history_{chat_row}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        # Chat container with fixed height
        chat_container = st.container(height=350)
        
        with chat_container:
            # Display History
            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # Chat Input (always visible at bottom)
        if prompt := st.chat_input("Ask about this item..."):
            logger.info(f"User chat for row {chat_row}", prompt[:100])
            
            # Add user message
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            
            # Get Agent Response
            with st.spinner("Thinking..."):
                response = service.chat_with_row(chat_row, prompt)
            
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
        - **Question Column**: `Question`, `Requirement`, `Item`, `Description`, `Check`, or `Domanda`
        
        ### Example
        | ID | Question | Status |
        |----|----------|--------|
        | 1  | Is there a DPO appointed? | PENDING |
        | 2  | Are access controls documented? | PENDING |
        
        See `CHECKLIST_FORMAT.md` for full details.
        """)
