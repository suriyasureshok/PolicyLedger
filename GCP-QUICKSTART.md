# Google Cloud Quick Start Guide

## Prerequisites

1. **Google Cloud Account** - Sign up at [cloud.google.com](https://cloud.google.com)
2. **gcloud CLI** - Install from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
3. **Gemini API Key** - Get from [makersuite.google.com](https://makersuite.google.com/app/apikey)

## One-Command Setup (Recommended)

### Windows (PowerShell)
```powershell
.\setup-gcp.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x setup-gcp.sh
./setup-gcp.sh
```

This script will:
- ✅ Enable all required Google Cloud APIs
- ✅ Create Firestore database
- ✅ Set up Artifact Registry
- ✅ Configure service accounts
- ✅ Store Gemini API key in Secret Manager
- ✅ Create local `.env.local` file

## Manual Setup (Alternative)

### 1. Create Google Cloud Project

```bash
gcloud projects create policyledger-demo
gcloud config set project policyledger-demo
```

### 2. Enable APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Initialize Firestore

```bash
gcloud firestore databases create --location=us-central1
```

### 4. Store Gemini API Key

```bash
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
```

### 5. Create Local Environment File

Create `backend/.env`:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
ENABLE_GCP=true
GEMINI_API_KEY=your-gemini-api-key
VERTEX_AI_LOCATION=us-central1
```

## Testing Locally with GCP

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run with GCP Integration

```bash
# Load environment variables
set -a
source .env
set +a

# Start server
python start_server.py
```

### 3. Test Firestore Connection

```bash
curl http://localhost:8000/ledger
```

## Deploying to Cloud Run

### Option 1: Using Cloud Build (Recommended)

```bash
gcloud builds submit --config=cloudbuild.yaml
```

### Option 2: Manual Deploy

```bash
# Build image
cd backend
docker build -t gcr.io/PROJECT_ID/policyledger-api .

# Push to registry
docker push gcr.io/PROJECT_ID/policyledger-api

# Deploy
gcloud run deploy policyledger-api \
  --image gcr.io/PROJECT_ID/policyledger-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=PROJECT_ID,ENABLE_GCP=true \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

## Verification

### 1. Check Service Health

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe policyledger-api --region us-central1 --format 'value(status.url)')

# Test endpoint
curl $SERVICE_URL/health
```

### 2. Test Firestore Integration

```bash
curl $SERVICE_URL/ledger
```

### 3. View Logs

```bash
gcloud run logs tail policyledger-api
```

## Monitoring

### View Dashboard

```bash
# Open Cloud Console
gcloud run services describe policyledger-api --region us-central1 --format 'value(status.url)' | xargs -I {} open https://console.cloud.google.com/run
```

### Real-time Logs

```bash
gcloud run logs tail policyledger-api --log-filter="severity>=WARNING"
```

## Troubleshooting

### Common Issues

1. **Firestore Permission Denied**
   - Ensure service account has `roles/datastore.user`
   - Check Firestore security rules

2. **Secret Not Found**
   - Verify secret exists: `gcloud secrets list`
   - Grant access: `gcloud secrets add-iam-policy-binding gemini-api-key --member=serviceAccount:... --role=roles/secretmanager.secretAccessor`

3. **Build Fails**
   - Check Docker is installed
   - Verify Artifact Registry is enabled
   - Check cloudbuild.yaml syntax

### Get Help

- Cloud Run docs: [cloud.google.com/run/docs](https://cloud.google.com/run/docs)
- Firestore docs: [cloud.google.com/firestore/docs](https://cloud.google.com/firestore/docs)
- Full checklist: See [checklist.md](checklist.md)

## Cost Estimation

### Free Tier (Monthly)
- Cloud Run: 2M requests
- Firestore: 50K reads, 20K writes
- Gemini API: Varies by model

### Typical Usage (Small Project)
- Estimated cost: $5-20/month
- Set budget alerts in Cloud Console

## Next Steps

1. ✅ Complete setup using script
2. ✅ Test locally with `.env.local`
3. ✅ Deploy to Cloud Run
4. 🚀 Use in production!

For detailed deployment options, see [checklist.md](checklist.md)
