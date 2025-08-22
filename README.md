# AI Tools Wiki Slack Bot 🤖

**A Community Wiki for AI Tools** with Reddit-style voting and democratic tagging for AI coding tools. Team members can contribute, vote, and collaboratively tag tools to build a curated knowledge base. Features automated security evaluation using AI to determine if tools are approved, restricted, or prohibited based on your workplace security policies.

## Motivation
Experimental project to create a slackbot and learn how Warp works. I intentionally started with a project plan that would enable a coding assistant do all the heavy lifting. A voting system for AI tools seemed appropriate. 

## ✨ Key Features

- 🤖 **AI-Powered Content**: Automatic tool summaries and tagging using Google Gemini
- 🔒 **Security Evaluation**: Automated AI-powered security assessment against company policies
- 📊 **Reddit-Style Voting**: Upvote/downvote tools directly in Slack with real-time scores  
- 🏷️ **Democratic Tagging**: Community-driven tag suggestions with voting approval
- 🔍 **Smart Search**: Find tools by keywords, tags, or content with relevance ranking
- 🚀 **One-Click UX**: Streamlined interface with interactive buttons
- 🔧 **Admin Management**: Complete oversight tools for content moderation
- 💾 **Intelligent Caching**: Prevents duplicate AI calls, saves costs and time

## 🚀 Quick Start

### Essential Commands
```bash
# Get help
/aitools

# Add a new tool (AI will analyze and categorize it)
/aitools-add Cursor | https://cursor.com

# Search for tools
/aitools-search code-generation

# List trending tools (with voting buttons)
/aitools-list

# Show top-rated tools
/aitools-top 5

# Browse available tags
/aitools-tags
```

### Interactive Features
- **👍/👎 Voting**: Click buttons to rate tools
- **🏷️ Tag Suggestions**: One-click tag suggestions via buttons
- **📊 Live Scores**: Real-time community rankings
- **🤖 AI Analysis**: Auto-generated summaries and categorization
- **🔒 Security Indicators**: Visual status (approved ✅, restricted ⚠️, prohibited 🚫)

## 🚀 Quick Start Examples

### Adding a Tool
```
/aitools-add Cursor | https://cursor.sh
```
Bot response:
```
✅ Added *Cursor* 🔍 Requires security team review
🔗 https://cursor.com
📝 AI-powered code editor with GitHub Copilot integration...
🏷️ Tags: code-editor, ai-assistant, vscode
👍 0 | 👎 0 [Suggest Tag]
```

### Community Tag Workflow
1. **Find a tool**: `/aitools-list code-editor`
2. **Suggest a tag**: Click "🏷️ Suggest Tag" button
3. **Get guided prompt**: Copy pre-filled command
4. **Run command**: `/aitools-suggest-tag abc12345 typescript`
5. **Community votes**: Others vote 👍/👎 on your suggestion
6. **Auto-approval**: Tag approved at 3+ net votes

### Admin Management
```
/aitools-admin-tags
```
Shows pending suggestions with vote counts and approve/reject buttons.

## ⚙️ Setup

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Set up BigQuery:**
   ```bash
   # Enable BigQuery API in your GCP project
   # Set up authentication (service account key or gcloud auth)
   python scripts/setup.py
   ```

4. **Run the bot:**
   ```bash
   python app.py
   ```

### 🚀 Production Deployment (Google Cloud Run)

For production deployment, see the comprehensive [Deployment Guide](docs/guides/DEPLOYMENT.md) which covers:

- Google Cloud Run setup
- Docker containerization
- Secret management
- Slack app configuration
- Monitoring and scaling

**Quick Deploy:**
```bash
# 1. Set up Google Cloud project and authenticate
gcloud config set project YOUR_PROJECT_ID

# 2. Create secrets for Slack tokens
echo -n 'your-bot-token' | gcloud secrets create slack-bot-token --data-file=-
echo -n 'your-signing-secret' | gcloud secrets create slack-signing-secret --data-file=-

# 3. Set up database
python scripts/setup.py

# 4. Deploy with the automated script
./scripts/deploy.sh
```

The bot will automatically:
- ✅ Scale from 0-10 instances based on demand
- ✅ Handle SSL termination and health checks
- ✅ Manage secrets securely with Google Secret Manager
- ✅ Provide production-ready logging and monitoring

## 📚 Documentation

### Quick Links
- **[API Documentation](docs/api/COMMANDS.md)** - Complete command reference with examples
- **[Deployment Guide](docs/guides/DEPLOYMENT.md)** - Production deployment to Google Cloud Run
- **[Admin Guide](docs/admin/ADMIN_GUIDE.md)** - Admin operations and management
- **[Setup Scripts](scripts/README.md)** - Database setup and migration guide

### Detailed Guides
- **[Community Tag System](docs/guides/COMMUNITY_TAG_SYSTEM.md)** - How the democratic tagging works
- **[Tag Suggestion UX Guide](docs/guides/TAG_SUGGESTION_UX_GUIDE.md)** - User experience design
- **[Project Plan](docs/guides/PROJECT_PLAN.md)** - Architecture and development roadmap

## 📁 Project Structure

```
.
├── .dockerignore                    # Docker ignore patterns
├── .env.example                     # Environment variable template
├── .env.prod.template               # Production environment template
├── .gitignore                       # Git ignore patterns
├── Dockerfile                       # Container configuration
├── app.py                           # Main application entry point
├── config/
│   ├── settings.py                  # Configuration management
│   └── tags.py                      # Core tag definitions
├── services/
│   ├── ai_service.py                # Google Gen AI integration
│   ├── bigquery_service.py           # BigQuery operations
│   ├── scraper_service.py            # Web scraping functionality
│   ├── security_service.py           # AI-powered security evaluation
│   └── tag_suggestions_service.py    # Community tag system
├── handlers/
│   ├── add_handler.py               # /aitools-add command
│   ├── admin_handler.py             # Admin commands (/aitools-admin-*)
│   ├── list_handler.py              # /aitools-list command
│   ├── search_handler.py            # /aitools-search command
│   ├── suggest_tag_handler.py       # /aitools-suggest-tag command
│   ├── tags_handler.py              # /aitools-tags command
│   └── top_handler.py               # /aitools-top command
├── docs/
│   ├── api/
│   │   └── COMMANDS.md              # Complete API documentation
│   ├── admin/
│   │   └── ADMIN_GUIDE.md           # Admin operations guide
│   └── guides/
│       ├── DEPLOYMENT.md            # Production deployment guide
│       ├── PROJECT_PLAN.md          # Project roadmap and architecture
│       ├── COMMUNITY_TAG_SYSTEM.md  # Tag system documentation
│       └── TAG_SUGGESTION_UX_GUIDE.md # UX design guide
├── scripts/
│   ├── deploy.sh                    # Automated deployment script
│   ├── setup.py                     # Complete database setup
│   └── README.md                    # Setup documentation
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

