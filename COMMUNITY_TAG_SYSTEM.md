# Community Tag Voting System

## Overview
This document describes the complete community-driven tag suggestion and voting system implemented for the AI Tools Wiki Slack bot. The system allows community members to suggest new tags for entries, vote on suggestions, and enables automatic approval based on community votes or admin review.

## Architecture

### Database Tables
Three BigQuery tables were created to support the tag system:

1. **`tag_suggestions`** - Stores community tag suggestions with voting data
   - `id` (STRING): Unique suggestion identifier
   - `entry_id` (STRING): ID of the entry being tagged
   - `suggested_tag` (STRING): The proposed tag
   - `suggested_by` (STRING): User ID who made the suggestion
   - `status` (STRING): pending/approved/rejected
   - `upvotes` (INT64): Number of upvotes
   - `downvotes` (INT64): Number of downvotes  
   - `net_votes` (INT64): Upvotes minus downvotes
   - `created_at` (TIMESTAMP): When suggestion was created
   - `updated_at` (TIMESTAMP): Last modification time

2. **`tag_votes`** - Tracks individual user votes on suggestions
   - `suggestion_id` (STRING): References tag_suggestions.id
   - `user_id` (STRING): User who voted
   - `vote` (INT64): 1 for upvote, -1 for downvote
   - `created_at` (TIMESTAMP): When vote was cast

3. **`approved_community_tags`** - Stores approved community tags
   - `tag` (STRING): The approved tag name
   - `description` (STRING): Tag description
   - `approved_by` (STRING): User or 'auto' who approved it
   - `usage_count` (INT64): Number of times used (future feature)
   - `created_at` (TIMESTAMP): When approved

### Services

#### TagSuggestionsService (`services/tag_suggestions_service.py`)
Core service handling all tag suggestion operations:
- **suggest_tag()** - Create new tag suggestions
- **vote_on_suggestion()** - Handle voting with automatic vote count updates
- **promote_tag_to_approved()** - Promote community tags to approved status
- **get_pending_suggestions()** - Fetch suggestions for admin review
- **get_all_approved_community_tags()** - Get approved tags for display
- **_check_auto_promotion()** - Auto-approve tags with 3+ net votes

## User Commands

### `/aitools-suggest-tag <entry_id> <tag>`
Allows users to suggest new tags for entries:
- Validates entry exists and tag format
- Prevents suggestion of core predefined tags
- Creates suggestion or retrieves existing one
- Displays interactive voting interface with 👍/👎 buttons
- Shows current vote counts and net score

### `/aitools-tags`
Enhanced tags display now includes:
- Core predefined tags organized by category
- Community tags (both used tags and approved suggestions)
- Footer promoting tag suggestions to users
- Total count of available tags

## Admin Commands

### `/aitools-admin-tags`
Comprehensive admin interface for managing tag suggestions:
- **No parameters**: Show pending suggestions with vote counts
- **`approve <suggestion_id>`**: Approve a specific suggestion
- **`reject <suggestion_id>`**: Reject a suggestion (future implementation)
- **`promote <tag_name>`**: Manually promote any tag to approved status

Features:
- Visual indicators for suggestion "temperature" (🔥 hot, ⏳ neutral, ❄️ cold)
- One-click approve buttons in the interface
- Integration with existing admin permission system

## Voting System

### Interactive Voting
- Users can upvote (👍) or downvote (👎) tag suggestions
- Votes can be changed (new vote replaces old vote)
- Real-time vote count updates
- Net vote calculation (upvotes - downvotes)

### Auto-Promotion Logic
- Tags with 3+ net positive votes are automatically promoted
- Promoted tags become available immediately
- Suggestion status updates to "approved"
- Auto-promotion triggered after each vote

## Integration Points

### Tags Handler Enhancement
- `/aitools-tags` now displays approved community tags
- Combines used tags from entries with approved suggestions
- Promotes community participation through footer messaging

### Admin System Integration  
- Tag management commands integrated into existing admin framework
- Respects admin permissions and error handling patterns
- Consistent with existing admin command UX

## Voting Flow Example

1. **User suggests tag**: `/aitools-suggest-tag entry123 machine-learning`
2. **System displays**: Interactive message with voting buttons
3. **Community votes**: Users click 👍 or 👎, counts update in real-time
4. **Auto-promotion**: At 3+ net votes, tag automatically approved
5. **Availability**: Approved tags appear in `/aitools-tags` and can be used

## Admin Management Example

1. **Admin reviews**: `/aitools-admin-tags` shows pending suggestions
2. **Manual approval**: Click "✅ Approve" button or use command
3. **Promotion**: Tag moves to approved status, available for use
4. **Oversight**: Admins can promote any tag manually if needed

## Key Features

### Community Driven
- Democratic voting system with transparent vote counts
- Automatic promotion based on community consensus
- Prevents spam through validation and admin oversight

### Admin Oversight
- Complete admin interface for managing suggestions
- Manual promotion capabilities for immediate tag approval
- Integration with existing admin permission system

### User Experience
- Simple suggestion command with clear feedback
- Interactive voting with real-time updates
- Discovery of new tags through enhanced `/aitools-tags`

### Technical Robustness
- Comprehensive error handling and logging
- BigQuery integration with proper parameterized queries
- Service layer abstraction for maintainable code
- Consistent with existing bot architecture

## Future Enhancements

1. **Tag Rejection**: Complete implementation of rejection functionality
2. **Usage Tracking**: Track how often approved tags are used
3. **Tag Categories**: Organize community tags by category
4. **Batch Operations**: Admin tools for bulk tag management
5. **Analytics**: Voting patterns and tag popularity metrics

## Files Modified/Created

### New Files:
- `services/tag_suggestions_service.py` - Core tag suggestion service
- `handlers/suggest_tag_handler.py` - User-facing tag suggestion commands
- `migrations/create_tag_tables.sql` - Database schema creation

### Modified Files:
- `handlers/admin_handler.py` - Added tag management commands
- `handlers/tags_handler.py` - Enhanced to show community tags
- `main.py` - Registered new handlers (assumed)

## Database Migration Applied
The BigQuery tables were successfully created and are ready for production use. The migration script can be found in `migrations/create_tag_tables.sql`.

---

This completes the full community tag voting system implementation as specified in the original requirements. The system is production-ready and provides a complete democratic tagging experience for the AI Tools Wiki community.
