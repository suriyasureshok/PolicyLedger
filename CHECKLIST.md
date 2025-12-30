# PolicyLedger: Google Cloud Deployment Checklist

**Complete deployment guide for running PolicyLedger on Google Cloud Platform**

---

## 📋 Overview

This checklist covers deploying PolicyLedger to Google Cloud Platform (GCP) with production-grade infrastructure including:
- Firestore for distributed ledger storage
- Vertex AI for scalable policy verification
- Cloud Run for API hosting
- Gemini API for AI-powered explanations
- Cloud Functions for event-driven workflows

---

## ✅ Pre-Deployment Checklist

### 1. Google Cloud Project Setup

- [ ] **Create GCP Project**
  ```bash
  gcloud projects create policyledger-prod --name="PolicyLedger Production"
  gcloud config set project policyledger-prod
  ```

- [ ] **Enable Required APIs**
  ```bash
  gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    cloudfunctions.googleapis.com \
    artifactregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
  ```

- [ ] **Set Up Billing**
  - Link billing account to project
  - Set up budget alerts
  - Configure cost controls

### 2. Authentication & IAM

- [ ] **Create Service Accounts**
  ```bash
  # Verifier service account
  gcloud iam service-accounts create policyledger-verifier \
    --display-name="PolicyLedger Verifier"
  
  # API service account
  gcloud iam service-accounts create policyledger-api \
    --display-name="PolicyLedger API"
  
  # Cloud Functions service account
  gcloud iam service-accounts create policyledger-functions \
    --display-name="PolicyLedger Functions"
  ```

- [ ] **Assign IAM Roles**
  ```bash
  # Verifier permissions
  gcloud projects add-iam-policy-binding policyledger-prod \
    --member="serviceAccount:policyledger-verifier@policyledger-prod.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
  
  gcloud projects add-iam-policy-binding policyledger-prod \
    --member="serviceAccount:policyledger-verifier@policyledger-prod.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
  ```

- [ ] **Download Service Account Keys** (for local testing)
  ```bash
  gcloud iam service-accounts keys create ~/policyledger-api-key.json \
    --iam-account=policyledger-api@policyledger-prod.iam.gserviceaccount.com
  
  export GOOGLE_APPLICATION_CREDENTIALS=~/policyledger-api-key.json
  ```

### 3. Environment Configuration

- [ ] **Create Environment Variables File**
  ```bash
  cat > .env.production << EOF
  GOOGLE_CLOUD_PROJECT=policyledger-prod
  FIRESTORE_DATABASE=(default)
  GEMINI_API_KEY=your_gemini_api_key_here
  VERTEX_AI_LOCATION=us-central1
  ENVIRONMENT=production
  EOF
  ```

- [ ] **Set Up Gemini API Key**
  - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Create new API key
  - Store in Secret Manager:
    ```bash
    echo -n "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-
    ```

---

## 🗄️ Firestore Setup

### 1. Initialize Firestore

- [ ] **Create Firestore Database**
  ```bash
  gcloud firestore databases create --location=us-central1 --type=firestore-native
  ```

### 2. Configure Security Rules

- [ ] **Create Firestore Security Rules**
  ```javascript
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      // Ledger entries are append-only
      match /ledger_entries/{policyHash} {
        allow read: if true;
        allow create: if request.auth != null;
        allow update, delete: if false; // Immutable
      }
      
      // Policies can be written by API
      match /policies/{policyHash} {
        allow read: if true;
        allow write: if request.auth != null;
      }
      
      // Verification jobs
      match /verification_jobs/{jobId} {
        allow read: if true;
        allow write: if request.auth != null;
      }
    }
  }
  ```

---

## 🚀 Cloud Run Deployment (API Server)

### 1. Containerize Application

- [ ] **Build Container Image**
  ```bash
  cd backend
  docker build -t us-central1-docker.pkg.dev/policyledger-prod/policyledger-repo/api:v1 .
  ```

- [ ] **Push to Artifact Registry**
  ```bash
  docker push us-central1-docker.pkg.dev/policyledger-prod/policyledger-repo/api:v1
  ```

### 2. Deploy to Cloud Run

- [ ] **Deploy Service**
  ```bash
  gcloud run deploy policyledger-api \
    --image=us-central1-docker.pkg.dev/policyledger-prod/policyledger-repo/api:v1 \
    --platform=managed \
    --region=us-central1 \
    --service-account=policyledger-api@policyledger-prod.iam.gserviceaccount.com \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=policyledger-prod" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --max-instances=10
  ```

---

## 🧠 Vertex AI Setup (Policy Verification)

- [ ] **Create Custom Training Container**
- [ ] **Configure Verification Jobs**
- [ ] **Test Vertex AI Job Submission**

---

## ⚡ Cloud Functions Setup

### 1. Ledger Update Trigger

- [ ] **Deploy Firestore Trigger Function**
  ```bash
  gcloud functions deploy on-ledger-update \
    --gen2 \
    --runtime=python310 \
    --region=us-central1 \
    --source=functions/on_ledger_update \
    --entry-point=on_ledger_update \
    --trigger-event-filters="type=google.cloud.firestore.document.v1.created"
  ```

---

## 🌐 Frontend Deployment

### 1. Build Frontend

- [ ] **Build Production Bundle**
  ```bash
  cd frontend/policy-ledger-insights
  npm run build
  ```

### 2. Deploy to Firebase Hosting

- [ ] **Deploy to Firebase Hosting**
  ```bash
  firebase deploy --only hosting
  ```

---

## 📊 Monitoring & Logging

- [ ] **Set Up Cloud Logging**
- [ ] **Create Monitoring Dashboard**
- [ ] **Configure Alerts**
- [ ] **Enable Error Reporting**

---

## 🔐 Security Hardening

- [ ] **Enable Cloud Armor** (DDoS protection)
- [ ] **Set Up API Keys**
- [ ] **Configure VPC Service Controls**
- [ ] **Rotate Service Account Keys Regularly**

---

## 🧪 Testing & Validation

- [ ] **Test Firestore Connection**
- [ ] **Test Gemini API**
- [ ] **Test Vertex AI Access**
- [ ] **End-to-End Workflow Test**
- [ ] **Load Testing**

---

## 💰 Cost Optimization

- [ ] **Set Cloud Run Min Instances to 0**
- [ ] **Configure Firestore Backup Retention**
- [ ] **Enable Committed Use Discounts**
- [ ] **Create Budget Alerts**

---

## ✅ Post-Deployment Checklist

- [ ] **Verify all services are running**
- [ ] **Test complete workflow**
- [ ] **Check monitoring dashboards**
- [ ] **Verify logging is working**
- [ ] **Test error alerting**
- [ ] **Document service URLs**

---

**Last Updated**: December 30, 2025  
**Version**: 1.0
