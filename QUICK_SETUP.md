# AI Tools Wiki Bot - Quick Setup Guide

This guide will get you from zero to a working test bot in about 15 minutes.

## 🎯 Prerequisites Checklist

- [ ] Google Cloud Platform account (free tier is fine)
- [ ] Slack workspace where you have admin permissions
- [ ] Python 3.9+ installed locally
- [ ] `gcloud` CLI installed ([Install Guide](https://cloud.google.com/sdk/docs/install))

## 📋 Step-by-Step Setup

### 1. 🔧 Google Cloud Platform Setup

#### A. Create/Select Project
```bash
# Login to GCP
gcloud auth login

# Create a new project (or use existing)
gcloud projects create aitools-wiki-bot-RANDOMID --name="AI Tools Wiki Bot"

# Set as active project
gcloud config set project aitools-wiki-bot-RANDOMID
```

#### B. Enable Required APIs
```bash
# Enable all required APIs in one command
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com
```

#### C. Create Service Account
```bash
# Get your project ID first
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create aitools-bot \
    --display-name="AI Tools Wiki Bot Service Account" \
    --description="Service account for AI Tools Wiki Slack Bot"

# Wait a moment for service account to propagate
echo "Waiting for service account to be created..."
sleep 10

# Verify service account exists
gcloud iam service-accounts describe aitools-bot@$PROJECT_ID.iam.gserviceaccount.com \
    --format="value(email)" || {
    echo "❌ Service account creation failed. Please try again."
    exit 1
}

echo "✅ Service account created successfully"

# Grant required permissions
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

# Wait a moment for permissions to propagate
sleep 5

# Create and download service account key
echo "Creating service account key..."
gcloud iam service-accounts keys create ~/aitools-bot-key.json \
    --iam-account=aitools-bot@$PROJECT_ID.iam.gserviceaccount.com

echo "✅ Service account key created at ~/aitools-bot-key.json"
```

**📝 Note**: Save the path to `~/aitools-bot-key.json` - you'll need it later.

### 2. 📱 Slack App Setup

#### A. Create Slack App
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From scratch"**
4. App Name: `AI Tools Wiki Bot`
5. Pick your workspace
6. Click **"Create App"**

#### B. Configure Bot Permissions
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

#### C. Enable Socket Mode (for local testing)
1. Go to **"Socket Mode"** in the left sidebar
2. Toggle **"Enable Socket Mode"** to ON
3. Click **"Generate Token"**
4. Token Name: `connections`
5. Add scope: `connections:write`
6. Click **"Generate"**
7. **📋 Copy the App Token** (starts with `xapp-`) - save this!

#### D. Create Slash Commands
1. Go to **"Slash Commands"** in the left sidebar
2. Create these 4 commands (for now, use placeholder URL `https://example.com`):

| Command | Description | Usage Hint |
|---------|-------------|------------|
| `/aitools` | Show help for AI Tools Wiki Bot | |
| `/aitools-add` | Add a new AI tool | `<title> \| <url or description>` |
| `/aitools-search` | Search for AI tools | `<keyword>` |
| `/aitools-list` | List trending AI tools | `[tag]` |

#### E. Install App to Workspace
1. Go to **"Install App"** in the left sidebar
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **📋 Copy the Bot User OAuth Token** (starts with `xoxb-`) - save this!

#### F. Get Signing Secret
1. Go to **"Basic Information"** in the left sidebar
2. Scroll to **"App Credentials"**
3. **📋 Copy the Signing Secret** - save this!

### 3. 💻 Local Development Setup

#### A. Clone and Setup Project
```bash
# Navigate to your projects directory
cd ~/slack_projects/bot_aitools

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### B. Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your actual values
nano .env  # or use your preferred editor
```

**Fill in these values in `.env`:**
```bash
# Slack App Configuration
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-FROM-STEP-2E
SLACK_SIGNING_SECRET=YOUR-SIGNING-SECRET-FROM-STEP-2F  
SLACK_APP_TOKEN=xapp-YOUR-APP-TOKEN-FROM-STEP-2C

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=aitools-wiki-bot-RANDOMID  # Your project ID
GOOGLE_APPLICATION_CREDENTIALS=/Users/YOURUSERNAME/aitools-bot-key.json

# BigQuery Configuration (defaults are fine)
BIGQUERY_DATASET=aitools_wiki
BIGQUERY_LOCATION=US

# Optional: Custom settings (defaults are fine)
GEMINI_MODEL=gemini-1.5-pro
VERTEX_LOCATION=us-central1
```

#### C. Setup Database
```bash
# Create BigQuery dataset and tables
python scripts/setup_database.py
```

You should see:
```
🚀 Setting up AI Tools Wiki BigQuery database...
🔨 Creating dataset: your-project.aitools_wiki
✅ Created dataset: your-project.aitools_wiki
🔨 Creating table: entries
✅ Created table: entries
🔨 Creating table: votes  
✅ Created table: votes

🎉 BigQuery setup complete!
```

### 4. 🧪 Test the Bot

#### A. Start the Bot
```bash
# Make sure you're in the project directory and venv is activated
python app.py
```

You should see:
```
INFO - Starting AI Tools Wiki Bot...
INFO - AI service initialized successfully
INFO - BigQuery service initialized successfully  
INFO - Slack app initialized successfully
INFO - Starting bot in Socket Mode for local development...
⚡️ Bolt app is running!
```

#### B. Test in Slack
1. Go to your Slack workspace
2. In any channel (or DM with the bot), try:

**Test basic help:**
```
/aitools
```

**Test adding a tool:**
```
/aitools-add Cursor | https://cursor.sh
```

**Test search:**
```
/aitools-search cursor
```

**Test list:**
```
/aitools-list
```

### 5. 🐛 Troubleshooting

#### Common Issues & Solutions

**"AI service not initialized"**
```bash
# Check if Vertex AI API is enabled
gcloud services list --enabled --filter="name:aiplatform.googleapis.com"

# If not listed, enable it:
gcloud services enable aiplatform.googleapis.com
```

**"BigQuery permission denied"**
```bash
# Verify your service account has the right roles
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:aitools-bot*"
```

**"Socket Mode connection failed"**
- Check that `SLACK_APP_TOKEN` starts with `xapp-`
- Verify Socket Mode is enabled in your Slack app
- Check internet connection

**"Command not found"**
- Slash commands will show "dispatch failed" until deployed to production
- For now, Socket Mode bypasses this - bot should still respond

#### Debug Mode
Add this to your `.env` for more detailed logging:
```bash
PYTHONPATH=.
SLACK_APP_LOG_LEVEL=DEBUG
```

### 6. 🎉 Success Indicators

✅ **Bot is working if you see:**
- Bot responds to `/aitools` with help text
- Bot processes `/aitools add` commands (even if slowly due to AI processing)
- Voting buttons appear and work
- Search and list commands return results
- No error messages in terminal

### 7. 📊 Verify Data in BigQuery

```bash
# Check that data is being stored
bq query --use_legacy_sql=false \
  "SELECT title, tags, score FROM \`$(gcloud config get-value project).aitools_wiki.entries_with_scores\` LIMIT 5"
```

## 🚀 Next Steps

Once your test bot is working:

1. **Add more tools** to build up your knowledge base
2. **Invite team members** to test and vote
3. **Deploy to production** using the `DEPLOYMENT.md` guide
4. **Customize prompts** in `services/ai_service.py` for your domain

## 💰 Cost Estimates (Free Tier)

- **BigQuery**: Free up to 1TB queries/month (should be plenty for testing)
- **Vertex AI**: Free tier includes limited Gemini API calls
- **Total expected cost for testing**: $0-5/month

## 📞 Getting Help

If you run into issues:

1. **Check logs**: Look at the terminal output for error messages
2. **Verify credentials**: Make sure all tokens and keys are correct
3. **Test components**: Try the database setup script separately
4. **Check permissions**: Ensure service account has all required roles

The bot includes comprehensive error handling and logging to help identify issues quickly.
