"""
Handler for /aitools-tags command.
"""

import logging
from typing import List
from slack_bolt import App

from services.bigquery_service import bigquery_service
from services.tag_suggestions_service import tag_suggestions_service
from config.tags import CORE_TAGS, get_tag_description

logger = logging.getLogger(__name__)

def register_tags_handler(app: App):
    """Register the /aitools-tags command handler."""
    
    @app.command("/aitools-tags")
    def handle_tags_command(ack, say, command):
        """Handle the /aitools-tags command."""
        ack()
        
        try:
            # Get database tags (used tags from actual entries)
            db_tags = bigquery_service.get_all_tags()
            
            # Get approved community tags
            approved_community_tags = tag_suggestions_service.get_all_approved_community_tags()
            
            # Combine core tags with used community tags
            core_tags_in_use = [tag for tag in CORE_TAGS if tag in db_tags]
            
            # Include both used community tags from entries AND approved community tags
            all_community_tags = list(set(
                [tag for tag in db_tags if tag not in CORE_TAGS] +  # Used community tags
                approved_community_tags  # Approved community tags
            ))
            all_community_tags.sort()
            
            # Format the response
            response = format_tags_response(core_tags_in_use, all_community_tags)
            say(response)
            
        except Exception as e:
            logger.error(f"Error getting tags: {e}")
            say("❌ An error occurred while fetching tags. Please try again.")

def format_tags_response(core_tags: List[str], community_tags: List[str]) -> dict:
    """
    Format the tags list for Slack display.
    
    Args:
        core_tags: List of core predefined tags that are in use
        community_tags: List of community-generated tags
        
    Returns:
        Formatted Slack message with blocks
    """
    total_tags = len(core_tags) + len(community_tags)
    
    if total_tags == 0:
        return {
            "text": "🏷️ No tags available yet.",
            "blocks": [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🏷️ *No tags found yet.*\n\nTags are automatically generated when you add tools with `/aitools-add`!"
                }
            }]
        }
    
    # Build blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🏷️ *Available Tags ({total_tags} total)*\n\nUse these tags with `/aitools-list <tag>` to filter tools."
            }
        },
        {"type": "divider"}
    ]
    
    # Add core tags section
    if core_tags:
        # Organize core tags by category
        use_case_tags = [tag for tag in core_tags if tag in ['code-assistant', 'search-engine', 'chatbot', 'content-creation', 'data-analysis', 'design-tool', 'productivity', 'learning']]
        user_tags = [tag for tag in core_tags if tag in ['developer', 'researcher', 'business', 'student', 'creative']]
        tech_tags = [tag for tag in core_tags if tag in ['api-available', 'no-code', 'open-source', 'browser-based', 'mobile-app', 'language-model', 'image-generation', 'code-generation', 'real-time-data', 'automation', 'voice-ai']]
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"**🎯 Core Categories ({len(core_tags)})**"
            }
        })
        
        if use_case_tags:
            tags_text = " • ".join([f"`{tag}`" for tag in use_case_tags])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Use Cases:* {tags_text}"
                }
            })
        
        if user_tags:
            tags_text = " • ".join([f"`{tag}`" for tag in user_tags])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Target Users:* {tags_text}"
                }
            })
        
        if tech_tags:
            tags_text = " • ".join([f"`{tag}`" for tag in tech_tags])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Technical:* {tags_text}"
                }
            })
    
    # Add community tags section
    if community_tags:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"**🌟 Community Tags ({len(community_tags)})**"
            }
        })
        
        # Show community tags in groups of 8
        for i in range(0, len(community_tags), 8):
            chunk = community_tags[i:i+8]
            tags_text = " • ".join([f"`{tag}`" for tag in chunk])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": tags_text
                }
            })
    
    # Add footer with usage examples and tag suggestion info
    blocks.extend([
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 *Examples:* `/aitools-list code-assistant` • `/aitools-list developer` • `/aitools-list open-source`"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🏷️ *Missing a tag?* Use `/aitools-suggest-tag <entry_id> <tag>` to suggest new community tags!"
                }
            ]
        }
    ])
    
    return {
        "text": f"Available Tags ({total_tags} total)",
        "blocks": blocks
    }
