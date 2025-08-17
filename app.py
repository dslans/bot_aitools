#!/usr/bin/env python3
"""
AI Tools Wiki Slack Bot - Main Application
"""

import sys
import os
import logging

# Check Python version early
if sys.version_info < (3, 9):
    print("❌ Error: Python 3.9 or higher is required.")
    print(f"Current version: {sys.version}")
    print("Please upgrade Python and try again.")
    sys.exit(1)
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config.settings import settings
from handlers.add_handler import register_add_handler
from handlers.search_handler import register_search_handler  
from handlers.list_handler import register_list_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Slack app."""
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        return None
    
    # Initialize Slack app
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET
    )
    
    # Register command handlers
    register_add_handler(app)
    register_search_handler(app)
    register_list_handler(app)
    
    # Add a simple health check command
    @app.command("/aitools")
    def aitools_help(ack, say, command):
        """Handle the base /aitools command with help."""
        ack()
        
        help_text = """
🤖 *AI Tools Wiki Bot Commands*

• `/aitools add <title> | <url or description>` - Add a new AI tool
• `/aitools search <keyword>` - Search for tools by keyword
• `/aitools list [tag]` - List trending tools (optionally filtered by tag)

*Examples:*
• `/aitools add Aider | https://github.com/paul-gauthier/aider`
• `/aitools search code-assistant`
• `/aitools list python`

Need help? The bot will automatically generate summaries and tags for tools you add! 🚀
        """
        
        say(help_text)
    
    # Handle app mentions for help
    @app.event("app_mention")
    def handle_mention(event, say):
        """Handle when the bot is mentioned."""
        say(
            f"Hi <@{event['user']}>! 👋\n\n"
            "I'm the AI Tools Wiki Bot. Use `/aitools` to see available commands!"
        )
    
    logger.info("Slack app initialized successfully")
    return app

def main():
    """Main application entry point."""
    logger.info("Starting AI Tools Wiki Bot...")
    
    app = create_app()
    if not app:
        logger.error("Failed to create Slack app. Exiting.")
        return
    
    # Check if we're using Socket Mode (for local development)
    app_token = os.getenv('SLACK_APP_TOKEN')
    
    if app_token:
        # Socket Mode for local development
        logger.info("Starting bot in Socket Mode for local development...")
        handler = SocketModeHandler(app, app_token)
        handler.start()
    else:
        # HTTP Mode for production deployment
        logger.info("Starting bot in HTTP Mode...")
        app.start(port=int(os.environ.get("PORT", 3000)))

if __name__ == "__main__":
    main()
