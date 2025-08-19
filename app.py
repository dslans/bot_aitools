#!/usr/bin/env python3
"""
AI Tools Wiki Slack Bot - Main Application
"""

import sys
import os
import logging
from typing import List, Dict

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
from handlers.admin_handler import register_admin_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def register_global_voting_handlers(app: App):
    """Register global voting button handlers."""
    logger.info("🔧 Registering global voting handlers...")
    from services.bigquery_service import bigquery_service
    
    def handle_vote_action(body: dict, respond, vote_value: int):
        """Handle a vote action (upvote or downvote)."""
        try:
            # Extract information from the action
            action = body.get('actions', [{}])[0]
            entry_id = action.get('value')
            user_id = body.get('user', {}).get('id')
            
            logger.info(f"Processing vote: user={user_id}, entry={entry_id}, vote={vote_value}")
            
            if not entry_id or not user_id:
                logger.error("Missing entry_id or user_id in vote action")
                respond({
                    "text": "❌ Error: Missing user or entry information.",
                    "response_type": "ephemeral"
                })
                return
            
            # Update the vote
            success = bigquery_service.add_or_update_vote(entry_id, user_id, vote_value)
            
            if success:
                # Get updated entry to show new score
                entry = bigquery_service.get_entry_with_score(entry_id)
                
                if entry:
                    vote_text = "upvoted 👍" if vote_value == 1 else "downvoted 👎"
                    response_text = f"You {vote_text} *{entry['title']}*! New score: {entry['score']:+d}"
                    respond({
                        "text": response_text,
                        "response_type": "ephemeral"
                    })
                else:
                    respond({
                        "text": "Vote recorded! ✅",
                        "response_type": "ephemeral"
                    })
            else:
                respond({
                    "text": "❌ Failed to record your vote. Please try again.",
                    "response_type": "ephemeral"
                })
                
        except Exception as e:
            logger.error(f"Error handling vote action: {e}")
            respond({
                "text": "❌ An error occurred while recording your vote.",
                "response_type": "ephemeral"
            })
    
    import re
    
    @app.action(re.compile(r"upvote_.+"))
    def handle_upvote(ack, body, respond):
        """Handle upvote button clicks."""
        logger.info("📤 Upvote handler triggered!")
        ack()
        handle_vote_action(body, respond, 1)
    
    @app.action(re.compile(r"downvote_.+"))
    def handle_downvote(ack, body, respond):
        """Handle downvote button clicks."""
        logger.info("📤 Downvote handler triggered!")
        ack()
        handle_vote_action(body, respond, -1)
    
    
    logger.info("✅ Global voting handlers registered successfully")

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
    register_admin_handler(app)
    
    # Register global voting handlers for buttons
    register_global_voting_handlers(app)
    
    # Help command (main /aitools command)
    @app.command("/aitools")
    def aitools_help(ack, say, command):
        """Handle the base /aitools command with help."""
        ack()
        
        help_text = """
🤖 *AI Tools Wiki Bot Commands*

• `/aitools-add <title> | <url or description>` - Add a new AI tool
• `/aitools-search <keyword>` - Search for tools by keyword
• `/aitools-list [tag]` - List trending tools (optionally filtered by tag)

*Examples:*
• `/aitools-add Aider | https://aider.chat/`
• `/aitools-search code-assistant`
• `/aitools-list python`

Need help? The bot will automatically generate summaries and tags for tools you add! 🚀
        """
        
        say(help_text)
    
    # Handle app mentions for help
    @app.event("app_mention")
    def handle_mention(event, say):
        """Handle when the bot is mentioned."""
        say(
            f"Hi <@{event['user']}>! 👋\n\n"
            "I'm the AI Tools Wiki Bot. Use `/aitools` to see available commands!\n\n"
            "You can also DM me directly or mention me with:\n"
            "• `help` - Show commands\n"
            "• `add [title] | [url]` - Add a tool\n"
            "• `search [keyword]` - Search tools\n"
            "• `list [tag]` - List tools"
        )
    
    # Handle direct messages
    @app.event("message")
    def handle_direct_message(message, say):
        """Handle direct messages to the bot."""
        # Ignore messages from the bot itself
        if message.get('bot_id'):
            return
            
        text = message.get('text', '').strip().lower()
        user_id = message.get('user')
        
        logger.info(f"Received message from {user_id}: {text}")
        
        # Handle different message types
        if text in ['help', 'hi', 'hello', 'hey']:
            say(
                "👋 Hi there! Here's what I can help you with:\n\n"
                "🤖 **Commands:**\n"
                "• `add [title] | [url/description]` - Add a new AI tool\n"
                "• `search [keyword]` - Search for tools\n"
                "• `list [tag]` - List trending tools\n\n"
                "📝 **Examples:**\n"
                "• `add Cursor | https://cursor.sh`\n"
                "• `search code-assistant`\n"
                "• `list python`\n\n"
                "Or use slash commands like `/aitools-add`!"
            )
            
        elif text.startswith('add '):
            handle_message_add(message, say, user_id)
            
        elif text.startswith('search '):
            keyword = text[7:].strip()  # Remove 'search '
            handle_message_search(keyword, say)
            
        elif text.startswith('list'):
            tag = text[4:].strip() if len(text) > 4 else None  # Remove 'list '
            handle_message_list(tag, say)
            
        else:
            say(
                "🤔 I'm not sure what you mean. Try:\n"
                "• `help` - Show commands\n"
                "• `add [title] | [url]` - Add a tool\n"
                "• `search [keyword]` - Search tools\n"
                "• `list [tag]` - List tools"
            )
    
    logger.info("Slack app initialized successfully")
    return app

def handle_message_add(message, say, user_id):
    """Handle 'add' messages."""
    from handlers.add_handler import parse_add_command, process_add_entry, format_entry_response
    from services.bigquery_service import bigquery_service
    
    text = message.get('text', '').strip()
    # Remove 'add ' from the beginning
    content = text[4:].strip()
    
    if not content:
        say("❌ Please provide a title and URL/description.\n"
            "Format: `add <title> | <url or description>`\n"
            "Example: `add Cursor | https://cursor.sh`")
        return
    
    # Parse title and content
    title, url_or_desc = parse_add_command(content)
    
    if not title or not url_or_desc:
        say("❌ Invalid format. Please use: `add <title> | <url or description>`")
        return
    
    say("🔄 Processing your request... This may take a moment while I analyze the tool.")
    
    try:
        entry_id = process_add_entry(title, url_or_desc, user_id)
        
        if entry_id:
            entry = bigquery_service.get_entry_with_score(entry_id)
            if entry:
                response = format_entry_response(entry)
                say(response)
            else:
                say("✅ Tool added successfully!")
        else:
            say("❌ Sorry, I couldn't process that tool. Please try again.")
            
    except Exception as e:
        logger.error(f"Error processing message add: {e}")
        say("❌ An error occurred while processing your request. Please try again.")

def handle_message_search(keyword, say):
    """Handle 'search' messages."""
    from handlers.search_handler import format_search_results
    from services.bigquery_service import bigquery_service
    from config.settings import settings
    
    if not keyword:
        say("❌ Please provide a search keyword.\n"
            "Example: `search code-assistant`")
        return
    
    try:
        entries = bigquery_service.search_entries(keyword, settings.MAX_SEARCH_RESULTS)
        
        if not entries:
            say(f"🔍 No results found for *{keyword}*.\n"
                "Try a different keyword or add more tools!")
            return
        
        response = format_search_results(keyword, entries)
        say(response)
        
    except Exception as e:
        logger.error(f"Error performing message search: {e}")
        say("❌ An error occurred while searching. Please try again.")

def handle_message_list(tag, say):
    """Handle 'list' messages."""
    from handlers.list_handler import format_list_results
    from services.bigquery_service import bigquery_service
    from config.settings import settings
    
    try:
        entries = bigquery_service.list_entries(tag, settings.MAX_LIST_RESULTS)
        
        if not entries:
            if tag:
                say(f"🏷️ No tools found with tag *{tag}*.\n"
                    "Try a different tag or add more tools!")
            else:
                say("📋 No tools found in the wiki yet.\n"
                    "Be the first to add one!")
            return
        
        response = format_list_results(tag, entries)
        say(response)
        
    except Exception as e:
        logger.error(f"Error listing entries via message: {e}")
        say("❌ An error occurred while fetching the list. Please try again.")

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
