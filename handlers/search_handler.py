"""
Handler for /aitools search command.
"""

import logging
from typing import List, Dict, Any
from slack_bolt import App

from config.settings import settings
from services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)

def register_search_handler(app: App):
    """Register the /aitools search command handler."""
    
    @app.command("/aitools-search")
    def handle_search_command(ack, say, command):
        """Handle the /aitools search command."""
        ack()
        
        # Parse the command text
        keyword = command.get('text', '').strip()
        
        if not keyword:
            say("❌ Please provide a search keyword.\n"
                "Format: `/aitools search <keyword>`\n"
                "Example: `/aitools search code-assistant`")
            return
        
        # Perform the search
        try:
            entries = bigquery_service.search_entries(keyword, settings.MAX_SEARCH_RESULTS)
            
            if not entries:
                say(f"🔍 No results found for *{keyword}*.\n"
                    "Try a different keyword or add more tools with `/aitools add`!")
                return
            
            # Format the response
            response = format_search_results(keyword, entries)
            say(response)
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            say("❌ An error occurred while searching. Please try again.")

def format_search_results(keyword: str, entries: List[Dict[str, Any]]) -> dict:
    """
    Format search results for Slack display.
    
    Args:
        keyword: The search keyword
        entries: List of entry dictionaries
        
    Returns:
        Formatted Slack message with blocks
    """
    # Header
    header = f"🔍 *Top results for '{keyword}':*\n"
    
    # Build result blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add each result as a block
    for i, entry in enumerate(entries, 1):
        result_text = format_entry_summary(i, entry)
        
        entry_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": result_text
            }
        }
        
        blocks.append(entry_block)
        
        # Add voting buttons for each entry (as separate action block)
        if entry.get('id'):
            voting_block = {
                "type": "actions",
                "block_id": f"voting_{entry['id']}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍 Upvote"
                        },
                        "style": "primary",
                        "action_id": f"upvote_{entry['id']}",
                        "value": entry['id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👎 Downvote"
                        },
                        "style": "danger",  # Make downvote button red
                        "action_id": f"downvote_{entry['id']}",
                        "value": entry['id']
                    }
                ]
            }
            blocks.append(voting_block)
            
            # Add score as a context block (text only)
            score_text = f"Score: {entry.get('score', 0):+d}" if entry.get('score', 0) != 0 else "Score: 0"
            score_block = {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 {score_text}"
                    }
                ]
            }
            blocks.append(score_block)
        
        # Add divider between entries (except after the last one)
        if i < len(entries):
            blocks.append({"type": "divider"})
    
    # Add footer with help text
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Found {len(entries)} result{'s' if len(entries) != 1 else ''}. Use `/aitools list` to see all trending tools."
            }
        ]
    })
    
    return {
        "text": f"Search results for {keyword}",
        "blocks": blocks
    }

def format_entry_summary(index: int, entry: Dict[str, Any]) -> str:
    """
    Format a single entry summary for search results.
    
    Args:
        index: Result number (1-based)
        entry: Entry dictionary
        
    Returns:
        Formatted entry text
    """
    title = entry.get('title', 'Untitled')
    score = entry.get('score', 0)
    ai_summary = entry.get('ai_summary')
    target_audience = entry.get('target_audience')
    url = entry.get('url')
    tags = entry.get('tags', [])
    
    # Start with title and score
    result_parts = [f"*{index}. {title}* (score: {score:+d})"]
    
    # Add URL if present
    if url:
        result_parts.append(f"🔗 {url}")
    
    # Add AI summary (truncated)
    if ai_summary:
        summary = ai_summary
        if len(summary) > 150:
            summary = summary[:147] + "..."
        result_parts.append(f"_{summary}_")
    
    # Add target audience if present
    if target_audience:
        result_parts.append(f"👥 Best for: {target_audience}")
    
    # Add security status if present
    security_display = entry.get('security_display')
    if security_display:
        result_parts.append(f"🔒 {security_display}")
    
    # Add tags
    if tags:
        tags_str = ', '.join(tags[:3])  # Show first 3 tags
        if len(tags) > 3:
            tags_str += f" +{len(tags)-3} more"
        result_parts.append(f"🏷️ {tags_str}")
    
    return '\n'.join(result_parts)
