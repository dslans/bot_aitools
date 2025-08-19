# AI Tools Wiki Slack Bot 🤖

**Production-Ready Community Wiki** with Reddit-style voting and democratic tagging for AI coding tools. Team members can contribute, vote, and collaboratively tag tools to build a curated knowledge base.

## ✨ Features

### Core Functionality
- 🤖 **AI-Powered Content**: Automatic tool summaries and tagging using Google Gemini
- 📊 **Reddit-Style Voting**: Upvote/downvote tools directly in Slack with real-time scores
- 🔍 **Smart Search**: Find tools by keywords, tags, or content with relevance ranking
- 💾 **Intelligent Caching**: Prevents duplicate AI calls, saves costs and time
- 🏷️ **AI Auto-Tagging**: Automatically extracts relevant tags for categorization

### Community Features (NEW!)
- 🏷️ **Community Tag Suggestions**: Users can suggest new tags for any tool
- 🗳️ **Democratic Tag Voting**: Vote on tag suggestions with 👍/👎 buttons
- ⚡ **Auto-Approval**: Tags with 3+ net votes automatically approved
- 🛡️ **Admin Oversight**: Complete admin interface for managing suggestions
- 🎯 **One-Click UX**: "Suggest Tag" buttons eliminate complex workflows

### Admin Features
- 🔧 **Complete Admin Interface**: Manage entries, tags, and user suggestions
- 📊 **Analytics Dashboard**: View pending suggestions with vote indicators
- 🚀 **Manual Controls**: Approve, reject, or promote tags instantly
- 🌡️ **Visual Indicators**: "Temperature" display for suggestion popularity

## 💬 Commands

### User Commands
- `/aitools-add <title> | <url or description>` - Add a new AI tool
- `/aitools-search <keyword>` - Search for tools by content, tags, or title
- `/aitools-list [tag]` - List trending tools with interactive voting and tag suggestion buttons
- `/aitools-tags` - Browse all available tags (core + community-approved)
- `/aitools-suggest-tag <entry_id> <tag>` - Suggest community tags for tools

### Admin Commands (Requires Admin Permissions)
- `/aitools-admin-list [limit]` - Manage all entries
- `/aitools-admin-edit <entry_id>` - Edit entry details manually
- `/aitools-admin-tags` - Review and manage community tag suggestions
- `/aitools-admin-retag <entry_id>` - Regenerate AI content
- `/aitools-admin-delete <entry_id>` - Remove entries permanently

## 🚀 Quick Start Examples

### Adding a Tool
```
/aitools-add Cursor | https://cursor.sh
```
Bot response:
```
✅ Added *Cursor*
🔗 https://cursor.sh
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

## Project Structure

```
.
├── app.py                           # Main application entry point
├── config/
│   ├── settings.py                  # Configuration management
│   └── tags.py                      # Core tag definitions
├── services/
│   ├── ai_service.py                # Google Gen AI integration
│   ├── bigquery_service.py           # BigQuery operations
│   ├── scraper_service.py            # Web scraping functionality
│   └── tag_suggestions_service.py    # Community tag system
├── handlers/
│   ├── __init__.py
│   ├── add_handler.py               # /aitools-add command
│   ├── admin_handler.py             # Admin commands (/aitools-admin-*)
│   ├── list_handler.py              # /aitools-list command
│   ├── search_handler.py            # /aitools-search command
│   ├── suggest_tag_handler.py       # /aitools-suggest-tag command
│   └── tags_handler.py              # /aitools-tags command
├── migrations/
│   └── create_tag_tables.sql        # Community tag system database schema
├── scripts/
│   ├── setup.py                     # Complete database setup & migration
│   └── README.md                    # Setup script documentation
├── docs/
│   ├── COMMUNITY_TAG_SYSTEM.md      # Complete system documentation
│   └── TAG_SUGGESTION_UX_GUIDE.md   # User experience guide
├── PROJECT_PLAN.md               # Complete project plan and roadmap
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
