# AI Tools Wiki Bot - Admin Guide

This guide explains how to set up and use the admin features for manual management of AI tool entries when the AI service fails or for quality control.

## Setup

### 1. Configure Admin Users

Add admin user IDs to your `.env` file:

```bash
# Comma-separated list of Slack user IDs that should have admin access
ADMIN_USER_IDS=U1234567890,U0987654321
```

To find a user's Slack ID:
1. Go to their Slack profile
2. Click the "More" (three dots) button
3. Click "Copy member ID"

### 2. Run Database Migration

If you're upgrading from an older version, run the migration to add the `target_audience` column:

```bash
python scripts/migrate_add_target_audience.py
```

## Admin Commands

All admin commands are restricted to users listed in `ADMIN_USER_IDS`.

### `/aitools-admin`
Shows the admin help menu with all available commands.

### `/aitools-admin-list [limit]`
Lists entries for management with detailed information including:
- Entry ID (for editing)
- Title, summary, target audience, tags
- Vote counts and scores
- Author and creation date
- Edit buttons for quick access

**Examples:**
- `/aitools-admin-list` - Show 20 entries (default)
- `/aitools-admin-list 50` - Show up to 50 entries

### `/aitools-admin-search <keyword>`
Search for entries to edit by keyword. Useful when you need to find and edit specific entries.

**Example:**
- `/aitools-admin-search cursor` - Find entries related to "cursor"

### `/aitools-admin-edit <entry_id>`
Edit an entry manually. Can be used in two ways:

#### 1. Show Current Details
```
/aitools-admin-edit abc123-def456-789
```
This shows current entry details and editing instructions.

#### 2. Update Entry Fields
```
/aitools-admin-edit abc123-def456-789
title: Updated Tool Name
description: New description of the tool
summary: New AI-generated summary (max 100 words)
audience: Developers, Data Scientists, etc.
tags: python, cli, automation, ai-assistant
```

**Supported fields:**
- `title` - Tool name
- `description` - Tool description  
- `summary` - AI-generated summary
- `audience` - Target audience description
- `tags` - Comma-separated tags (lowercase, hyphenated)

**Notes:**
- All fields are optional - only provide what you want to update
- Tags will completely replace existing tags
- Use lowercase, hyphenated format for tags (e.g., `code-generation`, `ai-assistant`)

### `/aitools-admin-retag <entry_id>`
Automatically regenerate AI content (summary, target audience, tags) for an entry using the current AI service.

**Example:**
```
/aitools-admin-retag abc123-def456-789
```

This is useful when:
- An entry was added when AI service was down
- You want to refresh outdated AI-generated content
- AI service has been improved and you want updated content

### `/aitools-admin-delete <entry_id>`
Permanently delete an entry and all its associated votes from the database.

**Example:**
```
/aitools-admin-delete abc123-def456-789
```

**⚠️ Warning:** This action cannot be undone. The entry and all its votes will be permanently removed from the database.

Use this when:
- Removing duplicate entries
- Deleting spam or inappropriate content
- Cleaning up test entries
- Removing entries that violate guidelines

## Common Admin Scenarios

### When AI Service Fails During Entry Addition

When users add entries and the AI service is unavailable:

1. **Entry is still created** - The bot gracefully handles AI failures
2. **User sees placeholder messages** - "AI summary will be added by admins"
3. **Admin can add missing content** using `/aitools-admin-edit` or `/aitools-admin-retag`

### Manually Tagging Entries

1. Find the entry: `/aitools-admin-search <keyword>` or `/aitools-admin-list`
2. Get the entry ID from the results
3. Edit manually:
   ```
   /aitools-admin-edit abc123-def456-789
   summary: A powerful AI-powered code editor that helps developers write better code faster
   audience: Software developers, particularly those working with Python, JavaScript, or TypeScript
   tags: code-editor, ai-assistant, vscode, productivity, autocomplete
   ```

### Quality Control

Use admin commands to:
- Fix typos in titles or descriptions
- Improve AI-generated summaries that are too generic
- Add better tags for discoverability
- Update target audience information
- Consolidate duplicate entries (manual process)

### Bulk Operations

For bulk operations, you can:
1. Use `/aitools-admin-list 50` to see many entries at once
2. Use the Edit buttons for quick access
3. For entries with missing AI content, use `/aitools-admin-retag` to batch regenerate

## Best Practices

### Tagging Guidelines

Use these tag categories:
- **Tool type**: `cli`, `web-app`, `browser-extension`, `ide-plugin`
- **AI capability**: `code-generation`, `ai-assistant`, `autocomplete`, `debugging`, `testing`
- **Language/tech**: `python`, `javascript`, `typescript`, `react`, `node-js`
- **Use case**: `pair-programming`, `code-review`, `documentation`, `learning`
- **Platform**: `vscode`, `intellij`, `terminal`, `github`, `web`

### Summary Guidelines

Good summaries should:
- Be 50-100 words max
- Explain what the tool does clearly
- Mention key benefits or features
- Be written for the target audience

**Example:**
> "Cursor is an AI-powered code editor built on VS Code that provides intelligent code completion, error detection, and natural language code generation. It helps developers write code faster by understanding context and suggesting entire functions or code blocks."

### Target Audience Guidelines

Be specific about who would benefit:
- "Software developers working with Python and JavaScript"
- "Data scientists and ML engineers using Jupyter notebooks" 
- "DevOps engineers managing CI/CD pipelines"
- "Frontend developers building React applications"

## Error Handling

If admin commands fail:
1. Check that your user ID is in the `ADMIN_USER_IDS` environment variable
2. Verify the entry ID is correct (copy from admin list results)
3. Check the bot logs for detailed error messages
4. Ensure the BigQuery database is accessible

## Security Notes

- Admin access is controlled by `ADMIN_USER_IDS` in environment variables
- Only configured users can see or use admin commands
- All admin actions are logged
- Regular users cannot access admin functionality even if they know the commands

---

For technical support or feature requests, check the bot logs or contact the development team.
