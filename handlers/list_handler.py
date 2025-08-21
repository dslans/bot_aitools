"""
Handler for /aitools list command.
"""

import logging
from typing import List, Dict, Any, Optional
from slack_bolt import App

from config.settings import settings
from services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)

def register_list_handler(app: App):
    """Register the /aitools list command handler."""
    
    @app.command("/aitools-list")
    def handle_list_command(ack, say, command):
        """Handle the /aitools list command."""
        ack()
        
        # Parse the command text (optional tag filter)
        tag = command.get('text', '').strip()
        tag = tag if tag else None
        
        # Perform the list query
        try:
            entries = bigquery_service.list_entries(tag, settings.MAX_LIST_RESULTS)
            
            if not entries:
                if tag:
                    say(f"🏷️ No tools found with tag *{tag}*.\n"
                        "Try a different tag or add more tools with `/aitools-add`!")
                else:
                    say("📋 No tools found in the wiki yet.\n"
                        "Be the first to add one with `/aitools-add`!")
                return
            
            # Format the response
            response = format_list_results(tag, entries)
            say(response)
            
        except Exception as e:
            logger.error(f"Error listing entries: {e}")
            say("❌ An error occurred while fetching the list. Please try again.")

def format_list_results(tag: Optional[str], entries: List[Dict[str, Any]]) -> dict:
    """
    Format list results for Slack display.
    
    Args:
        tag: Optional tag filter
        entries: List of entry dictionaries
        
    Returns:
        Formatted Slack message with blocks
    """
    # Header
    if tag:
        header = f"🏷️ *Top tools tagged '{tag}':*"
    else:
        header = "📋 *Trending AI tools:*"
    
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
        result_text = format_list_entry(i, entry)
        
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
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🏷️ Suggest Tag"
                        },
                        "action_id": f"suggest_tag_{entry['id']}",
                        "value": entry['id']
                    }
                ]
            }
            blocks.append(voting_block)
            
            # Add score as a context block
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
    footer_text = f"Showing {len(entries)} tool{'s' if len(entries) != 1 else ''}."
    if not tag:
        footer_text += " Use `/aitools-list <tag>` to filter by tag."
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": footer_text
            }
        ]
    })
    
    return {
        "text": f"AI Tools List" + (f" - {tag}" if tag else ""),
        "blocks": blocks
    }

def format_list_entry(index: int, entry: Dict[str, Any]) -> str:
    """
    Format a single entry for list results.
    
    Args:
        index: Entry number (1-based)
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
    result_parts = [f"*{index}. {title}* (Score: {score:+d})"]
    
    # Add URL if present
    if url:
        result_parts.append(f"🔗 {url}")
    
    # Add AI summary (truncated)
    if ai_summary:
        summary = ai_summary
        if len(summary) > 120:
            summary = summary[:117] + "..."
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
        tags_str = ', '.join(tags[:4])  # Show first 4 tags
        if len(tags) > 4:
            tags_str += f" +{len(tags)-4} more"
        result_parts.append(f"🏷️ {tags_str}")
    
    return '\n'.join(result_parts)

def create_entry_voting_buttons(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create voting button elements for an entry.
    
    Args:
        entry: Entry dictionary
        
    Returns:
        List of button elements
    """
    score = entry.get('score', 0)
    entry_id = entry['id']
    
    return [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "👍"
            },
            "style": "primary",
            "action_id": f"upvote_{entry_id}",
            "value": entry_id
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "👎"
            },
            "action_id": f"downvote_{entry_id}",
            "value": entry_id
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": f"{score:+d}" if score != 0 else "0"
            },
            "action_id": f"score_{entry_id}",
            "value": entry_id
        }
    ]
