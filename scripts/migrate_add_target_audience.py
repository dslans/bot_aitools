#!/usr/bin/env python3
"""
Migration script to add target_audience column to the entries table.
"""

import os
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from dotenv import load_dotenv

def migrate_target_audience_column():
    """Add target_audience column to the entries table if it doesn't exist."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not found in environment variables")
        print("Please set GOOGLE_CLOUD_PROJECT in your .env file")
        sys.exit(1)
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        
        # Get table reference
        table_id = f"{project_id}.{dataset_id}.entries"
        table = client.get_table(table_id)
        
        # Check if target_audience column already exists
        existing_fields = [field.name for field in table.schema]
        
        if 'target_audience' in existing_fields:
            print("✅ target_audience column already exists")
            return
        
        print("🔨 Adding target_audience column to entries table...")
        
        # Add the new column
        new_schema = list(table.schema)
        new_schema.append(bigquery.SchemaField("target_audience", "STRING", mode="NULLABLE"))
        
        table.schema = new_schema
        updated_table = client.update_table(table, ["schema"])
        
        print(f"✅ Successfully added target_audience column to {table_id}")
        print(f"📋 Table now has {len(updated_table.schema)} columns")
        
        # Display current schema
        print("\n📊 Current table schema:")
        for field in updated_table.schema:
            print(f"  • {field.name} ({field.field_type}, {field.mode})")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

def main():
    """Main migration function."""
    print("🚀 Starting target_audience column migration...")
    migrate_target_audience_column()
    print("\n🎉 Migration completed successfully!")
    print("\n💡 You can now use the admin commands to add target audience information to entries.")

if __name__ == "__main__":
    main()
