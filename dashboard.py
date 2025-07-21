"""
Dashboard components for data visualization and report formatting.
Provides utilities for creating charts, metrics, and persona-specific views.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

def create_momentum_chart(momentum_data: List[Dict[str, Any]]):
    """
    Create an interactive momentum chart showing competitor impact scores.
    
    Args:
        momentum_data: List of dictionaries with competitor momentum information
    """
    if not momentum_data:
        st.info("No momentum data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(momentum_data)
    
    # Create the chart
    fig = px.bar(
        df,
        x='competitor',
        y='impact_score',
        color='confidence',
        title='Competitive Momentum Analysis',
        labels={
            'impact_score': 'Impact Score (0-100)',
            'competitor': 'Competitor',
            'confidence': 'Confidence Level'
        },
        color_discrete_map={
            'high': '#2E8B57',    # Sea Green
            'medium': '#FFD700',  # Gold
            'low': '#DC143C'      # Crimson
        }
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title="Competitor",
        yaxis_title="Impact Score",
        showlegend=True,
        height=400
    )
    
    # Add horizontal line at average
    avg_score = df['impact_score'].mean()
    fig.add_hline(
        y=avg_score,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Average: {avg_score:.1f}"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Average Impact", f"{avg_score:.1f}")
    
    with col2:
        high_impact = len(df[df['impact_score'] > 75])
        st.metric("High Impact (>75)", high_impact)
    
    with col3:
        high_confidence = len(df[df['confidence'] == 'high'])
        st.metric("High Confidence", high_confidence)

def format_summary_card(competitor_name: str, summary: Dict[str, Any]):
    """
    Format a competitor summary as a Streamlit card.
    
    Args:
        competitor_name: Name of the competitor
        summary: Summary data dictionary
    """
    with st.container():
        # Header with competitor name and confidence
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"🏢 {competitor_name}")
        
        with col2:
            confidence = summary.get('confidence_level', 'unknown')
            confidence_colors = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🔴'
            }
            st.write(f"Confidence: {confidence_colors.get(confidence, '⚪')} {confidence.title()}")
        
        # Impact score and categories
        col1, col2 = st.columns([1, 2])
        
        with col1:
            impact_score = summary.get('impact_score', 0)
            st.metric("Impact Score", impact_score)
        
        with col2:
            categories = summary.get('categories', [])
            if categories:
                category_badges = " ".join([f"`{cat}`" for cat in categories[:3]])
                st.write(f"**Categories:** {category_badges}")
        
        # Summary bullets
        st.write("**Key Updates:**")
        bullets = summary.get('summary_bullets', [])
        for bullet in bullets:
            st.write(f"• {bullet}")
        
        # Strategic insight
        insight = summary.get('strategic_insight', '')
        if insight:
            st.info(f"💡 **Strategic Insight:** {insight}")
        
        # Metadata
        if summary.get('used_fallback_content'):
            st.warning("⚠️ Analysis based on AI-generated content (scraping failed)")
        
        st.divider()

def create_trend_analysis(summaries: List[Dict[str, Any]]):
    """
    Create trend analysis across multiple competitors.
    
    Args:
        summaries: List of competitor summary dictionaries
    """
    if not summaries:
        st.info("No data available for trend analysis")
        return
    
    st.subheader("📈 Market Trend Analysis")
    
    # Category frequency analysis
    all_categories = []
    for summary in summaries:
        categories = summary.get('categories', [])
        all_categories.extend(categories)
    
    if all_categories:
        category_counts = pd.Series(all_categories).value_counts()
        
        # Create category trends chart
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="Update Categories Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Trending categories
        st.write("**Trending Categories:**")
        for i, (category, count) in enumerate(category_counts.head(3).items()):
            st.write(f"{i+1}. **{category}** - {count} competitors")
    
    # Impact distribution
    impact_scores = [s.get('impact_score', 0) for s in summaries]
    if impact_scores:
        col1, col2 = st.columns(2)
        
        with col1:
            avg_impact = sum(impact_scores) / len(impact_scores)
            st.metric("Average Market Impact", f"{avg_impact:.1f}")
        
        with col2:
            high_impact_count = len([s for s in impact_scores if s > 75])
            st.metric("High Impact Updates", high_impact_count)

def create_persona_view(summaries: List[Dict[str, Any]], persona: str):
    """
    Create persona-specific views (PM, Sales, Design).
    
    Args:
        summaries: List of competitor summary dictionaries
        persona: Target persona ('pm', 'sales', 'design')
    """
    if not summaries:
        return
    
    if persona == 'pm':
        st.subheader("👨‍💼 Product Manager View")
        
        # Focus on features and strategic insights
        for summary in summaries:
            competitor = summary.get('competitor', 'Unknown')
            categories = summary.get('categories', [])
            
            if any(cat in ['Feature', 'AI', 'Integration'] for cat in categories):
                st.write(f"**{competitor}:**")
                bullets = summary.get('summary_bullets', [])
                for bullet in bullets:
                    if any(keyword in bullet.lower() for keyword in ['feature', 'launch', 'release', 'new']):
                        st.write(f"• {bullet}")
                
                insight = summary.get('strategic_insight', '')
                if insight:
                    st.info(f"💡 {insight}")
    
    elif persona == 'sales':
        st.subheader("💼 Sales Team View")
        
        # Focus on pricing and competitive positioning
        for summary in summaries:
            competitor = summary.get('competitor', 'Unknown')
            categories = summary.get('categories', [])
            
            if 'Pricing' in categories or summary.get('impact_score', 0) > 70:
                st.write(f"**{competitor} - Competitive Alert:**")
                bullets = summary.get('summary_bullets', [])
                for bullet in bullets:
                    st.write(f"• {bullet}")
                
                # Sales-specific strategic alert
                alert = create_sales_alert(summary)
                if alert:
                    st.warning(f"🚨 {alert}")
    
    elif persona == 'design':
        st.subheader("🎨 Design Team View")
        
        # Focus on UI/UX changes
        for summary in summaries:
            competitor = summary.get('competitor', 'Unknown')
            categories = summary.get('categories', [])
            
            if 'UI' in categories:
                st.write(f"**{competitor} - Design Update:**")
                bullets = summary.get('summary_bullets', [])
                for bullet in bullets:
                    if any(keyword in bullet.lower() for keyword in ['ui', 'ux', 'design', 'interface']):
                        st.write(f"• {bullet}")

def create_sales_alert(summary: Dict[str, Any]) -> str:
    """
    Generate sales-specific alerts from summary data.
    
    Args:
        summary: Competitor summary dictionary
        
    Returns:
        Sales alert message or empty string
    """
    competitor = summary.get('competitor', 'Unknown')
    categories = summary.get('categories', [])
    impact_score = summary.get('impact_score', 0)
    
    if 'Pricing' in categories:
        return f"{competitor} has pricing changes - review competitive positioning"
    elif impact_score > 85:
        return f"{competitor} major update - prepare competitive response materials"
    elif 'AI' in categories and impact_score > 70:
        return f"{competitor} AI features - update battle cards and positioning"
    else:
        return ""

def display_competitive_matrix(summaries: List[Dict[str, Any]]):
    """
    Display a competitive comparison matrix.
    
    Args:
        summaries: List of competitor summary dictionaries
    """
    if not summaries:
        return
    
    st.subheader("📊 Competitive Matrix")
    
    # Create DataFrame for the matrix
    matrix_data = []
    for summary in summaries:
        matrix_data.append({
            'Competitor': summary.get('competitor', 'Unknown'),
            'Impact Score': summary.get('impact_score', 0),
            'Confidence': summary.get('confidence_level', 'unknown'),
            'Categories': ', '.join(summary.get('categories', [])),
            'Fallback Used': '✅' if summary.get('used_fallback_content') else '❌'
        })
    
    df = pd.DataFrame(matrix_data)
    
    # Style the dataframe
    styled_df = df.style.format({
        'Impact Score': '{:.0f}'
    }).background_gradient(subset=['Impact Score'], cmap='RdYlGn')
    
    st.dataframe(styled_df, use_container_width=True)

def create_executive_summary(summaries: List[Dict[str, Any]]) -> str:
    """
    Generate an executive summary of competitive intelligence.
    
    Args:
        summaries: List of competitor summary dictionaries
        
    Returns:
        Executive summary text
    """
    if not summaries:
        return "No competitive intelligence data available."
    
    total_competitors = len(summaries)
    avg_impact = sum(s.get('impact_score', 0) for s in summaries) / total_competitors
    high_impact_count = len([s for s in summaries if s.get('impact_score', 0) > 75])
    
    # Category analysis
    all_categories = []
    for summary in summaries:
        all_categories.extend(summary.get('categories', []))
    
    category_counts = pd.Series(all_categories).value_counts()
    top_category = category_counts.index[0] if len(category_counts) > 0 else "Unknown"
    
    # Fallback usage
    fallback_count = len([s for s in summaries if s.get('used_fallback_content')])
    
    summary_text = f"""
    **Executive Summary - Competitive Intelligence Report**
    
    Analyzed {total_competitors} competitors with an average impact score of {avg_impact:.1f}/100.
    
    **Key Findings:**
    • {high_impact_count} competitors showed high-impact updates (>75 score)
    • {top_category} is the dominant category for updates this period
    • {fallback_count} analyses used AI fallback due to scraping limitations
    
    **Strategic Recommendations:**
    • Monitor {top_category} developments closely for market trends
    • Prioritize competitive response for high-impact updates
    • Consider enhancing our {top_category} capabilities
    """
    
    return summary_text
