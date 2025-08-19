# Production Deployment Guide - AI Tools Wiki Slack Bot

This guide covers deploying your AI Tools Wiki Slack Bot to Google Cloud Run for production use.

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud SDK** installed and authenticated
2. **Docker** installed on your local machine
3. **Google Cloud Project** with billing enabled
4. **BigQuery API** and **Cloud Run API** enabled in your project
5. **Slack App** configured (covered in this guide)

## Step 1: Prepare Your Application for Production

### 1.1 Update app.py for Production

Your `app.py` needs to be modified to run in HTTP mode for Cloud Run. Add this code to your existing `app.py`:

```python
import os
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Initialize your Slack app (keep existing initialization)
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Create Flask app for Cloud Run
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# Add health check endpoint
@flask_app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Handle Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

# Keep all your existing handlers and commands here
# (your existing @app.command, @app.event handlers)

if __name__ == "__main__":
    # Production mode - run with gunicorn via Cloud Run
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

### 1.2 Create Production Environment File

Create `.env.production` with your production environment variables:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-production-bot-token
SLACK_SIGNING_SECRET=your-production-signing-secret
SLACK_APP_TOKEN=xapp-your-production-app-token

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET=aitools_wiki_prod

# Application Configuration
ENVIRONMENT=production
PORT=8080
```

### 1.3 Update requirements.txt

Ensure your `requirements.txt` includes all production dependencies:

```txt
slack-bolt>=1.18.0
google-cloud-bigquery>=3.11.0
python-dotenv>=1.0.0
flask>=2.3.0
gunicorn>=21.0.0
requests>=2.31.0
```

## Step 2: Create Docker Configuration

### 2.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "60", "app:flask_app"]
```

### 2.2 Create .dockerignore

```dockerignore
.env
.env.local
.env.production
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git/
.gitignore
*.md
.DS_Store
node_modules/
.vscode/
.idea/
tests/
*.log
```

## Step 3: Set Up Google Cloud Resources

### 3.1 Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3.2 Set Up BigQuery Dataset

Run your consolidated setup script:

```bash
python scripts/setup.py
```

This will create your production dataset and all required tables.

## Step 4: Deploy to Cloud Run

### 4.1 Build and Deploy

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Deploy to Cloud Run
gcloud run deploy aitools-wiki-bot \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 60 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=aitools_wiki_prod,ENVIRONMENT=production" \
    --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,SLACK_SIGNING_SECRET=slack-signing-secret:latest"
```

### 4.2 Store Secrets in Google Secret Manager

First, create your secrets:

```bash
# Store Slack Bot Token
echo -n "xoxb-your-bot-token" | gcloud secrets create slack-bot-token --data-file=-

# Store Slack Signing Secret
echo -n "your-signing-secret" | gcloud secrets create slack-signing-secret --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding slack-bot-token \
    --member="serviceAccount:$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding slack-signing-secret \
    --member="serviceAccount:$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 4.3 Get Your Cloud Run URL

After deployment, get your service URL:

```bash
gcloud run services describe aitools-wiki-bot \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

## Step 5: Configure Slack App for Production

### 5.1 Update Slack App Settings

In your Slack App configuration (api.slack.com):

1. **OAuth & Permissions**:
   - Update "Redirect URLs" if using OAuth flow
   - Ensure these scopes are enabled:
     - `app_mentions:read`
     - `channels:history`
     - `channels:read`
     - `chat:write`
     - `commands`
     - `im:history`
     - `im:read`
     - `im:write`
     - `users:read`

2. **Event Subscriptions**:
   - Enable Events: `On`
   - Request URL: `https://your-cloud-run-url/slack/events`
   - Subscribe to events:
     - `app_mention`
     - `message.im`

3. **Slash Commands**:
   - `/aitools-search`: `https://your-cloud-run-url/slack/events`
   - `/aitools-add`: `https://your-cloud-run-url/slack/events`
   - `/aitools-suggest-tag`: `https://your-cloud-run-url/slack/events`
   - `/aitools-admin`: `https://your-cloud-run-url/slack/events`

4. **Interactivity & Shortcuts**:
   - Enable Interactivity: `On`
   - Request URL: `https://your-cloud-run-url/slack/events`

### 5.2 Install App to Workspace

1. Go to "Install App" in your Slack App settings
2. Click "Install to Workspace"
3. Copy the "Bot User OAuth Token" and update your secret

## Step 6: Verify Deployment

### 6.1 Test Health Endpoint

```bash
curl https://your-cloud-run-url/health
```

Expected response: `{"status":"healthy"}`

### 6.2 Test Slack Commands

In your Slack workspace, try:
- `/aitools-search machine learning`
- `/aitools-suggest-tag` (should show entry selection)

## Step 7: Monitor and Scale

### 7.1 View Logs

```bash
gcloud run services logs read aitools-wiki-bot \
    --platform managed \
    --region us-central1 \
    --limit 50
```

### 7.2 Monitor Performance

```bash
# View service details
gcloud run services describe aitools-wiki-bot \
    --platform managed \
    --region us-central1
```

### 7.3 Update Deployment

For future updates:

```bash
gcloud run deploy aitools-wiki-bot \
    --source . \
    --platform managed \
    --region us-central1
```

## Troubleshooting

### Common Issues

1. **503 Service Unavailable**:
   - Check if your app is binding to `0.0.0.0:8080`
   - Verify PORT environment variable is set correctly
   - Check application logs for startup errors

2. **Slack Events Not Working**:
   - Verify your Cloud Run service allows unauthenticated requests
   - Check that Event Subscription URL in Slack matches your Cloud Run URL
   - Ensure `/slack/events` endpoint is correctly configured

3. **BigQuery Permission Errors**:
   - Verify your Cloud Run service account has BigQuery permissions
   - Check that your dataset exists in the correct project

4. **Timeout Errors**:
   - Increase Cloud Run timeout (max 60 minutes)
   - Optimize database queries
   - Consider increasing memory allocation

### Debug Commands

```bash
# Check service status
gcloud run services list

# View detailed service info
gcloud run services describe aitools-wiki-bot --region us-central1

# Stream logs in real-time
gcloud run services logs tail aitools-wiki-bot --region us-central1
```

## Security Considerations

1. **Use Secret Manager** for sensitive data (tokens, secrets)
2. **Enable Binary Authorization** for production workloads
3. **Use least-privilege IAM** roles
4. **Enable VPC Connector** if accessing private resources
5. **Set up monitoring and alerting** for security events

## Cost Optimization

1. **Set min-instances to 0** for development/staging
2. **Use appropriate CPU and memory** allocations
3. **Monitor request patterns** and adjust scaling settings
4. **Set up budget alerts** in Google Cloud Console

## Next Steps After Deployment

1. **Set up monitoring** with Google Cloud Monitoring
2. **Configure alerting** for critical failures
3. **Implement CI/CD pipeline** for automated deployments
4. **Set up staging environment** for testing changes
5. **Document operational procedures** for your team

---

Your AI Tools Wiki Slack Bot is now ready for production! The bot will automatically scale based on demand and provide a reliable service for your team.
