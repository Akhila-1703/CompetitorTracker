"""
Notification module for sending competitor intelligence updates via Slack and other channels.
Handles webhook delivery and message formatting for different platforms.
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackNotifier:
    """Handles Slack webhook notifications for competitor intelligence updates."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL for posting messages
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.max_message_length = 4000  # Slack message limit
    
    def send_digest(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str) -> bool:
        """
        Send a formatted competitor digest to Slack.
        
        Args:
            summaries: List of competitor summaries
            momentum_scores: Dictionary of momentum scores
            trend_analysis: Trend analysis text
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            message = self._format_digest_message(summaries, momentum_scores, trend_analysis)
            
            payload = {
                "text": "🚨 Weekly Competitor Intelligence Update",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Weekly Competitor Intelligence Update"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add momentum leaderboard as separate section
            if momentum_scores:
                leaderboard_text = self._format_momentum_leaderboard(momentum_scores)
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": leaderboard_text
                    }
                })
            
            # Add trend analysis if available
            if trend_analysis:
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Trend Analysis:*\n{trend_analysis}"
                    }
                })
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Slack message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False
    
    def send_alert(self, company: str, alert_message: str, urgency: str = "medium") -> bool:
        """
        Send an individual competitor alert to Slack.
        
        Args:
            company: Company name
            alert_message: Alert message
            urgency: Alert urgency level (low, medium, high)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            urgency_emojis = {
                "low": "ℹ️",
                "medium": "⚠️", 
                "high": "🚨"
            }
            
            urgency_colors = {
                "low": "#36a64f",
                "medium": "#ff9500",
                "high": "#ff0000"
            }
            
            emoji = urgency_emojis.get(urgency, "⚠️")
            color = urgency_colors.get(urgency, "#ff9500")
            
            payload = {
                "text": f"{emoji} Competitor Alert: {company}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": f"Alert for {company}",
                                "value": alert_message,
                                "short": False
                            }
                        ],
                        "footer": "Competitor Intelligence Dashboard",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent for {company}")
                return True
            else:
                logger.error(f"Failed to send Slack alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def _format_digest_message(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str) -> str:
        """
        Format competitor summaries into a Slack-friendly message.
        
        Args:
            summaries: List of competitor summaries
            momentum_scores: Dictionary of momentum scores
            trend_analysis: Trend analysis text
            
        Returns:
            Formatted message string
        """
        message_parts = []
        
        for summary in summaries[:5]:  # Limit to first 5 to avoid message length issues
            company = summary.get('competitor', 'Unknown')
            bullets = summary.get('summary_bullets', [])
            confidence = summary.get('confidence_level', 'medium')
            momentum = momentum_scores.get(company, 0)
            
            company_section = f"*{company}* (Momentum: {momentum}, Confidence: {confidence.upper()})\n"
            
            for bullet in bullets[:3]:  # Limit bullets to avoid length issues
                company_section += f"• {bullet}\n"
            
            strategic_insight = summary.get('strategic_insight', '')
            if strategic_insight:
                company_section += f"💡 _{strategic_insight[:200]}{'...' if len(strategic_insight) > 200 else ''}_\n"
            
            company_section += "\n"
            message_parts.append(company_section)
        
        return "".join(message_parts)
    
    def _format_momentum_leaderboard(self, momentum_scores: Dict[str, int]) -> str:
        """
        Format momentum scores as a leaderboard for Slack.
        
        Args:
            momentum_scores: Dictionary of momentum scores
            
        Returns:
            Formatted leaderboard string
        """
        if not momentum_scores:
            return ""
        
        leaderboard = "*🏁 Momentum Leaderboard:*\n"
        sorted_scores = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (company, score) in enumerate(sorted_scores[:10]):  # Top 10 only
            medal = medals[i] if i < 3 else f"{i+1}."
            leaderboard += f"{medal} {company} – {score}\n"
        
        return leaderboard
    
    def test_connection(self) -> bool:
        """
        Test the Slack webhook connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("No webhook URL configured for testing")
            return False
        
        try:
            test_payload = {
                "text": "🧪 Test message from Competitor Intelligence Dashboard",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This is a test message to verify webhook connectivity. If you see this, your Slack integration is working! 🎉"
                        }
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            success = response.status_code == 200
            if success:
                logger.info("Slack webhook test successful")
            else:
                logger.error(f"Slack webhook test failed: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Slack webhook test error: {str(e)}")
            return False

class EmailNotifier:
    """Handles email notifications (placeholder for future implementation)."""
    
    def __init__(self, smtp_server: Optional[str] = None, smtp_port: int = 587):
        """Initialize email notifier."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        logger.info("Email notifications not yet implemented")
    
    def send_digest(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str, recipients: List[str]) -> bool:
        """Send digest via email (placeholder)."""
        logger.info("Email digest sending not yet implemented")
        return False

class DiscordNotifier:
    """Handles Discord webhook notifications (placeholder for future implementation)."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Discord notifier."""
        self.webhook_url = webhook_url
        logger.info("Discord notifications not yet implemented")
    
    def send_digest(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str) -> bool:
        """Send digest to Discord (placeholder)."""
        logger.info("Discord digest sending not yet implemented")
        return False

class NotificationManager:
    """Manages multiple notification channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.slack = SlackNotifier()
        self.email = EmailNotifier()
        self.discord = DiscordNotifier()
    
    def send_to_all_channels(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str, channels: List[str] = None) -> Dict[str, bool]:
        """
        Send notifications to multiple channels.
        
        Args:
            summaries: List of competitor summaries
            momentum_scores: Dictionary of momentum scores
            trend_analysis: Trend analysis text
            channels: List of channels to send to (default: all configured)
            
        Returns:
            Dictionary mapping channel names to success status
        """
        results = {}
        
        if not channels:
            channels = ["slack"]  # Default to Slack only for now
        
        if "slack" in channels:
            results["slack"] = self.slack.send_digest(summaries, momentum_scores, trend_analysis)
        
        if "email" in channels:
            results["email"] = self.email.send_digest(summaries, momentum_scores, trend_analysis, [])
        
        if "discord" in channels:
            results["discord"] = self.discord.send_digest(summaries, momentum_scores, trend_analysis)
        
        return results
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all notification channel connections."""
        return {
            "slack": self.slack.test_connection(),
            "email": False,  # Not implemented yet
            "discord": False  # Not implemented yet
        }
