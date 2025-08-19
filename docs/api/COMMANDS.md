# AI Tools Wiki Bot - API Documentation

This document provides comprehensive documentation for all available bot commands.

## 📖 User Commands

### `/aitools`
**Description**: Show help and available commands

**Usage**: `/aitools`

**Example**:
```
/aitools
```

**Response**:
Shows a comprehensive help menu with all available commands, examples, and usage instructions.

---

### `/aitools-add <title> | <url or description>`
**Description**: Add a new AI tool to the wiki

**Parameters**:
- `title`: Tool name
- `url or description`: Tool URL (preferred) or description text

**Usage**: `/aitools-add <title> | <url or description>`

**Examples**:
```
/aitools-add Cursor | https://cursor.sh
/aitools-add Custom AI Script | A Python script that generates code using GPT-4
```

**Response**:
- Shows processing message while AI analyzes the tool
- Displays formatted entry with auto-generated summary, target audience, and tags
- Includes interactive voting buttons (👍/👎)
- Shows current score (starts at 0)

**Features**:
- **Smart caching**: Duplicate URLs are detected and existing entries returned
- **AI-powered analysis**: Automatically generates summaries and tags using Google Gemini
- **Web scraping**: Extracts metadata from URLs when possible
- **Graceful fallback**: Creates entry even if AI service fails (admins can add content later)

---

### `/aitools-search <keyword>`
**Description**: Search for AI tools by keyword

**Parameters**:
- `keyword`: Search term (searches titles, summaries, and tags)

**Usage**: `/aitools-search <keyword>`

**Examples**:
```
/aitools-search cursor
/aitools-search code generation
/aitools-search python
```

**Response**:
- Shows top matching tools (up to 5 by default)
- Includes tool titles, summaries, and scores
- Results ranked by relevance and community voting

**Search Coverage**:
- Tool titles
- AI-generated summaries
- Tags (exact match)
- User descriptions

---

### `/aitools-list [tag]`
**Description**: List trending AI tools, optionally filtered by tag

**Parameters**:
- `tag` (optional): Filter results by specific tag

**Usage**: `/aitools-list [tag]`

**Examples**:
```
/aitools-list
/aitools-list python
/aitools-list code-generation
/aitools-list ai-assistant
```

**Response**:
- Shows top tools ordered by community score
- Each entry includes:
  - Tool title (linked if URL available)
  - AI-generated summary
  - Target audience information
  - Tags (first 3 shown, "+X more" if needed)
  - Current score with vote breakdown
  - Interactive voting buttons (👍/👎)
  - **🏷️ Suggest Tag** button for community tag suggestions

**Features**:
- **Interactive voting**: Click buttons to upvote/downvote
- **Community tagging**: One-click tag suggestion via buttons
- **Smart display**: Limits summary length and tag display for readability

---

### `/aitools-top [limit]`
**Description**: Show top-rated AI tools by score

**Parameters**:
- `limit` (optional): Number of entries to show (default: 10, max: 50)

**Usage**: `/aitools-top [limit]`

**Examples**:
```
/aitools-top
/aitools-top 5
/aitools-top 25
```

**Response**:
- Shows highest-scoring tools in ranked order (#1, #2, etc.)
- Each entry includes:
  - Ranking number and linked title
  - AI-generated summary (truncated if needed)
  - Target audience
  - Top 3 tags ("+X more" if additional tags exist)
  - Score with detailed vote breakdown (upvotes/downvotes)

**Features**:
- **Flexible limits**: Show anywhere from 1-50 entries
- **Smart truncation**: Summaries limited to ~300 characters for readability
- **Score transparency**: Shows both net score and vote breakdown
- **Dynamic header**: Shows actual count when different from default

---

### `/aitools-tags`
**Description**: Browse all available tags

**Usage**: `/aitools-tags`

**Example**:
```
/aitools-tags
```

**Response**:
- **Core Tags**: Predefined tags organized by category:
  - **Development**: `python`, `javascript`, `typescript`, etc.
  - **AI Features**: `code-generation`, `ai-assistant`, `autocomplete`, etc.
  - **Tools**: `cli`, `web-app`, `browser-extension`, etc.
  - **Use Cases**: `debugging`, `testing`, `documentation`, etc.

- **Community Tags**: Tags suggested and approved by community voting

**Features**:
- **Organized display**: Tags grouped by logical categories
- **Usage counts**: Shows which tags are most popular
- **Community promotion**: Encourages community participation in tagging

---

### `/aitools-suggest-tag <entry_id> <tag>`
**Description**: Suggest a new community tag for an entry

**Parameters**:
- `entry_id`: ID of the entry to tag
- `tag`: Proposed tag name (lowercase, hyphenated format)

**Usage**: `/aitools-suggest-tag <entry_id> <tag>`

**Examples**:
```
/aitools-suggest-tag abc12345 machine-learning
/aitools-suggest-tag def67890 typescript-support
```

**Response**:
- Shows the suggested tag with entry context
- Provides interactive voting buttons (👍/👎)
- Displays current vote counts
- Auto-approval notification at 3+ net votes

**Discovery Methods**:
1. **🏷️ Suggest Tag buttons** in `/aitools-list` (recommended)
2. **Admin interface** shows full entry IDs
3. **Manual lookup** if entry ID known

**Features**:
- **Democratic voting**: Community decides on tag approval
- **Auto-promotion**: Tags with 3+ net votes automatically approved
- **Duplicate prevention**: Prevents suggesting existing tags
- **Real-time updates**: Vote counts update immediately

---

## 🔧 Admin Commands

Admin commands require user ID to be listed in `ADMIN_USER_IDS` environment variable.

### `/aitools-admin-list [limit]`
**Description**: List entries for admin management

**Parameters**:
- `limit` (optional): Number of entries to show (default: 20)

**Usage**: `/aitools-admin-list [limit]`

**Examples**:
```
/aitools-admin-list
/aitools-admin-list 50
```

**Response**:
- Detailed entry information including:
  - Full entry ID
  - Title, summary, target audience, tags
  - Vote counts and scores
  - Author and creation date
  - **Edit** buttons for quick access

---

### `/aitools-admin-edit <entry_id>`
**Description**: Edit entry details manually

**Parameters**:
- `entry_id`: Full entry ID to edit

**Usage**: 
```
# Show current details
/aitools-admin-edit abc123-def456-789

# Update specific fields
/aitools-admin-edit abc123-def456-789
title: Updated Tool Name
summary: New AI-generated summary
audience: Software developers
tags: python, cli, automation
```

**Supported Fields**:
- `title`: Tool name
- `description`: Tool description
- `summary`: AI-generated summary
- `audience`: Target audience
- `tags`: Comma-separated tags (replaces all existing tags)

---

### `/aitools-admin-retag <entry_id>`
**Description**: Regenerate AI content for an entry

**Parameters**:
- `entry_id`: Entry ID to regenerate content for

**Usage**: `/aitools-admin-retag abc123-def456-789`

**Use Cases**:
- Entry added when AI service was down
- Refresh outdated AI content
- Apply improved AI models to existing entries

---

### `/aitools-admin-delete <entry_id>`
**Description**: Permanently delete an entry and all associated votes

**Parameters**:
- `entry_id`: Entry ID to delete

**Usage**: `/aitools-admin-delete abc123-def456-789`

**⚠️ Warning**: This action cannot be undone. Use for:
- Removing duplicate entries
- Deleting spam or inappropriate content
- Cleaning up test entries

---

### `/aitools-admin-tags [action] [parameter]`
**Description**: Manage community tag suggestions

**Usage Patterns**:
```
# Show pending suggestions
/aitools-admin-tags

# Approve specific suggestion
/aitools-admin-tags approve abc123-def456

# Manually promote any tag
/aitools-admin-tags promote machine-learning
```

**Features**:
- **Visual indicators**: 🔥 hot, ⏳ neutral, ❄️ cold suggestions
- **One-click approval**: Interactive buttons for quick management
- **Manual promotion**: Override community voting when needed

---

## 🤖 Interactive Features

### Voting Buttons
Available on tool listings, triggered by clicking 👍 or 👎 buttons:

**Response**: 
- Ephemeral confirmation message
- Shows updated score
- Prevents vote spam (one vote per user per tool)
- Users can change their vote

**Example Response**:
```
You upvoted 👍 Cursor! New score: +12
```

### Tag Suggestion Buttons
Available on tool listings via **🏷️ Suggest Tag** buttons:

**Response**:
- Shows entry details and pre-filled command
- Guides users through the suggestion process
- Eliminates need to manually find entry IDs

**Example Response**:
```
💡 To suggest a tag for Cursor, use:
/aitools-suggest-tag abc12345 your-suggested-tag

Replace "your-suggested-tag" with your suggestion (e.g., "typescript-support")
```

### Tag Vote Buttons
Available on tag suggestions, triggered by 👍 or 👎 voting:

**Response**:
- Updates vote count in real-time
- Shows auto-approval at 3+ net votes
- Allows users to change votes

---

## 💬 Direct Message Support

The bot supports direct message interactions with natural language commands:

### Supported DM Commands
```
help                    → Show help
add [title] | [url]     → Add new tool
search [keyword]        → Search tools
list [tag]             → List tools
```

### Examples
```
help
add Cursor | https://cursor.sh
search code generation
list python
```

---

## 📊 Response Formats

### Entry Display Format
```
✅ Added *Tool Name*
🔗 https://tool-url.com
📝 AI-generated summary describing the tool's capabilities...
👥 Best for: Software developers working with Python
🏷️ Tags: python, cli, ai-assistant
📊 Score: +5 (8↑ 3↓)
[👍] [👎] [🏷️ Suggest Tag]
```

### Search Results Format
```
🔍 Search Results for "keyword":

1. **Tool Name** (+5) - Brief summary of the tool
2. **Another Tool** (+3) - Another brief summary
```

### Tag Display Format
```
🏷️ Available Tags

**Development:**
`python` `javascript` `typescript`

**Community Tags:**
`machine-learning` `react-components` `docker-support`
```

---

## ⚡ Performance Considerations

- **Search**: Limited to 5 results by default for performance
- **Listing**: Default 10 results, configurable via settings
- **AI Processing**: May take 10-30 seconds for content generation
- **Caching**: Duplicate URLs return cached results immediately
- **Rate Limiting**: Built-in protection against spam

---

## 🔗 Integration Points

### BigQuery Tables
- `entries`: Main tool data
- `votes`: User voting records
- `tag_suggestions`: Community tag proposals
- `tag_votes`: Votes on tag suggestions
- `approved_community_tags`: Approved community tags

### External Services
- **Google Gemini AI**: Content generation and analysis
- **Web Scraping**: Metadata extraction from URLs
- **Google BigQuery**: Data storage and querying

---

For deployment information, see [docs/guides/DEPLOYMENT.md](../guides/DEPLOYMENT.md)
For admin operations, see [docs/admin/ADMIN_GUIDE.md](../admin/ADMIN_GUIDE.md)
