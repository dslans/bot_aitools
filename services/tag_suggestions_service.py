"""
Tag suggestions service for community-driven tag voting system.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from google.cloud import bigquery

from config.settings import settings
from config.tags import CORE_TAGS, validate_tags

logger = logging.getLogger(__name__)

class TagSuggestionsService:
    """Service for managing community tag suggestions and voting."""
    
    def __init__(self):
        """Initialize the service."""
        self.client = None
        self.table_ids = settings.get_bigquery_table_ids()
        # Add new table IDs for tag system
        self.table_ids.update({
            'tag_suggestions': f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.tag_suggestions",
            'tag_votes': f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.tag_votes",
            'approved_community_tags': f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.approved_community_tags"
        })
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the BigQuery client."""
        try:
            self.client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            logger.info("Tag suggestions service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tag suggestions service: {e}")
            raise
    
    def suggest_tag(self, entry_id: str, suggested_tag: str, suggested_by: str) -> Optional[str]:
        """
        Create a new tag suggestion for an entry.
        
        Args:
            entry_id: ID of the entry to tag
            suggested_tag: The proposed tag
            suggested_by: User ID who made the suggestion
            
        Returns:
            Suggestion ID if successful, None if failed
        """
        # Validate and clean the suggested tag
        cleaned_tags = validate_tags([suggested_tag])
        if not cleaned_tags:
            logger.warning(f"Invalid tag suggested: {suggested_tag}")
            return None
            
        cleaned_tag = cleaned_tags[0]
        
        # Don't allow suggesting core tags
        if cleaned_tag in CORE_TAGS:
            logger.info(f"Core tag {cleaned_tag} suggested - not adding as suggestion")
            return None
        
        # Check if this tag is already suggested for this entry
        existing = self.get_suggestion_for_entry_and_tag(entry_id, cleaned_tag)
        if existing:
            logger.info(f"Tag {cleaned_tag} already suggested for entry {entry_id}")
            return existing['id']
        
        suggestion_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            # Insert the suggestion
            query = f"""
            INSERT INTO `{self.table_ids['tag_suggestions']}`
            (id, entry_id, suggested_tag, suggested_by, status, upvotes, downvotes, net_votes, created_at, updated_at)
            VALUES (@id, @entry_id, @suggested_tag, @suggested_by, 'pending', 0, 0, 0, @created_at, @updated_at)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", suggestion_id),
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id),
                    bigquery.ScalarQueryParameter("suggested_tag", "STRING", cleaned_tag),
                    bigquery.ScalarQueryParameter("suggested_by", "STRING", suggested_by),
                    bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", now),
                    bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            logger.info(f"Created tag suggestion {suggestion_id}: {cleaned_tag} for entry {entry_id}")
            return suggestion_id
            
        except Exception as e:
            logger.error(f"Error creating tag suggestion: {e}")
            return None
    
    def vote_on_suggestion(self, suggestion_id: str, user_id: str, vote: int) -> bool:
        """
        Vote on a tag suggestion.
        
        Args:
            suggestion_id: ID of the suggestion
            user_id: ID of the user voting
            vote: 1 for upvote, -1 for downvote
            
        Returns:
            True if successful
        """
        if vote not in [1, -1]:
            logger.warning(f"Invalid vote value: {vote}")
            return False
        
        try:
            # First, remove any existing vote by this user for this suggestion
            delete_query = f"""
            DELETE FROM `{self.table_ids['tag_votes']}`
            WHERE suggestion_id = @suggestion_id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("suggestion_id", "STRING", suggestion_id),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                ]
            )
            
            self.client.query(delete_query, job_config=job_config).result()
            
            # Insert the new vote
            insert_query = f"""
            INSERT INTO `{self.table_ids['tag_votes']}`
            (suggestion_id, user_id, vote, created_at)
            VALUES (@suggestion_id, @user_id, @vote, @created_at)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("suggestion_id", "STRING", suggestion_id),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("vote", "INT64", vote),
                    bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", datetime.utcnow()),
                ]
            )
            
            self.client.query(insert_query, job_config=job_config).result()
            
            # Update the suggestion vote counts
            self._update_suggestion_vote_counts(suggestion_id)
            
            # Check for auto-promotion
            self._check_auto_promotion(suggestion_id)
            
            logger.info(f"Recorded vote {vote} by user {user_id} on suggestion {suggestion_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error voting on suggestion: {e}")
            return False
    
    def _update_suggestion_vote_counts(self, suggestion_id: str):
        """Update vote counts for a suggestion."""
        try:
            update_query = f"""
            UPDATE `{self.table_ids['tag_suggestions']}` 
            SET 
                upvotes = (SELECT COUNT(*) FROM `{self.table_ids['tag_votes']}` WHERE suggestion_id = @suggestion_id AND vote = 1),
                downvotes = (SELECT COUNT(*) FROM `{self.table_ids['tag_votes']}` WHERE suggestion_id = @suggestion_id AND vote = -1),
                net_votes = (SELECT COUNT(*) FROM `{self.table_ids['tag_votes']}` WHERE suggestion_id = @suggestion_id AND vote = 1) - 
                           (SELECT COUNT(*) FROM `{self.table_ids['tag_votes']}` WHERE suggestion_id = @suggestion_id AND vote = -1),
                updated_at = @updated_at
            WHERE id = @suggestion_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("suggestion_id", "STRING", suggestion_id),
                    bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", datetime.utcnow()),
                ]
            )
            
            self.client.query(update_query, job_config=job_config).result()
            
        except Exception as e:
            logger.error(f"Error updating vote counts: {e}")
    
    def _check_auto_promotion(self, suggestion_id: str):
        """Check if a suggestion should be auto-promoted to approved status."""
        try:
            suggestion = self.get_suggestion_by_id(suggestion_id)
            if not suggestion:
                return
            
            # Auto-promote if net votes >= 3 and status is still pending
            if suggestion['net_votes'] >= 3 and suggestion['status'] == 'pending':
                self.promote_tag_to_approved(suggestion['suggested_tag'], 'auto')
                
                # Update suggestion status to approved
                update_query = f"""
                UPDATE `{self.table_ids['tag_suggestions']}`
                SET status = 'approved', updated_at = @updated_at
                WHERE id = @suggestion_id
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("suggestion_id", "STRING", suggestion_id),
                        bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", datetime.utcnow()),
                    ]
                )
                
                self.client.query(update_query, job_config=job_config).result()
                logger.info(f"Auto-promoted tag: {suggestion['suggested_tag']}")
                
        except Exception as e:
            logger.error(f"Error checking auto-promotion: {e}")
    
    def get_suggestion_by_id(self, suggestion_id: str) -> Optional[Dict[str, Any]]:
        """Get a tag suggestion by ID."""
        try:
            query = f"""
            SELECT id, entry_id, suggested_tag, suggested_by, status, upvotes, downvotes, net_votes, created_at, updated_at
            FROM `{self.table_ids['tag_suggestions']}`
            WHERE id = @suggestion_id
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("suggestion_id", "STRING", suggestion_id)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return {
                    'id': row.id,
                    'entry_id': row.entry_id,
                    'suggested_tag': row.suggested_tag,
                    'suggested_by': row.suggested_by,
                    'status': row.status,
                    'upvotes': int(row.upvotes),
                    'downvotes': int(row.downvotes),
                    'net_votes': int(row.net_votes),
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting suggestion by ID: {e}")
            return None
    
    def get_suggestion_for_entry_and_tag(self, entry_id: str, tag: str) -> Optional[Dict[str, Any]]:
        """Check if a tag is already suggested for an entry."""
        try:
            query = f"""
            SELECT id, entry_id, suggested_tag, suggested_by, status, upvotes, downvotes, net_votes, created_at, updated_at
            FROM `{self.table_ids['tag_suggestions']}`
            WHERE entry_id = @entry_id AND suggested_tag = @tag
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entry_id", "STRING", entry_id),
                    bigquery.ScalarQueryParameter("tag", "STRING", tag)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return {
                    'id': row.id,
                    'entry_id': row.entry_id,
                    'suggested_tag': row.suggested_tag,
                    'suggested_by': row.suggested_by,
                    'status': row.status,
                    'upvotes': int(row.upvotes),
                    'downvotes': int(row.downvotes),
                    'net_votes': int(row.net_votes),
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing suggestion: {e}")
            return None
    
    def get_pending_suggestions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get pending tag suggestions for admin review."""
        try:
            query = f"""
            SELECT ts.id, ts.entry_id, ts.suggested_tag, ts.suggested_by, ts.status, 
                   ts.upvotes, ts.downvotes, ts.net_votes, ts.created_at, ts.updated_at,
                   e.title as entry_title
            FROM `{self.table_ids['tag_suggestions']}` ts
            JOIN `{self.table_ids['entries']}` e ON ts.entry_id = e.id
            WHERE ts.status = 'pending'
            ORDER BY ts.net_votes DESC, ts.created_at DESC
            LIMIT @limit
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            suggestions = []
            for row in results:
                suggestions.append({
                    'id': row.id,
                    'entry_id': row.entry_id,
                    'suggested_tag': row.suggested_tag,
                    'suggested_by': row.suggested_by,
                    'status': row.status,
                    'upvotes': int(row.upvotes),
                    'downvotes': int(row.downvotes),
                    'net_votes': int(row.net_votes),
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'entry_title': row.entry_title
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting pending suggestions: {e}")
            return []
    
    def promote_tag_to_approved(self, tag: str, approved_by: str) -> bool:
        """Promote a community tag to approved status."""
        try:
            # Check if already approved
            existing = self.get_approved_community_tag(tag)
            if existing:
                return True
            
            query = f"""
            INSERT INTO `{self.table_ids['approved_community_tags']}`
            (tag, description, approved_by, usage_count, created_at)
            VALUES (@tag, @description, @approved_by, 0, @created_at)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("tag", "STRING", tag),
                    bigquery.ScalarQueryParameter("description", "STRING", f"Community-approved tag"),
                    bigquery.ScalarQueryParameter("approved_by", "STRING", approved_by),
                    bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", datetime.utcnow()),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            logger.info(f"Promoted community tag to approved: {tag}")
            return True
            
        except Exception as e:
            logger.error(f"Error promoting tag: {e}")
            return False
    
    def get_approved_community_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """Check if a tag is in approved community tags."""
        try:
            query = f"""
            SELECT tag, description, approved_by, usage_count, created_at
            FROM `{self.table_ids['approved_community_tags']}`
            WHERE tag = @tag
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("tag", "STRING", tag)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return {
                    'tag': row.tag,
                    'description': row.description,
                    'approved_by': row.approved_by,
                    'usage_count': int(row.usage_count),
                    'created_at': row.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting approved community tag: {e}")
            return None
    
    def get_all_approved_community_tags(self) -> List[str]:
        """Get list of all approved community tags."""
        try:
            query = f"""
            SELECT tag
            FROM `{self.table_ids['approved_community_tags']}`
            ORDER BY usage_count DESC, tag ASC
            """
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            return [row.tag for row in results]
            
        except Exception as e:
            logger.error(f"Error getting approved community tags: {e}")
            return []

# Global service instance
tag_suggestions_service = TagSuggestionsService()
