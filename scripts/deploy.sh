#!/bin/bash
# Google Cloud Run Deployment Script for AI Tools Wiki Slack Bot

set -e  # Exit on any error

echo "🚀 Deploying AI Tools Wiki Slack Bot to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get the current project ID
PROJECT_ID=$(gcloud config get-value project)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No Google Cloud project is set."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Deploying to project: $PROJECT_ID"

# Check if required APIs are enabled
echo "🔧 Ensuring required APIs are enabled..."
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Prompt user to verify secrets exist
echo ""
echo "⚠️  Before deploying, ensure you have created the following secrets:"
echo "   - slack-bot-token (your Slack Bot Token)"
echo "   - slack-signing-secret (your Slack Signing Secret)"
echo ""
echo "To create secrets, run:"
echo "   echo -n 'your-token' | gcloud secrets create slack-bot-token --data-file=-"
echo "   echo -n 'your-secret' | gcloud secrets create slack-signing-secret --data-file=-"
echo ""
read -p "Have you created the required secrets? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please create the secrets first, then run this script again."
    exit 1
fi

# Grant Secret Manager access to the service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "🔐 Granting Secret Manager Secret Accessor role to $SERVICE_ACCOUNT..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --condition=None > /dev/null

echo "🤖 Granting AI Platform User role to $SERVICE_ACCOUNT..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/aiplatform.user" --condition=None > /dev/null

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy aitools-wiki-bot \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=production" \
    --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,SLACK_SIGNING_SECRET=slack-signing-secret:latest"

# Get the service URL
echo "📍 Getting service URL..."
SERVICE_URL=$(gcloud run services describe aitools-wiki-bot \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)')

echo ""
echo "✅ Deployment successful!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Health check: $SERVICE_URL/health"
echo "🤖 Slack events endpoint: $SERVICE_URL/slack/events"
echo ""
echo "🔧 Next steps:"
echo "1. Update your Slack app configuration at https://api.slack.com"
echo "2. Set Event Subscriptions Request URL to: $SERVICE_URL/slack/events"
echo "3. Set Slash Commands Request URL to: $SERVICE_URL/slack/events"
echo "4. Set Interactivity Request URL to: $SERVICE_URL/slack/events"
echo "5. Test the health endpoint: curl $SERVICE_URL/health"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT_GUIDE.md"
