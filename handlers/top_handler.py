"""
Handler for /aitools-top command
Shows the top AI tools by score with optional limit parameter
"""

import logging

logger = logging.getLogger(__name__)

def handle_aitools_top(ack, say, client, command, context):
    """Handle /aitools-top command with optional limit parameter"""
    ack()
    
    try:
        from services.bigquery_service import BigQueryService
        
        # Parse the limit parameter (default to 10)
        limit = 10
        command_text = command.get('text', '').strip()
        
        if command_text:
            try:
                limit = int(command_text)
                # Enforce reasonable bounds
                if limit < 1:
                    say("❌ Number must be at least 1.")
                    return
                elif limit > 50:
                    say("❌ Maximum limit is 50 entries.")
                    return
            except ValueError:
                say("❌ Please provide a valid number. Example: `/aitools-top 5`")
                return
        
        # Get top entries
        bigquery_service = BigQueryService()
        top_entries = bigquery_service.get_top_entries(limit=limit)
        
        if not top_entries:
            say("No AI tools found in the database yet! Use `/aitools-add` to add the first tool.")
            return
        
        # Build the response blocks
        header_text = f"🏆 Top {len(top_entries)} AI Tools by Score" if len(top_entries) != 10 else "🏆 Top AI Tools by Score"
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i, entry in enumerate(top_entries, 1):
            # Safely get values with fallbacks
            title = entry.get('title') or 'Untitled'
            url = entry.get('url') or ''
            summary = entry.get('ai_summary') or 'No summary available'
            target_audience = entry.get('target_audience') or ''
            tags = entry.get('tags') or []
            score = entry.get('score', 0)
            upvotes = entry.get('upvotes', 0)
            downvotes = entry.get('downvotes', 0)
            
            # Format title with ranking
            title_text = f"#{i} {title}"
            if url:
                title_text = f"<{url}|{title_text}>"
            
            # Build description
            description_parts = []
            if summary and len(summary) > 2:  # More than just empty/minimal text
                # Limit summary to ~100 words for display
                summary_display = summary if len(summary) <= 300 else summary[:297] + "..."
                description_parts.append(summary_display)
            
            if target_audience and len(target_audience) > 2:
                description_parts.append(f"*Best for:* {target_audience}")
            
            if tags and len(tags) > 0:
                # Limit to first 3 tags for display
                display_tags = tags[:3]
                tags_text = " ".join([f"`{tag}`" for tag in display_tags])
                if len(tags) > 3:
                    tags_text += f" +{len(tags) - 3} more"
                description_parts.append(f"*Tags:* {tags_text}")
            
            description = "\n".join(description_parts) if description_parts else "No details available"
            
            # Score display
            score_text = f"Score: {score}"
            if upvotes > 0 or downvotes > 0:
                score_text += f" ({upvotes}↑ {downvotes}↓)"
            
            # Add entry block
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title_text}*\n{description}\n_{score_text}_"
                }
            })
            
            # Add divider between entries (except for last one)
            if i < len(top_entries):
                blocks.append({"type": "divider"})
        
        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Use `/aitools-list` to see all tools, or `/aitools-add <url>` to add a new tool!"
                }
            ]
        })
        
        # Send the response
        say(blocks=blocks)
        
    except Exception as e:
        print(f"Error in handle_aitools_top: {e}")
        say("Sorry, I encountered an error while fetching the top AI tools. Please try again later.")
