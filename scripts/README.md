# Setup Scripts

## 🚀 Quick Start

Run the comprehensive setup script to initialize the complete database:

```bash
python scripts/setup.py
```

This single script handles everything:

## ✅ What the Setup Script Does

### 1. **Dataset Creation**
- Creates BigQuery dataset (e.g., `aitools_wiki`)
- Sets appropriate location and description
- Handles existing datasets gracefully

### 2. **Core Tables** 
- **`entries`** - Tool submissions with complete schema including `target_audience`
- **`votes`** - User voting records for Reddit-style scoring

### 3. **Community Tag System**
- **`tag_suggestions`** - Community tag proposals with voting metadata
- **`tag_votes`** - Individual votes on tag suggestions  
- **`approved_community_tags`** - Community-approved tags for use

### 4. **Schema Migrations**
- Automatically adds missing columns to existing tables
- Handles incremental schema updates
- Preserves existing data

### 5. **Verification**
- Confirms all tables were created successfully
- Shows table statistics (columns, row counts)
- Reports any issues found

## 🔧 Smart Features

- **Idempotent**: Safe to run multiple times
- **Migration-aware**: Adds missing columns to existing tables  
- **Error handling**: Clear error messages and troubleshooting
- **Verification**: Built-in verification of setup completion

## 📋 Prerequisites

1. **Google Cloud Project** set up with BigQuery API enabled
2. **Authentication** configured (service account or `gcloud auth`)
3. **Environment variables** in `.env` file:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   BIGQUERY_DATASET=aitools_wiki
   BIGQUERY_LOCATION=US
   ```

## 🎯 Output Example

```
============================================================
🤖 AI Tools Wiki Bot - Complete Database Setup
============================================================
🚀 Setting up AI Tools Wiki Bot database...
📊 Project: my-project-123
📊 Dataset: aitools_wiki
🌍 Location: US

✅ Dataset my-project-123.aitools_wiki already exists

📋 Setting up core tables...
✅ Table entries already exists
🔧 Adding 1 missing columns to entries:
   + target_audience (STRING)
✅ Updated schema for entries
✅ Table votes already exists

🏷️ Setting up community tag system...
🔨 Creating table: tag_suggestions
✅ Created table: tag_suggestions
🔨 Creating table: tag_votes
✅ Created table: tag_votes
🔨 Creating table: approved_community_tags
✅ Created table: approved_community_tags

🎉 Complete database setup finished!
✅ Dataset created
✅ Core tables: entries, votes
✅ Community tag system: tag_suggestions, tag_votes, approved_community_tags
✅ All schema migrations applied

🔍 Verifying setup...
✅ entries: 9 columns, 0 rows
✅ votes: 4 columns, 0 rows
✅ tag_suggestions: 10 columns, 0 rows
✅ tag_votes: 4 columns, 0 rows
✅ approved_community_tags: 5 columns, 0 rows

🎉 All tables verified successfully!

============================================================
🚀 Setup Complete! You can now run: python app.py
============================================================
```

## 🔄 Migration from Old Scripts

If you previously used the individual setup scripts:
- `setup_database.py` ❌ (replaced)
- `add_tag_suggestions_table.py` ❌ (replaced) 
- `migrate_add_target_audience.py` ❌ (replaced)

The new `setup.py` script handles all of these functions automatically and includes additional improvements like verification and better error handling.

## 🆘 Troubleshooting

### Authentication Issues
```bash
# Set up application default credentials
gcloud auth application-default login

# Or use service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### Permission Issues
Ensure your Google Cloud account has:
- BigQuery Data Editor
- BigQuery Job User  
- BigQuery Admin (for dataset creation)

### Environment Variables
Make sure your `.env` file contains:
```
GOOGLE_CLOUD_PROJECT=your-actual-project-id
BIGQUERY_DATASET=aitools_wiki
```

## 📞 Need Help?

If you encounter issues:
1. Check the error messages - they're designed to be helpful
2. Verify your Google Cloud project and permissions
3. Ensure BigQuery API is enabled in your project
4. Run the script again - it's safe and will show what's already done
