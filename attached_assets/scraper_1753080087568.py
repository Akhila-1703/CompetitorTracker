"""
Changelog scraper module for extracting content from competitor websites.
Handles different platform types and provides robust content extraction.
"""

import requests
import trafilatura
import time
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangelogScraper:
    """Web scraper for extracting changelog content from competitor sites."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the scraper with configuration options."""
        self.verbose = verbose
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Rate limiting
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            if self.verbose:
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def scrape_changelog(self, url: str, platform: str = "generic") -> Optional[str]:
        """
        Scrape changelog content from a given URL.
        
        Args:
            url: The URL to scrape
            platform: Platform type ('generic', 'notion', 'linear')
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            self._rate_limit()
            
            if self.verbose:
                logger.info(f"Scraping {url} (platform: {platform})")
            
            # Platform-specific handling
            if platform == "notion":
                return self._scrape_notion(url)
            elif platform == "linear":
                return self._scrape_linear(url)
            else:
                return self._scrape_generic(url)
                
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def _scrape_generic(self, url: str) -> Optional[str]:
        """Generic scraping using trafilatura."""
        try:
            # Fetch the webpage
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return "Error: Failed to download webpage"
            
            # Extract text content
            text = trafilatura.extract(downloaded)
            if not text:
                return "Error: No content extracted"
            
            # Clean and limit content length
            cleaned_text = self._clean_content(text)
            
            if self.verbose:
                logger.info(f"Extracted {len(cleaned_text)} characters")
            
            return cleaned_text
            
        except Exception as e:
            return f"Error: Generic scraping failed - {str(e)}"
    
    def _scrape_notion(self, url: str) -> Optional[str]:
        """Notion-specific scraping with enhanced content extraction."""
        try:
            # Use trafilatura for Notion pages
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return "Error: Failed to download Notion page"
            
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if not text:
                return "Error: No content extracted from Notion"
            
            # Notion-specific content processing
            cleaned_text = self._clean_notion_content(text)
            
            if self.verbose:
                logger.info(f"Extracted {len(cleaned_text)} characters from Notion")
            
            return cleaned_text
            
        except Exception as e:
            return f"Error: Notion scraping failed - {str(e)}"
    
    def _scrape_linear(self, url: str) -> Optional[str]:
        """Linear-specific scraping with changelog formatting."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return "Error: Failed to download Linear changelog"
            
            text = trafilatura.extract(downloaded, include_comments=False)
            if not text:
                return "Error: No content extracted from Linear"
            
            # Linear-specific content processing
            cleaned_text = self._clean_linear_content(text)
            
            if self.verbose:
                logger.info(f"Extracted {len(cleaned_text)} characters from Linear")
            
            return cleaned_text
            
        except Exception as e:
            return f"Error: Linear scraping failed - {str(e)}"
    
    def _clean_content(self, text: str) -> str:
        """Clean and normalize extracted content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Limit content length to prevent token overflow
        max_length = 10000
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "... [content truncated]"
        
        return cleaned
    
    def _clean_notion_content(self, text: str) -> str:
        """Notion-specific content cleaning."""
        if not text:
            return ""
        
        # Remove Notion-specific artifacts
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('What\'s New'):
                # Remove date artifacts and clean formatting
                if len(line) > 10:  # Skip very short lines
                    lines.append(line)
        
        cleaned = '\n'.join(lines)
        return self._clean_content(cleaned)
    
    def _clean_linear_content(self, text: str) -> str:
        """Linear-specific content cleaning."""
        if not text:
            return ""
        
        # Linear changelog specific processing
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.lower().startswith('changelog'):
                # Clean Linear-specific formatting
                if len(line) > 15:  # Skip short lines
                    lines.append(line)
        
        cleaned = '\n'.join(lines)
        return self._clean_content(cleaned)
    
    def get_multiple_changelogs(self, competitors: list) -> Dict[str, Any]:
        """
        Scrape multiple competitor changelogs.
        
        Args:
            competitors: List of competitor dictionaries with name, url, platform
            
        Returns:
            Dictionary mapping competitor names to scraped content
        """
        results = {}
        
        for competitor in competitors:
            name = competitor.get('name', 'Unknown')
            url = competitor.get('url', '')
            platform = competitor.get('platform', 'generic')
            
            if self.verbose:
                logger.info(f"Processing {name}...")
            
            content = self.scrape_changelog(url, platform)
            results[name] = {
                'url': url,
                'platform': platform,
                'content': content,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content) if content else 0
            }
        
        return results
    
    def validate_url(self, url: str) -> bool:
        """Validate if a URL is accessible."""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

def get_changelog(url: str, platform: str = "generic") -> str:
    """
    Convenience function for single changelog scraping.
    Maintains compatibility with existing code.
    """
    scraper = ChangelogScraper(verbose=False)
    return scraper.scrape_changelog(url, platform)
