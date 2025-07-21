"""
Slack notification module for delivering competitor intelligence updates.
Handles formatted digest messages, momentum leaderboards, and strategic alerts.
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackNotifier:
    """Slack webhook integration for competitive intelligence notifications."""
    
    def __init__(self, webhook_url: str = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
        """
        if not webhook_url:
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        if not webhook_url:
            logger.warning("Slack webhook URL not configured - notifications disabled")
        
        self.webhook_url = webhook_url
        self.timeout = 10
    
    def send_notification(self, message: str, channel: str = None, username: str = "Competitor Intelligence Bot") -> bool:
        """
        Send a basic notification to Slack.
        
        Args:
            message: Message content
            channel: Slack channel (optional)
            username: Bot username
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.warning("Cannot send notification - webhook URL not configured")
            return False
        
        try:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": ":mag:"
            }
            
            if channel:
                payload["channel"] = channel
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def send_competitive_digest(self, summaries: List[Dict[str, Any]], analysis_period: str) -> bool:
        """
        Send a formatted competitive intelligence digest.
        
        Args:
            summaries: List of competitor summary dictionaries
            analysis_period: Description of the analysis period
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not summaries:
            return self.send_notification("No competitive intelligence updates for this period.")
        
        try:
            # Build the digest message
            digest = self._build_digest_message(summaries, analysis_period)
            
            # Create rich Slack message blocks
            blocks = self._create_digest_blocks(summaries, analysis_period)
            
            payload = {
                "text": f"Competitive Intelligence Digest - {analysis_period}",
                "username": "Competitor Intelligence Bot",
                "icon_emoji": ":chart_with_upwards_trend:",
                "blocks": blocks
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("Competitive digest sent successfully")
                return True
            else:
                logger.error(f"Digest notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending competitive digest: {str(e)}")
            return False
    
    def send_momentum_leaderboard(self, momentum_data: List[Dict[str, Any]]) -> bool:
        """
        Send a competitive momentum leaderboard.
        
        Args:
            momentum_data: List of competitor momentum data
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not momentum_data:
            return False
        
        try:
            # Sort by impact score
            sorted_data = sorted(momentum_data, key=lambda x: x.get('impact_score', 0), reverse=True)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🏆 Competitive Momentum Leaderboard"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Based on impact scores • {datetime.now().strftime('%B %d, %Y')}"
                        }
                    ]
                }
            ]
            
            # Add top 5 competitors
            for i, data in enumerate(sorted_data[:5]):
                position_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                competitor = data.get('competitor', 'Unknown')
                impact_score = data.get('impact_score', 0)
                confidence = data.get('confidence', 'unknown')
                
                confidence_emoji = {
                    'high': '🟢',
                    'medium': '🟡',
                    'low': '🔴'
                }.get(confidence, '⚪')
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{position_emoji} *{competitor}* • Score: {impact_score} • Confidence: {confidence_emoji}"
                    }
                })
            
            payload = {
                "text": "Competitive Momentum Leaderboard",
                "username": "Competitor Intelligence Bot",
                "icon_emoji": ":trophy:",
                "blocks": blocks
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending momentum leaderboard: {str(e)}")
            return False
    
    def send_strategic_alert(self, competitor: str, alert_message: str, summary: Dict[str, Any]) -> bool:
        """
        Send a strategic alert for high-impact competitor updates.
        
        Args:
            competitor: Competitor name
            alert_message: Alert message
            summary: Competitor summary data
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            impact_score = summary.get('impact_score', 0)
            categories = summary.get('categories', [])
            used_fallback = summary.get('used_fallback_content', False)
            
            # Determine alert urgency
            if impact_score > 85:
                urgency = "🚨 HIGH PRIORITY"
                color = "#FF0000"
            elif impact_score > 70:
                urgency = "⚠️ MEDIUM PRIORITY"
                color = "#FFA500"
            else:
                urgency = "ℹ️ LOW PRIORITY"
                color = "#0000FF"
            
            fallback_note = " (AI-generated analysis)" if used_fallback else ""
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{urgency}: {competitor} Update"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Alert:* {alert_message}{fallback_note}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Impact Score:*\n{impact_score}/100"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Categories:*\n{', '.join(categories) if categories else 'None'}"
                        }
                    ]
                }
            ]
            
            # Add key updates if available
            bullets = summary.get('summary_bullets', [])
            if bullets:
                bullet_text = "\n".join([f"• {bullet}" for bullet in bullets])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Key Updates:*\n{bullet_text}"
                    }
                })
            
            payload = {
                "text": f"Strategic Alert: {competitor}",
                "username": "Competitor Intelligence Bot",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "blocks": blocks
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending strategic alert: {str(e)}")
            return False
    
    def _build_digest_message(self, summaries: List[Dict[str, Any]], period: str) -> str:
        """Build a text digest message."""
        total_competitors = len(summaries)
        avg_impact = sum(s.get('impact_score', 0) for s in summaries) / total_competitors
        high_impact = len([s for s in summaries if s.get('impact_score', 0) > 75])
        
        digest = f"**Competitive Intelligence Digest - {period}**\n\n"
        digest += f"📊 Analyzed {total_competitors} competitors\n"
        digest += f"📈 Average impact score: {avg_impact:.1f}/100\n"
        digest += f"🔥 High-impact updates: {high_impact}\n\n"
        
        for summary in summaries:
            competitor = summary.get('competitor', 'Unknown')
            impact_score = summary.get('impact_score', 0)
            bullets = summary.get('summary_bullets', [])
            
            digest += f"**{competitor}** (Score: {impact_score})\n"
            for bullet in bullets[:2]:  # Show first 2 bullets
                digest += f"• {bullet}\n"
            digest += "\n"
        
        return digest
    
    def _create_digest_blocks(self, summaries: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        """Create Slack blocks for rich digest formatting."""
        total_competitors = len(summaries)
        avg_impact = sum(s.get('impact_score', 0) for s in summaries) / total_competitors
        high_impact = len([s for s in summaries if s.get('impact_score', 0) > 75])
        fallback_count = len([s for s in summaries if s.get('used_fallback_content')])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Competitive Intelligence Digest"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Analysis Period: {period} • Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Competitors:*\n{total_competitors}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Impact:*\n{avg_impact:.1f}/100"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High Impact:*\n{high_impact}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*AI Fallbacks:*\n{fallback_count}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # Add top competitors
        sorted_summaries = sorted(summaries, key=lambda x: x.get('impact_score', 0), reverse=True)
        
        for summary in sorted_summaries[:3]:  # Top 3 competitors
            competitor = summary.get('competitor', 'Unknown')
            impact_score = summary.get('impact_score', 0)
            bullets = summary.get('summary_bullets', [])
            used_fallback = summary.get('used_fallback_content', False)
            
            fallback_indicator = " 🤖" if used_fallback else ""
            bullet_text = "\n".join([f"• {bullet}" for bullet in bullets[:2]])
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{competitor}*{fallback_indicator} (Score: {impact_score})\n{bullet_text}"
                }
            })
        
        return blocks

def send_slack_notification(message: str, webhook_url: str = None) -> bool:
    """
    Convenience function for sending basic Slack notifications.
    
    Args:
        message: Message to send
        webhook_url: Optional webhook URL
        
    Returns:
        True if sent successfully, False otherwise
    """
    notifier = SlackNotifier(webhook_url)
    return notifier.send_notification(message)

def send_competitive_digest(summaries: List[Dict[str, Any]], period: str = "Latest Analysis") -> bool:
    """
    Convenience function for sending competitive digest.
    
    Args:
        summaries: List of competitor summaries
        period: Analysis period description
        
    Returns:
        True if sent successfully, False otherwise
    """
    notifier = SlackNotifier()
    return notifier.send_competitive_digest(summaries, period)
