"""
Competitor Intelligence Dashboard - Main Streamlit Application
Monitors competitor changelog updates, generates AI-powered insights, and tracks competitive momentum.
"""

import streamlit as st
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Import local modules
from scraper import ChangelogScraper, get_changelog
from summarizer import ChangelogSummarizer
from config import COMPETITORS
from dashboard import create_momentum_chart, format_summary_card
from database import DatabaseManager
from notifier import send_slack_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Competitor Intelligence Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function."""
    st.title("🔍 Competitor Intelligence Dashboard")
    st.markdown("Monitor competitor updates and generate AI-powered competitive intelligence.")
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # API Key status
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        st.sidebar.success("✅ OpenAI API Key configured")
    else:
        st.sidebar.error("❌ OpenAI API Key missing")
        st.sidebar.info("Please add OPENAI_API_KEY to your .env file")
    
    # Database connection status
    try:
        db = DatabaseManager()
        st.sidebar.success("✅ Database connected")
    except Exception as e:
        st.sidebar.error(f"❌ Database connection failed: {str(e)}")
        db = None
    
    # Competitor selection
    st.sidebar.subheader("Select Competitors")
    selected_competitors = []
    
    for i, competitor in enumerate(COMPETITORS):
        if st.sidebar.checkbox(competitor['name'], value=True, key=f"competitor_{i}"):
            selected_competitors.append(competitor)
    
    # Analysis settings
    st.sidebar.subheader("Analysis Settings")
    days_back = st.sidebar.slider("Days to analyze", 1, 30, 7)
    use_ai_summaries = st.sidebar.checkbox("Generate AI summaries", value=True)
    
    # Persona view selector
    st.sidebar.subheader("View Mode")
    view_mode = st.sidebar.selectbox(
        "Select Perspective",
        ["All Teams", "PM View", "Sales View", "Design View"],
        help="Filter insights by team perspective"
    )
    
    # Action buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔄 Analyze", type="primary"):
            if not selected_competitors:
                st.error("Please select at least one competitor")
            else:
                analyze_competitors(selected_competitors, days_back, use_ai_summaries, db, view_mode)
    
    with col2:
        if st.button("📊 Load History"):
            load_historical_data(db)
    
    # Main content area
    if st.session_state.analysis_results:
        display_analysis_results()
    else:
        display_welcome_message()

def analyze_competitors(competitors, days_back, use_ai_summaries, db, view_mode="All Teams"):
    """Analyze selected competitors and display results."""
    st.header("📈 Analysis Results")
    
    # Initialize components
    scraper = ChangelogScraper(verbose=True)
    summarizer = None
    
    if use_ai_summaries and os.getenv("OPENAI_API_KEY"):
        try:
            summarizer = ChangelogSummarizer(os.getenv("OPENAI_API_KEY"), verbose=True)
        except Exception as e:
            st.warning(f"Failed to initialize AI summarizer: {str(e)}")
            summarizer = None
    
    results = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, competitor in enumerate(competitors):
        status_text.text(f"Analyzing {competitor['name']}...")
        progress = (i + 1) / len(competitors)
        progress_bar.progress(progress)
        
        try:
            # Scrape changelog content with automatic fallback
            content = scraper.scrape_changelog(
                competitor['url'], 
                competitor.get('platform', 'generic')
            )
            
            # If scraping fails, automatically generate fallback content
            if not content or content.startswith("Error:"):
                st.warning(f"⚠️ Scraping failed for {competitor['name']}, generating AI fallback")
                logger.warning(f"Scraping failed for {competitor['name']}: {content}")
                
                # Generate AI fallback content
                try:
                    fallback_content = scraper.get_changelog_fallback(competitor['name'])
                    if fallback_content and not fallback_content.startswith("⚠️"):
                        content = fallback_content
                        logger.info(f"Generated AI fallback content for {competitor['name']}")
                    else:
                        logger.error(f"Failed to generate fallback for {competitor['name']}: {fallback_content}")
                        content = fallback_content  # Keep the error message
                except Exception as e:
                    error_msg = f"Error generating fallback for {competitor['name']}: {str(e)}"
                    logger.error(error_msg)
                    content = f"Error: {error_msg}"
            
            # Generate AI summary if enabled and content is available (including fallback)
            summary = None
            if summarizer and content and not content.startswith("Error:"):
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                try:
                    summary = summarizer.summarize_changelog(
                        competitor['name'],
                        content,
                        start_date,
                        end_date
                    )
                    if summary:
                        logger.info(f"Generated AI summary for {competitor['name']}")
                    else:
                        logger.warning(f"Failed to generate summary for {competitor['name']}")
                except Exception as e:
                    logger.error(f"Error generating summary for {competitor['name']}: {str(e)}")
                    summary = None
            
            results[competitor['name']] = {
                'competitor': competitor,
                'content': content,
                'summary': summary,
                'scraped_at': datetime.now().isoformat(),
                'analysis_period': f"{days_back} days"
            }
            
            # Save to database if available
            if db and summary:
                try:
                    db.save_analysis(competitor['name'], summary, content)
                except Exception as e:
                    logger.error(f"Failed to save analysis to database: {str(e)}")
            
        except Exception as e:
            error_msg = f"Error analyzing {competitor['name']}: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
    
    progress_bar.empty()
    status_text.empty()
    
    # Store results in session state with view mode
    st.session_state.analysis_results = results
    st.session_state.view_mode = view_mode
    
    # Display trend of the week
    if summarizer and results:
        summaries = [data['summary'] for data in results.values() if data.get('summary')]
        if summaries:
            trend = summarizer.analyze_trend_of_week(summaries)
            st.success(f"📈 **Trend of the Week:** {trend}")
    
    # Display results
    display_analysis_results()

def display_analysis_results():
    """Display the analysis results in the main content area."""
    results = st.session_state.analysis_results
    
    if not results:
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Competitors Analyzed", len(results))
    
    with col2:
        successful_scrapes = sum(1 for r in results.values() 
                               if r['content'] and not r['content'].startswith("Error:"))
        st.metric("Successful Scrapes", successful_scrapes)
    
    with col3:
        ai_summaries = sum(1 for r in results.values() if r['summary'])
        st.metric("AI Summaries", ai_summaries)
    
    with col4:
        fallback_count = sum(1 for r in results.values() 
                           if r['content'] and "GPT-4 generated" in r['content'])
        st.metric("AI Fallbacks Used", fallback_count)
    
    st.divider()
    
    # Get view mode from session state
    view_mode = st.session_state.get('view_mode', 'All Teams')
    
    # Filter results based on view mode
    filtered_results = filter_results_by_persona(results, view_mode)
    
    # Detailed results
    tabs = st.tabs(["📋 Summary View", "📊 Momentum Analysis", "🔍 Detailed View"])
    
    with tabs[0]:
        display_summary_view(filtered_results, view_mode)
    
    with tabs[1]:
        display_momentum_analysis(filtered_results)
    
    with tabs[2]:
        display_detailed_view(filtered_results, view_mode)

def display_summary_view(results, view_mode="All Teams"):
    """Display summarized competitor insights."""
    st.subheader(f"🎯 Key Insights ({view_mode})")
    
    for name, data in results.items():
        summary = data.get('summary')
        if summary:
            format_summary_card(name, summary, view_mode)
        else:
            st.info(f"No AI summary available for {name}")

def display_momentum_analysis(results):
    """Display competitive momentum analysis."""
    st.subheader("📈 Competitive Momentum")
    
    # Extract momentum data
    momentum_data = []
    for name, data in results.items():
        summary = data.get('summary')
        if summary:
            impact_score = summary.get('impact_score', 50)
            confidence = summary.get('confidence_level', 'medium')
            momentum_data.append({
                'competitor': name,
                'impact_score': impact_score,
                'confidence': confidence
            })
    
    if momentum_data:
        create_momentum_chart(momentum_data)
    else:
        st.info("No momentum data available. Generate AI summaries to see momentum analysis.")

def display_detailed_view(results, view_mode="All Teams"):
    """Display detailed competitor analysis."""
    st.subheader(f"🔍 Detailed Analysis ({view_mode})")
    
    for i, (name, data) in enumerate(results.items()):
        with st.expander(f"{name} - Detailed Analysis"):
            competitor = data['competitor']
            
            # Competitor info
            st.markdown(f"**URL:** {competitor['url']}")
            st.markdown(f"**Platform:** {competitor.get('platform', 'generic')}")
            st.markdown(f"**Category:** {competitor.get('category', 'Unknown')}")
            
            # Content preview
            content = data.get('content', '')
            if content:
                if content.startswith("Error:"):
                    st.error(content)
                else:
                    st.markdown("**Content Preview:**")
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.text_area("Raw Content", preview, height=150, disabled=True, key=f"raw_content_{name}_{uuid.uuid4()}")
            
            # AI Summary
            summary = data.get('summary')
            if summary:
                st.markdown("**AI Summary:**")
                st.json(summary)

def load_historical_data(db):
    """Load and display historical analysis data."""
    if not db:
        st.error("Database not available")
        return
    
    try:
        historical_data = db.get_recent_analyses(limit=10)
        if historical_data:
            st.subheader("📚 Historical Analysis")
            
            for analysis in historical_data:
                with st.expander(f"{analysis['competitor']} - {analysis['created_at']}"):
                    st.json(analysis['summary_data'])
        else:
            st.info("No historical data available")
    
    except Exception as e:
        st.error(f"Failed to load historical data: {str(e)}")

def filter_results_by_persona(results, view_mode):
    """Filter results based on persona view."""
    if view_mode == "All Teams":
        return results
    
    # For now, return all results but will be used for filtering in the display functions
    return results

def format_summary_card(name, summary, view_mode="All Teams"):
    """Format summary card with persona-specific focus."""
    with st.container():
        # Header with confidence indicator
        confidence = summary.get('confidence_level', 'medium')
        confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        confidence_icon = confidence_color.get(confidence, "⚪")
        
        st.markdown(f"### {name} {confidence_icon}")
        
        # Persona-specific content filtering
        bullets = summary.get('summary_bullets', [])
        strategic_insight = summary.get('strategic_insight', '')
        
        if view_mode == "Sales View":
            # Focus on pricing, market positioning, competitive advantages
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['pricing', 'plan', 'subscription', 'cost', 'revenue', 'market', 'customer'])]
            if not filtered_bullets:
                filtered_bullets = bullets[:2]  # Show at least some content
            bullets = filtered_bullets
        elif view_mode == "Design View":
            # Focus on UI/UX, design, user experience
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['ui', 'ux', 'design', 'interface', 'user', 'visual', 'layout', 'experience'])]
            if not filtered_bullets:
                filtered_bullets = bullets[:2]
            bullets = filtered_bullets
        elif view_mode == "PM View":
            # Focus on features, strategy, roadmap
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['feature', 'product', 'launch', 'beta', 'roadmap', 'strategy', 'integration'])]
            if not filtered_bullets:
                filtered_bullets = bullets
            bullets = filtered_bullets
        
        # Display bullets
        for bullet in bullets:
            st.markdown(f"• {bullet}")
        
        # Strategic insight
        if strategic_insight:
            st.markdown(f"**💡 Strategic Insight:** {strategic_insight}")
        
        # Impact score
        impact_score = summary.get('impact_score', 50)
        st.progress(impact_score / 100, f"Impact Score: {impact_score}/100")
        
        st.divider()

def display_welcome_message():
    """Display welcome message and instructions."""
    st.markdown("""
    ## Welcome to the Competitor Intelligence Dashboard
    
    This dashboard helps you monitor competitor changelog updates and generate AI-powered insights.
    
    ### Features:
    - 🔍 **Web Scraping**: Automatically extracts changelog content from competitor websites
    - 🤖 **AI Fallback**: Uses GPT-4o to generate realistic changelogs when scraping fails
    - 📊 **Momentum Analysis**: Tracks competitive momentum and impact scores
    - 💾 **Data Persistence**: Stores analysis results in PostgreSQL database
    - 📱 **Slack Integration**: Send notifications to Slack channels
    
    ### Get Started:
    1. Select competitors from the sidebar
    2. Configure analysis settings
    3. Click "🔄 Analyze" to start monitoring
    
    ### Supported Platforms:
    - Generic websites
    - Notion pages
    - Linear changelogs
    - And more...
    """)

if __name__ == "__main__":
    main()
