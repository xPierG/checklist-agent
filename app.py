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
    auth_mode = os.environ.get("AUTH_MODE", "ADC") # Read AUTH_MODE, default to ADC
    try:
        st.session_state.service = ComplianceService(auth_mode=auth_mode) # Pass auth_mode
        st.success(f"✅ Compliance Service Initialized (Auth Mode: {auth_mode})")
    except Exception as e:
        st.error(f"Failed to initialize service: {e}")
        st.stop()

service = st.session_state.service

# Initialize selected row
if "selected_row" not in st.session_state:
    st.session_state.selected_row = 0

def mostra_interfaccia_principale():

    """

    Renders the main application interface, including sidebar and main content area.

    """

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



        if service.context_pdf_uris:
            st.caption(f"**Active:** {len(service.context_pdf_uris)} files")
            for doc_info in service.context_pdf_uris[:3]:
                filename = doc_info['filename'][:20]
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



        if service.target_pdf_uris:
            st.caption(f"**Active:** {len(service.target_pdf_uris)} files")
            for doc_info in service.target_pdf_uris[:3]:
                filename = doc_info['filename'][:20]
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



        st.markdown("---")

        if st.button("🆕 Start New Analysis", width="stretch"):

            for key in st.session_state.keys():

                del st.session_state[key]

            st.rerun()



    # Main Area

    if "checklist_df" in st.session_state:

        df = st.session_state.checklist_df

        

        st.markdown("### 📊 Progress")

        total_items = len(df)

        completed = len(df[df['Status'].isin(['APPROVED', 'REJECTED'])])

        completion_rate = (completed / total_items * 100) if total_items > 0 else 0

        st.progress(completion_rate / 100)

        

        col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)

        col_p1.metric("Total", total_items)

        col_p2.metric("⏳ Pending", len(df[df['Status'] == 'PENDING']))

        col_p3.metric("📝 Draft", len(df[df['Status'] == 'DRAFT']))

        col_p4.metric("✅ Approved", len(df[df['Status'] == 'APPROVED']))

        col_p5.metric("❌ Rejected", len(df[df['Status'] == 'REJECTED']))

        

        st.caption(f"**Completion:** {completion_rate:.1f}% ({completed}/{total_items} items)")

        st.markdown("---")

        

        st.markdown("### 🎯 Actions")

        col_btn1, col_btn2, col_btn3 = st.columns(3)

        if col_btn1.button("📦 Batch Analysis", width="stretch", type="primary"):

            st.session_state.show_batch_dialog = True

        if col_btn2.button("💾 Export Results", width="stretch"):

            output_file = "checklist_results.xlsx"

            df.to_excel(output_file, index=False)

            st.success(f"Exported to {output_file}")

        if col_btn3.button("🔄 Refresh", width="stretch"):

            st.rerun()



        if st.session_state.get('show_batch_dialog', False):



            with st.expander("📦 Batch Analysis Options", expanded=True):



                st.markdown("**Select rows to analyze:**")



                batch_mode = st.radio("Mode:", ["All Pending", "Range", "Specific Rows"], horizontal=True)



                rows_to_process = []



                if batch_mode == "All Pending":



                    pending_rows = df[df['Status'] == 'PENDING'].index.tolist()



                    st.info(f"Will analyze {len(pending_rows)} pending rows")



                    rows_to_process = pending_rows



                elif batch_mode == "Range":



                    col_r1, col_r2 = st.columns(2)



                    start_row = col_r1.number_input("From row:", min_value=0, max_value=len(df)-1, value=0)



                    end_row = col_r2.number_input("To row:", min_value=0, max_value=len(df)-1, value=min(2, len(df)-1))



                    if start_row <= end_row:



                        rows_to_process = list(range(start_row, end_row + 1))



                        st.info(f"Will analyze rows {start_row} to {end_row} ({len(rows_to_process)} rows)")



                    else:



                        st.error("Start row must be <= End row")



                else:



                    row_input = st.text_input("Enter row numbers (comma-separated):", placeholder="e.g., 0,2,5,7")



                    if row_input:



                        try:



                            rows_to_process = [int(r.strip()) for r in row_input.split(',')]



                            rows_to_process = [r for r in rows_to_process if 0 <= r < len(df)]



                            st.info(f"Will analyze {len(rows_to_process)} rows: {rows_to_process}")



                        except:



                            st.error("Invalid format. Use comma-separated numbers.")



                



                col_b1, col_b2 = st.columns(2)



                if col_b1.button("▶️ Start Batch", width="stretch", disabled=len(rows_to_process)==0):



                    with st.status("🚀 Starting batch analysis...", expanded=True) as status:



                        progress_bar = st.progress(0)



                        total = len(rows_to_process)



                        for i, idx in enumerate(rows_to_process, 1):



                            question = service.get_question_from_row(idx)



                            status.update(label=f"🔄 Analyzing row {idx}/{len(df)}: {question[:50]}...")



                            service.analyze_row(idx, question)



                            progress_bar.progress(i / total)



                            if i < total:



                                time.sleep(2)



                        status.update(label=f"✅ Batch Complete! Analyzed {total} rows", state="complete")



                    st.session_state.checklist_df = service.get_dataframe()



                    st.session_state.show_batch_dialog = False



                    st.rerun()



                if col_b2.button("❌ Cancel", width="stretch"):



                    st.session_state.show_batch_dialog = False



                    st.rerun()

        

        st.markdown("**🔍 Analyze Individual Row**")



        col_row1, col_row2 = st.columns([3, 1])



        row_to_analyze = col_row1.selectbox(



            "Select row:",



            df.index.tolist(),



            format_func=lambda x: f"Row {x}: {service.get_question_from_row(x)[:50]}...",



            key="individual_row_selector"



        )



        col_row2.markdown("<br>", unsafe_allow_html=True)



        if col_row2.button("🔍 Analyze", type="secondary", key="analyze_individual"):



            question = service.get_question_from_row(row_to_analyze)



            with st.status(f"🔄 Analyzing Row {row_to_analyze}...", expanded=True) as status:



                service.analyze_row(row_to_analyze, question)



                status.update(label="✅ Analysis Complete!", state="complete")



            st.session_state.checklist_df = service.get_dataframe()



            st.session_state.last_analyzed_row = row_to_analyze



            st.session_state.last_analysis_result = {



                'Risposta': st.session_state.checklist_df.at[row_to_analyze, 'Risposta'],



                'Giustificazione': st.session_state.checklist_df.at[row_to_analyze, 'Giustificazione']



            }



            st.rerun()

        

        

        if "last_analysis_result" in st.session_state and st.session_state.last_analyzed_row == row_to_analyze:



            with col_row1:



                st.markdown("---")



                st.markdown(f"### 📝 Analysis for Row {st.session_state.last_analyzed_row}")



                st.info(f"**Answer:** {st.session_state.last_analysis_result['Risposta']}")



                st.markdown("**Justification:**")



                st.markdown(st.session_state.last_analysis_result['Giustificazione'])

        



        st.markdown("---")



        st.markdown("### 📋 Checklist")



        filter_selection = st.radio("Show:", ["All", "Pending Only", "Draft Only", "Approved", "Rejected"], horizontal=True, key="status_filter")



        display_df = df.copy()



        if filter_selection != "All":



            display_df = display_df[display_df['Status'] == filter_selection.split(' ')[0].upper()]



        



        if len(display_df) == 0:



            st.info(f"No items match filter: {filter_selection}")



        else:



            st.data_editor(display_df, width="stretch", num_rows="fixed", hide_index=False, column_config={



                "Status": st.column_config.SelectboxColumn("Status", options=["PENDING", "DRAFT", "APPROVED", "REJECTED"], required=True),



                "Confidenza": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%d%%"),



                "Risposta": st.column_config.TextColumn("Answer", width="medium"),



                "Giustificazione": st.column_config.TextColumn("Justification", width="large")



            }, height=500, key="checklist_editor")

        



        st.markdown("---")



        st.subheader("💬 Ask Questions")



        chat_row = st.selectbox("About row:", df.index.tolist(), format_func=lambda x: f"Row {x}", key="chat_row_selector_new")



        st.caption(f"**Question:** {service.get_question_from_row(chat_row)[:100]}...")



        

        chat_key = f"chat_history_{chat_row}"



        if chat_key not in st.session_state:



            st.session_state[chat_key] = []



        

        with st.container(height=350):



            for msg in st.session_state[chat_key]:



                with st.chat_message(msg["role"]):



                    st.write(msg["content"])



        



        if prompt := st.chat_input("Ask about this item..."):



            st.session_state[chat_key].append({"role": "user", "content": prompt})



            with st.spinner("Thinking..."):



                response = service.chat_with_row(chat_row, prompt)



            st.session_state[chat_key].append({"role": "assistant", "content": response})



            st.rerun()

        



    else:



        st.info("👈 Please upload a checklist to begin.")



        with st.expander("📖 Checklist Format Guide"):



            st.markdown("""



            ### Required Columns

            - **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`

            - **Question Column**: `Question`, `Requirement`, `Item`, `Description`, `Check`, or `Domanda`

            See `CHECKLIST_FORMAT.md` for full details.

            """)



def mostra_wizard():



    """



    Renders the step-by-step document upload wizard.



    """



    st.session_state.wizard_step = st.session_state.get('wizard_step', 0)






    # --- Step 0: Welcome ---



    def wizard_step_0():



        st.title("🧙‍♂️ Benvenuto nel Wizard di Setup")



        st.markdown("""



        Questo wizard ti guiderà nel caricamento dei documenti necessari per avviare un'analisi di conformità.



        



        Il processo è suddiviso in 3 semplici passi:



        



        1.  **Carica la Checklist**: Il file Excel o CSV con i requisiti da verificare.



        2.  **Carica il Contesto**: I documenti PDF contenenti le regole, leggi e standard.



        3.  **Carica il Target**: I documenti PDF da analizzare per la conformità.



        



        Al termine, verrai reindirizzato all'interfaccia principale per avviare le analisi.



        """)



        if st.button("Inizia la Configurazione", type="primary"):



            st.session_state.wizard_step = 1



            st.rerun()






    # --- Step 1: Upload Checklist ---



    def wizard_step_1():



        st.title("Passo 1: Carica la Checklist 📋")



        st.info("Carica il file Excel (.xlsx, .xls) o .csv che contiene i punti di controllo.")



        



        uploaded_excel = st.file_uploader(



            "Carica file",



            type=["xlsx", "xls", "csv"],



            key="wizard_checklist_uploader",



            label_visibility="collapsed"



        )






        if uploaded_excel:



            df = service.load_checklist(uploaded_excel)



            st.session_state.checklist_df = df



            



            if service.question_column:



                st.success(f"✅ Checklist '{uploaded_excel.name}' caricata con successo! Contiene {len(df)} righe.")



            else:



                st.error("⚠️ Colonne non riconosciute. Assicurati che il file rispetti il formato richiesto.")



        



        # Navigation



        col1, col2 = st.columns([1,1])



        with col2:



            if st.button("Avanti →", type="primary", disabled=(service.checklist_df is None)):



                st.session_state.wizard_step = 2



                st.rerun()






    # --- Step 2: Upload Context PDFs ---



    def wizard_step_2():



        st.title("Passo 2: Carica il Contesto (Regole) 🏛️")



        st.info("Carica uno o più file PDF che contengono le regole, le normative e gli standard.")






        uploaded_context_pdfs = st.file_uploader(



            "Trascina i PDF qui",



            type="pdf",



            accept_multiple_files=True,



            key="wizard_context_uploader",



            label_visibility="collapsed"



        )






        if uploaded_context_pdfs:



            with st.spinner(f"Processo {len(uploaded_context_pdfs)} file di contesto..."):



                for uploaded_pdf in uploaded_context_pdfs:



                    temp_path = f"temp_{uploaded_pdf.name}"



                    with open(temp_path, "wb") as f:



                        f.write(uploaded_pdf.getbuffer())



                    service.load_context_pdf(temp_path)



                    os.remove(temp_path)



                st.success(f"✅ {len(service.context_pdf_uris)} file di contesto caricati e processati.")






        if service.context_pdf_uris:



            st.write("File di contesto caricati:")



            for doc_info in service.context_pdf_uris:



                st.caption(f"✓ {doc_info['filename']}")






        # Navigation



        col1, col2, col3 = st.columns([1, 1, 1])



        with col1:



            if st.button("← Indietro"):



                st.session_state.wizard_step = 1



                st.rerun()



        with col3:



            if st.button("Avanti →", type="primary", disabled=(len(service.context_pdf_uris) == 0)):



                st.session_state.wizard_step = 3



                st.rerun()






    # --- Step 3: Upload Target PDFs ---



    def wizard_step_3():



        st.title("Passo 3: Carica il Target (Contenuto) 📄")



        st.info("Carica uno o più file PDF da analizzare per la verifica di conformità.")






        uploaded_target_pdfs = st.file_uploader(



            "Trascina i PDF qui",



            type="pdf",



            accept_multiple_files=True,



            key="wizard_target_uploader",



            label_visibility="collapsed"



        )






        if uploaded_target_pdfs:



            with st.spinner(f"Processo {len(uploaded_target_pdfs)} file target..."):



                for uploaded_pdf in uploaded_target_pdfs:



                    temp_path = f"temp_{uploaded_pdf.name}"



                    with open(temp_path, "wb") as f:



                        f.write(uploaded_pdf.getbuffer())



                    service.load_target_pdf(temp_path)



                    os.remove(temp_path)



                st.success(f"✅ {len(service.target_pdf_uris)} file target caricati e processati.")






        if service.target_pdf_uris:



            st.write("File target caricati:")



            for doc_info in service.target_pdf_uris:



                st.caption(f"✓ {doc_info['filename']}")



        



        # Navigation



        col1, col2, col3 = st.columns([1, 1, 1])



        with col1:



            if st.button("← Indietro"):



                st.session_state.wizard_step = 2



                st.rerun()



        with col3:



            if st.button("✨ Fine", type="primary", disabled=(len(service.target_pdf_uris) == 0)):



                st.session_state.wizard_mode = False



                st.success("🎉 Setup completato! Reindirizzamento all'interfaccia principale...")



                time.sleep(1)



                st.rerun()






    # --- Router for steps ---



    if st.session_state.wizard_step == 0:



        wizard_step_0()



    elif st.session_state.wizard_step == 1:



        wizard_step_1()



    elif st.session_state.wizard_step == 2:



        wizard_step_2()



    elif st.session_state.wizard_step == 3:



        wizard_step_3()



        

# --- Main Logic ---



if st.session_state.get('wizard_mode', True):



    mostra_wizard()



else:



    mostra_interfaccia_principale()