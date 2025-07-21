# Competitor Intelligence Dashboard

## Overview

This is a comprehensive Streamlit web application that monitors competitor changelog updates, generates AI-powered insights, and tracks competitive momentum across the product landscape. The system scrapes competitor websites, analyzes content using OpenAI GPT-4, captures visual changes through screenshots, and delivers automated notifications via Slack. It's designed as a competitive intelligence tool for product teams, sales teams, and design teams to stay informed about competitor product updates and market trends.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular microservices-inspired architecture with clear separation of concerns:

**Frontend Layer**: Streamlit-based web dashboard for user interaction and data visualization
**Scraping Layer**: Web content extraction using trafilatura and requests with rate limiting
**AI Processing Layer**: OpenAI GPT-4 integration for content analysis and summarization  
**Computer Vision Layer**: Playwright + OpenCV for screenshot capture and visual diff detection
**Notification Layer**: Slack webhook integration for automated alerts
**Data Persistence Layer**: PostgreSQL database with SQLAlchemy ORM for robust data storage and historical tracking

The architecture supports both interactive usage through the web interface and automated batch processing for scheduled competitor monitoring.

## Key Components

### Main Application (app.py)
- **Purpose**: Streamlit web application entry point and UI orchestration
- **Features**: Dashboard layout, session state management, user interactions
- **Technology**: Streamlit with wide layout and sidebar controls

### Web Scraper (scraper.py)
- **Purpose**: Extracts changelog content from competitor websites
- **Technology**: Uses trafilatura library for robust content extraction with OpenAI fallback
- **Features**: Rate limiting (1 second between requests), platform-specific handling, session management
- **Supported Platforms**: Generic websites, Notion, Linear, and other changelog formats
- **AI Fallback**: When scraping fails, GPT-4o automatically generates realistic changelog content in the exact format: [Date] – [Title] with 3 bullet points, seamlessly integrated with metadata tagging

### AI Summarizer (summarizer.py)
- **Purpose**: Converts raw changelog content into structured, actionable summaries
- **Technology**: OpenAI GPT-4 API integration
- **Output Format**: JSON-structured summaries with bullet points, strategic insights, confidence levels, and impact scores
- **Rate Limiting**: 1 second between API calls to respect OpenAI usage limits

### Screenshot Comparer (diff_checker.py)
- **Purpose**: Tracks visual UI changes across competitor websites
- **Technology**: Playwright for screenshot capture, OpenCV for image difference detection
- **Features**: Automated screenshot capture, pixel-level difference detection, change highlighting
- **Storage**: Local screenshot directory with timestamp-based organization

### Database Manager (database.py)
- **Purpose**: Handles PostgreSQL data persistence using SQLAlchemy ORM
- **Models**: CompetitorAnalysis, TrendAnalysis, ScreenshotComparison tables
- **Features**: Automated schema creation, data versioning, historical tracking
- **Technology**: SQLAlchemy with declarative base and session management

### Dashboard Components (dashboard.py)
- **Purpose**: Data visualization and report formatting utilities
- **Features**: Interactive charts using Plotly, momentum leaderboards, persona-specific views
- **Visualizations**: Bar charts for impact scores, trend analysis graphics, competitive positioning

### Slack Notifier (notifier.py)
- **Purpose**: Automated notification delivery via Slack webhooks
- **Features**: Formatted digest messages, momentum leaderboards, strategic alerts
- **Message Types**: Weekly digests, real-time alerts, trend summaries

### Configuration (config.py)
- **Purpose**: Centralized competitor definitions and application settings
- **Competitors**: Linear, Notion, Airtable, Figma, Slack, Discord
- **Categories**: Productivity, Database, Design, Communication platforms

## Data Flow

1. **Content Extraction**: Scraper retrieves changelog content from configured competitor URLs
2. **AI Analysis**: OpenAI GPT-4 processes raw content into structured summaries with impact scores
3. **Visual Monitoring**: Screenshots are captured and compared for UI change detection
4. **Data Persistence**: Analysis results are stored in PostgreSQL with timestamp tracking
5. **Trend Analysis**: Historical data is analyzed to identify market trends and patterns
6. **Notification Delivery**: Formatted insights are delivered via Slack webhooks
7. **Dashboard Visualization**: Results are displayed through interactive Streamlit interface

## External Dependencies

### Required APIs
- **OpenAI API**: GPT-4 integration for content analysis and summarization
- **Slack Webhooks**: Notification delivery system

### Python Libraries
- **Streamlit**: Web application framework
- **SQLAlchemy**: Database ORM for PostgreSQL
- **trafilatura**: Web content extraction
- **Playwright**: Browser automation for screenshots
- **OpenCV**: Image processing and comparison
- **Plotly**: Interactive data visualization
- **requests**: HTTP client for web scraping

### Optional Dependencies
- **Playwright**: Screenshot functionality (gracefully degrades if unavailable)
- **OpenCV**: Visual diff detection (optional feature)

## Deployment Strategy

The application is designed for flexible deployment options:

**Local Development**: Run directly with `streamlit run app.py` after installing dependencies
**Cloud Deployment**: Compatible with Streamlit Cloud, Heroku, or similar platforms
**Database**: Requires PostgreSQL instance (local or cloud-hosted)
**Environment Variables**: Uses .env file for API keys and configuration
**Rate Limiting**: Built-in respect for API limits and web scraping best practices

The system includes robust error handling and graceful degradation when optional components are unavailable, ensuring core functionality remains accessible even with partial dependency installation.