# AI Tools Wiki Bot - Deployment Guide

This comprehensive guide covers deploying your AI Tools Wiki Slack Bot to Google Cloud Run for production use.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Google Cloud SDK** installed and authenticated
2. **Docker** installed on your local machine (optional for Cloud Build)
3. **Google Cloud Project** with billing enabled
4. **Required APIs** enabled in your project
5. **Slack App** configured (covered in this guide)

## 🚀 Quick Deploy (Recommended)

For fastest setup, use the automated deployment script:

```bash
# 1. Set up Google Cloud project and authenticate
gcloud config set project YOUR_PROJECT_ID
gcloud auth login

# 2. Create secrets for Slack tokens
echo -n 'your-bot-token' | gcloud secrets create slack-bot-token --data-file=-
echo -n 'your-signing-secret' | gcloud secrets create slack-signing-secret --data-file=-

# 3. Set up database
uv pip install -r requirements.txt 
python scripts/setup.py

# 4. Deploy with the automated script
./scripts/deploy.sh
```

## 🔧 Step-by-Step Manual Setup

### Step 1: Google Cloud Platform Setup

#### 1.1 Create/Select Project
```bash
# Login to GCP
gcloud auth login

# Create a new project (or use existing)
gcloud projects create aitools-wiki-bot-RANDOMID --name="AI Tools Wiki Bot"

# Set as active project
gcloud config set project aitools-wiki-bot-RANDOMID
```

#### 1.2 Enable Required APIs
```bash
# Enable all required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com
```

#### 1.3 Set Up Service Account (Optional)
```bash
# Get your project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Create service account
gcloud iam service-accounts create aitools-bot \
    --display-name="AI Tools Wiki Bot Service Account" \
    --description="Service account for AI Tools Wiki Slack Bot"

# Grant required permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

### Step 2: Slack App Setup

#### 2.1 Create Slack App
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. App Name: `AI Tools Wiki Bot`
4. Choose your workspace
5. Click **"Create App"**

#### 2.2 Configure Bot Permissions
1. Go to **"OAuth & Permissions"** in the left sidebar
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `app_mentions:read`
   - `channels:read`
   - `chat:write`
   - `commands`
   - `groups:read`
   - `im:read`
   - `mpim:read`

#### 2.3 Create Slash Commands
Create these commands in **"Slash Commands"** (use placeholder URL for now):

| Command | Description | Usage Hint |
|---------|-------------|------------|
| `/aitools` | Show help for AI Tools Wiki Bot | |
| `/aitools-add` | Add a new AI tool | `<title> | <url or description>` |
| `/aitools-search` | Search for AI tools | `<keyword>` |
| `/aitools-list` | List trending AI tools | `[tag]` |
| `/aitools-top` | Show top AI tools by score | `[limit]` |
| `/aitools-tags` | Show available tags | |
| `/aitools-suggest-tag` | Suggest community tags | `<entry_id> <tag>` |

#### 2.4 Enable Event Subscriptions (Production Only)
1. Go to **"Event Subscriptions"**
2. Enable Events: **On**
3. Request URL: `https://your-cloud-run-url/slack/events` (update after deployment)
4. Subscribe to Bot Events:
   - `app_mention`
   - `message.im`

#### 2.5 Enable Interactivity (Production Only)
1. Go to **"Interactivity & Shortcuts"**
2. Enable Interactivity: **On**
3. Request URL: `https://your-cloud-run-url/slack/events` (update after deployment)

#### 2.6 Install App to Workspace
1. Go to **"Install App"**
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **📋 Copy the Bot User OAuth Token** (starts with `xoxb-`)

#### 2.7 Get App Credentials
1. Go to **"Basic Information"**
2. **📋 Copy the Signing Secret** from App Credentials

### Step 3: Set Up Database

Run the comprehensive setup script:

```bash
# Configure environment variables first
cp .env.example .env
# Edit .env with your Google Cloud project details

# Set up BigQuery dataset and tables
python scripts/setup.py
```

### Step 4: Deploy to Cloud Run

#### 4.1 Store Secrets in Google Secret Manager

```bash
# Store Slack Bot Token
echo -n "xoxb-your-bot-token" | gcloud secrets create slack-bot-token --data-file=-

# Store Slack Signing Secret
echo -n "your-signing-secret" | gcloud secrets create slack-signing-secret --data-file=-

# Grant Cloud Run access to secrets (using default compute service account)
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding slack-bot-token \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding slack-signing-secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### 4.2 Deploy to Cloud Run

```bash
# Set your project ID
export PROJECT_ID=$(gcloud config get-value project)

# Deploy to Cloud Run
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
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=aitools_wiki,ENVIRONMENT=production,VERTEX_LOCATION=us-central1" \
    --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,SLACK_SIGNING_SECRET=slack-signing-secret:latest"
```

#### 4.3 Get Your Cloud Run URL

```bash
gcloud run services describe aitools-wiki-bot \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

### Step 5: Configure Slack App for Production

Update your Slack app with the Cloud Run URL:

1. **Event Subscriptions**: Update Request URL to `https://your-cloud-run-url/slack/events`
2. **Slash Commands**: Update all command URLs to `https://your-cloud-run-url/slack/events`
3. **Interactivity**: Update Request URL to `https://your-cloud-run-url/slack/events`

### Step 6: Verify Deployment

#### 6.1 Test Health Endpoint
```bash
curl https://your-cloud-run-url/health
```
Expected response: `{"status":"healthy"}`

#### 6.2 Test Slack Commands
In your Slack workspace, try:
- `/aitools` - Should show help text
- `/aitools-add Test Tool | A test tool for verification`
- `/aitools-list` - Should show the test tool
- `/aitools-top 5` - Should show top 5 tools

## 📊 Monitoring and Operations

### View Logs
```bash
# Stream logs in real-time
gcloud run services logs tail aitools-wiki-bot --region us-central1

# View recent logs
gcloud run services logs read aitools-wiki-bot \
    --platform managed \
    --region us-central1 \
    --limit 50
```

### Monitor Performance
```bash
# View service details
gcloud run services describe aitools-wiki-bot \
    --platform managed \
    --region us-central1
```

### Update Deployment
For future updates:
```bash
gcloud run deploy aitools-wiki-bot \
    --source . \
    --platform managed \
    --region us-central1
```

## 🔧 Troubleshooting

### Common Issues

#### 1. 503 Service Unavailable
- **Check**: App binding to `0.0.0.0:8080`
- **Check**: PORT environment variable set correctly
- **Check**: Application startup logs for errors

#### 2. Slack Events Not Working
- **Check**: Cloud Run service allows unauthenticated requests
- **Check**: Event Subscription URL matches Cloud Run URL exactly
- **Check**: `/slack/events` endpoint configured correctly

#### 3. BigQuery Permission Errors
- **Check**: Service account has BigQuery permissions
- **Check**: Dataset exists in correct project
- **Check**: `GOOGLE_CLOUD_PROJECT` environment variable is correct

#### 4. AI Service Errors
- **Check**: Vertex AI API is enabled
- **Check**: Service account has `aiplatform.user` role
- **Check**: `VERTEX_LOCATION` is set correctly

#### 5. Secret Manager Errors
- **Check**: Secrets exist and have correct names
- **Check**: Service account has `secretmanager.secretAccessor` role
- **Check**: Secret names match environment variable references

### Debug Commands
```bash
# Check service status
gcloud run services list

# View detailed service info
gcloud run services describe aitools-wiki-bot --region us-central1

# Check secrets
gcloud secrets list

# Test BigQuery connection
bq query --use_legacy_sql=false "SELECT 1 as test"
```

## 🔒 Security Best Practices

1. **Use Secret Manager** for all sensitive data
2. **Enable Binary Authorization** for production workloads
3. **Use least-privilege IAM** roles
4. **Set up monitoring and alerting** for security events
5. **Regularly rotate secrets** and service account keys
6. **Enable audit logging** for Cloud Run and BigQuery

## 💰 Cost Optimization

1. **Set min-instances to 0** to avoid idle costs
2. **Use appropriate CPU and memory** allocations
3. **Monitor request patterns** and adjust scaling settings
4. **Set up budget alerts** in Google Cloud Console
5. **Monitor BigQuery usage** and optimize queries

## 📈 Next Steps After Deployment

1. **Set up monitoring** with Google Cloud Monitoring
2. **Configure alerting** for critical failures
3. **Implement CI/CD pipeline** for automated deployments
4. **Set up staging environment** for testing changes
5. **Document operational procedures** for your team

## 🎯 Production Checklist

- [ ] Google Cloud APIs enabled
- [ ] Secrets created and accessible
- [ ] BigQuery dataset and tables created
- [ ] Cloud Run service deployed successfully
- [ ] Slack app configured with production URLs
- [ ] Health check endpoint responding
- [ ] All slash commands working
- [ ] Voting buttons functional
- [ ] AI content generation working
- [ ] Admin commands accessible (for admin users)
- [ ] Monitoring and alerting configured

---

**Your AI Tools Wiki Slack Bot is now ready for production!** 🎉

For operational guidance, see [docs/admin/ADMIN_GUIDE.md](../admin/ADMIN_GUIDE.md)
For API documentation, see [docs/api/COMMANDS.md](../api/COMMANDS.md)
