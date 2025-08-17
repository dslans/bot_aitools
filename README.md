# AI Tools Wiki Slack Bot

A Slack-integrated wiki with Reddit-style voting for AI coding tools. Team members can contribute posts about AI tools and upvote/downvote them so the best content rises to the top.

## Features

- 🤖 **AI-powered summaries**: Automatic tool summaries and tagging using Google Gemini
- 📊 **Reddit-style voting**: Upvote/downvote tools directly in Slack
- 🔍 **Smart search**: Find tools by keywords, tags, or content
- 💾 **Caching**: Prevents duplicate AI calls for the same URLs
- 🏷️ **Auto-tagging**: AI extracts relevant tags for easy categorization

## Commands

- `/aitools add <title> | <url or description>` - Add a new AI tool
- `/aitools search <keyword>` - Search for tools
- `/aitools list [tag]` - List trending tools (optionally filtered by tag)

## Setup

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
   python scripts/setup_database.py
   ```

4. **Run the bot:**
   ```bash
   python app.py
   ```

## Project Structure

```
.
├── app.py                 # Main application entry point
├── config/
│   └── settings.py        # Configuration management
├── services/
│   ├── ai_service.py      # Google Gen AI integration
│   ├── bigquery_service.py # BigQuery operations
│   └── scraper_service.py # Web scraping functionality
├── handlers/
│   ├── __init__.py
│   ├── add_handler.py     # /aitools add command
│   ├── search_handler.py  # /aitools search command
│   └── list_handler.py    # /aitools list command
├── scripts/
│   └── setup_database.py  # Database initialization
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
