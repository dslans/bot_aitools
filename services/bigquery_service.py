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
    
    def _get_fresh_table(self, table_id: str):
        """Get a fresh table reference to avoid caching issues."""
        return self.client.get_table(table_id)
    
    def create_entry(self, title: str, url: Optional[str], description: Optional[str], 
                    ai_summary: Optional[str], target_audience: Optional[str], tags: List[str], 
                    author_id: str, security_status: Optional[str] = None, 
                    security_display: Optional[str] = None) -> str:
        """
        Create a new entry in the database.
        
        Args:
            title: Entry title
            url: Optional URL
            description: Optional description
            ai_summary: AI-generated summary
            target_audience: Target audience description
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
            'target_audience': target_audience,
            'tags': tags,
            'author_id': author_id,
            'security_status': security_status,
            'security_display': security_display,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Get a fresh table reference to avoid caching issues
            table = self._get_fresh_table(self.table_ids['entries'])
            
            # Log table schema for debugging
            schema_fields = [f.name for f in table.schema]
            logger.info(f"Table schema fields: {schema_fields}")
            logger.info(f"Row keys being inserted: {list(row.keys())}")
            
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Error inserting entry: {errors}")
                
                # Try to handle missing field errors by progressively removing problematic fields
                problematic_fields = []
                
                # Check for target_audience field errors
                if any('target_audience' in str(error) for error in errors):
                    problematic_fields.append('target_audience')
                    logger.warning("target_audience field error detected")
                
                # Check for security field errors
                if any('security_status' in str(error) or 'security_display' in str(error) for error in errors):
                    problematic_fields.extend(['security_status', 'security_display'])
                    logger.warning("security fields error detected")
                
                if problematic_fields:
                    logger.warning(f"Trying insert without problematic fields: {problematic_fields}")
                    # Remove problematic fields and retry
                    fallback_row = {k: v for k, v in row.items() if k not in problematic_fields}
                    fallback_errors = self.client.insert_rows_json(table, [fallback_row])
                    if fallback_errors:
                        logger.error(f"Fallback insert also failed: {fallback_errors}")
                        raise Exception(f"Failed to insert entry: {fallback_errors}")
                    else:
                        logger.info(f"Created entry {entry_id} without fields: {problematic_fields}")
                        return entry_id
                else:
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
            e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at,
            e.security_status, e.security_display,
            COALESCE(SUM(v.vote), 0) AS score,
            COUNT(CASE WHEN v.vote = 1 THEN 1 END) AS upvotes,
            COUNT(CASE WHEN v.vote = -1 THEN 1 END) AS downvotes
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        WHERE e.id = @entry_id
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at, e.security_status, e.security_display
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
                    'target_audience': getattr(row, 'target_audience', None),
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at,
                    'security_status': getattr(row, 'security_status', None),
                    'security_display': getattr(row, 'security_display', None),
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
            e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        WHERE 
            LOWER(e.title) LIKE LOWER(CONCAT('%', @keyword, '%'))
            OR LOWER(e.ai_summary) LIKE LOWER(CONCAT('%', @keyword, '%'))
            OR @keyword IN UNNEST(e.tags)
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at
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
                    'target_audience': getattr(row, 'target_audience', None),
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
            e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        {where_clause}
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at
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
                    'target_audience': getattr(row, 'target_audience', None),
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at,
                    'score': int(row.score)
                })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error listing entries: {e}")
            return []
    
    def update_entry(self, entry_id: str, title: Optional[str] = None, 
                    description: Optional[str] = None, ai_summary: Optional[str] = None,
                    target_audience: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        """
        Update an existing entry (admin only).
        
        Args:
            entry_id: Entry ID to update
            title: New title (optional)
            description: New description (optional) 
            ai_summary: New AI summary (optional)
            target_audience: New target audience (optional)
            tags: New tags list (optional)
            
        Returns:
            True if successful
        """
        # Build update clauses dynamically
        update_clauses = []
        query_params = [bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id)]
        
        if title is not None:
            update_clauses.append("title = @title")
            query_params.append(bigquery.ScalarQueryParameter("title", "STRING", title))
            
        if description is not None:
            update_clauses.append("description = @description")
            query_params.append(bigquery.ScalarQueryParameter("description", "STRING", description))
            
        if ai_summary is not None:
            update_clauses.append("ai_summary = @ai_summary")
            query_params.append(bigquery.ScalarQueryParameter("ai_summary", "STRING", ai_summary))
            
        if target_audience is not None:
            update_clauses.append("target_audience = @target_audience")
            query_params.append(bigquery.ScalarQueryParameter("target_audience", "STRING", target_audience))
            
        if tags is not None:
            update_clauses.append("tags = @tags")
            query_params.append(bigquery.ArrayQueryParameter("tags", "STRING", tags))
        
        if not update_clauses:
            logger.warning("No fields to update")
            return False
            
        query = f"""
        UPDATE `{self.table_ids['entries']}`
        SET {', '.join(update_clauses)}
        WHERE id = @entry_id
        """
        
        try:
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            logger.info(f"Updated entry {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry: {e}")
            return False
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entry by ID.
        
        Args:
            entry_id: The entry ID
            
        Returns:
            Entry dict or None
        """
        query = f"""
        SELECT id, title, url, description, ai_summary, target_audience, tags, author_id, created_at
        FROM `{self.table_ids['entries']}`
        WHERE id = @entry_id
        LIMIT 1
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
                    'target_audience': getattr(row, 'target_audience', None),  # Handle missing column gracefully
                    'tags': list(row.tags) if row.tags else [],
                    'author_id': row.author_id,
                    'created_at': row.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting entry by ID: {e}")
            return None
    
    def list_all_entries_for_admin(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all entries for admin management (includes more details).
        
        Args:
            limit: Maximum results to return
            
        Returns:
            List of entry dicts with scores and additional details
        """
        query = f"""
        SELECT 
            e.id, e.title, e.url, e.description, e.ai_summary, 
            e.target_audience, e.tags, e.author_id, e.created_at,
            e.security_status, e.security_display,
            COALESCE(SUM(v.vote), 0) AS score,
            COUNT(CASE WHEN v.vote = 1 THEN 1 END) AS upvotes,
            COUNT(CASE WHEN v.vote = -1 THEN 1 END) AS downvotes
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at, e.security_status, e.security_display
        ORDER BY e.created_at DESC
        LIMIT @limit
        """
        
        try:
            logger.info(f"Executing admin list query with limit: {limit}")
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            entries = []
            row_count = 0
            for row in results:
                row_count += 1
                try:
                    # Safely handle each field
                    entry_data = {
                        'id': getattr(row, 'id', None),
                        'title': getattr(row, 'title', None) or 'No title',
                        'url': getattr(row, 'url', None),
                        'description': getattr(row, 'description', None),
                        'ai_summary': getattr(row, 'ai_summary', None),
                        'target_audience': getattr(row, 'target_audience', None),
                        'tags': list(getattr(row, 'tags', [])) if getattr(row, 'tags', None) else [],
                        'author_id': getattr(row, 'author_id', None),
                        'created_at': getattr(row, 'created_at', None),
                        'security_status': getattr(row, 'security_status', None),
                        'security_display': getattr(row, 'security_display', None),
                        'score': int(getattr(row, 'score', 0)),
                        'upvotes': int(getattr(row, 'upvotes', 0)),
                        'downvotes': int(getattr(row, 'downvotes', 0))
                    }
                    entries.append(entry_data)
                    logger.debug(f"Processed entry {row_count}: {entry_data['id']} - {entry_data['title']}")
                except Exception as row_error:
                    logger.error(f"Error processing row {row_count}: {row_error}")
                    # Continue processing other rows
                    continue
            
            logger.info(f"Successfully retrieved {len(entries)} entries for admin")
            return entries
            
        except Exception as e:
            logger.error(f"Error listing entries for admin: {e}")
            logger.error(f"Query was: {query}")
            return []
    
    def regenerate_ai_content(self, entry_id: str) -> bool:
        """
        Regenerate AI content for an entry.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            True if successful
        """
        from services.ai_service import ai_service
        
        # Get the entry
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            logger.error(f"Entry {entry_id} not found")
            return False
        
        try:
            # Generate new AI content
            content = entry.get('description', '') or entry.get('url', '')
            ai_summary, target_audience, tags = ai_service.generate_summary_and_tags_sync(
                entry['title'], content
            )
            
            # Update the entry with new AI content
            return self.update_entry(
                entry_id=entry_id,
                ai_summary=ai_summary,
                target_audience=target_audience,
                tags=tags if tags else entry['tags']  # Keep existing tags if AI fails
            )
            
        except Exception as e:
            logger.error(f"Error regenerating AI content: {e}")
            return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry and all its associated votes (admin only).
        
        Args:
            entry_id: Entry ID to delete
            
        Returns:
            True if successful
        """
        try:
            # First delete all votes for this entry
            delete_votes_query = f"""
            DELETE FROM `{self.table_ids['votes']}`
            WHERE entry_id = @entry_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id)
                ]
            )
            self.client.query(delete_votes_query, job_config=job_config).result()
            
            # Then delete the entry itself
            delete_entry_query = f"""
            DELETE FROM `{self.table_ids['entries']}`
            WHERE id = @entry_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id)
                ]
            )
            result = self.client.query(delete_entry_query, job_config=job_config).result()
            
            # Check if any rows were affected
            if result.num_dml_affected_rows > 0:
                logger.info(f"Deleted entry {entry_id} and associated votes")
                return True
            else:
                logger.warning(f"No entry found with ID {entry_id}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            if "streaming buffer" in error_msg:
                logger.warning(f"Cannot delete entry {entry_id}: BigQuery streaming buffer limitation. Try again in 90 minutes.")
                # Could add retry logic here if needed
                return False
            else:
                logger.error(f"Error deleting entry: {e}")
                return False
    
    def get_top_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top entries by score (highest scoring first).
        
        Args:
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            List of entry dicts with scores, ordered by score descending
        """
        query = f"""
        SELECT 
            e.id, e.title, e.url, e.description, e.ai_summary, 
            e.target_audience, e.tags, e.author_id, e.created_at,
            COALESCE(SUM(v.vote), 0) AS score,
            COUNT(CASE WHEN v.vote = 1 THEN 1 END) AS upvotes,
            COUNT(CASE WHEN v.vote = -1 THEN 1 END) AS downvotes
        FROM `{self.table_ids['entries']}` e
        LEFT JOIN `{self.table_ids['votes']}` v ON e.id = v.entry_id
        GROUP BY e.id, e.title, e.url, e.description, e.ai_summary, e.target_audience, e.tags, e.author_id, e.created_at
        ORDER BY score DESC, e.created_at DESC
        LIMIT @limit
        """
        
        try:
            logger.info(f"Getting top {limit} entries by score")
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            entries = []
            for row in results:
                try:
                    entry_data = {
                        'id': getattr(row, 'id', None),
                        'title': getattr(row, 'title', None) or 'No title',
                        'url': getattr(row, 'url', None),
                        'description': getattr(row, 'description', None),
                        'ai_summary': getattr(row, 'ai_summary', None),
                        'target_audience': getattr(row, 'target_audience', None),
                        'tags': list(getattr(row, 'tags', [])) if getattr(row, 'tags', None) else [],
                        'author_id': getattr(row, 'author_id', None),
                        'created_at': getattr(row, 'created_at', None),
                        'score': int(getattr(row, 'score', 0)),
                        'upvotes': int(getattr(row, 'upvotes', 0)),
                        'downvotes': int(getattr(row, 'downvotes', 0))
                    }
                    entries.append(entry_data)
                except Exception as row_error:
                    logger.error(f"Error processing top entry row: {row_error}")
                    continue
            
            logger.info(f"Successfully retrieved {len(entries)} top entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error getting top entries: {e}")
            return []
    
    def update_entry_security(self, entry_id: str, security_status: str, security_display: str) -> bool:
        """
        Update the security status of an entry.
        
        Args:
            entry_id: Entry ID
            security_status: Security status ('approved', 'restricted', 'prohibited', 'review')
            security_display: User-friendly display text
            
        Returns:
            True if successful
        """
        query = f"""
        UPDATE `{self.table_ids['entries']}`
        SET security_status = @security_status,
            security_display = @security_display
        WHERE id = @entry_id
        """
        
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id),
                    bigquery.ScalarQueryParameter("security_status", "STRING", security_status),
                    bigquery.ScalarQueryParameter("security_display", "STRING", security_display)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            result = query_job.result()
            
            if result.num_dml_affected_rows > 0:
                logger.info(f"Updated security status for entry {entry_id}: {security_status}")
                return True
            else:
                logger.warning(f"No entry found with ID {entry_id} for security update")
                return False
                
        except Exception as e:
            # If security fields don't exist, log warning but don't fail
            if "security_status" in str(e) or "security_display" in str(e):
                logger.warning(f"Security fields not available in database schema: {e}")
                return False
            logger.error(f"Error updating entry security: {e}")
            return False
    
    def get_all_entries_for_security_refresh(self) -> List[Dict[str, Any]]:
        """
        Get all entries for security status refresh.
        
        Returns:
            List of entries with basic info needed for security evaluation
        """
        query = f"""
        SELECT id, title, url, description, ai_summary, tags
        FROM `{self.table_ids['entries']}`
        ORDER BY created_at DESC
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            entries = []
            for row in results:
                entries.append({
                    'id': row.id,
                    'title': row.title,
                    'url': getattr(row, 'url', None),
                    'description': getattr(row, 'description', None),
                    'ai_summary': getattr(row, 'ai_summary', None),
                    'tags': list(row.tags) if row.tags else []
                })
            
            logger.info(f"Retrieved {len(entries)} entries for security refresh")
            return entries
            
        except Exception as e:
            logger.error(f"Error getting entries for security refresh: {e}")
            return []
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all entries, sorted by frequency.
        
        Returns:
            List of tags sorted by most frequently used
        """
        query = f"""
        SELECT tag, COUNT(*) as frequency
        FROM `{self.table_ids['entries']}`,
        UNNEST(tags) as tag
        WHERE tag IS NOT NULL AND tag != ''
        GROUP BY tag
        ORDER BY frequency DESC, tag ASC
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            tags = []
            for row in results:
                tags.append(row.tag)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return []

# Global BigQuery service instance
bigquery_service = BigQueryService()
