# Guida al Deployment

Questa guida documenta il processo per il deployment e l'aggiornamento dell'applicazione Checklist Agent su Google Cloud Run.

---

## 1. Configurazione Iniziale (Una Tantum)

Questi passaggi devono essere eseguiti solo una volta per la configurazione iniziale del progetto.

### 1.1. Configurazione dell'Ambiente GCP

Le seguenti risorse sono state configurate nel progetto GCP `<REDACTED_PROJECT_ID>`:

1.  **API Abilitate:** È stato confermato che le seguenti API sono abilitate:
    *   Cloud Run API (`run.googleapis.com`)
    *   Artifact Registry API (`artifactregistry.googleapis.com`)
    *   Cloud Build API (`cloudbuild.googleapis.com`)

2.  **Repository di Artifact Registry:** È stato creato un repository per archiviare le immagini Docker.
    *   **Comando:**
        ```bash
        gcloud artifacts repositories create checklist-agent-repo \
          --repository-format=docker \
          --location=europe-west1 \
          --description="Repository for checklist-agent images"
        ```

3.  **Service Account:** È stato identificato un service account esistente con i permessi necessari (`roles/ml.admin`) per l'applicazione.
    *   **Service Account Selezionato:** `<REDACTED_SERVICE_ACCOUNT>`

### 1.2. Configurazione dell'Ambiente Locale

1.  **Dockerfile:** Un file `Dockerfile` è stato creato nella root del progetto per definire l'immagine del container.

2.  **Autenticazione Docker:** Il client Docker della tua macchina locale è stato configurato per autenticarsi con Artifact Registry.
    *   **Comando:**
        ```bash
        gcloud auth configure-docker europe-west1-docker.pkg.dev
        ```

---

## 2. Processo di Deployment (Da ripetere per ogni aggiornamento)

Segui questi passaggi ogni volta che vuoi rilasciare una nuova versione dell'applicazione.

### Passo 2.1: Costruisci l'Immagine Docker (Macchina Locale)

Dalla directory principale del tuo progetto, esegui il comando `docker build`. Questo impacchetta la tua applicazione in un'immagine container.

```bash
docker build -t europe-west1-docker.pkg.dev/<REDACTED_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest .
```

### Passo 2.2: Pubblica l'Immagine Docker (Macchina Locale)

Esegui il "push" dell'immagine appena creata su Artifact Registry.

```bash
docker push europe-west1-docker.pkg.dev/<REDACTED_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest
```

### Passo 2.3: Esegui il Deploy su Cloud Run

Esegui il deploy della nuova immagine su Cloud Run. Questo comando può essere lanciato dalla tua macchina locale o da Cloud Shell.



```bash
gcloud run deploy checklist-agent \
  --image=europe-west1-docker.pkg.dev/<REDACTED_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest \
  --region=europe-west1 \
  --service-account=<REDACTED_SERVICE_ACCOUNT> \
  --allow-unauthenticated \
  --set-env-vars="AUTH_MODE=ADC" \
  --set-env-vars="GCP_PROJECT_ID=<REDACTED_PROJECT_ID>" \
  --set-env-vars="GCP_REGION=europe-west1" \
  --platform=managed
```
