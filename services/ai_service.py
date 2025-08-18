"""
Google Gen AI service for generating summaries and tags.
"""

import asyncio
import logging
from typing import Tuple, List, Optional
from google import genai
from google.genai import types

from config.settings import settings

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered content generation using Google Gemini."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client."""
        try:
            self.client = genai.Client(
                vertexai=True,
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.VERTEX_LOCATION
            )
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.warning(f"AI service initialization failed: {e}")
            logger.warning("Bot will continue without AI features")
            self.client = None
    
    async def generate_summary_and_tags(self, title: str, content: str) -> Tuple[Optional[str], List[str]]:
        """
        Generate a summary and tags for an AI tool.
        
        Args:
            title: The tool title
            content: The tool description/content
            
        Returns:
            Tuple of (summary, tags_list)
        """
        if not self.client:
            logger.error("AI client not initialized")
            return None, []
        
        try:
            prompt = self._build_prompt(title, content)
            
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000,  # Increased for gemini-2.5 which uses thought tokens
                )
            )
            
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            logger.error(f"Error generating summary and tags: {e}")
            return None, []
    
    def _build_prompt(self, title: str, content: str) -> str:
        """Build the prompt for AI generation."""
        return f"""Analyze this AI coding tool and provide:
1. A concise summary (max 100 words) that explains what the tool does and its key benefits
2. Who this tool would be best suited for
3. Up to 5 relevant tags for categorization (use lowercase, hyphenated format)

Tool: {title}
Content: {content[:2000]}

Format your response as:
SUMMARY: [your summary here]
TAGS: [tag1, tag2, tag3, ...]

Focus on:
- What the tool does
- Key features or benefits
- Target use cases
- Technology stack (if mentioned)

For tags, use categories like:
- ai-assistant, code-generation, debugging, testing, cli, web-app
- python, javascript, typescript, etc. (for languages)
- vscode, intellij, terminal (for platforms)
- pair-programming, code-review, documentation (for use cases)"""
    
    def _parse_ai_response(self, response_text: str) -> Tuple[Optional[str], List[str]]:
        """Parse the AI response to extract summary and tags."""
        if not response_text:
            return None, []
        
        lines = response_text.strip().split('\n')
        summary = None
        tags = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                summary = line[8:].strip()  # Remove "SUMMARY:" prefix
            elif line.upper().startswith("TAGS:"):
                tags_str = line[5:].strip()  # Remove "TAGS:" prefix
                # Parse tags, handling both comma and bracket formats
                if tags_str.startswith('[') and tags_str.endswith(']'):
                    tags_str = tags_str[1:-1]
                
                tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
                tags = [tag for tag in tags if len(tag) > 0 and len(tag) <= 30]  # Filter valid tags
        
        # Fallback: if no explicit SUMMARY/TAGS format, try to extract from plain text
        if not summary and response_text:
            # Take first 100 words as summary if no explicit format
            words = response_text.split()
            if words:
                summary = ' '.join(words[:100])
        
        return summary, tags[:5]  # Limit to 5 tags max
    
    def generate_summary_and_tags_sync(self, title: str, content: str) -> Tuple[Optional[str], List[str]]:
        """Synchronous wrapper for generate_summary_and_tags."""
        return asyncio.run(self.generate_summary_and_tags(title, content))

# Global AI service instance
ai_service = AIService()
