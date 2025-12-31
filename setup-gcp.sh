#!/bin/bash
# PolicyLedger Google Cloud Setup Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}PolicyLedger Google Cloud Setup${NC}"
echo "========================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Error: gcloud CLI not found. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
echo -e "${BLUE}Step 1: Project Configuration${NC}"
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Error: Project ID cannot be empty${NC}"
    exit 1
fi

gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set to: $PROJECT_ID${NC}"
echo ""

# Enable APIs
echo -e "${BLUE}Step 2: Enabling Required APIs${NC}"
echo "This may take a few minutes..."

gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    cloudfunctions.googleapis.com \
    artifactregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    secretmanager.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Create Artifact Registry repository
echo -e "${BLUE}Step 3: Creating Artifact Registry Repository${NC}"
gcloud artifacts repositories create policyledger-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="PolicyLedger container images" \
    2>/dev/null || echo "Repository already exists"

echo -e "${GREEN}✓ Artifact Registry ready${NC}"
echo ""

# Initialize Firestore
echo -e "${BLUE}Step 4: Initializing Firestore${NC}"
gcloud firestore databases create \
    --location=us-central1 \
    --type=firestore-native \
    2>/dev/null || echo "Firestore already initialized"

echo -e "${GREEN}✓ Firestore ready${NC}"
echo ""

# Setup Gemini API Key
echo -e "${BLUE}Step 5: Gemini API Key Setup${NC}"
echo "Get your Gemini API key from: https://makersuite.google.com/app/apikey"
read -p "Enter your Gemini API key (or press Enter to skip): " GEMINI_KEY

if [ ! -z "$GEMINI_KEY" ]; then
    echo -n "$GEMINI_KEY" | gcloud secrets create gemini-api-key \
        --data-file=- \
        --replication-policy="automatic" \
        2>/dev/null || \
    echo -n "$GEMINI_KEY" | gcloud secrets versions add gemini-api-key \
        --data-file=-
    
    echo -e "${GREEN}✓ Gemini API key stored in Secret Manager${NC}"
else
    echo -e "${YELLOW}⚠ Skipped Gemini API key setup${NC}"
fi
echo ""

# Create service accounts
echo -e "${BLUE}Step 6: Creating Service Accounts${NC}"

# API service account
gcloud iam service-accounts create policyledger-api \
    --display-name="PolicyLedger API" \
    2>/dev/null || echo "API service account already exists"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:policyledger-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:policyledger-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None

echo -e "${GREEN}✓ Service accounts configured${NC}"
echo ""

# Create environment file
echo -e "${BLUE}Step 7: Creating Local Environment File${NC}"
cat > backend/.env.local << EOF
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
EOF

echo -e "${GREEN}✓ Created backend/.env.local${NC}"
echo ""

# Setup complete
echo -e "${GREEN}========================================"
echo "✓ Google Cloud Setup Complete!"
echo "========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Test locally: cd backend && source .env.local && python start_server.py"
echo "2. Deploy to Cloud Run: gcloud builds submit --config=cloudbuild.yaml"
echo "3. Monitor logs: gcloud run logs tail policyledger-api"
echo ""
echo "For detailed deployment guide, see: checklist.md"
