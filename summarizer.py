"""
AI-powered summarizer using OpenAI GPT-4o to generate structured changelog summaries.
Creates consistent, actionable insights from raw changelog content.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Optional, List
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangelogSummarizer:
    """AI-powered changelog summarizer using OpenAI GPT."""
    
    def __init__(self, api_key: str = None, verbose: bool = False):
        """Initialize the summarizer with OpenAI API key."""
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.verbose = verbose
        # Rate limiting for API calls
        self.last_api_call = 0
        self.min_api_interval = 1.0  # 1 second between API calls
    
    def _rate_limit_api(self):
        """Implement rate limiting for OpenAI API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        if time_since_last < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last
            if self.verbose:
                logger.info(f"API rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def _create_summary_prompt(self, competitor_name: str, content: str, start_date: datetime, end_date: datetime) -> str:
        """Create a prompt for GPT to summarize the changelog content."""
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        # Check if content is GPT-generated fallback
        is_fallback = "GPT-4 generated" in content if content else False
        content_note = " (Note: This content was AI-generated as a fallback when scraping failed)" if is_fallback else ""
        
        prompt = f"""
You are an expert product analyst tasked with summarizing competitor changelog information.

Analyze the following changelog content from {competitor_name} and create a structured summary focusing on changes from {date_range}.{content_note}

CHANGELOG CONTENT:
{content}

Please provide a summary in the following JSON format:
{{
    "competitor": "{competitor_name}",
    "summary_bullets": [
        "First key change or feature (be specific and actionable)",
        "Second key change or feature (be specific and actionable)", 
        "Third key change or feature (be specific and actionable)"
    ],
    "strategic_insight": "One strategic insight about what these changes mean for the competitive landscape, market direction, or business implications (1-2 sentences)",
    "confidence_level": "high|medium|low",
    "relevant_dates": ["YYYY-MM-DD", "YYYY-MM-DD"],
    "categories": ["AI", "Feature", "UI", "Pricing", "Integration"],
    "impact_score": 85,
    "content_source": "{"fallback" if is_fallback else "scraped"}"
}}

GUIDELINES:
- Focus only on significant product changes, new features, or important updates
- Ignore minor bug fixes, routine maintenance, or trivial updates unless they indicate larger trends
- Be specific and actionable in bullet points - avoid vague statements
- The strategic insight should provide business intelligence value
- Only include changes that appear to be from the specified date range when possible
- If no significant changes are found in the content, indicate low confidence
- Keep bullet points concise but informative (max 25 words each)
- Strategic insight should be forward-looking and analytical
- Categories should reflect the main themes of the updates
- Impact score should be 0-100 based on strategic importance
- For AI-generated fallback content, adjust confidence level accordingly
"""
        return prompt
    
    def summarize_changelog(self, competitor_name: str, content: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """
        Generate an AI summary of changelog content.
        
        Args:
            competitor_name: Name of the competitor
            content: Raw changelog content to summarize
            start_date: Start date for the analysis period
            end_date: End date for the analysis period
        
        Returns:
            Dictionary with summary data or None if summarization failed
        """
        if self.verbose:
            logger.info(f"Generating AI summary for {competitor_name}")
        
        try:
            self._rate_limit_api()
            
            prompt = self._create_summary_prompt(competitor_name, content, start_date, end_date)
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert product analyst specializing in competitive intelligence and changelog analysis. Provide accurate, actionable summaries in the requested JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent outputs
                max_tokens=1000
            )
            
            # Parse the JSON response
            summary_text = response.choices[0].message.content
            if not summary_text:
                if self.verbose:
                    logger.warning("Empty response from OpenAI API")
                return None
            summary_data = json.loads(summary_text)
            
            # Validate the response structure
            required_fields = ["competitor", "summary_bullets", "strategic_insight", "confidence_level"]
            if not all(field in summary_data for field in required_fields):
                if self.verbose:
                    logger.warning("AI response missing required fields")
                return None
            
            # Validate bullet points
            if not isinstance(summary_data["summary_bullets"], list) or len(summary_data["summary_bullets"]) != 3:
                if self.verbose:
                    logger.warning("AI response doesn't have exactly 3 bullet points")
                return None
            
            # Add metadata
            summary_data["generated_at"] = datetime.now().isoformat()
            summary_data["content_length"] = len(content) if content else 0
            summary_data["analysis_period"] = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
            
            # Detect if this was generated from fallback content
            is_fallback = "GPT-4 generated" in content if content else False
            summary_data["used_fallback_content"] = is_fallback
            
            if self.verbose:
                logger.info(f"Generated summary with confidence: {summary_data.get('confidence_level', 'unknown')}")
                if is_fallback:
                    logger.info("Summary based on AI-generated fallback content")
            
            return summary_data
            
        except json.JSONDecodeError as e:
            if self.verbose:
                logger.error(f"Error parsing AI response as JSON: {str(e)}")
            return None
        except Exception as e:
            if self.verbose:
                logger.error(f"Error calling OpenAI API: {str(e)}")
            
            # If OpenAI API fails, generate a basic fallback summary
            if "429" in str(e) or "quota" in str(e).lower():
                if self.verbose:
                    logger.info("Generating fallback summary due to API quota limit")
                return self._generate_fallback_summary(competitor_name, content, start_date, end_date)
            
            return None
    
    def _generate_fallback_summary(self, competitor: str, content: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Generate a basic fallback summary when OpenAI API is not available.
        
        Args:
            competitor: Name of the competitor
            content: Changelog content (could be AI-generated fallback)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Basic summary dictionary
        """
        try:
            # Extract basic information from content
            content_lines = content.split('\n') if content else []
            bullet_points = []
            
            # Look for bullet points or generate basic ones from content structure
            for line in content_lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
                    bullet_points.append(line[2:].strip())
                elif line and len(line) > 20 and not line.startswith('['):
                    # Convert regular lines to bullet points
                    bullet_points.append(line[:100] + "..." if len(line) > 100 else line)
            
            # Ensure we have exactly 3 bullet points
            if len(bullet_points) < 3:
                default_bullets = [
                    f"{competitor} released new product features and enhancements",
                    "Various improvements to user experience and performance",
                    "Continued platform development and integration capabilities"
                ]
                while len(bullet_points) < 3:
                    bullet_points.append(default_bullets[len(bullet_points) % len(default_bullets)])
            
            # Take only first 3 bullet points
            bullet_points = bullet_points[:3]
            
            # Generate basic fallback summary
            fallback_summary = {
                "competitor": competitor,
                "summary_bullets": bullet_points,
                "strategic_insight": f"{competitor} continues active product development with regular feature updates and improvements.",
                "confidence_level": "low",
                "impact_score": 60,  # Moderate default impact
                "categories": ["product-updates", "general-improvements"],
                "generated_at": datetime.now().isoformat(),
                "content_length": len(content) if content else 0,
                "analysis_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "used_fallback_content": "GPT-4 generated" in content if content else False,
                "fallback_summary": True  # Mark as fallback
            }
            
            if self.verbose:
                logger.info(f"Generated fallback summary for {competitor}")
            
            return fallback_summary
            
        except Exception as e:
            if self.verbose:
                logger.error(f"Error generating fallback summary: {str(e)}")
            return None
    
    def batch_summarize(self, changelog_data: List[Dict]) -> List[Dict]:
        """
        Summarize multiple changelogs in batch with proper rate limiting.
        
        Args:
            changelog_data: List of dictionaries with changelog information
        
        Returns:
            List of summary dictionaries
        """
        summaries = []
        
        for i, data in enumerate(changelog_data):
            if self.verbose:
                logger.info(f"Processing changelog {i+1}/{len(changelog_data)}: {data.get('competitor', 'Unknown')}")
            
            summary = self.summarize_changelog(
                data.get('competitor', 'Unknown'),
                data.get('content', ''),
                data.get('start_date', datetime.now()),
                data.get('end_date', datetime.now())
            )
            
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def create_strategic_alert(self, summary: Dict) -> str:
        """
        Generate a strategic alert based on the summary data.
        
        Args:
            summary: Summary dictionary with competitor analysis
            
        Returns:
            Strategic alert message
        """
        competitor = summary.get('competitor', 'Unknown')
        categories = summary.get('categories', [])
        impact_score = summary.get('impact_score', 50)
        used_fallback = summary.get('used_fallback_content', False)
        
        # Add context for fallback-generated content
        fallback_note = " (AI-generated analysis)" if used_fallback else ""
        
        # Generate context-specific alerts
        if 'AI' in categories and impact_score > 70:
            return f"{competitor}'s AI advancement signals market shift — evaluate our AI roadmap urgency.{fallback_note}"
        elif 'Pricing' in categories:
            return f"{competitor} pricing changes suggest repositioning — monitor customer reaction.{fallback_note}"
        elif impact_score > 85:
            return f"High-impact updates from {competitor} — immediate competitive response needed.{fallback_note}"
        elif len(categories) >= 3:
            return f"Multi-category updates from {competitor} — assess feature gap priorities.{fallback_note}"
        else:
            return f"{competitor} incremental progress — monitor for strategic pattern emergence.{fallback_note}"

def summarize(text: str, company: str) -> str:
    """
    Legacy function for backward compatibility.
    Creates a simple formatted summary without AI processing.
    """
    try:
        # Clean and normalize the text
        clean_text = text.replace('\n', ' ').replace('\t', ' ')
        
        # Simple feature extraction
        import re
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        entries = []
        
        # Look for meaningful content
        for line in lines:
            if len(line) < 15:
                continue
                
            if any(keyword in line.lower() for keyword in [':', 'new', 'added', 'launched', 'released', 'feature', 'update']):
                clean_line = re.sub(r'^[0-9\.,\s]*', '', line)
                clean_line = re.sub(r'^\w+\s+\d+[,\s]*\d*[,\s]*\d*[:\s]*', '', clean_line)
                
                if len(clean_line) > 10:
                    entries.append(clean_line)
        
        # Fallback to sentences
        if not entries:
            sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 20]
            entries = sentences[:5]
        
        # Categorize features
        features = []
        for entry in entries[:3]:
            entry_lower = entry.lower()
            
            if any(keyword in entry_lower for keyword in ['interface', 'design', 'ui', 'ux']):
                category = "UI"
            elif any(keyword in entry_lower for keyword in ['price', 'pricing', 'plan']):
                category = "Pricing" 
            elif any(keyword in entry_lower for keyword in ['ai', 'artificial intelligence']):
                category = "AI"
            else:
                category = "Feature"
            
            clean_entry = entry.strip()
            if len(clean_entry) > 60:
                clean_entry = clean_entry[:60] + "..."
            
            features.append((clean_entry, category))
        
        # Format output
        result = f"**{company} - {datetime.now().strftime('%B %d, %Y')}**\n"
        
        for feature, category in features:
            result += f"- 🆕 {feature} **({category})**\n"
        
        return result
        
    except Exception as e:
        return f"Error processing summary: {str(e)}"
