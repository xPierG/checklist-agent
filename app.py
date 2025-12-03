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
        st.success("Compliance Service Initialized")
    except Exception as e:
        st.error(f"Failed to initialize service: {e}")
        st.stop()

service = st.session_state.service

# Sidebar
with st.sidebar:
    st.title("Compliance Agent")
    
    # PDF Upload
    uploaded_pdf = st.file_uploader("Upload Policy Document (PDF)", type="pdf")
    if uploaded_pdf:
        # Save to temp file
        temp_path = f"temp_{uploaded_pdf.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        
        if st.button("Process PDF"):
            with st.spinner("Uploading to Gemini..."):
                uri = service.load_pdf(temp_path)
                st.success(f"PDF Loaded: {uri}")
                os.remove(temp_path)

    # Checklist Upload
    uploaded_excel = st.file_uploader("Upload Checklist (Excel)", type=["xlsx", "xls"])
    if uploaded_excel:
        if st.button("Load Checklist"):
            df = service.load_checklist(uploaded_excel)
            st.session_state.checklist_df = df
            st.success("Checklist Loaded")

# Main Area
if "checklist_df" in st.session_state:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Checklist")
        df = st.session_state.checklist_df
        
        # Display Data Grid
        # We use a simple dataframe display. For interactivity, we might need st.data_editor in future
        st.dataframe(df, use_container_width=True)
        
        # Row Selection
        row_indices = df.index.tolist()
        selected_row = st.selectbox("Select Row to Analyze/Discuss", row_indices)
        
        if st.button("Analyze Selected Row"):
            question = df.at[selected_row, "Domanda"] if "Domanda" in df.columns else df.iloc[selected_row, 0]
            with st.spinner("Agent is analyzing..."):
                response = service.analyze_row(selected_row, str(question))
                st.session_state.checklist_df = service.get_dataframe() # Refresh
                st.rerun()

    with col2:
        st.subheader("Contextual Chat")
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
    st.info("Please upload a checklist to begin.")
