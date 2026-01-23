import streamlit as st
import pandas as pd
import os
import time
import streamlit_antd_components as sac
from services.compliance_service import ComplianceService
from utils.logger import logger

# Page Config
st.set_page_config(layout="wide", page_title="ADK Compliance Agent")

# Function to load css
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load custom CSS
load_css("assets/style.css")

# Initialize Service in Session State
if "service" not in st.session_state:
    auth_mode = os.environ.get("AUTH_MODE", "ADC") # Read AUTH_MODE, default to ADC
    try:
        st.session_state.service = ComplianceService(auth_mode=auth_mode) # Pass auth_mode
        st.toast(f"✅ Service Initialized (Auth Mode: {auth_mode})")
    except Exception as e:
        st.error(f"Failed to initialize service: {e}")
        st.stop()

service = st.session_state.service

# Initialize selected row
if "selected_row" not in st.session_state:
    st.session_state.selected_row = 0

def mostra_interfaccia_principal():
    """
    Renders the main application interface using a tabbed layout and Mantine components.
    """
    # --- Sidebar remains mostly the same ---
    with st.sidebar:
        st.title("🔍 Compliance Agent")

        # Quick Stats at top
        if service.checklist_df is not None or service.context_doc_info or service.target_doc_info:
            sac.divider(label='Stats', icon='bar-chart-2', align='center')
            col1, col2, col3 = st.columns(3)
            col1.metric("📚", len(service.context_doc_info), "Rules")
            col2.metric("📄", len(service.target_doc_info), "Content")
            if service.checklist_df is not None:
                pending = len(service.checklist_df[service.checklist_df['Status'] == 'PENDING'])
                col3.metric("⏳", pending, "Pending")
            else:
                col3.metric("📋", 0, "Items")
        
        sac.divider(label='Setup', icon='upload-cloud', align='center')

        # CONTEXT Documents - Regulations/Policies
        with st.expander("🏛️ Rules & Regulations", expanded=True):
            uploaded_context_files = st.file_uploader(
                "Upload policies, standards, regulations",
                type=["pdf", "docx", "txt"], accept_multiple_files=True, key="context_uploader"
            )
            if uploaded_context_files:
                if st.button("📤 Process Rules", width="stretch", key="process_context"):
                    with st.spinner(f"Processing {len(uploaded_context_files)} file(s)..."):
                        for uploaded_file in uploaded_context_files:
                            temp_path = f"temp_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            service.load_context_document(temp_path)
                            os.remove(temp_path)
                        st.toast(f'✅ Rules Loaded: {len(uploaded_context_files)} files processed.')

            if service.context_doc_info:
                st.caption(f"**Active:** {len(service.context_doc_info)} files")
                for doc_info in service.context_doc_info[:3]:
                    st.caption(f"🟢 {doc_info['filename'][:25]}")
                if len(service.context_doc_info) > 3:
                    st.caption(f"... +{len(service.context_doc_info) - 3} more")

        # TARGET Documents - Documents to Analyze
        with st.expander("📄 Content to Analyze", expanded=True):
            uploaded_target_files = st.file_uploader(
                "Upload documents to verify",
                type=["pdf", "docx", "txt"], accept_multiple_files=True, key="target_uploader"
            )
            if uploaded_target_files:
                if st.button("📤 Process Content", width="stretch", key="process_target"):
                    with st.spinner(f"Processing {len(uploaded_target_files)} file(s)..."):
                        for uploaded_file in uploaded_target_files:
                            temp_path = f"temp_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            service.load_target_document(temp_path)
                            os.remove(temp_path)
                        st.toast(f'✅ Content Loaded: {len(uploaded_target_files)} files processed.')

            if service.target_doc_info:
                st.caption(f"**Active:** {len(service.target_doc_info)} files")
                for doc_info in service.target_doc_info[:3]:
                    st.caption(f"🟢 {doc_info['filename'][:25]}")
                if len(service.target_doc_info) > 3:
                    st.caption(f"... +{len(service.target_doc_info) - 3} more")

        # CHECKLIST
        with st.expander("📋 Checklist", expanded=True):
            uploaded_excel = st.file_uploader(
                "Upload Excel/CSV with questions",
                type=["xlsx", "xls", "csv"], key="checklist_uploader"
            )
            if uploaded_excel:
                if st.button("📊 Load Checklist", width="stretch"):
                    df = service.load_checklist(uploaded_excel)
                    st.session_state.checklist_df = df
                    if service.question_column:
                        st.toast(f'✅ Checklist Loaded: {len(df)} items found.')
                    else:
                        st.error('⚠️ Load Failed: Could not detect required columns.')

            if service.checklist_df is not None:
                pending = len(service.checklist_df[service.checklist_df['Status'] == 'PENDING'])
                st.caption(f"**Active:** {len(service.checklist_df)} items ({pending} pending)")

        sac.divider(label='Actions', icon='activity', align='center')
        if st.button("🆕 New Analysis", help="Clears all data and restarts the application"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

        if service.checklist_df is not None:
            # Export button
            import io
            buffer = io.BytesIO()
            st.session_state.checklist_df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            
            st.download_button(
                label="💾 Export Results",
                data=buffer,
                file_name="checklist_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Download the current checklist with all results to an Excel file"
            )
        
    # --- Main Area ---
    if "checklist_df" not in st.session_state:
        st.info("👈 Please upload a checklist from the sidebar to begin.")
        with st.expander("📖 Checklist Format Guide"):
            st.markdown("""
            ### Required Columns
            - **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`
            - **Question Column**: `Question`, `Requirement`, `Item`, `Description`, `Check`, or `Domanda`
            See `CHECKLIST_FORMAT.md` for full details.
            """)
        return

    df = st.session_state.checklist_df
    
    # --- TABS ---
    with st.container():
        selected_tab = sac.tabs([
            sac.TabsItem(label='DASHBOARD', icon='clipboard-data'),
            sac.TabsItem(label='ANALYZE & DISCUSS', icon='robot'),
            sac.TabsItem(label='BATCH ANALYSIS', icon='box-seam'),
            sac.TabsItem(label='ACTIVITY LOGS', icon='terminal'),
        ], format_func='title', align='center', variant='outline')

    # --- TAB 1: DASHBOARD ---
    if selected_tab == 'DASHBOARD':
        
        with st.container(border=True):
            st.subheader("📊 Progress Overview")
            total_items = len(df)
            completed = len(df[df['Status'].isin(['APPROVED', 'REJECTED'])])
            completion_rate = (completed / total_items * 100) if total_items > 0 else 0
            
            sac.Tag(label=f"{completion_rate:.1f}% Complete", color='blue', bordered=False)
            st.progress(completion_rate / 100)
            
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("Total Items", total_items)
            m_col2.metric("Pending", len(df[df['Status'] == 'PENDING']))
            m_col3.metric("Draft", len(df[df['Status'] == 'DRAFT']))
            m_col4.metric("Approved", len(df[df['Status'] == 'APPROVED']))
            m_col5.metric("Rejected", len(df[df['Status'] == 'REJECTED']))

        st.subheader("📋 Checklist")
        filter_selection = sac.segmented(
            items=["All", "Pending", "Draft", "Approved", "Rejected"],
            align='center',
            size='sm'
        )

        display_df = df.copy()
        if filter_selection != "All":
            display_df = display_df[display_df['Status'] == filter_selection.upper()]

        if len(display_df) == 0:
            st.info(f"No items match filter: {filter_selection}")
        else:
            # Data editor logic remains the same...
            id_c, q_c, d_c = service.id_column, service.question_column, service.description_column
            cols_to_show = []
            col_config = {}
            
            display_df['#'] = display_df.index + 1
            cols_to_show.append('#')
            col_config['#'] = st.column_config.NumberColumn("#", width="small", format="%d")
            cols_to_show.append('Status')
            col_config['Status'] = st.column_config.SelectboxColumn("Status", options=["PENDING", "DRAFT", "APPROVED", "REJECTED"], required=True, width="small")
            
            if id_c and id_c in display_df.columns: cols_to_show.append(id_c); col_config[id_c] = st.column_config.TextColumn("ID", width="small")
            if q_c and q_c in display_df.columns: cols_to_show.append(q_c); col_config[q_c] = st.column_config.TextColumn("Question", width="medium")
            if d_c and d_c in display_df.columns: cols_to_show.append(d_c); col_config[d_c] = st.column_config.TextColumn("Description", width="medium", help="Additional details")
            
            cols_to_show.extend(['Risposta', 'Confidenza', 'Giustificazione', 'Manually_Edited'])
            col_config.update({
                "Risposta": st.column_config.TextColumn("AI Answer", width="medium", disabled=False), # Make editable
                "Confidenza": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%d%%", width="small"),
                "Giustificazione": st.column_config.TextColumn("Justification", width="large", disabled=True), # Make read-only
                "Manually_Edited": st.column_config.CheckboxColumn("Edited", width="small", disabled=True)
            })
            
            editor_df = display_df[cols_to_show].copy()
            edited_df = st.data_editor(
                editor_df, width="stretch", num_rows="fixed", hide_index=True, column_config=col_config, height=500, key="checklist_editor",
            )
            
            if edited_df is not None:
                for idx, row in edited_df.iterrows():
                    original_row_idx = display_df.index[idx] # Get original index from filtered df
                    
                    # Update Status if changed
                    if st.session_state.checklist_df.at[original_row_idx, 'Status'] != row['Status']:
                        st.session_state.checklist_df.at[original_row_idx, 'Status'] = row['Status']
                        st.session_state.checklist_df.at[original_row_idx, 'Manually_Edited'] = True # Mark as edited
                    
                    # Update Risposta and track manual edits
                    if st.session_state.checklist_df.at[original_row_idx, 'Risposta'] != row['Risposta']:
                        st.session_state.checklist_df.at[original_row_idx, 'Risposta'] = row['Risposta']
                        st.session_state.checklist_df.at[original_row_idx, 'Manually_Edited'] = True

    # --- TAB 2: ANALYZE & DISCUSS (Refactored to single column) ---
    elif selected_tab == 'ANALYZE & DISCUSS':
        st.subheader("🔬 Analyze & Discuss")
        
        with st.container(border=True):
            st.markdown("##### Select Row for Analysis")
            row_to_analyze = st.selectbox(
                "Select a row to focus on:",
                df.index.tolist(),
                format_func=lambda x: f"Row {x+1}: {service.get_question_from_row(x)[:60]}...",
                key="individual_row_selector",
                index=st.session_state.get('last_analyzed_row', 0)
            )

            if st.button("Analyze Row", type="primary", key="analyze_individual", use_container_width=True):
                question = service.get_question_from_row(row_to_analyze)
                with st.status(f"🔄 Analyzing Row {row_to_analyze}...", expanded=True) as status:
                    service.analyze_row(row_to_analyze, question)
                    status.update(label="✅ Analysis Complete!", state="complete")
                st.session_state.checklist_df = service.get_dataframe()
                st.session_state.last_analyzed_row = row_to_analyze
                st.rerun()

        with st.container(border=True):
            st.markdown("##### Analysis Result")
            row_data = df.loc[row_to_analyze]
            question = service.get_question_from_row(row_to_analyze)
            desc = service.get_description_from_row(row_to_analyze)
            
            st.markdown(f"**Question:** {question}")
            if desc:
                st.caption(f"**Description:** {desc}")
            
            sac.divider()
            
            st.markdown(f"**AI Answer:** {row_data.get('Risposta', 'N/A')}")
            st.metric("Confidence", f"{row_data.get('Confidenza', 0)}%")
            st.markdown("**Justification:**")
            st.markdown(row_data.get('Giustificazione', 'Not yet analyzed.'))

        with st.container(border=True):
            st.markdown("##### Chat about this Row")
            st.caption(f"Discussing: {service.get_question_from_row(row_to_analyze)[:80]}...")

            chat_key = f"chat_history_{row_to_analyze}"
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []

            with st.container(height=300):
                for msg in st.session_state[chat_key]:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
            
            if prompt := st.chat_input("Ask a follow-up question..."):
                st.session_state[chat_key].append({"role": "user", "content": prompt})
                with st.spinner("Thinking..."):
                    response = service.chat_with_row(row_to_analyze, prompt)
                st.session_state[chat_key].append({"role": "assistant", "content": response})
                st.rerun()

    # --- TAB 3: BATCH ANALYSIS ---
    elif selected_tab == 'BATCH ANALYSIS':
        st.subheader("🚀 Batch Analysis")
        with st.container(border=True):
            st.markdown("##### Batch Processing Options")
            batch_mode = sac.segmented(
                items=["All Pending", "Range", "Specific Rows"],
                align='center'
            )
            
            # Concurrency Slider
            concurrency = st.slider(
                "⚡ Parallel Threads (Concurrency)",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of agents running in parallel. Higher values are faster but may hit API limits."
            )

            rows_to_process = []

            if batch_mode == "All Pending":
                pending_rows = df[df['Status'] == 'PENDING'].index.tolist()
                st.info(f"Will analyze {len(pending_rows)} pending rows.")
                rows_to_process = pending_rows
            elif batch_mode == "Range":
                col_r1, col_r2 = st.columns(2)
                # FIX: Change to 1-based indexing for user
                start_row_input = col_r1.number_input("From row:", min_value=1, max_value=len(df), value=1)
                end_row_input = col_r2.number_input("To row:", min_value=1, max_value=len(df), value=min(3, len(df)))
                
                if start_row_input <= end_row_input:
                    # Convert back to 0-based index for internal use
                    start_row = start_row_input - 1
                    end_row = end_row_input - 1
                    rows_to_process = list(range(start_row, end_row + 1))
                    st.info(f"Will analyze rows {start_row_input} to {end_row_input} ({len(rows_to_process)} rows).")
                else:
                    st.error("Start row must be <= End row.")
            else: # Specific Rows
                row_input = st.text_input("Enter row numbers (comma-separated):", placeholder="e.g., 1, 3, 6, 8")
                if row_input:
                    try:
                        # Convert 1-based input to 0-based index
                        rows_to_process = [int(r.strip()) - 1 for r in row_input.split(',')]
                        rows_to_process = [r for r in rows_to_process if 0 <= r < len(df)]
                        st.info(f"Will analyze {len(rows_to_process)} rows: {[r + 1 for r in rows_to_process]}")
                    except:
                        st.error("Invalid format. Use comma-separated numbers (e.g., 1, 3, 6).")

            if st.button("▶️ Start Batch", disabled=not rows_to_process, type='primary', use_container_width=True):
                # Use a unique key for the status container to avoid issues with reruns
                status_key = f"batch_status_{time.time()}" 
                with st.status(f"🚀 Starting parallel batch analysis ({len(rows_to_process)} items, {concurrency} threads)...", expanded=True) as status:
                    progress_bar = st.progress(0)
                    processed_count = 0
                    total_to_process = len(rows_to_process)
                    
                    # Run the batch and iterate over yielded results
                    for result in service.batch_analyze(row_indices=rows_to_process, concurrency=concurrency):
                        if result["status"] == "success":
                            processed_count += 1
                            progress_bar.progress(processed_count / total_to_process)
                            status.write(f"✅ Processed row {result['index'] + 1} (ID: {df.at[result['index'], service.id_column] if service.id_column else result['index']})")
                        elif result["status"] == "error":
                            processed_count += 1 # Count errors as processed for progress bar
                            progress_bar.progress(processed_count / total_to_process)
                            status.write(f"❌ Error processing row {result['index'] + 1}: {result['error']}")
                            logger.error(f"Batch item error: {result['error']}")
                        elif result["status"] == "info":
                            status.write(f"ℹ️ {result['message']}")
                        
                    status.update(label=f"✅ Batch Complete! Processed {processed_count} items", state="complete")
                        
                    # After batch completion, refresh the dataframe and rerun
                    st.session_state.checklist_df = service.get_dataframe()
                    st.rerun() # Rerun to update dashboard

        # The alert below will be shown only if st.rerun() is not called from inside the batch processing loop
        # and batch_analysis_complete is set. Since we are calling rerun inside, this may not be strictly necessary,
        # but good to keep as a fallback or for clarity if behavior changes.
        if st.session_state.get('batch_analysis_complete', False):
            sac.alert(
                label="Batch Analysis Completed!",
                description="Please navigate to the **DASHBOARD** tab to review the updated checklist and results.",
                closable=True,
                key="batch_complete_alert"
            )
            del st.session_state['batch_analysis_complete'] # Clear flag

    # --- TAB 4: ACTIVITY LOGS ---
    elif selected_tab == 'ACTIVITY LOGS':
        st.subheader("📝 Activity Logs")
        st.write("Shows the most recent activities performed by the agents.")
        
        activities = logger.get_recent_activities(limit=50)
        
        if not activities:
            st.info("No activities logged yet.")
        else:
            for i, act in enumerate(activities):
                if act['level'] == 'SUCCESS':
                    color = 'green'
                elif act['level'] == 'ERROR':
                    color = 'red'
                elif act['level'] == 'WARNING':
                    color = 'yellow'
                else: # INFO
                    color = 'blue'
                
                sac.alert(label=f"**{act['message']}**", description=act.get('details'), color=color, closable=True, key=f"log_{i}")

def mostra_wizard():
    """
    Renders the step-by-step document upload wizard.
    """
    st.session_state.wizard_step = st.session_state.get('wizard_step', 0)
    
    # --- Step 0: Welcome ---
    def wizard_step_0():
        st.title("🧙‍♂️ Welcome to the Setup Wizard")
        st.markdown("""
        This wizard will guide you through loading the necessary documents to start a compliance analysis.
        The process is divided into 3 simple steps:
        1.  **Upload Checklist**: The Excel or CSV file with the requirements to be verified.
        2.  **Upload Context**: the PDF documents containing the rules, laws, and standards.
        3.  **Upload Target**: The PDF documents to be analyzed for compliance.
        At the end, you will be redirected to the main interface to start the analysis.
        """)
        if st.button("Start Setup", type="primary"):
            st.session_state.wizard_step = 1
            st.rerun()

    # --- Step 1, 2, 3 are the same as before ---
    def wizard_step_1():
        st.title("Step 1: Upload Checklist 📋")
        st.info("Upload the Excel (.xlsx, .xls) or .csv file containing the control points.")
        uploaded_excel = st.file_uploader("Upload file", type=["xlsx", "xls", "csv"], key="wizard_checklist_uploader", label_visibility="collapsed")
        if uploaded_excel:
            df = service.load_checklist(uploaded_excel)
            st.session_state.checklist_df = df
            if service.question_column:
                st.success(f"✅ Checklist '{uploaded_excel.name}' uploaded successfully! It contains {len(df)} rows.")
            else:
                st.error("⚠️ Unrecognized columns. Make sure the file follows the required format.")
        col1, col2 = st.columns([1,1])
        with col2:
            if st.button("Next →", type="primary", disabled=(service.checklist_df is None)):
                st.session_state.wizard_step = 2
                st.rerun()
    
    def wizard_step_2():
        st.title("Step 2: Upload Context (Rules) 🏛️")
        st.info("Upload one or more PDF, DOCX, or TXT files containing the rules, regulations, and standards.")
        uploaded_context_files = st.file_uploader("Drag files here", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="wizard_context_uploader", label_visibility="collapsed")
        if uploaded_context_files:
            with st.spinner(f"Processing {len(uploaded_context_files)} context files..."):
                for uploaded_file in uploaded_context_files:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    service.load_context_document(temp_path)
                    os.remove(temp_path)
                st.success(f"✅ {len(service.context_doc_info)} context files uploaded and processed.")
        if service.context_doc_info:
            st.write("Uploaded context files:")
            for doc_info in service.context_doc_info: st.caption(f"✓ {doc_info['filename']}")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back"):
                st.session_state.wizard_step = 1
                st.rerun()
        with col3:
            if st.button("Next →", type="primary", disabled=(len(service.context_doc_info) == 0)):
                st.session_state.wizard_step = 3
                st.rerun()

    def wizard_step_3():
        st.title("Step 3: Upload Target (Content) 📄")
        st.info("Upload one or more PDF, DOCX, or TXT files to be analyzed for compliance verification.")
        uploaded_target_files = st.file_uploader("Drag files here", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="wizard_target_uploader", label_visibility="collapsed")
        if uploaded_target_files:
            with st.spinner(f"Processing {len(uploaded_target_files)} target files..."):
                for uploaded_file in uploaded_target_files:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    service.load_target_document(temp_path)
                    os.remove(temp_path)
                st.success(f"✅ {len(service.target_doc_info)} target files uploaded and processed.")
        if service.target_doc_info:
            st.write("Uploaded target files:")
            for doc_info in service.target_doc_info: st.caption(f"✓ {doc_info['filename']}")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back"):
                st.session_state.wizard_step = 2
                st.rerun()
        with col3:
            if st.button("✨ Finish", type="primary", disabled=(len(service.target_doc_info) == 0)):
                st.session_state.wizard_mode = False
                st.success("🎉 Setup complete! Redirecting to the main interface...")
                time.sleep(1)
                st.rerun()

    # Router for steps
    if st.session_state.wizard_step == 0: wizard_step_0()
    elif st.session_state.wizard_step == 1: wizard_step_1()
    elif st.session_state.wizard_step == 2: wizard_step_2()
    elif st.session_state.wizard_step == 3: wizard_step_3()
        
# --- Main Logic ---
if st.session_state.get('wizard_mode', True):
    mostra_wizard()
else:
    mostra_interfaccia_principal()