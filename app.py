import streamlit as st
import os
import uuid
from datetime import datetime, timedelta
import logging

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

# Set page configuration
st.set_page_config(
    page_title="🧠 Competitor Intelligence Dashboard",
    layout="wide",
    page_icon="🔍",
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
    openai_key = st.secrets.get("OPENAI_API_KEY", None)
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
    
    # Competitor selection (including custom ones)
    st.sidebar.subheader("Select Competitors")
    selected_competitors = []
    
    # Get all competitors (built-in + custom)
    all_competitors = COMPETITORS.copy()
    if 'custom_competitors' in st.session_state:
        all_competitors.extend(st.session_state.custom_competitors)
    
    for i, competitor in enumerate(all_competitors):
        label = competitor['name']
        if competitor.get('category') == 'custom':
            label += " (Custom)"
        
        if st.sidebar.checkbox(label, value=True, key=f"competitor_{i}"):
            selected_competitors.append(competitor)
    
    # Analysis settings
    st.sidebar.subheader("Analysis Settings")
    days_back = st.sidebar.slider("Days to analyze", 1, 30, 7)
    use_ai_summaries = st.sidebar.checkbox("Generate AI summaries", value=True)
    
    # Persona view selector with emojis
    st.sidebar.subheader("🎯 View Mode")
    view_mode = st.sidebar.selectbox(
        "Select Perspective",
        ["🧑‍🤝‍🧑 All Teams", "👩‍💼 PM View", "💰 Sales View", "🎨 Design View"],
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
    
    # New Competitor Addition Section
    st.sidebar.subheader("➕ Add New Competitor")
    with st.sidebar.expander("Add Custom Competitor"):
        new_name = st.text_input("Company Name", key="new_competitor_name")
        new_url = st.text_input("Changelog URL", key="new_competitor_url")
        new_platform = st.selectbox(
            "Platform Type",
            ["generic", "notion", "linear", "github", "appstore"],
            key="new_competitor_platform"
        )
        
        if st.button("➕ Add Competitor", key="add_competitor_btn"):
            if new_name and new_url:
                add_new_competitor(new_name, new_url, new_platform, db)
            else:
                st.error("Please provide both name and URL")
    
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
            # User-friendly error handling
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                st.warning(f"⚠️ AI summary temporarily unavailable for {competitor['name']} (API quota exceeded)")
            else:
                st.error(f"❌ Analysis failed for {competitor['name']}: {error_str}")
            logger.error(f"Error analyzing {competitor['name']}: {error_str}")
    
    progress_bar.empty()
    status_text.empty()
    
    # Store results in session state with view mode
    st.session_state.analysis_results = results
    st.session_state.view_mode = view_mode
    
    # Display trend of the week with enhanced styling
    if summarizer and results:
        summaries = [data['summary'] for data in results.values() if data.get('summary')]
        if summaries:
            trend = summarizer.analyze_trend_of_week(summaries)
            st.markdown(
                f"""
                <div style='background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 5px solid #2196F3; margin: 10px 0;'>
                    <h3 style='color: #1976D2; margin: 0;'>📈 Trend of the Week</h3>
                    <p style='font-size: 18px; font-weight: bold; color: #424242; margin: 5px 0 0 0;'>{trend}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
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
    
    # Detailed results with momentum leaderboard
    tabs = st.tabs(["📋 Summary View", "🏁 Momentum Leaderboard", "📊 Momentum Analysis", "🔍 Detailed View"])
    
    with tabs[0]:
        display_summary_view(filtered_results, view_mode)
    
    with tabs[1]:
        display_momentum_leaderboard(filtered_results)
    
    with tabs[2]:
        display_momentum_analysis(filtered_results)
    
    with tabs[3]:
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
    # Clean view mode string
    clean_view_mode = view_mode.replace("🧑‍🤝‍🧑 ", "").replace("👩‍💼 ", "").replace("💰 ", "").replace("🎨 ", "")
    
    if clean_view_mode == "All Teams":
        return results
    
    # For now, return all results but filtering is handled in display functions
    return results

def format_impact_score(score):
    """Format impact score with visual indicators."""
    if score >= 80:
        return f"🔥 {score}/100 (High)"
    elif score >= 60:
        return f"⚠️ {score}/100 (Moderate)"
    else:
        return f"💤 {score}/100 (Low)"

def display_momentum_leaderboard(results):
    """Display momentum leaderboard ranking competitors by impact score."""
    st.subheader("🏁 Momentum Leaderboard")
    
    # Extract impact scores
    leaderboard_data = []
    for name, data in results.items():
        summary = data.get('summary')
        if summary:
            impact_score = summary.get('impact_score', 50)
            confidence = summary.get('confidence_level', 'medium')
            leaderboard_data.append({
                'Competitor': name,
                'Impact Score': impact_score,
                'Confidence': confidence,
                'Visual': format_impact_score(impact_score)
            })
    
    if leaderboard_data:
        # Sort by impact score
        leaderboard_data.sort(key=lambda x: x['Impact Score'], reverse=True)
        
        # Add rank
        for i, item in enumerate(leaderboard_data):
            rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            item['Rank'] = rank_emoji
        
        # Display as table
        st.markdown("**Top Performers This Week:**")
        
        for item in leaderboard_data:
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                st.markdown(f"**{item['Rank']}**")
            with col2:
                st.markdown(f"**{item['Competitor']}**")
            with col3:
                st.markdown(item['Visual'])
        
        # Show bar chart
        st.markdown("---")
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame(leaderboard_data)
        fig = px.bar(
            df, 
            x='Competitor', 
            y='Impact Score',
            title='Momentum Scores by Competitor',
            color='Impact Score',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No momentum data available. Generate AI summaries to see the leaderboard.")

def add_new_competitor(name, url, platform, db):
    """Add a new competitor dynamically."""
    try:
        # Add to global competitors list (in-memory)
        new_competitor = {
            'name': name,
            'url': url,
            'platform': platform,
            'category': 'custom'
        }
        
        # Store in session state
        if 'custom_competitors' not in st.session_state:
            st.session_state.custom_competitors = []
        
        st.session_state.custom_competitors.append(new_competitor)
        
        # Save to database if available
        if db:
            try:
                db.save_competitor_analysis(name, {
                    'url': url,
                    'platform': platform,
                    'added_at': datetime.now().isoformat(),
                    'custom_competitor': True
                }, {'status': 'added'})
            except Exception as e:
                st.warning(f"Failed to save to database: {str(e)}")
        
        st.success(f"✅ Added {name} to competitor list!")
        
        # Trigger rerun to update the interface
        st.rerun()
        
    except Exception as e:
        st.error(f"Failed to add competitor: {str(e)}")

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
        
        # Clean view mode for comparison
        clean_view_mode = view_mode.replace("🧑‍🤝‍🧑 ", "").replace("👩‍💼 ", "").replace("💰 ", "").replace("🎨 ", "")
        
        if clean_view_mode == "Sales View":
            # Focus on pricing, market positioning, competitive advantages
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['pricing', 'plan', 'subscription', 'cost', 'revenue', 'market', 'customer', 'enterprise', 'tier'])]
            if not filtered_bullets:
                filtered_bullets = bullets[:2]  # Show at least some content
            bullets = filtered_bullets
        elif clean_view_mode == "Design View":
            # Focus on UI/UX, design, user experience
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['ui', 'ux', 'design', 'interface', 'user', 'visual', 'layout', 'experience', 'theme', 'mobile'])]
            if not filtered_bullets:
                filtered_bullets = bullets[:2]
            bullets = filtered_bullets
        elif clean_view_mode == "PM View":
            # Focus on features, strategy, roadmap
            filtered_bullets = [b for b in bullets if any(word in b.lower() 
                              for word in ['feature', 'product', 'launch', 'beta', 'roadmap', 'strategy', 'integration', 'api', 'workflow'])]
            if not filtered_bullets:
                filtered_bullets = bullets
            bullets = filtered_bullets
        
        # Display bullets
        for bullet in bullets:
            st.markdown(f"• {bullet}")
        
        # Strategic insight
        if strategic_insight:
            st.markdown(f"**💡 Strategic Insight:** {strategic_insight}")
        
        # Enhanced impact score with visual indicators
        impact_score = summary.get('impact_score', 50)
        impact_visual = format_impact_score(impact_score)
        st.markdown(f"**Impact Score:** {impact_visual}")
        st.progress(impact_score / 100)
        
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
