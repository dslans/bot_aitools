# AI Tools Wiki Bot - Deployment Guide

This guide covers how to set up and deploy the AI Tools Wiki Slack Bot.

## Prerequisites

- Python 3.9 or higher
- Google Cloud Platform account
- Slack workspace with admin permissions

## 1. Google Cloud Platform Setup

### Enable Required APIs

```bash
# Login to GCP
gcloud auth login

# Set your project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### Create Service Account

```bash
# Set your project ID (replace with your actual project ID)
PROJECT_ID="YOUR_PROJECT_ID"
echo "Using project: $PROJECT_ID"

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create aitools-bot \
    --display-name="AI Tools Wiki Bot Service Account" \
    --description="Service account for AI Tools Wiki Slack Bot"

# Wait for service account to propagate
echo "Waiting for service account to be created..."
sleep 10

# Verify service account exists
gcloud iam service-accounts describe aitools-bot@$PROJECT_ID.iam.gserviceaccount.com \
    --format="value(email)" || {
    echo "❌ Service account creation failed. Please try again."
    exit 1
}

echo "✅ Service account created successfully"

# Grant necessary roles
echo "Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aitools-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser" \
    --condition=None

echo "✅ Permissions granted successfully"

# Wait for permissions to propagate
sleep 5

# Create and download service account key
echo "Creating service account key..."
gcloud iam service-accounts keys create aitools-bot-key.json \
    --iam-account=aitools-bot@$PROJECT_ID.iam.gserviceaccount.com

echo "✅ Service account key created at aitools-bot-key.json"
```

## 2. Slack App Setup

### Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "AI Tools Wiki Bot"
4. Choose your workspace

### Configure OAuth & Permissions

Add these Bot Token Scopes:
- `app_mentions:read`
- `channels:read`
- `chat:write`
- `commands`
- `groups:read`
- `im:read`
- `mpim:read`

### Create Slash Commands

Create these slash commands (replace YOUR_DOMAIN with your deployment URL):

1. `/aitools` - `https://YOUR_DOMAIN/slack/events` - "Show help for AI Tools Wiki Bot"
2. `/aitools-add` - `https://YOUR_DOMAIN/slack/events` - "Add a new AI tool"
3. `/aitools-search` - `https://YOUR_DOMAIN/slack/events` - "Search for AI tools"
4. `/aitools-list` - `https://YOUR_DOMAIN/slack/events` - "List trending AI tools"

### Enable Socket Mode (for local development)

1. Go to "Socket Mode" in your app settings
2. Enable Socket Mode
3. Create an App-Level Token with `connections:write` scope
4. Copy the token (starts with `xapp-`)

### Install App to Workspace

1. Go to "Install App"
2. Click "Install to Workspace"
3. Copy the Bot Token (starts with `xoxb-`)

## 3. Local Development Setup

### Clone and Install

```bash
# Clone the repository (if from git)
git clone <repository-url>
cd slack_projects/bot_aitools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# SLACK_BOT_TOKEN=xoxb-your-bot-token
# SLACK_SIGNING_SECRET=your-signing-secret
# SLACK_APP_TOKEN=xapp-your-app-token (for Socket Mode)
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/aitools-bot-key.json
```

### Set Up Database

```bash
# Create BigQuery dataset and tables
python scripts/setup_database.py
```

### Run Locally

```bash
# Run the bot
python app.py
```

## 4. Production Deployment

### Option A: Google Cloud Run

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "app.py"]
```

Deploy:

```bash
# Build and deploy to Cloud Run
gcloud run deploy aitools-bot \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID" \
    --set-env-vars "SLACK_BOT_TOKEN=YOUR_BOT_TOKEN" \
    --set-env-vars "SLACK_SIGNING_SECRET=YOUR_SIGNING_SECRET"
```

### Option B: Google App Engine

Create `app.yaml`:

```yaml
runtime: python311

env_variables:
  GOOGLE_CLOUD_PROJECT: your-project-id
  SLACK_BOT_TOKEN: your-bot-token
  SLACK_SIGNING_SECRET: your-signing-secret
  BIGQUERY_DATASET: aitools_wiki
  BIGQUERY_LOCATION: US

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

Deploy:

```bash
gcloud app deploy
```

### Update Slack App URLs

After deployment, update your Slack app's:
1. Slash command URLs to point to your deployed service
2. Event subscriptions URL (if using)
3. Interactive components URL

## 5. Testing

### Test Commands

1. In Slack, try: `/aitools`
2. Add a tool: `/aitools add Cursor | https://cursor.sh`
3. Search: `/aitools search code-assistant`
4. List: `/aitools list`

### Verify Database

```bash
# Check BigQuery tables have data
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`YOUR_PROJECT.aitools_wiki.entries\`"
```

## 6. Monitoring and Maintenance

### Logs

- **Cloud Run**: `gcloud logs read --service=aitools-bot`
- **App Engine**: `gcloud logs read --service=default`

### BigQuery Monitoring

Monitor costs and usage in BigQuery console:
- Check query costs
- Set up billing alerts
- Optimize queries if needed

### Error Handling

The bot includes comprehensive error handling and logging. Check logs for:
- AI service failures
- BigQuery connection issues
- Slack API errors

## 7. Customization

### AI Prompts

Edit `services/ai_service.py` to customize:
- Summary generation prompts
- Tag categorization logic
- Response formatting

### Slack Interface

Edit handlers in `handlers/` to customize:
- Command responses
- Button interactions
- Message formatting

### Database Schema

Modify BigQuery tables in `scripts/setup_database.py` to add:
- Additional fields
- New indexes
- Custom views

## Troubleshooting

### Common Issues

1. **"AI service not initialized"**
   - Check Google Cloud credentials
   - Verify Vertex AI API is enabled

2. **"BigQuery permission denied"**
   - Ensure service account has proper roles
   - Check project ID is correct

3. **"Slack command not found"**
   - Verify slash commands are configured
   - Check request URLs match deployment

4. **Socket Mode connection issues**
   - Verify app token has `connections:write` scope
   - Check internet connection

### Getting Help

- Check application logs first
- Verify all environment variables are set
- Test individual components (BigQuery, AI service)
- Review Slack app configuration

## Security Notes

- Never commit `.env` files or service account keys
- Use environment variables for all secrets
- Regularly rotate service account keys
- Monitor BigQuery usage for cost control
- Review Slack app permissions periodically
