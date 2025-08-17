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
    
    @app.command("/aitools list")
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
                        "Try a different tag or add more tools with `/aitools add`!")
                else:
                    say("📋 No tools found in the wiki yet.\n"
                        "Be the first to add one with `/aitools add`!")
                return
            
            # Format the response
            response = format_list_results(tag, entries)
            say(response)
            
        except Exception as e:
            logger.error(f"Error listing entries: {e}")
            say("❌ An error occurred while fetching the list. Please try again.")
    
    # Also register voting button handlers
    register_voting_handlers(app)

def register_voting_handlers(app: App):
    """Register button handlers for voting."""
    
    @app.action("upvote_*")
    def handle_upvote(ack, body, say):
        """Handle upvote button clicks."""
        ack()
        handle_vote_action(body, say, 1)
    
    @app.action("downvote_*")
    def handle_downvote(ack, body, say):
        """Handle downvote button clicks."""
        ack()
        handle_vote_action(body, say, -1)

def handle_vote_action(body: dict, say, vote_value: int):
    """
    Handle a vote action (upvote or downvote).
    
    Args:
        body: Slack action body
        say: Slack say function
        vote_value: 1 for upvote, -1 for downvote
    """
    try:
        # Extract information from the action
        action = body.get('actions', [{}])[0]
        entry_id = action.get('value')
        user_id = body.get('user', {}).get('id')
        
        if not entry_id or not user_id:
            logger.error("Missing entry_id or user_id in vote action")
            return
        
        # Update the vote
        success = bigquery_service.add_or_update_vote(entry_id, user_id, vote_value)
        
        if success:
            # Get updated entry to show new score
            entry = bigquery_service.get_entry_with_score(entry_id)
            
            if entry:
                vote_text = "upvoted 👍" if vote_value == 1 else "downvoted 👎"
                response_text = f"You {vote_text} *{entry['title']}*! New score: {entry['score']:+d}"
                say(response_text, response_type="ephemeral")
            else:
                say("Vote recorded! ✅", response_type="ephemeral")
        else:
            say("❌ Failed to record your vote. Please try again.", response_type="ephemeral")
            
    except Exception as e:
        logger.error(f"Error handling vote action: {e}")
        say("❌ An error occurred while recording your vote.", response_type="ephemeral")

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
        
        # Add voting buttons for each entry
        if entry.get('id'):
            voting_elements = create_entry_voting_buttons(entry)
            entry_block["accessory"] = {
                "type": "overflow",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": f"👍 Upvote (Score: {entry.get('score', 0):+d})"
                        },
                        "value": f"upvote_{entry['id']}"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": f"👎 Downvote (Score: {entry.get('score', 0):+d})"
                        },
                        "value": f"downvote_{entry['id']}"
                    }
                ],
                "action_id": f"vote_menu_{entry['id']}"
            }
        
        blocks.append(entry_block)
        
        # Add divider between entries (except after the last one)
        if i < len(entries):
            blocks.append({"type": "divider"})
    
    # Add footer with help text
    footer_text = f"Showing {len(entries)} tool{'s' if len(entries) != 1 else ''}."
    if not tag:
        footer_text += " Use `/aitools list <tag>` to filter by tag."
    
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
