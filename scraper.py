"""
Changelog scraper module for extracting content from competitor websites.
Handles different platform types and provides robust content extraction with OpenAI fallback.
"""

import requests
import trafilatura
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangelogScraper:
    """Web scraper for extracting changelog content from competitor sites with AI fallback."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the scraper with configuration options."""
        self.verbose = verbose
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Rate limiting
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize OpenAI client for fallback
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            logger.warning("OpenAI API key not found - fallback generation disabled")
    
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
    
    def get_changelog_fallback(self, company: str) -> str:
        """
        Generate realistic changelog using OpenAI GPT-4o when scraping fails.
        
        Args:
            company: Name of the company to generate changelog for
            
        Returns:
            GPT-generated changelog content or error message
        """
        if not self.openai_client:
            return "⚠️ Could not generate fallback - OpenAI API key not configured."
        
        try:
            if self.verbose:
                logger.info(f"Generating AI fallback changelog for {company}")
            
            # Rate limit API calls
            self._rate_limit()
            
            prompt = f"""Generate a realistic changelog update for {company} with today's date. 
            
            Format the response exactly as follows:
            [Date] – [Title]
            - Bullet point 1 (specific feature or improvement)
            - Bullet point 2 (specific feature or improvement)  
            - Bullet point 3 (specific feature or improvement)
            
            Make the updates realistic and relevant to {company}'s typical product offerings. 
            Use today's date ({datetime.now().strftime('%B %d, %Y')}) and create a meaningful title.
            Keep bullet points concise but specific."""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a product manager creating realistic changelog entries. Generate authentic-sounding product updates."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Some creativity for realistic content
                max_tokens=300
            )
            
            fallback_content = response.choices[0].message.content
            if fallback_content:
                fallback_content = fallback_content.strip()
            else:
                fallback_content = f"Failed to generate fallback content for {company}"
            
            # Add metadata to indicate this was generated
            fallback_with_metadata = f"{fallback_content}\n\n[GPT-4 generated fallback for {company}]"
            
            if self.verbose:
                logger.info(f"Successfully generated fallback content for {company}")
            
            return fallback_with_metadata
            
        except Exception as e:
            error_msg = f"⚠️ Could not generate fallback: {str(e)}"
            logger.error(f"Error generating AI fallback for {company}: {str(e)}")
            return error_msg
    
    def scrape_changelog(self, url: str, platform: str = "generic") -> Optional[str]:
        """
        Scrape changelog content from a given URL with automatic fallback.
        
        Args:
            url: The URL to scrape
            platform: Platform type ('generic', 'notion', 'linear')
            
        Returns:
            Extracted text content or AI-generated fallback if scraping failed
        """
        try:
            self._rate_limit()
            
            if self.verbose:
                logger.info(f"Scraping {url} (platform: {platform})")
            
            # Platform-specific handling
            if platform == "notion":
                content = self._scrape_notion(url)
            elif platform == "linear":
                content = self._scrape_linear(url)
            else:
                content = self._scrape_generic(url)
            
            # Check if scraping was successful
            if not content or content.startswith("Error:") or len(content.strip()) < 50:
                # Extract company name from URL for fallback
                company_name = self._extract_company_name(url)
                logger.warning(f"Scraping failed for {url}, attempting AI fallback")
                return self.get_changelog_fallback(company_name)
            
            return content
                
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            logger.error(error_msg)
            
            # Attempt AI fallback on exception
            company_name = self._extract_company_name(url)
            logger.warning(f"Exception during scraping {url}, attempting AI fallback")
            return self.get_changelog_fallback(company_name)
    
    def _extract_company_name(self, url: str) -> str:
        """Extract company name from URL for fallback generation."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes and suffixes
            domain = domain.replace('www.', '').replace('blog.', '').replace('changelog.', '')
            
            # Extract the main part (before first dot)
            if '.' in domain:
                company = domain.split('.')[0]
            else:
                company = domain
            
            # Capitalize for better presentation
            return company.capitalize()
            
        except Exception:
            return "Unknown Company"
    
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
        Scrape multiple competitor changelogs with fallback support.
        
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
                'content_length': len(content) if content else 0,
                'fallback_used': 'GPT-4 generated' in content if content else False
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
    Convenience function for single changelog scraping with automatic fallback.
    Maintains compatibility with existing code.
    """
    scraper = ChangelogScraper(verbose=False)
    return scraper.scrape_changelog(url, platform)
