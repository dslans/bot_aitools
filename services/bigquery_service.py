"""
BigQuery service for database operations.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from config.settings import settings

logger = logging.getLogger(__name__)

class BigQueryService:
    """Service for BigQuery database operations."""
    
    def __init__(self):
        """Initialize the BigQuery service."""
        self.client = None
        self.table_ids = settings.get_bigquery_table_ids()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the BigQuery client."""
        try:
            self.client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            logger.info("BigQuery service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery service: {e}")
            raise
    
    def create_entry(self, title: str, url: Optional[str], description: Optional[str], 
                    ai_summary: Optional[str], tags: List[str], author_id: str) -> str:
        """
        Create a new entry in the database.
        
        Args:
            title: Entry title
            url: Optional URL
            description: Optional description
            ai_summary: AI-generated summary
            tags: List of tags
            author_id: Slack user ID
            
        Returns:
            Entry ID
        """
        entry_id = str(uuid.uuid4())
        
        row = {
            'id': entry_id,
            'title': title,
            'url': url,
            'description': description,
            'ai_summary': ai_summary,
            'tags': tags,
            'author_id': author_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            table = self.client.get_table(self.table_ids['entries'])
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Error inserting entry: {errors}")
                raise Exception(f"Failed to insert entry: {errors}")
            
            logger.info(f"Created entry {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error creating entry: {e}")
            raise
    
    def get_entry_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get an entry by URL for caching purposes.
        
        Args:
            url: The URL to search for
            
        Returns:
            Entry dict or None
        """
        if not url:
            return None
        
        query = f"""
        SELECT id, title, url, description, ai_summary, tags, author_id, created_at
        FROM `{self.table_ids['entries']}`
        WHERE url = @url
        LIMIT 1
        """
        
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("url", "STRING", url)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return {
                    'id': row.id,
                    'title': row.title,
                    'url': row.url,
                    'description': row.description,
                    'ai_summary': row.ai_summary,
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting entry by URL: {e}")
            return None
    
    def get_entry_with_score(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entry with its current vote score.
        
        Args:
            entry_id: The entry ID
            
        Returns:
            Entry dict with score or None
        """
        query = f"""
        SELECT 
            e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score,
            COUNT(CASE WHEN v.vote = 1 THEN 1 END) AS upvotes,
            COUNT(CASE WHEN v.vote = -1 THEN 1 END) AS downvotes
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        WHERE e.id = @entry_id
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at
        """
        
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return {
                    'id': row.id,
                    'title': row.title,
                    'url': row.url,
                    'description': row.description,
                    'ai_summary': row.ai_summary,
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at,
                    'score': int(row.score),
                    'upvotes': int(row.upvotes),
                    'downvotes': int(row.downvotes)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting entry with score: {e}")
            return None
    
    def add_or_update_vote(self, entry_id: str, user_id: str, vote: int) -> bool:
        """
        Add or update a vote for an entry.
        
        Args:
            entry_id: Entry ID
            user_id: Slack user ID
            vote: 1 for upvote, -1 for downvote
            
        Returns:
            True if successful
        """
        # First, try to update existing vote
        delete_query = f"""
        DELETE FROM `{self.table_ids['votes']}`
        WHERE entry_id = @entry_id AND user_id = @user_id
        """
        
        # Then insert the new vote
        insert_query = f"""
        INSERT INTO `{self.table_ids['votes']}`
        (entry_id, user_id, vote, created_at)
        VALUES (@entry_id, @user_id, @vote, @created_at)
        """
        
        try:
            # Delete existing vote
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
                ]
            )
            self.client.query(delete_query, job_config=job_config).result()
            
            # Insert new vote
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("vote", "INT64", vote),
                    bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", datetime.utcnow())
                ]
            )
            self.client.query(insert_query, job_config=job_config).result()
            
            logger.info(f"Updated vote for entry {entry_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating vote: {e}")
            return False
    
    def search_entries(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search entries by keyword.
        
        Args:
            keyword: Search keyword
            limit: Maximum results to return
            
        Returns:
            List of entry dicts with scores
        """
        query = f"""
        SELECT 
            e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        WHERE 
            LOWER(e.title) LIKE LOWER(CONCAT('%', @keyword, '%'))
            OR LOWER(e.ai_summary) LIKE LOWER(CONCAT('%', @keyword, '%'))
            OR @keyword IN UNNEST(e.tags)
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at
        ORDER BY score DESC, e.created_at DESC
        LIMIT @limit
        """
        
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("keyword", "STRING", keyword.lower()),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            entries = []
            for row in results:
                entries.append({
                    'id': row.id,
                    'title': row.title,
                    'url': row.url,
                    'description': row.description,
                    'ai_summary': row.ai_summary,
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at,
                    'score': int(row.score)
                })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            return []
    
    def list_entries(self, tag: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List entries, optionally filtered by tag.
        
        Args:
            tag: Optional tag to filter by
            limit: Maximum results to return
            
        Returns:
            List of entry dicts with scores
        """
        if tag:
            where_clause = "WHERE @tag IN UNNEST(e.tags)"
            query_params = [
                bigquery.ScalarQueryParameter("tag", "STRING", tag.lower()),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        else:
            where_clause = ""
            query_params = [
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        
        query = f"""
        SELECT 
            e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        {where_clause}
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.tags, e.author_id, e.created_at
        ORDER BY score DESC, e.created_at DESC
        LIMIT @limit
        """
        
        try:
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            entries = []
            for row in results:
                entries.append({
                    'id': row.id,
                    'title': row.title,
                    'url': row.url,
                    'description': row.description,
                    'ai_summary': row.ai_summary,
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at,
                    'score': int(row.score)
                })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error listing entries: {e}")
            return []

# Global BigQuery service instance
bigquery_service = BigQueryService()
