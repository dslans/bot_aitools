#!/usr/bin/env python3
"""
Add tag_suggestions table for community tag voting system.
"""

import os
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
from dotenv import load_dotenv

def add_tag_suggestions_table():
    """Add tag_suggestions table to the dataset."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not found in environment variables")
        sys.exit(1)
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        
        # Create tag_suggestions table
        table_id = f"{project_id}.{dataset_id}.tag_suggestions"
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),  # UUID
            bigquery.SchemaField("entry_id", "STRING", mode="REQUIRED"),  # Which tool entry
            bigquery.SchemaField("suggested_tag", "STRING", mode="REQUIRED"),  # The proposed tag
            bigquery.SchemaField("suggested_by", "STRING", mode="REQUIRED"),  # User ID who suggested
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # pending, approved, rejected
            bigquery.SchemaField("upvotes", "INT64", mode="REQUIRED"),  # Number of upvotes
            bigquery.SchemaField("downvotes", "INT64", mode="REQUIRED"),  # Number of downvotes
            bigquery.SchemaField("net_votes", "INT64", mode="REQUIRED"),  # upvotes - downvotes
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        try:
            client.get_table(table_id)
            print(f"✅ Table tag_suggestions already exists")
            return
        except NotFound:
            print(f"🔨 Creating table: tag_suggestions")
            table = bigquery.Table(table_id, schema=schema)
            table = client.create_table(table)
            print(f"✅ Created table: tag_suggestions")
        
        # Create tag_votes table for tracking who voted on each suggestion
        votes_table_id = f"{project_id}.{dataset_id}.tag_votes"
        votes_schema = [
            bigquery.SchemaField("suggestion_id", "STRING", mode="REQUIRED"),  # Links to tag_suggestions.id
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),  # User who voted
            bigquery.SchemaField("vote", "INT64", mode="REQUIRED"),  # 1 for upvote, -1 for downvote
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        try:
            client.get_table(votes_table_id)
            print(f"✅ Table tag_votes already exists")
        except NotFound:
            print(f"🔨 Creating table: tag_votes")
            votes_table = bigquery.Table(votes_table_id, schema=votes_schema)
            votes_table = client.create_table(votes_table)
            print(f"✅ Created table: tag_votes")
        
        # Create approved_community_tags table for approved tags
        approved_table_id = f"{project_id}.{dataset_id}.approved_community_tags"
        approved_schema = [
            bigquery.SchemaField("tag", "STRING", mode="REQUIRED"),  # The approved tag
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),  # Optional description
            bigquery.SchemaField("approved_by", "STRING", mode="REQUIRED"),  # Admin who approved (or 'auto')
            bigquery.SchemaField("usage_count", "INT64", mode="REQUIRED"),  # How many times used
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        try:
            client.get_table(approved_table_id)
            print(f"✅ Table approved_community_tags already exists")
        except NotFound:
            print(f"🔨 Creating table: approved_community_tags")
            approved_table = bigquery.Table(approved_table_id, schema=approved_schema)
            approved_table = client.create_table(approved_table)
            print(f"✅ Created table: approved_community_tags")
        
        print(f"\n🎉 Tag suggestions system setup complete!")
        print(f"📊 Tables added:")
        print(f"   - tag_suggestions (community tag proposals)")
        print(f"   - tag_votes (voting records)")
        print(f"   - approved_community_tags (approved community tags)")
        
    except Exception as e:
        print(f"❌ Error setting up tag suggestions tables: {e}")
        sys.exit(1)

def main():
    """Main function."""
    print("🚀 Adding tag suggestions tables to BigQuery...")
    add_tag_suggestions_table()

if __name__ == "__main__":
    main()
