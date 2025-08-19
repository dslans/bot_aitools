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

logger = logging.getLogger(__name__)

def register_admin_handler(app: App):
    """Register admin command handlers."""
    logger.info("🔧 Registering admin handlers...")
    
    def check_admin_permission(user_id: str) -> bool:
        """Check if user has admin permissions."""
        return settings.is_admin(user_id)
    
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
            
            entries = bigquery_service.list_all_entries_for_admin(limit=limit)
            
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
                # Truncate long titles and summaries
                title = entry['title'][:50] + "..." if len(entry['title']) > 50 else entry['title']
                summary = entry.get('ai_summary') or 'No AI summary'
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                
                tags_text = ", ".join(entry.get('tags', [])[:3]) if entry.get('tags') else 'No tags'
                if len(entry.get('tags', [])) > 3:
                    tags_text += f" (+{len(entry['tags']) - 3} more)"
                
                audience = entry.get('target_audience', 'No target audience')
                if len(audience) > 50:
                    audience = audience[:50] + "..."
                
                entry_text = f"""**{title}**
*ID:* `{entry['id'][:8]}...` | *Score:* {entry['score']:+d} ({entry['upvotes']}👍 {entry['downvotes']}👎)
*Summary:* {summary}
*Audience:* {audience}  
*Tags:* {tags_text}
*Author:* <@{entry['author_id']}> | *Created:* {entry['created_at'].strftime('%Y-%m-%d')}"""
                
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

logger.info("✅ Admin handlers registered successfully")
