"""
Google Gen AI service for generating summaries and tags.
"""

import asyncio
import logging
from typing import Tuple, List, Optional
from google import genai
from google.genai import types

from config.settings import settings
from config.tags import validate_tags, build_ai_prompt_tags_section

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
    
    async def generate_summary_and_tags(self, title: str, content: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Generate a summary, target audience, and tags for an AI tool.
        
        Args:
            title: The tool title
            content: The tool description/content
            
        Returns:
            Tuple of (summary, target_audience, tags_list)
        """
        if not self.client:
            logger.error("AI client not initialized")
            return None, None, []
        
        try:
            prompt = self._build_prompt(title, content)
            logger.debug(f"Generated prompt: {prompt[:200]}...")
            
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4000,
                )
            )
            
            logger.debug(f"AI response received: {response}")
            logger.debug(f"AI response text: {response.text}")
            
            # Check for token limit issues
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                    finish_reason = str(candidate.finish_reason)
                    if 'MAX_TOKENS' in finish_reason:
                        logger.warning("AI response hit token limit, trying with shorter prompt")
                        # Retry with a much shorter prompt
                        short_prompt = f"Summarize this AI tool in 50 words or less: {title}. {content[:500]}"
                        response = await self.client.aio.models.generate_content(
                            model=settings.GEMINI_MODEL,
                            contents=short_prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.3,
                                max_output_tokens=1000,
                            )
                        )
                        logger.debug(f"Retry response text: {response.text}")
            
            result = self._parse_ai_response(response.text or "")
            logger.debug(f"Parsed result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating summary and tags: {e}")
            return None, None, []
    
    def _build_prompt(self, title: str, content: str) -> str:
        """Build the prompt for AI generation."""
        tags_section = build_ai_prompt_tags_section()
        
        return f"""Analyze this AI tool:

Tool: {title}
Content: {content[:1500]}

{tags_section}

Provide:
1. SUMMARY: Concise description (40-60 words)
2. AUDIENCE: Target users (brief description)
3. TAGS: Select 2-4 most relevant tags from the list above

Format exactly as:
SUMMARY: [description]
AUDIENCE: [target users]
TAGS: [tag1, tag2, tag3]"""
    
    def _parse_ai_response(self, response_text: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """Parse the AI response to extract summary, audience, and tags."""
        if not response_text:
            return None, None, []
        
        lines = response_text.strip().split('\n')
        summary = None
        audience = None
        tags = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                summary = line[8:].strip()  # Remove "SUMMARY:" prefix
            elif line.upper().startswith("AUDIENCE:"):
                audience = line[9:].strip()  # Remove "AUDIENCE:" prefix
            elif line.upper().startswith("TAGS:"):
                tags_str = line[5:].strip()  # Remove "TAGS:" prefix
                # Parse tags, handling both comma and bracket formats
                if tags_str.startswith('[') and tags_str.endswith(']'):
                    tags_str = tags_str[1:-1]
                
                tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
                tags = [tag for tag in tags if len(tag) > 0 and len(tag) <= 30]  # Filter valid tags
        
        # Fallback: if no explicit SUMMARY/AUDIENCE/TAGS format, try to extract from plain text
        if not summary and response_text:
            # Take first 100 words as summary if no explicit format
            words = response_text.split()
            if words:
                summary = ' '.join(words[:100])
        
        # Validate and clean tags
        validated_tags = validate_tags(tags)
        
        return summary, audience, validated_tags
    
    def generate_summary_and_tags_sync(self, title: str, content: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """Synchronous wrapper for generate_summary_and_tags."""
        import concurrent.futures
        import threading
        
        try:
            # Check if there's an existing event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to run in a separate thread
            logger.info("Running AI operation in thread pool to avoid blocking event loop")
            
            # Create a thread pool executor to run the async function
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_in_new_loop, title, content)
                return future.result(timeout=30)  # 30 second timeout
                
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(self.generate_summary_and_tags(title, content))
        except concurrent.futures.TimeoutError:
            logger.error("AI service timed out")
            return None, None, []
        except Exception as e:
            logger.error(f"Error in AI service sync wrapper: {e}")
            return None, None, []
    
    def _run_in_new_loop(self, title: str, content: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """Run the async method in a new event loop in a separate thread."""
        return asyncio.run(self.generate_summary_and_tags(title, content))

# Global AI service instance
ai_service = AIService()
