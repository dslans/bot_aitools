"""
Web scraping service for extracting content from URLs.
"""

import requests
import logging
import validators
from bs4 import BeautifulSoup
from typing import Tuple, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class ScraperService:
    """Service for web scraping and content extraction."""
    
    def __init__(self):
        """Initialize the scraper service."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Compatible AI Tools Wiki Bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid."""
        return validators.url(url) is True
    
    def scrape_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Tuple of (title, content) or (None, None) if failed
        """
        if not self.is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return None, None
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title and content
            title = self._extract_title(soup, url)
            content = self._extract_content(soup, url)
            
            logger.info(f"Successfully scraped content from {url}")
            return title, content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None, None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract title from HTML."""
        # Try different title sources in order of preference
        title_selectors = [
            ('meta[property="og:title"]', 'content'),
            ('meta[name="twitter:title"]', 'content'),
            ('title', 'text'),
            ('h1', 'text'),
        ]
        
        for selector, attr in title_selectors:
            elements = soup.select(selector)
            if elements:
                if attr == 'content':
                    title = elements[0].get('content', '').strip()
                else:  # text
                    title = elements[0].get_text().strip()
                
                if title:
                    return title[:200]  # Limit title length
        
        # Fallback: use URL path
        parsed_url = urlparse(url)
        if parsed_url.path and parsed_url.path != '/':
            return parsed_url.path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract main content from HTML."""
        # Handle GitHub specifically
        if 'github.com' in url:
            return self._extract_github_content(soup)
        
        # Handle GitLab specifically
        if 'gitlab.com' in url or 'gitlab' in url:
            return self._extract_gitlab_content(soup)
        
        # Generic content extraction
        return self._extract_generic_content(soup)
    
    def _extract_github_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content from GitHub repository."""
        content_parts = []
        
        # Repository description
        description = soup.select_one('p.f4')
        if description:
            content_parts.append(description.get_text().strip())
        
        # README content
        readme_content = soup.select_one('article.markdown-body')
        if readme_content:
            # Get first few paragraphs
            paragraphs = readme_content.select('p')[:3]
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content_parts.append(text)
        
        # Topics/tags
        topics = soup.select('a.topic-tag')
        if topics:
            topic_text = "Topics: " + ", ".join([t.get_text().strip() for t in topics])
            content_parts.append(topic_text)
        
        # Languages
        languages = soup.select('span.Progress-item')
        if languages:
            lang_text = "Languages: " + ", ".join([
                lang.get('aria-label', '').split()[0] for lang in languages[:3]
            ])
            content_parts.append(lang_text)
        
        return ' '.join(content_parts) if content_parts else None
    
    def _extract_gitlab_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content from GitLab repository."""
        content_parts = []
        
        # Project description
        description = soup.select_one('.project-description')
        if description:
            content_parts.append(description.get_text().strip())
        
        # README content
        readme = soup.select_one('.file-content .md')
        if readme:
            paragraphs = readme.select('p')[:3]
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:
                    content_parts.append(text)
        
        return ' '.join(content_parts) if content_parts else None
    
    def _extract_generic_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content from generic webpage."""
        content_parts = []
        
        # Meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc:
            desc = meta_desc.get('content', '').strip()
            if desc:
                content_parts.append(desc)
        
        # Open Graph description
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and not content_parts:  # Only if no meta description
            desc = og_desc.get('content', '').strip()
            if desc:
                content_parts.append(desc)
        
        # Main content selectors (in order of preference)
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '#content',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Get first few paragraphs from the main content
                paragraphs = elements[0].select('p')[:3]
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 30:  # Skip short paragraphs
                        content_parts.append(text)
                        if len(' '.join(content_parts)) > 500:  # Limit content
                            break
                break
        
        # Fallback: get first few paragraphs from anywhere
        if not content_parts:
            paragraphs = soup.select('p')[:5]
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 30:
                    content_parts.append(text)
                    if len(' '.join(content_parts)) > 300:
                        break
        
        return ' '.join(content_parts) if content_parts else None

# Global scraper service instance
scraper_service = ScraperService()
