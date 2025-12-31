# PolicyLedger Google Cloud Setup Script (PowerShell)
# Run this on Windows to setup Google Cloud integration

Write-Host "PolicyLedger Google Cloud Setup" -ForegroundColor Blue
Write-Host "========================================" 
Write-Host ""

# Check if gcloud is installed
try {
    gcloud version | Out-Null
} catch {
    Write-Host "Error: gcloud CLI not found. Please install it first." -ForegroundColor Yellow
    Write-Host "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Get project ID
Write-Host "Step 1: Project Configuration" -ForegroundColor Blue
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"

if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "Error: Project ID cannot be empty" -ForegroundColor Yellow
    exit 1
}

gcloud config set project $PROJECT_ID
Write-Host "✓ Project set to: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Enable APIs
Write-Host "Step 2: Enabling Required APIs" -ForegroundColor Blue
Write-Host "This may take a few minutes..."

gcloud services enable `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    firestore.googleapis.com `
    aiplatform.googleapis.com `
    cloudfunctions.googleapis.com `
    artifactregistry.googleapis.com `
    logging.googleapis.com `
    monitoring.googleapis.com `
    secretmanager.googleapis.com

Write-Host "✓ APIs enabled" -ForegroundColor Green
Write-Host ""

# Create Artifact Registry repository
Write-Host "Step 3: Creating Artifact Registry Repository" -ForegroundColor Blue
gcloud artifacts repositories create policyledger-repo `
    --repository-format=docker `
    --location=us-central1 `
    --description="PolicyLedger container images" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Repository already exists" -ForegroundColor Yellow
}

Write-Host "✓ Artifact Registry ready" -ForegroundColor Green
Write-Host ""

# Initialize Firestore
Write-Host "Step 4: Initializing Firestore" -ForegroundColor Blue
gcloud firestore databases create `
    --location=us-central1 `
    --type=firestore-native 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Firestore already initialized" -ForegroundColor Yellow
}

Write-Host "✓ Firestore ready" -ForegroundColor Green
Write-Host ""

# Setup Gemini API Key
Write-Host "Step 5: Gemini API Key Setup" -ForegroundColor Blue
Write-Host "Get your Gemini API key from: https://makersuite.google.com/app/apikey"
$GEMINI_KEY = Read-Host "Enter your Gemini API key (or press Enter to skip)"

if (![string]::IsNullOrWhiteSpace($GEMINI_KEY)) {
    $GEMINI_KEY | gcloud secrets create gemini-api-key `
        --data-file=- `
        --replication-policy="automatic" 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        $GEMINI_KEY | gcloud secrets versions add gemini-api-key --data-file=-
    }
    
    Write-Host "✓ Gemini API key stored in Secret Manager" -ForegroundColor Green
} else {
    Write-Host "⚠ Skipped Gemini API key setup" -ForegroundColor Yellow
}
Write-Host ""

# Create service accounts
Write-Host "Step 6: Creating Service Accounts" -ForegroundColor Blue

gcloud iam service-accounts create policyledger-api `
    --display-name="PolicyLedger API" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "API service account already exists" -ForegroundColor Yellow
}

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:policyledger-api@$PROJECT_ID.iam.gserviceaccount.com" `
    --role="roles/datastore.user" `
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:policyledger-api@$PROJECT_ID.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor" `
    --condition=None

Write-Host "✓ Service accounts configured" -ForegroundColor Green
Write-Host ""

# Create environment file
Write-Host "Step 7: Creating Local Environment File" -ForegroundColor Blue
@"
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
VERTEX_AI_LOCATION=us-central1
FIRESTORE_DATABASE=(default)
ENABLE_GCP=true

# Gemini API Key
GEMINI_API_KEY=$GEMINI_KEY
GOOGLE_API_KEY=$GEMINI_KEY

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
"@ | Out-File -FilePath "backend\.env.local" -Encoding UTF8

Write-Host "✓ Created backend\.env.local" -ForegroundColor Green
Write-Host ""

# Setup complete
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Google Cloud Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test locally: cd backend; python start_server.py"
Write-Host "2. Deploy to Cloud Run: gcloud builds submit --config=cloudbuild.yaml"
Write-Host "3. Monitor logs: gcloud run logs tail policyledger-api"
Write-Host ""
Write-Host "For detailed deployment guide, see: checklist.md"
