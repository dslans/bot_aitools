"""
Admin handler for AI Tools Wiki Bot.
Provides commands for manual management of entries when AI features fail.
"""

import logging
import re
from typing import List, Dict, Optional

from slack_bolt import App
from config.settings import settings
from services.bigquery_service import bigquery_service
from services.ai_service import ai_service
from services.tag_suggestions_service import tag_suggestions_service

logger = logging.getLogger(__name__)

def register_admin_handler(app: App):
    """Register admin command handlers."""
    logger.info("🔧 Registering admin handlers...")
    
    def check_admin_permission(user_id: str) -> bool:
        """Check if user has admin permissions."""
        logger.info(f"Checking admin permission for user_id: {user_id}")
        logger.info(f"Configured admin user IDs: {settings.ADMIN_USER_IDS}")
        is_admin = settings.is_admin(user_id)
        logger.info(f"Is admin: {is_admin}")
        return is_admin
    
    def send_permission_error(respond):
        """Send permission denied message."""
        respond({
            "text": "❌ *Access Denied*\n\nYou don't have admin permissions to use this command.",
            "response_type": "ephemeral"
        })
    
    @app.command("/aitools-admin")
    def admin_help(ack, respond, command):
        """Show admin help."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        help_text = """🛠️ *AI Tools Wiki - Admin Commands*

*Management Commands:*
• `/aitools-admin-list [limit]` - List all entries for management
• `/aitools-admin-edit <entry_id>` - Edit an entry's details
• `/aitools-admin-retag <entry_id>` - Regenerate AI tags and summary
• `/aitools-admin-delete <entry_id>` - Delete an entry permanently
• `/aitools-admin-search <keyword>` - Search entries for editing
• `/aitools-admin-tags` - Manage community tag suggestions

*Entry Editing Format:*
Use `/aitools-admin-edit <entry_id>` then follow with:
```
title: New Title (optional)
description: New description (optional)
summary: New AI summary (optional)
audience: Target audience (optional)
tags: tag1, tag2, tag3 (optional)
```

*Examples:*
• `/aitools-admin-list 20`
• `/aitools-admin-edit abc123`
• `/aitools-admin-retag abc123`
• `/aitools-admin-delete abc123`

*Note:* These commands are only available to configured admin users."""

        respond({
            "text": help_text,
            "response_type": "ephemeral"
        })
    
    @app.command("/aitools-admin-list")
    def admin_list(ack, respond, command):
        """List entries for admin management."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            text = command.get('text', '').strip()
            limit = 20  # Default limit
            
            if text.isdigit():
                limit = min(int(text), 50)  # Max 50 entries
            
            logger.info(f"Admin list called with limit: {limit}")
            
            entries = bigquery_service.list_all_entries_for_admin(limit=limit)
            
            logger.info(f"BigQuery returned: {type(entries)} with value: {entries}")
            
            # Handle case where query returns None instead of empty list
            if entries is None:
                logger.warning("BigQuery returned None, converting to empty list")
                entries = []
            elif not isinstance(entries, list):
                logger.error(f"BigQuery returned unexpected type: {type(entries)}")
                entries = []
            
            if not entries:
                respond({
                    "text": "📋 No entries found in the database.",
                    "response_type": "ephemeral"
                })
                return
            
            # Format entries for display
            entry_blocks = []
            entry_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📋 *Admin Entry List* (showing {len(entries)} entries)"
                }
            })
            entry_blocks.append({"type": "divider"})
            
            for entry in entries:
                # Safely handle entry fields that might be None
                entry_title = entry.get('title') or 'No title'
                title = entry_title[:50] + "..." if len(entry_title) > 50 else entry_title
                
                entry_summary = entry.get('ai_summary') or 'No AI summary'
                summary = entry_summary[:100] + "..." if len(entry_summary) > 100 else entry_summary
                
                entry_tags = entry.get('tags') or []
                tags_text = ", ".join(entry_tags[:3]) if entry_tags else 'No tags'
                if len(entry_tags) > 3:
                    tags_text += f" (+{len(entry_tags) - 3} more)"
                
                entry_audience = entry.get('target_audience') or 'No target audience'
                audience = entry_audience[:50] + "..." if len(entry_audience) > 50 else entry_audience
                
                # Safely handle other fields
                entry_id = entry.get('id') or 'unknown'
                entry_id_short = entry_id[:8] + "..." if len(entry_id) > 8 else entry_id
                
                score = entry.get('score', 0)
                upvotes = entry.get('upvotes', 0)
                downvotes = entry.get('downvotes', 0)
                
                author_id = entry.get('author_id') or 'unknown'
                
                # Handle date formatting safely
                created_at = entry.get('created_at')
                if created_at:
                    try:
                        date_str = created_at.strftime('%Y-%m-%d')
                    except:
                        date_str = str(created_at)[:10]
                else:
                    date_str = 'unknown'
                
                entry_text = f"""**{title}**
*ID:* `{entry_id_short}` | *Score:* {score:+d} ({upvotes}👍 {downvotes}👎)
*Summary:* {summary}
*Audience:* {audience}  
*Tags:* {tags_text}
*Author:* <@{author_id}> | *Created:* {date_str}"""
                
                entry_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn", 
                        "text": entry_text
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Edit"
                        },
                        "action_id": f"admin_edit_{entry['id']}",
                        "value": entry['id']
                    }
                })
                entry_blocks.append({"type": "divider"})
            
            # Add instruction
            entry_blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "💡 Use `/aitools-admin-edit <entry_id>` to edit an entry manually"
                }]
            })
            
            respond({
                "blocks": entry_blocks,
                "response_type": "ephemeral"
            })
            
        except Exception as e:
            logger.error(f"Error in admin list: {e}")
            respond({
                "text": f"❌ Error listing entries: {str(e)}",
                "response_type": "ephemeral"
            })
    
    @app.command("/aitools-admin-edit")
    def admin_edit(ack, respond, command):
        """Edit an entry manually."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            text = command.get('text', '').strip()
            
            if not text:
                respond({
                    "text": "❌ Please provide an entry ID. Usage: `/aitools-admin-edit <entry_id>`",
                    "response_type": "ephemeral"
                })
                return
            
            lines = text.split('\n')
            entry_id = lines[0].strip()
            
            # Get the entry
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                respond({
                    "text": f"❌ Entry with ID `{entry_id}` not found.",
                    "response_type": "ephemeral"
                })
                return
            
            # If only entry ID provided, show current details and edit form
            if len(lines) == 1:
                show_edit_form(respond, entry)
                return
            
            # Parse edit instructions
            updates = parse_edit_instructions(lines[1:])
            
            if not updates:
                respond({
                    "text": "❌ No valid updates found. Please provide fields to update:\n" +
                           "title: New title\ndescription: New description\nsummary: New summary\n" +
                           "audience: Target audience\ntags: tag1, tag2, tag3",
                    "response_type": "ephemeral"
                })
                return
            
            # Perform updates
            success = bigquery_service.update_entry(entry_id, **updates)
            
            if success:
                updated_fields = list(updates.keys())
                respond({
                    "text": f"✅ Successfully updated entry `{entry_id}`\n" +
                           f"Updated fields: {', '.join(updated_fields)}",
                    "response_type": "ephemeral"
                })
            else:
                respond({
                    "text": f"❌ Failed to update entry `{entry_id}`. Please check the logs.",
                    "response_type": "ephemeral"
                })
        
        except Exception as e:
            logger.error(f"Error in admin edit: {e}")
            respond({
                "text": f"❌ Error editing entry: {str(e)}",
                "response_type": "ephemeral"
            })
    
    @app.command("/aitools-admin-retag")
    def admin_retag(ack, respond, command):
        """Regenerate AI content for an entry."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            entry_id = command.get('text', '').strip()
            
            if not entry_id:
                respond({
                    "text": "❌ Please provide an entry ID. Usage: `/aitools-admin-retag <entry_id>`",
                    "response_type": "ephemeral"
                })
                return
            
            # Check if entry exists
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                respond({
                    "text": f"❌ Entry with ID `{entry_id}` not found.",
                    "response_type": "ephemeral"
                })
                return
            
            respond({
                "text": f"🤖 Regenerating AI content for *{entry['title']}*...",
                "response_type": "ephemeral"
            })
            
            # Regenerate AI content
            success = bigquery_service.regenerate_ai_content(entry_id)
            
            if success:
                # Get updated entry to show new content
                updated_entry = bigquery_service.get_entry_by_id(entry_id)
                
                result_text = f"✅ Successfully regenerated AI content for *{entry['title']}*\n\n"
                
                if updated_entry.get('ai_summary'):
                    result_text += f"*New Summary:* {updated_entry['ai_summary'][:200]}...\n\n"
                
                if updated_entry.get('target_audience'): 
                    result_text += f"*New Target Audience:* {updated_entry['target_audience']}\n\n"
                
                if updated_entry.get('tags'):
                    result_text += f"*New Tags:* {', '.join(updated_entry['tags'])}"
                
                respond({
                    "text": result_text,
                    "response_type": "ephemeral"
                })
            else:
                respond({
                    "text": f"❌ Failed to regenerate AI content for `{entry_id}`. The AI service may be unavailable.",
                    "response_type": "ephemeral"
                })
        
        except Exception as e:
            logger.error(f"Error in admin retag: {e}")
            respond({
                "text": f"❌ Error regenerating content: {str(e)}",
                "response_type": "ephemeral"
            })
    
    @app.command("/aitools-admin-search")
    def admin_search(ack, respond, command):
        """Search entries for admin editing."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            keyword = command.get('text', '').strip()
            
            if not keyword:
                respond({
                    "text": "❌ Please provide a search keyword. Usage: `/aitools-admin-search <keyword>`",
                    "response_type": "ephemeral"
                })
                return
            
            entries = bigquery_service.search_entries(keyword, limit=10)
            
            if not entries:
                respond({
                    "text": f"🔍 No entries found matching '{keyword}'.",
                    "response_type": "ephemeral"
                })
                return
            
            # Format search results
            result_blocks = []
            result_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔍 *Search Results for '{keyword}'* ({len(entries)} found)"
                }
            })
            result_blocks.append({"type": "divider"})
            
            for entry in entries:
                title = entry['title'][:50] + "..." if len(entry['title']) > 50 else entry['title']
                summary = entry.get('ai_summary') or 'No summary'
                if len(summary) > 80:
                    summary = summary[:80] + "..."
                
                result_text = f"""**{title}**
*ID:* `{entry['id'][:8]}...` | *Score:* {entry['score']:+d}
*Summary:* {summary}
*Author:* <@{entry['author_id']}>"""
                
                result_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": result_text
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Edit"
                        },
                        "action_id": f"admin_edit_{entry['id']}",
                        "value": entry['id']
                    }
                })
                result_blocks.append({"type": "divider"})
            
            respond({
                "blocks": result_blocks,
                "response_type": "ephemeral"
            })
            
        except Exception as e:
            logger.error(f"Error in admin search: {e}")
            respond({
                "text": f"❌ Error searching entries: {str(e)}",
                "response_type": "ephemeral"
            })
    
    @app.command("/aitools-admin-delete")
    def admin_delete(ack, respond, command):
        """Delete an entry permanently."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            entry_id = command.get('text', '').strip()
            
            if not entry_id:
                respond({
                    "text": "❌ Please provide an entry ID. Usage: `/aitools-admin-delete <entry_id>`",
                    "response_type": "ephemeral"
                })
                return
            
            # Get the entry first to show what's being deleted
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                respond({
                    "text": f"❌ Entry with ID `{entry_id}` not found.",
                    "response_type": "ephemeral"
                })
                return
            
            # Delete the entry
            success = bigquery_service.delete_entry(entry_id)
            
            if success:
                respond({
                    "text": f"🗑️ Successfully deleted entry:\n\n" +
                           f"**{entry['title']}**\n" +
                           f"ID: `{entry_id}`\n" +
                           f"Author: <@{entry['author_id']}>\n\n" +
                           f"⚠️ This action cannot be undone.",
                    "response_type": "ephemeral"
                })
            else:
                # Check if it was a streaming buffer issue (for recently added entries)
                import time
                from datetime import datetime, timezone
                
                created_at = entry.get('created_at')
                if created_at:
                    # Calculate minutes since creation
                    now = datetime.now(timezone.utc)
                    minutes_old = (now - created_at).total_seconds() / 60
                    
                    if minutes_old < 90:  # Likely streaming buffer issue
                        respond({
                            "text": f"❌ Cannot delete entry `{entry_id}` yet.\n\n" +
                                   f"**Reason:** BigQuery streaming buffer limitation\n" +
                                   f"**Solution:** Wait {90 - int(minutes_old)} more minutes, then try again\n\n" +
                                   f"*This happens with recently added entries (< 90 minutes old)*",
                            "response_type": "ephemeral"
                        })
                        return
                
                respond({
                    "text": f"❌ Failed to delete entry `{entry_id}`. Please check the logs.",
                    "response_type": "ephemeral"
                })
        
        except Exception as e:
            logger.error(f"Error in admin delete: {e}")
            respond({
                "text": f"❌ Error deleting entry: {str(e)}",
                "response_type": "ephemeral"
            })
    
    @app.command("/aitools-admin-tags")
    def admin_tags(ack, respond, command):
        """Manage community tag suggestions."""
        ack()
        
        if not check_admin_permission(command.get('user_id')):
            send_permission_error(respond)
            return
        
        try:
            text = command.get('text', '').strip()
            
            if not text:
                # Show pending suggestions by default
                show_pending_tag_suggestions(respond)
                return
            
            # Parse command: approve <suggestion_id> | reject <suggestion_id> | promote <tag>
            parts = text.split(' ', 1)
            if len(parts) != 2:
                respond({
                    "text": "❌ Invalid format. Usage:\n" +
                           "• `/aitools-admin-tags` - Show pending suggestions\n" +
                           "• `/aitools-admin-tags approve <suggestion_id>`\n" +
                           "• `/aitools-admin-tags reject <suggestion_id>`\n" +
                           "• `/aitools-admin-tags promote <tag_name>`",
                    "response_type": "ephemeral"
                })
                return
            
            action, target = parts[0].lower().strip(), parts[1].strip()
            user_id = command.get('user_id')
            
            if action == 'approve':
                handle_admin_approve_tag(respond, target, user_id)
            elif action == 'reject':
                handle_admin_reject_tag(respond, target, user_id)
            elif action == 'promote':
                handle_admin_promote_tag(respond, target, user_id)
            else:
                respond({
                    "text": f"❌ Unknown action: {action}. Use: approve, reject, or promote",
                    "response_type": "ephemeral"
                })
                
        except Exception as e:
            logger.error(f"Error in admin tags: {e}")
            respond({
                "text": f"❌ Error managing tags: {str(e)}",
                "response_type": "ephemeral"
            })
    
    # Handle edit buttons from admin list/search
    @app.action(re.compile(r"admin_edit_.+"))
    def handle_admin_edit_button(ack, body, respond):
        """Handle edit buttons from admin interface."""
        ack()
        
        user_id = body.get('user', {}).get('id')
        if not check_admin_permission(user_id):
            respond({
                "text": "❌ Access denied.",
                "response_type": "ephemeral"
            })
            return
        
        try:
            action = body.get('actions', [{}])[0]
            entry_id = action.get('value')
            
            entry = bigquery_service.get_entry_by_id(entry_id)
            if not entry:
                respond({
                    "text": f"❌ Entry `{entry_id}` not found.",
                    "response_type": "ephemeral"
                })
                return
            
            show_edit_form(respond, entry)
            
        except Exception as e:
            logger.error(f"Error handling admin edit button: {e}")
            respond({
                "text": f"❌ Error: {str(e)}",
                "response_type": "ephemeral"
            })
    
    # Handle admin approve tag buttons
    @app.action(re.compile(r"admin_approve_tag_.+"))
    def handle_admin_approve_button(ack, body, respond):
        """Handle admin approve tag buttons."""
        ack()
        
        user_id = body.get('user', {}).get('id')
        if not check_admin_permission(user_id):
            respond({
                "text": "❌ Access denied.",
                "response_type": "ephemeral"
            })
            return
        
        try:
            action = body.get('actions', [{}])[0]
            suggestion_id = action.get('value')
            
            handle_admin_approve_tag(respond, suggestion_id, user_id)
            
        except Exception as e:
            logger.error(f"Error handling admin approve tag button: {e}")
            respond({
                "text": f"❌ Error: {str(e)}",
                "response_type": "ephemeral"
            })

def show_edit_form(respond, entry: Dict):
    """Show the edit form for an entry."""
    tags_str = ", ".join(entry.get('tags', []))
    
    edit_form = f"""📝 *Editing Entry: {entry['title']}*

*Current Details:*
• *ID:* `{entry['id']}`
• *Title:* {entry['title']}
• *URL:* {entry.get('url') or 'None'}
• *Description:* {entry.get('description') or 'None'}
• *AI Summary:* {entry.get('ai_summary') or 'None'}
• *Target Audience:* {entry.get('target_audience') or 'None'}
• *Tags:* {tags_str or 'None'}
• *Author:* <@{entry['author_id']}>

*To edit, use:*
```
/aitools-admin-edit {entry['id']}
title: New title (optional)
description: New description (optional)
summary: New AI summary (optional) 
audience: New target audience (optional)
tags: tag1, tag2, tag3 (optional)
```

*Or use:* `/aitools-admin-retag {entry['id']}` to regenerate AI content automatically."""

    respond({
        "text": edit_form,
        "response_type": "ephemeral"
    })

def parse_edit_instructions(lines: List[str]) -> Dict:
    """Parse edit instructions from command text."""
    updates = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if ':' not in line:
            continue
        
        field, value = line.split(':', 1)
        field = field.strip().lower()
        value = value.strip()
        
        if not value:
            continue
        
        if field in ['title']:
            updates['title'] = value
        elif field in ['description', 'desc']:
            updates['description'] = value
        elif field in ['summary', 'ai_summary']:
            updates['ai_summary'] = value  
        elif field in ['audience', 'target_audience']:
            updates['target_audience'] = value
        elif field in ['tags', 'tag']:
            # Parse comma-separated tags
            tag_list = [tag.strip().lower() for tag in value.split(',') if tag.strip()]
            updates['tags'] = tag_list
    
    return updates

def show_pending_tag_suggestions(respond):
    """Show pending tag suggestions for admin review."""
    suggestions = tag_suggestions_service.get_pending_suggestions(limit=10)
    
    if not suggestions:
        respond({
            "text": "🏷️ *No Pending Tag Suggestions*\n\nAll community tag suggestions have been reviewed!",
            "response_type": "ephemeral"
        })
        return
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🏷️ *Pending Tag Suggestions* ({len(suggestions)} items)"
            }
        },
        {"type": "divider"}
    ]
    
    for suggestion in suggestions:
        net_votes = suggestion['net_votes']
        status_emoji = "🔥" if net_votes >= 2 else "⏳" if net_votes >= 0 else "❄️"
        
        suggestion_text = f"**{suggestion['entry_title']}** {status_emoji}\n" +\
                         f"*Suggested Tag:* `{suggestion['suggested_tag']}`\n" +\
                         f"*Votes:* {suggestion['upvotes']}👍 {suggestion['downvotes']}👎 (net: {net_votes:+d})\n" +\
                         f"*Suggested by:* <@{suggestion['suggested_by']}>\n" +\
                         f"*ID:* `{suggestion['id'][:8]}...`"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": suggestion_text
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Approve"
                },
                "style": "primary",
                "action_id": f"admin_approve_tag_{suggestion['id']}",
                "value": suggestion['id']
            }
        })
        blocks.append({"type": "divider"})
    
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": "💡 Use `/aitools-admin-tags approve <id>` or `/aitools-admin-tags reject <id>` to manage suggestions"
        }]
    })
    
    respond({
        "blocks": blocks,
        "response_type": "ephemeral"
    })

def handle_admin_approve_tag(respond, suggestion_id, admin_user_id):
    """Handle admin approval of a tag suggestion."""
    suggestion = tag_suggestions_service.get_suggestion_by_id(suggestion_id)
    
    if not suggestion:
        respond({
            "text": f"❌ Tag suggestion `{suggestion_id}` not found.",
            "response_type": "ephemeral"
        })
        return
    
    if suggestion['status'] != 'pending':
        respond({
            "text": f"ℹ️ Tag suggestion `{suggestion['suggested_tag']}` is already {suggestion['status']}.",
            "response_type": "ephemeral"
        })
        return
    
    # Promote tag and mark suggestion as approved
    success = tag_suggestions_service.promote_tag_to_approved(suggestion['suggested_tag'], admin_user_id)
    
    if success:
        respond({
            "text": f"✅ **Tag Approved!**\n\n" +
                   f"Tag `{suggestion['suggested_tag']}` has been approved and is now available for community use.\n\n" +
                   f"*Tool:* {suggestion.get('entry_title', 'Unknown')}\n" +
                   f"*Votes:* {suggestion['upvotes']}👍 {suggestion['downvotes']}👎",
            "response_type": "ephemeral"
        })
    else:
        respond({
            "text": f"❌ Failed to approve tag `{suggestion['suggested_tag']}`. Please try again.",
            "response_type": "ephemeral"
        })

def handle_admin_reject_tag(respond, suggestion_id, admin_user_id):
    """Handle admin rejection of a tag suggestion."""
    # For now, just mark as rejected in the suggestions table
    # TODO: Implement rejection logic in tag_suggestions_service
    respond({
        "text": f"⚠️ Tag rejection feature is not yet implemented.\n\n" +
               f"For now, you can simply ignore unwanted suggestions.\n" +
               f"They won't be auto-promoted without enough votes.",
        "response_type": "ephemeral"
    })

def handle_admin_promote_tag(respond, tag_name, admin_user_id):
    """Handle admin manual promotion of a tag."""
    success = tag_suggestions_service.promote_tag_to_approved(tag_name, admin_user_id)
    
    if success:
        respond({
            "text": f"✅ **Tag Promoted!**\n\n" +
                   f"Tag `{tag_name}` has been manually promoted to approved status.\n\n" +
                   f"It is now available for community use.",
            "response_type": "ephemeral"
        })
    else:
        respond({
            "text": f"❌ Failed to promote tag `{tag_name}`. It may already be approved.",
            "response_type": "ephemeral"
        })

logger.info("✅ Admin handlers registered successfully")
