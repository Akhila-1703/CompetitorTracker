"""
Dashboard components and utilities for the Competitor Intelligence Dashboard.
Handles digest formatting, data visualization, and export functionality.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardComponents:
    """Components and utilities for dashboard functionality."""
    
    def __init__(self):
        """Initialize dashboard components."""
        self.persona_configs = {
            "pm": {
                "icon": "👩‍💼",
                "name": "Product Manager",
                "focus": "Evaluate strategic response and resource allocation",
                "bullet_prefix": "🎯"
            },
            "sales": {
                "icon": "💰",
                "name": "Sales",
                "focus": "Update objection handling and competitive positioning",
                "bullet_prefix": "🔥"
            },
            "design": {
                "icon": "🎨", 
                "name": "Design",
                "focus": "Monitor UX trends and interaction patterns",
                "bullet_prefix": "⚡"
            }
        }
    
    def create_momentum_chart(self, momentum_scores: Dict[str, int]) -> go.Figure:
        """
        Create a momentum leaderboard chart.
        
        Args:
            momentum_scores: Dictionary mapping company names to momentum scores
            
        Returns:
            Plotly figure object
        """
        if not momentum_scores:
            return go.Figure()
        
        # Sort companies by momentum score
        sorted_scores = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        companies = [item[0] for item in sorted_scores]
        scores = [item[1] for item in sorted_scores]
        
        # Create color scale based on scores
        colors = ['#FF6B6B' if score >= 80 else '#4ECDC4' if score >= 60 else '#45B7D1' if score >= 40 else '#96CEB4' for score in scores]
        
        fig = go.Figure(data=[
            go.Bar(
                x=companies,
                y=scores,
                marker_color=colors,
                text=scores,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Momentum Score: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Competitor Momentum Leaderboard",
            xaxis_title="Companies",
            yaxis_title="Momentum Score",
            yaxis=dict(range=[0, 100]),
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_category_distribution_chart(self, summaries: List[Dict]) -> go.Figure:
        """
        Create a pie chart showing distribution of update categories.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            Plotly figure object
        """
        categories = {}
        
        for summary in summaries:
            summary_categories = summary.get('categories', [])
            for category in summary_categories:
                categories[category] = categories.get(category, 0) + 1
        
        if not categories:
            return go.Figure()
        
        fig = px.pie(
            values=list(categories.values()),
            names=list(categories.keys()),
            title="Update Categories Distribution"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
    
    def create_confidence_distribution_chart(self, summaries: List[Dict]) -> go.Figure:
        """
        Create a chart showing confidence level distribution.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            Plotly figure object
        """
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        
        for summary in summaries:
            confidence = summary.get('confidence_level', 'medium')
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        colors = {'high': '#4CAF50', 'medium': '#FF9800', 'low': '#F44336'}
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(confidence_counts.keys()),
                y=list(confidence_counts.values()),
                marker_color=[colors[level] for level in confidence_counts.keys()],
                text=list(confidence_counts.values()),
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Analysis Confidence Distribution",
            xaxis_title="Confidence Level",
            yaxis_title="Number of Analyses",
            height=300
        )
        
        return fig
    
    def create_timeline_chart(self, summaries: List[Dict]) -> go.Figure:
        """
        Create a timeline chart of competitor updates.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            Plotly figure object
        """
        if not summaries:
            return go.Figure()
        
        # Extract dates and companies
        timeline_data = []
        for summary in summaries:
            company = summary.get('competitor', 'Unknown')
            generated_at = summary.get('generated_at', datetime.now().isoformat())
            impact_score = summary.get('impact_score', 50)
            
            timeline_data.append({
                'Company': company,
                'Date': generated_at,
                'Impact Score': impact_score
            })
        
        df = pd.DataFrame(timeline_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        fig = px.scatter(
            df,
            x='Date',
            y='Company',
            size='Impact Score',
            color='Impact Score',
            title="Competitor Update Timeline",
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def create_digest(self, summaries: List[Dict], trend_analysis: str, momentum_scores: Dict[str, int], persona: str = "pm") -> str:
        """
        Create a formatted markdown digest for a specific persona.
        
        Args:
            summaries: List of summary dictionaries
            trend_analysis: Trend analysis text
            momentum_scores: Dictionary of momentum scores
            persona: Target persona (pm, sales, design)
            
        Returns:
            Formatted markdown digest string
        """
        persona_config = self.persona_configs.get(persona, self.persona_configs["pm"])
        
        # Header
        digest = f"🚨 **Weekly Competitor Update Digest** ({persona_config['icon']} {persona_config['name']} View)\n\n"
        
        # Company summaries
        for summary in summaries:
            company = summary.get('competitor', 'Unknown')
            
            digest += f"**{company} - {datetime.now().strftime('%B %d, %Y')}** {persona_config['icon']}\n"
            
            # Bullets with persona-specific formatting
            for bullet in summary.get('summary_bullets', []):
                if persona == "sales":
                    digest += f"- {persona_config['bullet_prefix']} {bullet} - *New competitive differentiator*\n"
                elif persona == "design":
                    if 'UI' in bullet.upper():
                        digest += f"- 🎨 {bullet} - *Analyze UX patterns*\n"
                    else:
                        digest += f"- {persona_config['bullet_prefix']} {bullet} - *Consider interaction design*\n"
                else:  # PM view
                    digest += f"- {persona_config['bullet_prefix']} {bullet} - *Consider roadmap impact*\n"
            
            digest += f"📌 {persona_config['name']} Focus: {persona_config['focus']}.\n"
            
            # Strategic insight
            if summary.get('strategic_insight'):
                digest += f"📊 Strategic Alert: {summary['strategic_insight']}\n"
            
            digest += "\n"
        
        # Trend analysis
        if trend_analysis:
            digest += trend_analysis + "\n"
        
        # Momentum leaderboard
        if momentum_scores:
            digest += "\n🏁 Momentum Leaderboard:\n"
            sorted_scores = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
            for i, (company, score) in enumerate(sorted_scores, 1):
                digest += f"{i}. {company} – {score}\n"
        
        # Footer
        digest += "\n\n---\n"
        digest += "📸 **Future Enhancement Note:** In future versions, we'll use Playwright to take screenshots of competitor UIs weekly and compare changes visually (highlight diffs). This would catch silent UI shifts that don't appear in changelogs.\n"
        
        return digest
    
    def format_summary_card(self, summary: Dict) -> str:
        """
        Format a single summary as an HTML card for display.
        
        Args:
            summary: Summary dictionary
            
        Returns:
            HTML formatted card string
        """
        company = summary.get('competitor', 'Unknown')
        confidence = summary.get('confidence_level', 'medium')
        bullets = summary.get('summary_bullets', [])
        strategic_insight = summary.get('strategic_insight', '')
        
        confidence_colors = {
            'high': '#4CAF50',
            'medium': '#FF9800', 
            'low': '#F44336'
        }
        
        card_html = f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px 0; background-color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; color: #333;">{company}</h3>
                <span style="background-color: {confidence_colors.get(confidence, '#FF9800')}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    {confidence.upper()} CONFIDENCE
                </span>
            </div>
            
            <div style="margin-bottom: 12px;">
                <strong>Key Updates:</strong>
                <ul style="margin: 8px 0; padding-left: 20px;">
        """
        
        for bullet in bullets:
            card_html += f"<li style='margin: 4px 0;'>{bullet}</li>"
        
        card_html += "</ul></div>"
        
        if strategic_insight:
            card_html += f"""
            <div style="background-color: #f0f7ff; border-left: 4px solid #2196F3; padding: 12px; margin: 8px 0;">
                <strong>💡 Strategic Insight:</strong> {strategic_insight}
            </div>
            """
        
        card_html += "</div>"
        
        return card_html
    
    def generate_export_data(self, summaries: List[Dict], momentum_scores: Dict[str, int], trend_analysis: str) -> Dict[str, Any]:
        """
        Generate structured data for export.
        
        Args:
            summaries: List of summary dictionaries
            momentum_scores: Dictionary of momentum scores
            trend_analysis: Trend analysis text
            
        Returns:
            Dictionary with export data
        """
        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_competitors": len(summaries),
                "analysis_tool": "Competitor Intelligence Dashboard"
            },
            "summaries": summaries,
            "momentum_scores": momentum_scores,
            "trend_analysis": trend_analysis,
            "leaderboard": sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True) if momentum_scores else []
        }
        
        return export_data
    
    def create_summary_dataframe(self, summaries: List[Dict]) -> pd.DataFrame:
        """
        Convert summaries to a pandas DataFrame for analysis.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            DataFrame with summary data
        """
        df_data = []
        
        for summary in summaries:
            df_data.append({
                'Company': summary.get('competitor', 'Unknown'),
                'Confidence': summary.get('confidence_level', 'medium'),
                'Impact Score': summary.get('impact_score', 50),
                'Update Count': len(summary.get('summary_bullets', [])),
                'Categories': ', '.join(summary.get('categories', [])),
                'Generated At': summary.get('generated_at', ''),
                'Strategic Insight': summary.get('strategic_insight', '')
            })
        
        return pd.DataFrame(df_data)

def format_trend_analysis_html(trend_analysis: str) -> str:
    """
    Format trend analysis text as HTML for better display.
    
    Args:
        trend_analysis: Raw trend analysis text
        
    Returns:
        HTML formatted trend analysis
    """
    if not trend_analysis:
        return "<p>No trend analysis available.</p>"
    
    # Simple markdown-like formatting
    formatted = trend_analysis.replace('\n', '<br>')
    formatted = formatted.replace('📈', '<span style="font-size: 1.2em;">📈</span>')
    
    return f"<div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; margin: 16px 0;'>{formatted}</div>"
