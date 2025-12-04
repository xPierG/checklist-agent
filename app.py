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
    
    st.markdown("---")
    st.subheader("1️⃣ Upload Documents")
    
    # CONTEXT PDFs - Regulations/Policies
    st.markdown("**📚 Context Documents** (Regulations/Policies)")
    st.caption("These define the rules and requirements")
    
    uploaded_context_pdfs = st.file_uploader(
        "Upload context documents",
        type="pdf",
        accept_multiple_files=True,
        key="context_uploader",
        help="Regulations, policies, standards that define compliance requirements"
    )
    
    if uploaded_context_pdfs:
        if st.button("📤 Process Context PDFs", width="stretch", key="process_context"):
            with st.spinner(f"Uploading {len(uploaded_context_pdfs)} context PDF(s)..."):
                for uploaded_pdf in uploaded_context_pdfs:
                    temp_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    
                    uri = service.load_context_pdf(temp_path)
                    os.remove(temp_path)
                
                st.success(f"✅ {len(uploaded_context_pdfs)} Context PDF(s) Loaded")
    
    # Show loaded context PDFs
    if service.context_pdf_uris:
        with st.expander(f"📚 Loaded Context PDFs ({len(service.context_pdf_uris)})", expanded=False):
            for i, uri in enumerate(service.context_pdf_uris, 1):
                st.caption(f"{i}. {uri}")
    
    st.markdown("---")
    
    # TARGET PDFs - Documents to Analyze
    st.markdown("**📄 Target Documents** (To Analyze)")
    st.caption("These are the documents to verify for compliance")
    
    uploaded_target_pdfs = st.file_uploader(
        "Upload target documents",
        type="pdf",
        accept_multiple_files=True,
        key="target_uploader",
        help="Documents to analyze and verify against the rules"
    )
    
    if uploaded_target_pdfs:
        if st.button("📤 Process Target PDFs", width="stretch", key="process_target"):
            with st.spinner(f"Uploading {len(uploaded_target_pdfs)} target PDF(s)..."):
                for uploaded_pdf in uploaded_target_pdfs:
                    temp_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    
                    uri = service.load_target_pdf(temp_path)
                    os.remove(temp_path)
                
                st.success(f"✅ {len(uploaded_target_pdfs)} Target PDF(s) Loaded")
    
    # Show loaded target PDFs
    if service.target_pdf_uris:
        with st.expander(f"📄 Loaded Target PDFs ({len(service.target_pdf_uris)})", expanded=False):
            for i, uri in enumerate(service.target_pdf_uris, 1):
                st.caption(f"{i}. {uri}")

    # Checklist Upload
    uploaded_excel = st.file_uploader("Checklist (Excel)", type=["xlsx", "xls", "csv"])
    if uploaded_excel:
        if st.button("📊 Load Checklist", width="stretch"):
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
    st.subheader("2️⃣ Processing")
    
    st.caption("💡 Tip: Click on Status cells to change DRAFT → APPROVED/REJECTED")
    
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
    
    if st.button("Clear Activity Log", width="stretch"):
        logger.clear_activities()
        st.rerun()

# Main Area
if "checklist_df" in st.session_state:
    df = st.session_state.checklist_df
    
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
                    # Create progress containers
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total = len(rows_to_process)
                    for i, idx in enumerate(rows_to_process, 1):
                        question = service.get_question_from_row(idx)
                        question_preview = question[:60] + "..." if len(question) > 60 else question
                        
                        # Update status
                        status_text.info(f"🔍 Analyzing row {idx} ({i}/{total}): {question_preview}")
                        
                        # Analyze
                        service.analyze_row(idx, question)
                        
                        # Update progress
                        progress_bar.progress(i / total)
                        
                        # Add delay to avoid rate limiting (except for last item)
                        if i < total:
                            status_text.warning(f"⏳ Rate limit delay (2s)... Next: row {rows_to_process[i]}")
                            time.sleep(2)
                    
                    # Complete
                    progress_bar.progress(1.0)
                    status_text.success(f"✅ Completed! Analyzed {total} rows")
                    
                    st.session_state.checklist_df = service.get_dataframe()
                    st.session_state.show_batch_dialog = False
                    time.sleep(1)  # Let user see completion message
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
            with st.spinner("Analyzing..."):
                service.analyze_row(row_to_analyze, question)
                st.session_state.checklist_df = service.get_dataframe()
                st.rerun()
    
    st.markdown("---")
    
    # Main 2-column layout
    col_checklist, col_chat = st.columns([7, 3])
    
    with col_checklist:
        st.subheader("📋 Checklist")
        
        # Reorder columns: Original first, then AI columns
        all_cols = df.columns.tolist()
        ai_columns = ['Risposta', 'Confidenza', 'Giustificazione', 'Status', 'Discussion_Log']
        
        # Get original columns (not AI-generated)
        original_cols = [col for col in all_cols if col not in ai_columns]
        
        # Reorder: original columns, then AI columns
        ordered_cols = original_cols + [col for col in ai_columns if col in all_cols]
        df_display = df[ordered_cols]
        
        # Column configuration with styling
        column_config = {}
        
        # Original columns - no special config (will appear normal)
        for col in original_cols:
            if col == service.question_column:
                column_config[col] = st.column_config.TextColumn(
                    col,
                    width="large",
                    help="Domanda della checklist"
                )
        
        # AI columns with emoji and styling
        if 'Risposta' in all_cols:
            column_config['Risposta'] = st.column_config.TextColumn(
                "🤖 Risposta",
                help="Risposta generata dall'AI",
                width="medium"
            )
        
        if 'Confidenza' in all_cols:
            column_config['Confidenza'] = st.column_config.TextColumn(
                "🤖 Confidenza",
                help="Livello di confidenza (0-100%)",
                width="small"
            )
        
        if 'Giustificazione' in all_cols:
            column_config['Giustificazione'] = st.column_config.TextColumn(
                "🤖 Giustificazione",
                help="Snippet di testo e spiegazione",
                width="large"
            )
        
        if 'Status' in all_cols:
            column_config['Status'] = st.column_config.SelectboxColumn(
                "📊 Status",
                help="Stato dell'analisi - Click to change",
                width="small",
                options=['PENDING', 'DRAFT', 'APPROVED', 'REJECTED']
            )
        
        # Display editable dataframe
        edited_df = st.data_editor(
            df_display,
            column_config=column_config,
            hide_index=False,
            width="stretch",
            height=500,
            key="checklist_editor"
        )
        
        # Update service dataframe if edited
        if not edited_df.equals(df_display):
            service.checklist_df = edited_df
            st.session_state.checklist_df = edited_df
    
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
