"""
Handler for /aitools add command.
"""

import logging
import asyncio
from typing import Optional, Tuple
from slack_bolt import App

from services.ai_service import ai_service
from services.bigquery_service import bigquery_service
from services.scraper_service import scraper_service
from services.security_service import security_service

logger = logging.getLogger(__name__)

def register_add_handler(app: App):
    """Register the /aitools add command handler."""
    
    @app.command("/aitools-add")
    def handle_add_command(ack, say, command):
        """Handle the /aitools add command."""
        ack()
        
        # Parse the command text
        text = command.get('text', '').strip()
        user_id = command.get('user_id')
        
        if not text:
            say("❌ Please provide a title and URL/description.\n"
                "Format: `/aitools add <title> | <url or description>`\n"
                "Example: `/aitools add Aider | https://github.com/paul-gauthier/aider`")
            return
        
        # Parse title and content
        title, content = parse_add_command(text)
        
        if not title or not content:
            say("❌ Invalid format. Please use: `<title> | <url or description>`")
            return
        
        # Show processing message
        say("🔄 Processing your request... This may take a moment while I analyze the tool.")
        
        # Process the entry
        try:
            # Check for duplicate before processing (if it's a URL)
            if scraper_service.is_valid_url(content):
                existing_entry = bigquery_service.get_entry_by_url(content)
                if existing_entry:
                    # Get the existing entry with score for display
                    existing_entry_with_score = bigquery_service.get_entry_with_score(existing_entry['id'])
                    if existing_entry_with_score:
                        say(f"🔄 This URL has already been added to the wiki!\n\n**Existing Entry:**")
                        response = format_entry_response(existing_entry_with_score)
                        say(response)
                    else:
                        say(f"🔄 This URL has already been added: **{existing_entry['title']}**\n\nUse `/aitools-list` to browse existing tools.")
                    return
            
            entry_id = process_add_entry(title, content, user_id)
            
            if entry_id:
                # Get the entry with score for display
                entry = bigquery_service.get_entry_with_score(entry_id)
                if entry:
                    response = format_entry_response(entry)
                    say(response)
                else:
                    say("✅ Tool added successfully!")
            else:
                say("❌ Sorry, I couldn't process that tool. Please try again.")
                
        except Exception as e:
            logger.error(f"Error processing add command: {e}")
            say("❌ An error occurred while processing your request. Please try again.")

def parse_add_command(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the add command text to extract title and content.
    
    Args:
        text: The command text
        
    Returns:
        Tuple of (title, content) or (None, None) if invalid
    """
    if '|' not in text:
        return None, None
    
    parts = text.split('|', 1)
    if len(parts) != 2:
        return None, None
    
    title = parts[0].strip()
    content = parts[1].strip()
    
    if not title or not content:
        return None, None
    
    return title, content

def process_add_entry(title: str, content: str, user_id: str) -> Optional[str]:
    """
    Process a new entry by scraping, generating AI content, and saving to database.
    
    Args:
        title: Entry title
        content: URL or description
        user_id: Slack user ID
        
    Returns:
        Entry ID if successful, None otherwise
    """
    url = None
    description = None
    scraped_content = None
    
    # Check if content is a URL
    if scraper_service.is_valid_url(content):
        url = content
        
        # Check if we already have this URL cached
        existing_entry = bigquery_service.get_entry_by_url(url)
        if existing_entry:
            logger.info(f"Found existing entry for URL: {url}")
            # Return None to indicate duplicate found (handled in calling code)
            return None
        
        # Scrape content from URL
        scraped_title, scraped_content = scraper_service.scrape_content(url)
        
        # Use scraped title if provided title is generic
        if scraped_title and len(scraped_title) > len(title):
            title = scraped_title
        
        # Use scraped content for AI analysis
        content_for_ai = scraped_content if scraped_content else content
    else:
        # Content is a description
        description = content
        content_for_ai = content
    
    # Generate AI summary, target audience, and tags
    ai_summary = None
    target_audience = None
    tags = []
    
    try:
        ai_summary, target_audience, tags = ai_service.generate_summary_and_tags_sync(title, content_for_ai)
        logger.info(f"AI content generated successfully for {title}")
    except Exception as e:
        logger.warning(f"AI service failed for '{title}': {e}")
        logger.info("Entry will be created without AI-generated content (can be added later by admin)")
    
    # Generate security evaluation
    security_status = None
    security_display = None
    
    try:
        # Evaluate tool security using the AI summary and description
        from config.settings import settings
        security_status, security_display = security_service.evaluate_tool_security_sync(
            title=title,
            url=url,
            description=description,
            ai_summary=ai_summary,
            tags=tags or [],
            guidelines_url=settings.SECURITY_GUIDELINES_URL
        )
        logger.info(f"Security evaluation completed for {title}: {security_status}")
    except Exception as e:
        logger.warning(f"Security service failed for '{title}': {e}")
        logger.info("Entry will be created without security evaluation (can be added later by admin)")
    
    # Create the entry
    try:
        entry_id = bigquery_service.create_entry(
            title=title,
            url=url,
            description=description,
            ai_summary=ai_summary,
            target_audience=target_audience,
            tags=tags,
            author_id=user_id,
            security_status=security_status,
            security_display=security_display
        )
        return entry_id
    except Exception as e:
        logger.error(f"Error creating entry: {e}")
        return None

def format_entry_response(entry: dict) -> dict:
    """
    Format an entry for Slack display.
    
    Args:
        entry: Entry dictionary with score information
        
    Returns:
        Formatted Slack message with blocks
    """
    # Build the response
    response_parts = [f"✅ Added *{entry['title']}*"]
    
    # Add URL if present
    if entry['url']:
        response_parts.append(f"🔗 {entry['url']}")
    
    # Add AI summary if present
    if entry['ai_summary']:
        response_parts.append(f"📝 {entry['ai_summary']}")
    else:
        response_parts.append("📝 _AI summary will be added by admins_")
    
    # Add target audience if present
    if entry.get('target_audience'):
        response_parts.append(f"👥 Best for: {entry['target_audience']}")
    else:
        response_parts.append("👥 _Target audience will be added by admins_")
    
    # Add tags if present
    if entry['tags']:
        tags_str = ', '.join(entry['tags'])
        response_parts.append(f"🏷️ Tags: {tags_str}")
    else:
        response_parts.append("🏷️ _Tags will be added by admins_")
    
    # Add security information if present
    if entry.get('security_display'):
        response_parts.append(f"🔒 Security: {entry['security_display']}")
    else:
        response_parts.append("🔒 _Security evaluation pending_")
    
    # Add note about missing AI content if applicable
    if not entry['ai_summary'] or not entry['tags']:
        response_parts.append("\n💡 _Missing details will be added by our admin team shortly._")
    
    # Add vote counts
    score = entry.get('score', 0)
    upvotes = entry.get('upvotes', 0)
    downvotes = entry.get('downvotes', 0)
    
    response_parts.append(f"👍 {upvotes} | 👎 {downvotes}")
    
    response = '\n'.join(response_parts)
    
    # Create blocks with voting buttons and score text
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": response
            }
        },
        create_voting_blocks(entry['id']),
        create_score_block(score)
    ]
    
    return {
        "text": response,
        "blocks": blocks
    }

def create_voting_blocks(entry_id: str) -> dict:
    """
    Create Slack blocks for voting buttons.
    
    Args:
        entry_id: The entry ID
        
    Returns:
        Slack block elements
    """
    return {
        "type": "actions",
        "block_id": f"voting_{entry_id}",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "👍 Upvote"
                },
                "style": "primary",
                "action_id": f"upvote_{entry_id}",
                "value": entry_id
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "👎 Downvote"
                },
                "style": "danger",  # Make downvote button red
                "action_id": f"downvote_{entry_id}",
                "value": entry_id
            }
        ]
    }

def create_score_block(score: int) -> dict:
    """
    Create a score display block (text only).
    
    Args:
        score: Current score
        
    Returns:
        Slack context block
    """
    score_text = f"Score: {score:+d}" if score != 0 else "Score: 0"
    return {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📊 {score_text}"
            }
        ]
    }
