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
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
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
                    max_output_tokens=500,
                )
            )
            
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            logger.error(f"Error generating summary and tags: {e}")
            return None, []
    
    def _build_prompt(self, title: str, content: str) -> str:
        """Build the prompt for AI generation."""
        return f\"\"\"Analyze this AI coding tool and provide:\n1. A concise summary (max 100 words) that explains what the tool does and its key benefits\n2. Up to 5 relevant tags for categorization (use lowercase, hyphenated format)\n\nTool: {title}\nContent: {content[:2000]}  # Limit content to avoid token limits\n\nFormat your response as:\nSUMMARY: [your summary here]\nTAGS: [tag1, tag2, tag3, ...]\n\nFocus on:\n- What the tool does\n- Key features or benefits\n- Target use cases\n- Technology stack (if mentioned)\n\nFor tags, use categories like:\n- ai-assistant, code-generation, debugging, testing, cli, web-app\n- python, javascript, typescript, etc. (for languages)\n- vscode, intellij, terminal (for platforms)\n- pair-programming, code-review, documentation (for use cases)\"\"\"\n    \n    def _parse_ai_response(self, response_text: str) -> Tuple[Optional[str], List[str]]:\n        \"\"\"Parse the AI response to extract summary and tags.\"\"\"\n        if not response_text:\n            return None, []\n        \n        lines = response_text.strip().split('\\n')\n        summary = None\n        tags = []\n        \n        for line in lines:\n            line = line.strip()\n            if line.upper().startswith(\"SUMMARY:\"):\n                summary = line[8:].strip()  # Remove \"SUMMARY:\" prefix\n            elif line.upper().startswith(\"TAGS:\"):\n                tags_str = line[5:].strip()  # Remove \"TAGS:\" prefix\n                # Parse tags, handling both comma and bracket formats\n                if tags_str.startswith('[') and tags_str.endswith(']'):\n                    tags_str = tags_str[1:-1]\n                \n                tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]\n                tags = [tag for tag in tags if len(tag) > 0 and len(tag) <= 30]  # Filter valid tags\n        \n        # Fallback: if no explicit SUMMARY/TAGS format, try to extract from plain text\n        if not summary and response_text:\n            # Take first 100 words as summary if no explicit format\n            words = response_text.split()\n            if words:\n                summary = ' '.join(words[:100])\n        \n        return summary, tags[:5]  # Limit to 5 tags max\n    \n    def generate_summary_and_tags_sync(self, title: str, content: str) -> Tuple[Optional[str], List[str]]:\n        \"\"\"Synchronous wrapper for generate_summary_and_tags.\"\"\"\n        return asyncio.run(self.generate_summary_and_tags(title, content))\n\n# Global AI service instance\nai_service = AIService()
