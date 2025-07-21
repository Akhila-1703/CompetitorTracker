"""
Competitor Intelligence Dashboard - Streamlit Web Application
Main entry point for the dashboard application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Import custom modules
from scraper import ChangelogScraper
from summarizer import ChangelogSummarizer
from diff_checker import ScreenshotComparer
from dashboard import DashboardComponents
from notifier import SlackNotifier
from config import COMPETITOR_CONFIGS, SCRAPING_CONFIG, OPENAI_CONFIG
from utils import save_screenshot, load_historical_data, save_data
from database import get_db_manager, init_database

# Page configuration
st.set_page_config(
    page_title="Competitor Intelligence Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = []
if 'momentum_scores' not in st.session_state:
    st.session_state.momentum_scores = {}
if 'trend_analysis' not in st.session_state:
    st.session_state.trend_analysis = ""
if 'screenshot_comparisons' not in st.session_state:
    st.session_state.screenshot_comparisons = {}
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# Initialize database once per session
if not st.session_state.db_initialized:
    try:
        init_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        st.stop()

def main():
    """Main application entry point"""
    
    # Title and header
    st.title("🔍 Competitor Intelligence Dashboard")
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key validation
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            st.error("⚠️ OpenAI API Key not found in environment variables")
            st.stop()
        else:
            st.success("✅ OpenAI API Key configured")
        
        st.markdown("---")
        
        # Competitor selection
        st.subheader("🏢 Competitors")
        selected_competitors = []
        
        # Default competitors from config
        default_competitors = list(COMPETITOR_CONFIGS.keys())
        for comp in default_competitors:
            if st.checkbox(f"{comp}", value=True, key=f"default_{comp}"):
                selected_competitors.append({
                    'name': comp,
                    'url': COMPETITOR_CONFIGS[comp]['url'],
                    'platform': COMPETITOR_CONFIGS[comp]['platform']
                })
        
        # Custom competitor addition
        st.subheader("➕ Add Custom Competitor")
        with st.expander("Add New Competitor"):
            custom_name = st.text_input("Company Name", key="custom_name")
            custom_url = st.text_input("Changelog URL", key="custom_url")
            custom_platform = st.selectbox("Platform Type", ["generic", "notion", "linear"], key="custom_platform")
            
            if st.button("Add Competitor", key="add_custom"):
                if custom_name and custom_url:
                    selected_competitors.append({
                        'name': custom_name,
                        'url': custom_url,
                        'platform': custom_platform
                    })
                    st.success(f"Added {custom_name}")
        
        st.markdown("---")
        
        # Feature toggles
        st.subheader("🔧 Features")
        enable_screenshots = st.checkbox("📷 Visual UI Tracking", value=False)
        enable_slack = st.checkbox("💬 Slack Delivery", value=False)
        
        if enable_slack:
            slack_webhook = st.text_input("Slack Webhook URL", type="password")
        
        # Analysis parameters
        st.subheader("📊 Analysis Settings")
        analysis_days = st.slider("Analysis Period (days)", 1, 30, 7)
        confidence_threshold = st.select_slider(
            "Confidence Threshold", 
            options=["low", "medium", "high"], 
            value="medium"
        )
        
        st.markdown("---")
        
        # Database statistics
        st.subheader("💾 Database Status")
        try:
            db = get_db_manager()
            recent_analyses = db.get_recent_analyses(days=7, limit=5)
            st.metric("Recent Analyses (7 days)", len(recent_analyses))
            
            if recent_analyses:
                with st.expander("Recent Activity"):
                    for analysis in recent_analyses[:3]:
                        st.write(f"• {analysis['competitor']} - {analysis['analysis_date'][:10]}")
        except Exception as e:
            st.error(f"Database connection issue: {str(e)}")
        
        st.markdown("---")
        
        # Action buttons
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            run_competitor_analysis(selected_competitors, analysis_days, enable_screenshots, confidence_threshold)
        
        if st.button("📥 Load Historical Data", use_container_width=True):
            load_historical_analysis()
        
        if st.button("🗑️ Clear Data", use_container_width=True):
            clear_session_data()

    # Main dashboard content
    if st.session_state.processed_data:
        display_dashboard()
    else:
        display_welcome_screen()

def run_competitor_analysis(competitors, days, enable_screenshots, confidence_threshold):
    """Run the complete competitor analysis pipeline"""
    
    if not competitors:
        st.warning("⚠️ Please select at least one competitor")
        return
    
    # Progress tracking
    progress_container = st.container()
    
    with progress_container:
        st.subheader("🔄 Analysis Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize components
        scraper = ChangelogScraper(verbose=True)
        summarizer = ChangelogSummarizer(os.getenv("OPENAI_API_KEY"), verbose=True)
        screenshot_comparer = ScreenshotComparer() if enable_screenshots else None
        
        total_steps = len(competitors) * (3 if enable_screenshots else 2) + 2
        current_step = 0
        
        processed_summaries = []
        screenshot_results = {}
        
        # Process each competitor
        for i, competitor in enumerate(competitors):
            try:
                # Step 1: Scrape changelog
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                status_text.text(f"📥 Scraping {competitor['name']} changelog...")
                
                changelog_content = scraper.scrape_changelog(
                    competitor['url'], 
                    competitor['platform']
                )
                
                if not changelog_content or "Error" in changelog_content:
                    st.error(f"❌ Failed to scrape {competitor['name']}: {changelog_content}")
                    continue
                
                # Step 2: Generate AI summary
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                status_text.text(f"🤖 Analyzing {competitor['name']} with AI...")
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                summary_data = summarizer.summarize_changelog(
                    competitor['name'],
                    changelog_content,
                    start_date,
                    end_date
                )
                
                if summary_data:
                    processed_summaries.append(summary_data)
                    st.success(f"✅ Analyzed {competitor['name']}")
                
                # Step 3: Screenshot comparison (if enabled)
                if enable_screenshots and screenshot_comparer:
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
                    status_text.text(f"📷 Capturing {competitor['name']} UI...")
                    
                    # Extract base URL for screenshots
                    base_url = competitor['url'].split('/changelog')[0] if '/changelog' in competitor['url'] else competitor['url']
                    
                    screenshot_result = screenshot_comparer.capture_and_compare(
                        base_url, 
                        competitor['name']
                    )
                    
                    if screenshot_result:
                        screenshot_results[competitor['name']] = screenshot_result
                
            except Exception as e:
                st.error(f"❌ Error processing {competitor['name']}: {str(e)}")
                continue
        
        # Generate trend analysis
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        status_text.text("📈 Analyzing market trends...")
        
        if processed_summaries:
            trend_analysis = analyze_weekly_trends(processed_summaries)
            momentum_scores = calculate_all_momentum_scores(processed_summaries)
            
            # Store results in session state
            st.session_state.processed_data = processed_summaries
            st.session_state.momentum_scores = momentum_scores
            st.session_state.trend_analysis = trend_analysis
            st.session_state.screenshot_comparisons = screenshot_results
            
            # Save to database
            try:
                db = get_db_manager()
                
                # Save individual competitor analyses
                for summary in processed_summaries:
                    # Add momentum score to summary data
                    summary['momentum_score'] = momentum_scores.get(summary['competitor'], 0)
                    db.save_competitor_analysis(summary)
                
                # Save trend analysis
                if trend_analysis:
                    trend_data = {
                        'dominant_trend': trend_analysis.split('**')[1].split('**')[0] if '**' in trend_analysis else 'general',
                        'description': trend_analysis,
                        'companies_count': len(processed_summaries),
                        'raw_data': {
                            'momentum_scores': momentum_scores,
                            'summaries_count': len(processed_summaries)
                        }
                    }
                    db.save_trend_analysis(trend_data)
                
                # Save screenshot comparisons
                for company, screenshot_data in screenshot_results.items():
                    screenshot_data['company'] = company
                    db.save_screenshot_comparison(screenshot_data)
                    
                st.success("💾 Data saved to database")
                
            except Exception as e:
                st.warning(f"⚠️ Could not save to database: {str(e)}")
            
            # Final step
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            status_text.text("✅ Analysis complete!")
            
            # Save data for historical tracking (file backup)
            save_data({
                'timestamp': datetime.now().isoformat(),
                'summaries': processed_summaries,
                'momentum_scores': momentum_scores,
                'trend_analysis': trend_analysis,
                'screenshot_comparisons': screenshot_results
            })
            
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ No summaries generated. Please check your configuration.")

def display_dashboard():
    """Display the main dashboard with all analysis results"""
    
    # Dashboard header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader("📊 Competitor Intelligence Dashboard")
    with col2:
        st.metric("Competitors Analyzed", len(st.session_state.processed_data))
    with col3:
        if st.button("📄 Export Digest"):
            export_digest()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Summary View", 
        "📈 Momentum Board", 
        "🔍 Trend Analysis", 
        "📷 Visual Changes",
        "👥 Persona Views"
    ])
    
    with tab1:
        display_summary_view()
    
    with tab2:
        display_momentum_board()
    
    with tab3:
        display_trend_analysis()
    
    with tab4:
        display_visual_changes()
    
    with tab5:
        display_persona_views()

def display_summary_view():
    """Display competitor summaries in card format"""
    st.subheader("🏢 Competitor Updates")
    
    for i, summary in enumerate(st.session_state.processed_data):
        with st.container():
            # Company header
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {summary['competitor']}")
            with col2:
                confidence_color = {
                    'high': '🟢', 
                    'medium': '🟡', 
                    'low': '🔴'
                }.get(summary.get('confidence_level', 'medium'), '🟡')
                st.markdown(f"{confidence_color} {summary.get('confidence_level', 'medium').title()} Confidence")
            with col3:
                momentum = st.session_state.momentum_scores.get(summary['competitor'], 0)
                st.metric("Momentum", momentum)
            
            # Summary bullets
            st.markdown("**Key Updates:**")
            for bullet in summary.get('summary_bullets', []):
                st.markdown(f"• {bullet}")
            
            # Strategic insight
            if summary.get('strategic_insight'):
                st.info(f"💡 **Strategic Insight:** {summary['strategic_insight']}")
            
            st.markdown("---")

def display_momentum_board():
    """Display momentum scores and leaderboard"""
    st.subheader("🏁 Momentum Leaderboard")
    
    if st.session_state.momentum_scores:
        # Create DataFrame for visualization
        df = pd.DataFrame([
            {'Company': company, 'Momentum Score': score}
            for company, score in st.session_state.momentum_scores.items()
        ]).sort_values('Momentum Score', ascending=False)
        
        # Bar chart
        fig = px.bar(
            df, 
            x='Company', 
            y='Momentum Score',
            title="Competitor Momentum Scores",
            color='Momentum Score',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Leaderboard table
        st.subheader("📊 Detailed Rankings")
        df['Rank'] = range(1, len(df) + 1)
        st.dataframe(
            df[['Rank', 'Company', 'Momentum Score']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No momentum data available. Run an analysis first.")

def display_trend_analysis():
    """Display trend analysis and insights"""
    st.subheader("📈 Market Trend Analysis")
    
    if st.session_state.trend_analysis:
        st.markdown(st.session_state.trend_analysis)
        
        # Additional trend visualizations
        if st.session_state.processed_data:
            # Extract categories from summaries
            categories = {}
            for summary in st.session_state.processed_data:
                for bullet in summary.get('summary_bullets', []):
                    # Simple category extraction (this could be enhanced)
                    if 'AI' in bullet.upper():
                        categories['AI'] = categories.get('AI', 0) + 1
                    elif 'UI' in bullet.upper():
                        categories['UI'] = categories.get('UI', 0) + 1
                    elif 'FEATURE' in bullet.upper():
                        categories['Feature'] = categories.get('Feature', 0) + 1
                    else:
                        categories['Other'] = categories.get('Other', 0) + 1
            
            if categories:
                # Pie chart of categories
                fig = px.pie(
                    values=list(categories.values()),
                    names=list(categories.keys()),
                    title="Update Categories Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trend analysis available. Run an analysis first.")

def display_visual_changes():
    """Display screenshot comparisons and visual changes"""
    st.subheader("📷 Visual UI Changes")
    
    if st.session_state.screenshot_comparisons:
        for company, comparison in st.session_state.screenshot_comparisons.items():
            st.markdown(f"### {company}")
            
            if comparison.get('has_changes'):
                st.warning(f"🔄 UI changes detected for {company}")
                
                # Display side-by-side comparison if available
                if comparison.get('current_screenshot') and comparison.get('previous_screenshot'):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Previous**")
                        st.image(comparison['previous_screenshot'], use_column_width=True)
                    with col2:
                        st.markdown("**Current**")
                        st.image(comparison['current_screenshot'], use_column_width=True)
                
                if comparison.get('diff_image'):
                    st.markdown("**Changes Highlighted**")
                    st.image(comparison['diff_image'], use_column_width=True)
            else:
                st.success(f"✅ No UI changes detected for {company}")
            
            st.markdown("---")
    else:
        st.info("No visual comparison data available. Enable UI tracking and run an analysis.")

def display_persona_views():
    """Display persona-specific digest views"""
    st.subheader("👥 Persona-Specific Views")
    
    persona_tabs = st.tabs(["👩‍💼 PM View", "💰 Sales View", "🎨 Design View"])
    
    with persona_tabs[0]:
        display_pm_view()
    
    with persona_tabs[1]:
        display_sales_view()
    
    with persona_tabs[2]:
        display_design_view()

def display_pm_view():
    """Display PM-focused view"""
    st.markdown("### 👩‍💼 Product Manager View")
    
    for summary in st.session_state.processed_data:
        st.markdown(f"**{summary['competitor']}**")
        st.markdown("🎯 **PM Focus:** Evaluate strategic response and resource allocation.")
        
        for bullet in summary.get('summary_bullets', []):
            st.markdown(f"• {bullet}")
        
        if summary.get('strategic_insight'):
            st.info(f"📊 **Strategic Alert:** {summary['strategic_insight']}")
        
        st.markdown("---")

def display_sales_view():
    """Display Sales-focused view"""
    st.markdown("### 💰 Sales View")
    
    for summary in st.session_state.processed_data:
        st.markdown(f"**{summary['competitor']}**")
        st.markdown("📌 **Sales Focus:** Update objection handling and competitive positioning.")
        
        for bullet in summary.get('summary_bullets', []):
            # Add sales-specific context
            st.markdown(f"• 🔥 {bullet} - *New competitive differentiator*")
        
        if summary.get('strategic_insight'):
            st.info(f"📊 **Strategic Alert:** {summary['strategic_insight']}")
        
        st.markdown("---")

def display_design_view():
    """Display Design-focused view"""
    st.markdown("### 🎨 Design View")
    
    for summary in st.session_state.processed_data:
        st.markdown(f"**{summary['competitor']}**")
        st.markdown("📌 **Design Focus:** Monitor UX trends and interaction patterns.")
        
        for bullet in summary.get('summary_bullets', []):
            # Add design-specific context
            if 'UI' in bullet.upper():
                st.markdown(f"• 🎨 {bullet} - *Analyze UX patterns*")
            else:
                st.markdown(f"• ⚡ {bullet} - *Consider interaction design*")
        
        if summary.get('strategic_insight'):
            st.info(f"📊 **Strategic Alert:** {summary['strategic_insight']}")
        
        st.markdown("---")

def display_welcome_screen():
    """Display welcome screen when no data is available"""
    st.markdown("""
    ## 👋 Welcome to the Competitor Intelligence Dashboard
    
    This dashboard helps you track and analyze competitor changelog updates using AI-powered insights.
    
    ### 🚀 Get Started:
    1. **Select competitors** from the sidebar or add custom ones
    2. **Configure analysis settings** (time period, features)
    3. **Click "Run Analysis"** to start processing
    
    ### 📊 Features:
    - **AI-Powered Summaries**: GPT-4 analyzes changelogs for key insights
    - **Momentum Tracking**: Score competitors based on update frequency and impact
    - **Trend Analysis**: Identify market patterns across competitors
    - **Visual UI Tracking**: Screenshot comparison for UI changes
    - **Multi-Persona Views**: Tailored insights for PM, Sales, and Design teams
    
    ### 🔧 Configuration:
    Use the sidebar to configure your analysis parameters and select competitors to track.
    """)

def load_historical_analysis():
    """Load historical analysis data from database"""
    try:
        db = get_db_manager()
        
        # Load recent analyses from database
        recent_analyses = db.get_recent_analyses(days=30, limit=50)
        
        if recent_analyses:
            # Convert database format to session state format
            processed_summaries = []
            momentum_scores = {}
            
            for analysis in recent_analyses:
                processed_summaries.append({
                    'competitor': analysis['competitor'],
                    'summary_bullets': analysis['summary_bullets'],
                    'strategic_insight': analysis['strategic_insight'],
                    'confidence_level': analysis['confidence_level'],
                    'categories': analysis['categories'],
                    'impact_score': analysis['impact_score'],
                    'analysis_date': analysis['analysis_date'],
                    'url': analysis['url'],
                    'platform': analysis['platform']
                })
                momentum_scores[analysis['competitor']] = analysis['momentum_score']
            
            # Update session state
            st.session_state.processed_data = processed_summaries
            st.session_state.momentum_scores = momentum_scores
            
            # Generate trend analysis from loaded data
            if processed_summaries:
                trend_analysis = analyze_weekly_trends(processed_summaries)
                st.session_state.trend_analysis = trend_analysis
            
            st.success(f"✅ Loaded {len(recent_analyses)} historical analyses from database")
            st.rerun()
        else:
            # Fallback to file-based historical data
            historical_data = load_historical_data()
            if historical_data:
                st.session_state.processed_data = historical_data.get('summaries', [])
                st.session_state.momentum_scores = historical_data.get('momentum_scores', {})
                st.session_state.trend_analysis = historical_data.get('trend_analysis', "")
                st.session_state.screenshot_comparisons = historical_data.get('screenshot_comparisons', {})
                st.success("✅ Historical data loaded from files")
                st.rerun()
            else:
                st.info("No historical data available in database or files")
    except Exception as e:
        st.error(f"❌ Error loading historical data: {str(e)}")

def clear_session_data():
    """Clear all session data"""
    st.session_state.processed_data = []
    st.session_state.momentum_scores = {}
    st.session_state.trend_analysis = ""
    st.session_state.screenshot_comparisons = {}
    st.success("✅ Data cleared")
    st.rerun()

def export_digest():
    """Export analysis as markdown digest"""
    try:
        from dashboard import DashboardComponents
        dashboard_comp = DashboardComponents()
        
        # Generate markdown digest
        digest_content = dashboard_comp.create_digest(
            st.session_state.processed_data,
            st.session_state.trend_analysis,
            st.session_state.momentum_scores
        )
        
        # Download button
        st.download_button(
            label="📄 Download Markdown Digest",
            data=digest_content,
            file_name=f"competitor_digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
        
        st.success("✅ Digest ready for download")
    except Exception as e:
        st.error(f"❌ Error generating digest: {str(e)}")

def analyze_weekly_trends(summaries):
    """Analyze trends across competitor summaries"""
    if not summaries:
        return "No trend data available."
    
    # Extract all text for analysis
    all_text = " ".join([
        " ".join(summary.get('summary_bullets', [])) + " " + summary.get('strategic_insight', '')
        for summary in summaries
    ]).lower()
    
    # Define trend patterns
    trend_patterns = {
        'ai': ['ai', 'artificial intelligence', 'machine learning', 'automation'],
        'mobile': ['mobile', 'app', 'android', 'ios'],
        'integration': ['integration', 'api', 'webhook', 'connect'],
        'ui_ux': ['ui', 'ux', 'interface', 'design', 'redesign', 'visual'],
        'enterprise': ['enterprise', 'business', 'team', 'workspace'],
        'collaboration': ['collaboration', 'sharing', 'comments', 'real-time']
    }
    
    # Count occurrences
    trend_counts = {}
    for trend_name, keywords in trend_patterns.items():
        count = sum(all_text.count(keyword) for keyword in keywords)
        if count > 0:
            trend_counts[trend_name] = count
    
    if not trend_counts:
        return "\n📈 **Trend of the Week:** No dominant trends detected across competitors.\n"
    
    # Find dominant trend
    dominant_trend = max(trend_counts, key=trend_counts.get)
    
    trend_descriptions = {
        'ai': 'AI-powered features',
        'mobile': 'Mobile experience improvements',
        'integration': 'Third-party integrations',
        'ui_ux': 'UI/UX redesigns',
        'enterprise': 'Enterprise-focused updates',
        'collaboration': 'Collaboration enhancements'
    }
    
    trend_desc = trend_descriptions.get(dominant_trend, dominant_trend.replace('_', '/'))
    companies_count = len([s for s in summaries if any(keyword in " ".join(s.get('summary_bullets', [])).lower() for keyword in trend_patterns[dominant_trend])])
    
    return f"\n📈 **Trend of the Week:** {trend_desc} is the common theme among {companies_count} competitors.\n"

def calculate_all_momentum_scores(summaries):
    """Calculate momentum scores for all competitors"""
    momentum_scores = {}
    
    for summary in summaries:
        company = summary['competitor']
        bullets = summary.get('summary_bullets', [])
        
        # Simple scoring algorithm
        base_score = len(bullets) * 10  # Base score from number of updates
        
        # Category bonuses
        ai_bonus = sum(5 for bullet in bullets if 'ai' in bullet.lower())
        feature_bonus = sum(3 for bullet in bullets if any(word in bullet.lower() for word in ['feature', 'new', 'launch']))
        
        total_score = min(100, base_score + ai_bonus + feature_bonus)
        momentum_scores[company] = total_score
    
    return momentum_scores

if __name__ == "__main__":
    main()
