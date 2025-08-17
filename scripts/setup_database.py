#!/usr/bin/env python3
"""
BigQuery setup script for AI Tools Wiki Bot.
Creates the necessary dataset and tables.
"""

import os
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
from dotenv import load_dotenv

def setup_bigquery():
    """Set up BigQuery dataset and tables."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    location = os.getenv('BIGQUERY_LOCATION', 'US')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not found in environment variables")
        print("Please set GOOGLE_CLOUD_PROJECT in your .env file")
        sys.exit(1)
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        
        # Create dataset
        dataset_ref = client.dataset(dataset_id)
        
        try:
            client.get_dataset(dataset_ref)
            print(f"✅ Dataset {project_id}.{dataset_id} already exists")
        except NotFound:
            print(f"🔨 Creating dataset: {project_id}.{dataset_id}")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = location
            dataset.description = "AI Tools Wiki Slack Bot data"
            client.create_dataset(dataset)
            print(f"✅ Created dataset: {project_id}.{dataset_id}")
        
        # Create entries table
        entries_table_id = f"{project_id}.{dataset_id}.entries"
        entries_schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ai_summary", "STRING", mode="NULLABLE"),
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
        
        print("\n🎉 BigQuery setup complete!")
        print(f"📊 Dataset: {project_id}.{dataset_id}")
        print("📋 Tables: entries, votes")
        print("\n🚀 You can now run the bot with: python app.py")
        
    except Exception as e:
        print(f"❌ Error setting up BigQuery: {e}")
        sys.exit(1)

def create_table_if_not_exists(client, table_id, schema, table_name):
    """Create a table if it doesn't exist."""
    try:
        client.get_table(table_id)
        print(f"✅ Table {table_name} already exists")
    except NotFound:
        print(f"🔨 Creating table: {table_name}")
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"✅ Created table: {table_name}")

def main():
    """Main setup function."""
    print("🚀 Setting up AI Tools Wiki BigQuery database...")
    setup_bigquery()

if __name__ == "__main__":
    main()
