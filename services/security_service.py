"""
Security service for checking tool approval status using AI analysis.
"""

import logging
import requests
import asyncio
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta

from google import genai
from google.genai import types
from config.settings import settings

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for evaluating tool security compliance using AI."""
    
    def __init__(self):
        """Initialize the security service."""
        self.client = None
        self.guidelines_cache = None
        self.guidelines_cache_time = None
        self.cache_duration = timedelta(hours=24)  # Cache guidelines for 24 hours
        self._initialize_ai_client()
    
    def _initialize_ai_client(self):
        """Initialize the Gemini AI client."""
        try:
            self.client = genai.Client(
                vertexai=True,
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.VERTEX_LOCATION
            )
            logger.info("Security AI service initialized successfully")
        except Exception as e:
            logger.warning(f"Security AI service initialization failed: {e}")
            logger.warning("Security evaluations will be unavailable")
            self.client = None
    
    def fetch_guidelines(self, guidelines_url: str) -> Optional[str]:
        """
        Fetch security guidelines from URL.
        
        Args:
            guidelines_url: URL to fetch guidelines from
            
        Returns:
            Guidelines text or None if unavailable
        """
        # Check cache first
        if (self.guidelines_cache and 
            self.guidelines_cache_time and 
            datetime.utcnow() - self.guidelines_cache_time < self.cache_duration):
            logger.debug("Using cached security guidelines")
            return self.guidelines_cache
        
        try:
            logger.info(f"Fetching security guidelines from {guidelines_url}")
            response = requests.get(guidelines_url, timeout=30)
            response.raise_for_status()
            
            guidelines_text = response.text
            
            # Cache the guidelines
            self.guidelines_cache = guidelines_text
            self.guidelines_cache_time = datetime.utcnow()
            
            logger.info("Successfully fetched and cached security guidelines")
            return guidelines_text
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch security guidelines: {e}")
            # Return cached version if available
            if self.guidelines_cache:
                logger.info("Using previously cached guidelines")
                return self.guidelines_cache
            return None
        except Exception as e:
            logger.error(f"Error processing security guidelines: {e}")
            return None
    
    async def evaluate_tool_security(self, 
                                    title: str, 
                                    url: Optional[str], 
                                    description: Optional[str],
                                    ai_summary: Optional[str],
                                    tags: List[str],
                                    guidelines_url: str) -> Tuple[str, str]:
        """
        Evaluate a tool's security status using AI analysis.
        
        Args:
            title: Tool name
            url: Tool URL
            description: Tool description
            ai_summary: AI-generated summary
            tags: Tool tags
            guidelines_url: URL of security guidelines
            
        Returns:
            Tuple of (status, display_text) where:
            - status: 'approved', 'restricted', 'prohibited', or 'review'
            - display_text: Brief, user-friendly explanation (max 100 chars)
        """
        if not self.client:
            logger.warning("AI client not available for security evaluation")
            return "review", "⏳ Pending security review"
        
        # Fetch guidelines
        guidelines = self.fetch_guidelines(guidelines_url)
        if not guidelines:
            logger.warning("No security guidelines available")
            return "review", "⏳ Security guidelines unavailable"
        
        try:
            # Build the prompt for AI evaluation
            prompt = self._build_security_prompt(
                title, url, description, ai_summary, tags, guidelines
            )
            
            # Call Gemini AI
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for consistent evaluation
                    max_output_tokens=500,
                )
            )
            
            # Parse the AI response
            return self._parse_security_response(response.text or "")
            
        except Exception as e:
            logger.error(f"Error evaluating tool security: {e}")
            return "review", "⏳ Security check failed - needs manual review"
    
    def _build_security_prompt(self, 
                              title: str, 
                              url: Optional[str], 
                              description: Optional[str],
                              ai_summary: Optional[str],
                              tags: List[str],
                              guidelines: str) -> str:
        """Build the prompt for security evaluation."""
        
        # Truncate guidelines if too long (keep most relevant parts)
        max_guidelines_length = 3000
        if len(guidelines) > max_guidelines_length:
            guidelines = guidelines[:max_guidelines_length] + "...[truncated]"
        
        prompt = f"""Evaluate this AI tool against the company security guidelines:

TOOL INFORMATION:
Title: {title}
URL: {url or 'No URL provided'}
Description: {description or 'No description'}
AI Summary: {ai_summary or 'No AI summary'}
Tags: {', '.join(tags) if tags else 'No tags'}

SECURITY GUIDELINES:
{guidelines}

TASK:
Based on the security guidelines, evaluate if this tool should be:
1. APPROVED - Meets all security requirements and is safe to use
2. RESTRICTED - Can be used with limitations or for specific purposes only
3. PROHIBITED - Violates security policies and should not be used
4. REVIEW - Requires security team review (unclear or needs more info)

Provide your evaluation in this exact format:
STATUS: [APPROVED/RESTRICTED/PROHIBITED/REVIEW]
DISPLAY: [A brief, user-friendly message (max 80 characters) explaining the status]

Examples of good DISPLAY messages:
- "✅ Approved for all users"
- "⚠️ Restricted to development use only"
- "🚫 Prohibited - uses unapproved data storage"
- "🔍 Requires security team review"
- "✅ Approved - trusted Microsoft product"
- "⚠️ Restricted - requires manager approval"

Be specific but concise in the DISPLAY message. Focus on what users need to know."""
        
        return prompt
    
    def _parse_security_response(self, response_text: str) -> Tuple[str, str]:
        """Parse the AI response to extract status and display text."""
        if not response_text:
            return "review", "⏳ No security evaluation available"
        
        lines = response_text.strip().split('\n')
        status = "review"
        display_text = "⏳ Pending security review"
        
        for line in lines:
            line = line.strip()
            
            # Parse STATUS line
            if line.upper().startswith("STATUS:"):
                status_value = line[7:].strip().upper()
                if status_value in ["APPROVED", "RESTRICTED", "PROHIBITED", "REVIEW"]:
                    status = status_value.lower()
            
            # Parse DISPLAY line
            elif line.upper().startswith("DISPLAY:"):
                display_text = line[8:].strip()
                # Ensure display text is not too long
                if len(display_text) > 80:
                    display_text = display_text[:77] + "..."
                # Add emoji if not present
                if not any(emoji in display_text for emoji in ['✅', '⚠️', '🚫', '🔍', '⏳']):
                    emoji_map = {
                        'approved': '✅',
                        'restricted': '⚠️',
                        'prohibited': '🚫',
                        'review': '🔍'
                    }
                    display_text = f"{emoji_map.get(status, '🔍')} {display_text}"
        
        return status, display_text
    
    def evaluate_tool_security_sync(self, 
                                   title: str, 
                                   url: Optional[str], 
                                   description: Optional[str],
                                   ai_summary: Optional[str],
                                   tags: List[str],
                                   guidelines_url: str) -> Tuple[str, str]:
        """Synchronous wrapper for evaluate_tool_security."""
        return asyncio.run(self.evaluate_tool_security(
            title, url, description, ai_summary, tags, guidelines_url
        ))
    
    def format_security_indicator(self, status: str) -> str:
        """
        Format a short security indicator for inline display.
        
        Args:
            status: Security status
            
        Returns:
            Short indicator emoji
        """
        indicators = {
            'approved': '✅',
            'restricted': '⚠️',
            'prohibited': '🚫',
            'review': '🔍',
            'unknown': ''
        }
        return indicators.get(status, '')
    
    def should_show_in_listing(self, status: str) -> bool:
        """
        Determine if a tool should be shown in general listings.
        
        Args:
            status: Security status
            
        Returns:
            True if tool should be shown, False if it should be hidden
        """
        # Hide prohibited tools from general listings
        return status != 'prohibited'


# Global security service instance
security_service = SecurityService()
