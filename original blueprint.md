# **PROJECT BLUEPRINT V4: ADK Multi-Agent Compliance System**

## **1\. Project Overview**

Sviluppo di una piattaforma di Compliance assistita basata su Google Agent Development Kit (ADK).  
Il sistema utilizza un'architettura Multi-Agente per analizzare documenti di progetto e compilare checklist di sicurezza bancaria.  
Core Philosophy: Collaborative Intelligence. L'utente non si limita a correggere l'output, ma dialoga con l'Agente sui singoli punti per capire il ragionamento e raffinare la risposta.

## **2\. Tech Stack Constraints (ADK Based)**

* **Framework Agenti:** Google ADK (Python SDK).  
* **Modello AI:** Google Gemini 2.5 (Flash per routing, Pro per analisi profonda).  
* **Deployment:** Cloud Run (Containerizzazione dell'ADK Runtime).  
* **Frontend:** Streamlit (Client Web che chiama le API dell'ADK Agent).  
* **Input Dati:** PDF/Docx (Documenti) \+ Excel/JSON (Checklist).

## **3\. The "Team": Multi-Agent Architecture**

Utilizziamo il pattern **"Hierarchical Delegation"** dell'ADK.

### **🕵️‍♂️ Agent 1: The Orchestrator (Supervisor)**

* **Ruolo:** Il Capo Progetto.  
* **Compito:** Riceve la richiesta, pianifica il lavoro e delega. Gestisce lo stato della sessione.  
* **Tool:** delegate\_to\_auditor, read\_checklist\_file, export\_results.

### **📚 Agent 2: The Librarian (Document Retrieval)**

* **Ruolo:** L'Archivista.  
* **Compito:** Ha accesso ai file PDF. Trova i paragrafi rilevanti ("Grounding").  
* **Tool:** search\_documents (RAG o Context Caching su Gemini 2.5).

### **⚖️ Agent 3: The Auditor (Compliance Specialist)**

* **Ruolo:** L'Esperto di Rischi.  
* **Compito:** Valuta la conformità iniziale. Gestisce anche il **Q\&A contestuale** con l'utente (spiega il perché, cerca altre prove se richiesto).  
* **Tool:** Nessuno (ragionamento puro basato sui dati del Librarian).

## **4\. Data Flow & User Loop**

1. **Ingestion & Setup:**  
   * Utente carica PDF e Excel.  
   * Il sistema inizializza lo st.session\_state.  
2. **AI Analysis (Batch Iniziale):**  
   * L'Orchestrator cicla su tutte le righe dell'Excel.  
   * Per ogni riga: Librarian trova info \-\> Auditor propone una risposta \-\> Stato salvato come "Draft".  
3. **Collaborative Review (The "Dialogue Loop"):**  
   * L'utente clicca su una domanda specifica (es. "Crittografia").  
   * Si apre una **Chat dedicata** a quella domanda.  
   * L'Agente spiega: *"Ho messo SÌ perché a pag.12..."*  
   * L'Utente può chiedere: *"Sei sicuro? Controlla se si parla di RSA"*.  
   * L'Agente (Auditor) rilegge, risponde e se necessario **aggiorna** la proposta di risposta nella tabella.  
4. **Finalization:**  
   * Quando l'utente è soddisfatto della conversazione, clicca Conferma e Chiudi Punto.  
   * Lo stato diventa VALIDATED.  
5. **Export:**  
   * Generazione Excel finale.

## **5\. UI/UX Specifications (Dashboard)**

**Sidebar (Session Controls)**

* **Project Area:**  
  * Upload PDF (Multiplo).  
  * Upload Checklist (Excel).  
* **Actions:**  
  * 🟢 Avvia Analisi  
  * 🗑️ Nuova Sessione  
* **Export:**  
  * 💾 Download Excel

**Main Area (Split Screen)**

* **Sinistra: The Checklist Grid**  
  * Tabella interattiva (Dataframe).  
  * Cliccando su una riga, si "attiva" il focus sulla destra.  
  * Indicatori visivi dello stato della discussione (es. 💬 in corso, ✅ conclusa).  
* **Destra: The Contextual Chat (Focus Mode)**  
  * **Titolo:** Testo completo della domanda selezionata a sinistra.  
  * **History:** Cronologia della conversazione *solo per questa domanda*.  
    * *Msg 1 (AI):* "Ecco la mia analisi iniziale..."  
    * *Msg 2 (User):* "Spiegami meglio questo punto."  
    * *Msg 3 (AI):* "Certamente, nel documento X..."  
  * **Action Panel (Bottom):**  
    * Input box per chattare.  
    * Button ✅ Accetta Risposta Corrente (Blocca la modifica e aggiorna l'Excel in memoria).  
    * Button ✏️ Forza Modifica Manuale (Se l'utente vuole scrivere la risposta finale a mano ignorando la chat).

## **6\. Output Specification (Excel Strategy)**

File Excel generato con colonne aggiunte:

| Colonna Orig. | AI\_Proposal | Discussion\_Log | Final\_Answer | Status |
| :---- | :---- | :---- | :---- | :---- |
| Domanda 1 | Sì, AES-256 | *User ha chiesto chiarimenti su RSA...* | Sì, RSA 2048 | VALIDATED |

## **7\. Implementation Plan (ADK Focused)**

1. **Setup ADK:** Inizializzare adk-python.  
2. **Excel Handler:** Parsing Excel.  
3. **Agent Logic:**  
   * L'Auditor deve essere "Stateful": ricordare il contesto della singola domanda durante la chat.  
4. **UI Interactivity:**  
   * Implementare una chat window st.chat\_message che si pulisce e ricarica ogni volta che cambio selezione nella tabella a sinistra.