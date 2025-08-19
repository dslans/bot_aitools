"""
Configuration settings for AI Tools Wiki Bot.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # BigQuery Configuration
    BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'aitools_wiki')
    BIGQUERY_LOCATION = os.getenv('BIGQUERY_LOCATION', 'US')
    
    # AI Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-central1')
    
    # Application Settings
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '5'))
    MAX_LIST_RESULTS = int(os.getenv('MAX_LIST_RESULTS', '10'))
    
    # Admin Settings - Comma-separated list of Slack user IDs
    ADMIN_USER_IDS = os.getenv('ADMIN_USER_IDS', '').split(',') if os.getenv('ADMIN_USER_IDS') else []
    
    @classmethod
    def validate(cls):
        """Validate required settings."""
        required_settings = [
            'SLACK_BOT_TOKEN',
            'SLACK_SIGNING_SECRET',
            'GOOGLE_CLOUD_PROJECT',
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_settings)}"
            )
    
    @classmethod
    def is_admin(cls, user_id: str) -> bool:
        """Check if a user is an admin."""
        return user_id in cls.ADMIN_USER_IDS
    
    @classmethod
    def get_bigquery_table_ids(cls):
        """Get fully qualified BigQuery table IDs."""
        project = cls.GOOGLE_CLOUD_PROJECT
        dataset = cls.BIGQUERY_DATASET
        
        return {
            'entries': f"{project}.{dataset}.entries",
            'votes': f"{project}.{dataset}.votes",
        }

# Global settings instance
settings = Settings()
