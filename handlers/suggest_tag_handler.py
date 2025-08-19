"""
Handler for /aitools-suggest-tag command.
Allows users to suggest new community tags for entries.
"""

import logging
import re
from slack_bolt import App

from services.bigquery_service import bigquery_service
from services.tag_suggestions_service import tag_suggestions_service
from config.tags import CORE_TAGS

logger = logging.getLogger(__name__)

def register_suggest_tag_handler(app: App):
    """Register the /aitools-suggest-tag command handler and voting handlers."""
    
    # Register voting handlers first
    register_tag_voting_handlers(app)
    
    @app.command("/aitools-suggest-tag")
    def handle_suggest_tag_command(ack, say, command):
        """Handle the /aitools-suggest-tag command."""
        ack()
        
        try:
            text = command.get('text', '').strip()
            user_id = command.get('user_id')
            
            if not text:
                say({
                    "text": "❌ Please provide an entry ID and tag to suggest.",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "🏷️ *Suggest a Community Tag*\n\n" +
                                       "**Usage:** `/aitools-suggest-tag <entry_id> <tag>`\n\n" +
                                       "**Examples:**\n" +
                                       "• `/aitools-suggest-tag abc12345 machine-learning`\n" +
                                       "• `/aitools-suggest-tag def67890 python-library`\n\n" +
                                       "💡 *Tips:*\n" +
                                       "• Use lowercase, hyphen-separated tags\n" +
                                       "• Keep tags concise and descriptive\n" +
                                       "• Check existing tags with `/aitools-tags`"
                            }
                        }
                    ],
                    "response_type": "ephemeral"
                })
                return
            
            # Parse entry_id and tag from command
            parts = text.split(' ', 1)
            if len(parts) != 2:
                say({
                    "text": "❌ Invalid format. Use: `/aitools-suggest-tag <entry_id> <tag>`",
                    "response_type": "ephemeral"
                })
                return
                
            entry_id, suggested_tag = parts[0].strip(), parts[1].strip()
            
            # Validate entry exists
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                say({
                    "text": f"❌ Entry with ID `{entry_id}` not found.\n\n" +
                           "💡 *Tip:* Use `/aitools-list` to find entry IDs, or copy from admin commands.",
                    "response_type": "ephemeral"
                })
                return
            
            # Check if it's a core tag
            if suggested_tag.lower() in CORE_TAGS:
                say({
                    "text": f"ℹ️ `{suggested_tag}` is already a core tag and doesn't need community approval.\n\n" +
                           f"**{entry['title']}** may already have this tag, or you can suggest it to an admin for manual addition.",
                    "response_type": "ephemeral"
                })
                return
            
            # Create the suggestion
            suggestion_id = tag_suggestions_service.suggest_tag(entry_id, suggested_tag, user_id)
            
            if suggestion_id:
                # Format success response with voting buttons
                response = format_suggestion_success_response(entry, suggested_tag, suggestion_id)
                say(response)
            else:
                # Check if it already exists
                existing = tag_suggestions_service.get_suggestion_for_entry_and_tag(entry_id, suggested_tag.lower().replace(' ', '-'))
                if existing:
                    # Show existing suggestion with voting buttons
                    response = format_existing_suggestion_response(entry, existing)
                    say(response)
                else:
                    say({
                        "text": f"❌ Could not create tag suggestion. The tag `{suggested_tag}` may be invalid.",
                        "response_type": "ephemeral"
                    })
                
        except Exception as e:
            logger.error(f"Error in suggest tag command: {e}")
            say("❌ An error occurred while processing your tag suggestion. Please try again.")

def format_suggestion_success_response(entry: dict, suggested_tag: str, suggestion_id: str) -> dict:
    """Format the success response for a new tag suggestion."""
    return {
        "text": f"✅ Tag suggestion created: {suggested_tag}",
        "blocks": [
            {
                "type": "section", 
                "text": {
                    "type": "mrkdwn",
                    "text": f"🏷️ **New Tag Suggestion**\n\n" +
                           f"**Tool:** {entry['title']}\n" +
                           f"**Suggested Tag:** `{suggested_tag}`\n\n" +
                           f"Your suggestion has been created! Other users can now vote on it."
                }
            },
            {
                "type": "actions",
                "block_id": f"tag_suggestion_{suggestion_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍 Upvote"
                        },
                        "style": "primary",
                        "action_id": f"upvote_tag_{suggestion_id}",
                        "value": suggestion_id
                    },
                    {
                        "type": "button", 
                        "text": {
                            "type": "plain_text",
                            "text": "👎 Downvote"
                        },
                        "action_id": f"downvote_tag_{suggestion_id}",
                        "value": suggestion_id
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 Tags with 3+ net upvotes are automatically approved for use!"
                    }
                ]
            }
        ]
    }

def format_existing_suggestion_response(entry: dict, suggestion: dict) -> dict:
    """Format response for an existing tag suggestion."""
    net_votes = suggestion['net_votes'] 
    status_emoji = "🔥" if net_votes >= 3 else "⏳" if net_votes >= 0 else "❄️"
    
    return {
        "text": f"Tag suggestion already exists: {suggestion['suggested_tag']}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn", 
                    "text": f"🏷️ **Existing Tag Suggestion** {status_emoji}\n\n" +
                           f"**Tool:** {entry['title']}\n" +
                           f"**Suggested Tag:** `{suggestion['suggested_tag']}`\n" +
                           f"**Status:** {suggestion['status'].title()}\n" +
                           f"**Votes:** {suggestion['upvotes']}👍 {suggestion['downvotes']}👎 (net: {net_votes:+d})"
                }
            },
            {
                "type": "actions",
                "block_id": f"tag_suggestion_{suggestion['id']}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text", 
                            "text": "👍 Upvote"
                        },
                        "style": "primary",
                        "action_id": f"upvote_tag_{suggestion['id']}",
                        "value": suggestion['id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👎 Downvote" 
                        },
                        "action_id": f"downvote_tag_{suggestion['id']}",
                        "value": suggestion['id']
                    }
                ]
            }
        ]
    }

def register_tag_voting_handlers(app: App):
    """Register tag voting button handlers."""
    logger.info("🗳️ Registering tag voting handlers...")
    
    @app.action(re.compile(r"upvote_tag_.+"))
    def handle_tag_upvote(ack, body, say):
        """Handle upvote button clicks on tag suggestions."""
        ack()
        
        try:
            action = body.get('actions', [{}])[0]
            suggestion_id = action.get('value')
            user_id = body.get('user', {}).get('id')
            
            logger.info(f"Tag upvote: user={user_id}, suggestion={suggestion_id}")
            
            success = tag_suggestions_service.vote_on_suggestion(suggestion_id, user_id, 1)
            
            if success:
                # Get updated suggestion 
                suggestion = tag_suggestions_service.get_suggestion_by_id(suggestion_id)
                if suggestion:
                    net_votes = suggestion['net_votes']
                    
                    response_text = f"✅ You upvoted the tag `{suggestion['suggested_tag']}`!\n" +\
                                  f"Current votes: {suggestion['upvotes']}👍 {suggestion['downvotes']}👎 (net: {net_votes:+d})"
                    
                    if net_votes >= 3 and suggestion['status'] == 'approved':
                        response_text += f"\n\n🎉 This tag has been **auto-approved** for community use!"
                    
                    say({
                        "text": response_text,
                        "response_type": "ephemeral"
                    })
                else:
                    say({
                        "text": "✅ Vote recorded!",
                        "response_type": "ephemeral"
                    })
            else:
                say({
                    "text": "❌ Failed to record your vote. Please try again.",
                    "response_type": "ephemeral"
                })
                
        except Exception as e:
            logger.error(f"Error handling tag upvote: {e}")
            say("❌ An error occurred while voting.")
    
    @app.action(re.compile(r"downvote_tag_.+"))
    def handle_tag_downvote(ack, body, say):
        """Handle downvote button clicks on tag suggestions."""
        ack()
        
        try:
            action = body.get('actions', [{}])[0]
            suggestion_id = action.get('value')
            user_id = body.get('user', {}).get('id')
            
            logger.info(f"Tag downvote: user={user_id}, suggestion={suggestion_id}")
            
            success = tag_suggestions_service.vote_on_suggestion(suggestion_id, user_id, -1)
            
            if success:
                # Get updated suggestion
                suggestion = tag_suggestions_service.get_suggestion_by_id(suggestion_id)
                if suggestion:
                    net_votes = suggestion['net_votes'] 
                    response_text = f"👎 You downvoted the tag `{suggestion['suggested_tag']}`.\n" +\
                                  f"Current votes: {suggestion['upvotes']}👍 {suggestion['downvotes']}👎 (net: {net_votes:+d})"
                    
                    say({
                        "text": response_text,
                        "response_type": "ephemeral"
                    })
                else:
                    say({
                        "text": "✅ Vote recorded!",
                        "response_type": "ephemeral"
                    })
            else:
                say({
                    "text": "❌ Failed to record your vote. Please try again.",
                    "response_type": "ephemeral"
                })
                
        except Exception as e:
            logger.error(f"Error handling tag downvote: {e}")
            say("❌ An error occurred while voting.")
    
    # Handle "Suggest Tag" buttons from list entries
    @app.action(re.compile(r"suggest_tag_.+"))
    def handle_suggest_tag_button(ack, body, respond):
        """Handle suggest tag buttons from entry lists."""
        ack()
        
        try:
            action = body.get('actions', [{}])[0]
            entry_id = action.get('value')
            user_id = body.get('user', {}).get('id')
            
            # Get entry details for display
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                respond({
                    "text": f"❌ Entry not found.",
                    "response_type": "ephemeral"
                })
                return
            
            # Show modal or simple prompt for tag suggestion
            suggest_tag_prompt(respond, entry, user_id)
            
        except Exception as e:
            logger.error(f"Error handling suggest tag button: {e}")
            respond({
                "text": f"❌ Error: {str(e)}",
                "response_type": "ephemeral"
            })
    
def suggest_tag_prompt(respond, entry: dict, user_id: str):
    """Show a tag suggestion prompt for an entry."""
    entry_title = entry['title'][:50] + "..." if len(entry['title']) > 50 else entry['title']
    
    respond({
        "text": f"Suggest a tag for {entry_title}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🏷️ **Suggest a Tag**\n\n" +
                           f"**Tool:** {entry['title']}\n" +
                           f"**ID:** `{entry['id']}`\n\n" +
                           f"To suggest a tag, use:\n" +
                           f"`/aitools-suggest-tag {entry['id']} your-tag-name`\n\n" +
                           f"💡 *Examples:*\n" +
                           f"• `/aitools-suggest-tag {entry['id']} machine-learning`\n" +
                           f"• `/aitools-suggest-tag {entry['id']} python-library`\n" +
                           f"• `/aitools-suggest-tag {entry['id']} no-code-tool`"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Use lowercase, hyphen-separated words. Check existing tags with `/aitools-tags`"
                    }
                ]
            }
        ],
        "response_type": "ephemeral"
    })

logger.info("✅ Tag suggestion handlers registered successfully")
