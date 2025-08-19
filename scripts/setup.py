#!/usr/bin/env python3
"""
Comprehensive setup script for AI Tools Wiki Bot.
Handles all database initialization, schema creation, and migrations.
"""

import os
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
from dotenv import load_dotenv

def setup_complete_database():
    """Set up complete BigQuery dataset and all tables."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    location = os.getenv('BIGQUERY_LOCATION', 'US')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not found in environment variables")
        print("Please set GOOGLE_CLOUD_PROJECT in your .env file")
        sys.exit(1)
    
    try:
        print("🚀 Setting up AI Tools Wiki Bot database...")
        print(f"📊 Project: {project_id}")
        print(f"📊 Dataset: {dataset_id}")
        print(f"🌍 Location: {location}")
        print()
        
        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        
        # Create dataset
        setup_dataset(client, project_id, dataset_id, location)
        
        # Create all tables
        setup_core_tables(client, project_id, dataset_id)
        setup_community_tag_tables(client, project_id, dataset_id)
        
        print("\n🎉 Complete database setup finished!")
        print("✅ Dataset created")
        print("✅ Core tables: entries, votes")
        print("✅ Community tag system: tag_suggestions, tag_votes, approved_community_tags")
        print("✅ All schema migrations applied")
        print()
        print("🚀 You can now run the bot with: python app.py")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)

def setup_dataset(client, project_id, dataset_id, location):
    """Create dataset if it doesn't exist."""
    dataset_ref = client.dataset(dataset_id)
    
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset {project_id}.{dataset_id} already exists")
    except NotFound:
        print(f"🔨 Creating dataset: {project_id}.{dataset_id}")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset.description = "AI Tools Wiki Slack Bot - Complete database with community features"
        client.create_dataset(dataset)
        print(f"✅ Created dataset: {project_id}.{dataset_id}")

def setup_core_tables(client, project_id, dataset_id):
    """Create core tables: entries and votes."""
    print("\n📋 Setting up core tables...")
    
    # Create entries table with complete schema
    entries_table_id = f"{project_id}.{dataset_id}.entries"
    entries_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ai_summary", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("target_audience", "STRING", mode="NULLABLE"),  # Included from start
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("author_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    create_table_if_not_exists(client, entries_table_id, entries_schema, "entries")
    
    # Create votes table
    votes_table_id = f"{project_id}.{dataset_id}.votes"
    votes_schema = [
        bigquery.SchemaField("entry_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("vote", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    create_table_if_not_exists(client, votes_table_id, votes_schema, "votes")

def setup_community_tag_tables(client, project_id, dataset_id):
    """Create community tag system tables."""
    print("\n🏷️ Setting up community tag system...")
    
    # Create tag_suggestions table
    tag_suggestions_table_id = f"{project_id}.{dataset_id}.tag_suggestions"
    tag_suggestions_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),  # UUID
        bigquery.SchemaField("entry_id", "STRING", mode="REQUIRED"),  # Which tool entry
        bigquery.SchemaField("suggested_tag", "STRING", mode="REQUIRED"),  # The proposed tag
        bigquery.SchemaField("suggested_by", "STRING", mode="REQUIRED"),  # User ID who suggested
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # pending, approved, rejected
        bigquery.SchemaField("upvotes", "INT64", mode="REQUIRED", default_value_expression="0"),
        bigquery.SchemaField("downvotes", "INT64", mode="REQUIRED", default_value_expression="0"),
        bigquery.SchemaField("net_votes", "INT64", mode="REQUIRED", default_value_expression="0"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    create_table_if_not_exists(client, tag_suggestions_table_id, tag_suggestions_schema, "tag_suggestions")
    
    # Create tag_votes table
    tag_votes_table_id = f"{project_id}.{dataset_id}.tag_votes"
    tag_votes_schema = [
        bigquery.SchemaField("suggestion_id", "STRING", mode="REQUIRED"),  # Links to tag_suggestions.id
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),  # User who voted
        bigquery.SchemaField("vote", "INT64", mode="REQUIRED"),  # 1 for upvote, -1 for downvote
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    create_table_if_not_exists(client, tag_votes_table_id, tag_votes_schema, "tag_votes")
    
    # Create approved_community_tags table
    approved_tags_table_id = f"{project_id}.{dataset_id}.approved_community_tags"
    approved_tags_schema = [
        bigquery.SchemaField("tag", "STRING", mode="REQUIRED"),  # The approved tag
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),  # Optional description
        bigquery.SchemaField("approved_by", "STRING", mode="REQUIRED"),  # Admin who approved (or 'auto')
        bigquery.SchemaField("usage_count", "INT64", mode="REQUIRED", default_value_expression="0"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    create_table_if_not_exists(client, approved_tags_table_id, approved_tags_schema, "approved_community_tags")

def create_table_if_not_exists(client, table_id, schema, table_name):
    """Create a table if it doesn't exist."""
    try:
        table = client.get_table(table_id)
        print(f"✅ Table {table_name} already exists")
        
        # Check if we need to add any missing columns (basic migration)
        migrate_table_schema_if_needed(client, table, schema, table_name)
        
    except NotFound:
        print(f"🔨 Creating table: {table_name}")
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"✅ Created table: {table_name}")

def migrate_table_schema_if_needed(client, table, target_schema, table_name):
    """Add missing columns to existing table if needed."""
    existing_field_names = [field.name for field in table.schema]
    target_field_names = [field.name for field in target_schema]
    
    missing_fields = []
    for target_field in target_schema:
        if target_field.name not in existing_field_names:
            missing_fields.append(target_field)
    
    if missing_fields:
        print(f"🔧 Adding {len(missing_fields)} missing columns to {table_name}:")
        for field in missing_fields:
            print(f"   + {field.name} ({field.field_type})")
        
        # Add missing fields to schema
        new_schema = list(table.schema) + missing_fields
        table.schema = new_schema
        
        try:
            updated_table = client.update_table(table, ["schema"])
            print(f"✅ Updated schema for {table_name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not update schema for {table_name}: {e}")
    
def verify_setup(client, project_id, dataset_id):
    """Verify that all tables were created correctly."""
    print("\n🔍 Verifying setup...")
    
    expected_tables = [
        'entries',
        'votes', 
        'tag_suggestions',
        'tag_votes',
        'approved_community_tags'
    ]
    
    all_good = True
    for table_name in expected_tables:
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        try:
            table = client.get_table(table_id)
            row_count = table.num_rows
            print(f"✅ {table_name}: {len(table.schema)} columns, {row_count} rows")
        except Exception as e:
            print(f"❌ {table_name}: Error - {e}")
            all_good = False
    
    return all_good

def main():
    """Main setup function."""
    print("=" * 60)
    print("🤖 AI Tools Wiki Bot - Complete Database Setup")
    print("=" * 60)
    
    setup_complete_database()
    
    # Optional: Verify setup
    load_dotenv()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            if verify_setup(client, project_id, dataset_id):
                print("\n🎉 All tables verified successfully!")
            else:
                print("\n⚠️  Some tables may have issues. Check the output above.")
        except Exception as e:
            print(f"\n⚠️  Could not verify setup: {e}")
    
    print("\n" + "=" * 60)
    print("🚀 Setup Complete! You can now run: python app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
