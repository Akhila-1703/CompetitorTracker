"""
Configuration file for competitor changelog sources and application settings.
Defines competitors to track, scraping parameters, and AI analysis settings.
"""

from typing import Dict, Any

# Configuration for competitor changelog sources
# Add or modify competitors here to customize tracking
COMPETITOR_CONFIGS = {
    "Linear": {
        "url": "https://linear.app/changelog",
        "platform": "linear",
        "description": "Project management and issue tracking platform",
        "homepage_url": "https://linear.app",
        "category": "Productivity"
    },
    "Notion": {
        "url": "https://www.notion.so/What-s-New-157765353f2c4705bd45474e5ba8b46c",
        "platform": "notion", 
        "description": "All-in-one workspace for notes, docs, and collaboration",
        "homepage_url": "https://www.notion.so",
        "category": "Productivity"
    },
    "Airtable": {
        "url": "https://blog.airtable.com/category/product-news/",
        "platform": "generic",
        "description": "Cloud collaboration service and database platform",
        "homepage_url": "https://airtable.com",
        "category": "Database"
    },
    "Figma": {
        "url": "https://www.figma.com/whats-new/",
        "platform": "generic",
        "description": "Web-based design and prototyping tool",
        "homepage_url": "https://www.figma.com",
        "category": "Design"
    },
    "Slack": {
        "url": "https://slack.com/releases/updates",
        "platform": "generic", 
        "description": "Business communication platform",
        "homepage_url": "https://slack.com",
        "category": "Communication"
    },
    "Discord": {
        "url": "https://discord.com/category/announcements",
        "platform": "generic",
        "description": "Voice, video and text communication service",
        "homepage_url": "https://discord.com",
        "category": "Communication"
    },
    "GitHub": {
        "url": "https://github.blog/changelog/",
        "platform": "generic",
        "description": "Git repository hosting service",
        "homepage_url": "https://github.com",
        "category": "Development"
    },
    "Vercel": {
        "url": "https://vercel.com/changelog",
        "platform": "generic",
        "description": "Cloud platform for static sites and serverless functions",
        "homepage_url": "https://vercel.com",
        "category": "Development"
    },
    "Miro": {
        "url": "https://miro.com/blog/category/product-news/",
        "platform": "generic",
        "description": "Online collaborative whiteboard platform",
        "homepage_url": "https://miro.com",
        "category": "Design"
    },
    "Canva": {
        "url": "https://www.canva.com/newsroom/product-updates/",
        "platform": "generic",
        "description": "Graphic design platform",
        "homepage_url": "https://www.canva.com",
        "category": "Design"
    }
}

# Rate limiting configuration
SCRAPING_CONFIG = {
    "min_request_interval": 1.0,  # Minimum seconds between web requests
    "min_api_interval": 1.0,      # Minimum seconds between API calls
    "max_content_length": 10000,  # Maximum characters to process per changelog
    "timeout": 30,                # Request timeout in seconds
    "retries": 3,                 # Number of retries for failed requests
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# OpenAI configuration
OPENAI_CONFIG = {
    "model": "gpt-4o",           # OpenAI model to use (newest as of May 13, 2024)
    "temperature": 0.3,          # Lower temperature for consistent outputs
    "max_tokens": 1000,          # Maximum tokens in response
    "request_timeout": 60,       # API request timeout in seconds
    "response_format": {"type": "json_object"}  # Structured JSON responses
}

# Output configuration
OUTPUT_CONFIG = {
    "default_filename": "weekly_digest.md",
    "include_metadata": True,
    "include_timestamps": True,
    "sort_by_confidence": True,
    "personas": ["pm", "sales", "design"]
}

# Momentum scoring configuration
MOMENTUM_CONFIG = {
    "category_scores": {
        'AI': 3,           # High value for AI-related updates
        'Feature': 2,      # Standard feature updates
        'UI': 1,           # UI/UX improvements
        'Pricing': 2,      # Pricing strategy changes
        'Messaging': 1,    # Communication/messaging updates
        'Integration': 2,  # Third-party integrations
        'Enterprise': 3,   # Enterprise features
        'Security': 2      # Security improvements
    },
    "update_multiplier": 10,      # Base score per update
    "ai_bonus": 5,               # Additional bonus for AI mentions
    "max_score": 100             # Maximum momentum score
}

# Trend analysis configuration
TREND_ANALYSIS_CONFIG = {
    "trend_patterns": {
        'ai': ['ai', 'artificial intelligence', 'machine learning', 'automation', 'gpt', 'llm'],
        'mobile': ['mobile', 'app', 'android', 'ios', 'responsive'],
        'integration': ['integration', 'api', 'webhook', 'connect', 'sync'],
        'ui_ux': ['ui', 'ux', 'interface', 'design', 'redesign', 'visual', 'theme'],
        'enterprise': ['enterprise', 'business', 'team', 'workspace', 'organization'],
        'pricing': ['pricing', 'plan', 'subscription', 'billing', 'tier', 'cost'],
        'onboarding': ['onboarding', 'setup', 'getting started', 'tutorial', 'welcome'],
        'collaboration': ['collaboration', 'sharing', 'comments', 'real-time', 'co-edit'],
        'security': ['security', 'privacy', 'encryption', 'compliance', 'sso', '2fa'],
        'performance': ['performance', 'speed', 'optimization', 'faster', 'efficiency'],
        'analytics': ['analytics', 'insights', 'reports', 'metrics', 'dashboard'],
        'accessibility': ['accessibility', 'a11y', 'screen reader', 'keyboard', 'contrast']
    },
    "minimum_mentions": 2,        # Minimum mentions to consider a trend
    "trend_threshold": 0.3        # Percentage of companies needed to identify trend
}

# Screenshot comparison configuration
SCREENSHOT_CONFIG = {
    "viewport_size": {"width": 1920, "height": 1080},
    "diff_threshold": 0.1,       # Percentage difference threshold for change detection
    "screenshot_directory": "screenshots",
    "comparison_formats": ["png", "jpg"],
    "retention_days": 30,        # Days to keep old screenshots
    "capture_timeout": 30        # Screenshot capture timeout in seconds
}

# Notification configuration
NOTIFICATION_CONFIG = {
    "slack": {
        "max_message_length": 4000,
        "max_companies_per_digest": 10,
        "include_momentum_leaderboard": True,
        "include_trend_analysis": True
    },
    "email": {
        "max_recipients": 50,
        "include_attachments": True
    },
    "discord": {
        "max_message_length": 2000,
        "use_embeds": True
    }
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    "max_competitors_display": 20,
    "default_analysis_days": 7,
    "confidence_thresholds": ["low", "medium", "high"],
    "chart_colors": {
        "high_momentum": "#FF6B6B",
        "medium_momentum": "#4ECDC4", 
        "low_momentum": "#45B7D1",
        "minimal_momentum": "#96CEB4"
    },
    "export_formats": ["markdown", "json", "csv"]
}

# Application metadata
APP_CONFIG = {
    "name": "Competitor Intelligence Dashboard",
    "version": "1.0.0",
    "description": "AI-powered competitor analysis and monitoring dashboard",
    "author": "Competitor Intelligence Team",
    "support_email": "support@competitorintel.com",
    "github_repo": "https://github.com/company/competitor-intelligence",
    "documentation_url": "https://docs.competitorintel.com"
}

def get_competitor_by_name(name: str) -> Dict[str, Any]:
    """
    Get competitor configuration by name.
    
    Args:
        name: Competitor name
        
    Returns:
        Competitor configuration dictionary or empty dict if not found
    """
    return COMPETITOR_CONFIGS.get(name, {})

def get_competitors_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all competitors in a specific category.
    
    Args:
        category: Category name (e.g., "Productivity", "Design")
        
    Returns:
        Dictionary of competitors in the specified category
    """
    return {
        name: config for name, config in COMPETITOR_CONFIGS.items()
        if config.get('category') == category
    }

def get_all_categories() -> list:
    """
    Get list of all available competitor categories.
    
    Returns:
        List of unique categories
    """
    categories = set()
    for config in COMPETITOR_CONFIGS.values():
        if 'category' in config:
            categories.add(config['category'])
    return sorted(list(categories))

def validate_competitor_config(config: Dict[str, Any]) -> bool:
    """
    Validate a competitor configuration dictionary.
    
    Args:
        config: Competitor configuration to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['url', 'platform', 'description']
    return all(field in config for field in required_fields)
