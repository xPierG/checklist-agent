# Deployment Guide

This guide documents the process for deploying and updating the Checklist Agent application on Google Cloud Run.

---

## 1. Initial Setup (One-Time)

These steps should be performed once for the initial project configuration.

### 1.1. GCP Environment Configuration

The following resources need to be configured in your GCP project:

1.  **Enable APIs:** Ensure the following APIs are enabled:
    *   Cloud Run API (`run.googleapis.com`)
    *   Artifact Registry API (`artifactregistry.googleapis.com`)
    *   Cloud Build API (`cloudbuild.googleapis.com`)

2.  **Create Artifact Registry Repository:** Create a repository to store Docker images.
    ```bash
    gcloud artifacts repositories create checklist-agent-repo \
      --repository-format=docker \
      --location=<YOUR_GCP_REGION> \
      --description="Repository for checklist-agent images"
    ```

3.  **Service Account:** Identify or create a service account with the necessary permissions (e.g., `roles/ml.admin` for Vertex AI access).

### 1.2. Local Environment Configuration

1.  **Dockerfile:** A `Dockerfile` is included in the project root to define the container image.

2.  **Docker Authentication:** Configure your local Docker client to authenticate with Artifact Registry.
    ```bash
    gcloud auth configure-docker <YOUR_GCP_REGION>-docker.pkg.dev
    ```

---

## 2. Deployment Process (Repeat for Each Update)

Follow these steps each time you want to release a new version of the application.

### Step 2.1: Build the Docker Image (Local Machine)

From the project root directory, run the `docker build` command.

```bash
docker build -t <YOUR_GCP_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest .
```

### Step 2.2: Push the Docker Image (Local Machine)

Push the newly created image to Artifact Registry.

```bash
docker push <YOUR_GCP_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest
```

### Step 2.3: Deploy to Cloud Run

Deploy the new image to Cloud Run.

```bash
gcloud run deploy checklist-agent \
  --image=<YOUR_GCP_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/checklist-agent-repo/checklist-agent:latest \
  --region=<YOUR_GCP_REGION> \
  --service-account=<YOUR_SERVICE_ACCOUNT_EMAIL> \
  --allow-unauthenticated \
  --set-env-vars="AUTH_MODE=ADC" \
  --set-env-vars="GCP_PROJECT_ID=<YOUR_PROJECT_ID>" \
  --set-env-vars="GCP_REGION=<YOUR_GCP_REGION>" \
  --platform=managed
```

---

## Configuration Placeholders

Replace the following placeholders with your actual values:

| Placeholder | Description | Example |
|---|---|---|
| `<YOUR_PROJECT_ID>` | Your GCP Project ID | `my-gcp-project` |
| `<YOUR_GCP_REGION>` | GCP Region for deployment | `europe-west1` |
| `<YOUR_SERVICE_ACCOUNT_EMAIL>` | Service Account email | `sa-name@project.iam.gserviceaccount.com` |
