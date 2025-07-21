"""
Configuration management for the Competitor Intelligence Dashboard.
Centralizes competitor definitions and application settings.
"""

import os
from typing import List, Dict, Any

# Competitor configurations
COMPETITORS = [
    {
        "name": "Linear",
        "url": "https://linear.app/changelog",
        "platform": "linear",
        "description": "Issue tracking and project management tool",
        "homepage": "https://linear.app",
        "category": "Project Management"
    },
    {
        "name": "Notion",
        "url": "https://www.notion.so/What-s-New-157765353f2c4705bd45474e5ba8b46c",
        "platform": "notion",
        "description": "All-in-one workspace for notes, docs, and collaboration",
        "homepage": "https://notion.so",
        "category": "Productivity"
    },
    {
        "name": "Airtable",
        "url": "https://blog.airtable.com/category/product/",
        "platform": "generic",
        "description": "Cloud-based database and collaboration platform",
        "homepage": "https://airtable.com",
        "category": "Database"
    },
    {
        "name": "Figma",
        "url": "https://www.figma.com/blog/category/product/",
        "platform": "generic",
        "description": "Collaborative design and prototyping tool",
        "homepage": "https://figma.com",
        "category": "Design"
    },
    {
        "name": "Slack",
        "url": "https://slack.com/blog/category/product",
        "platform": "generic",
        "description": "Business communication and collaboration platform",
        "homepage": "https://slack.com",
        "category": "Communication"
    },
    {
        "name": "Discord",
        "url": "https://discord.com/category/product",
        "platform": "generic",
        "description": "Communication platform for communities and teams",
        "homepage": "https://discord.com",
        "category": "Communication"
    },
    {
        "name": "Asana",
        "url": "https://blog.asana.com/category/product/",
        "platform": "generic",
        "description": "Work management and team collaboration platform",
        "homepage": "https://asana.com",
        "category": "Project Management"
    },
    {
        "name": "Trello",
        "url": "https://blog.trello.com/topic/product-features",
        "platform": "generic",
        "description": "Visual project management tool with boards and cards",
        "homepage": "https://trello.com",
        "category": "Project Management"
    }
]

# Application settings
APP_SETTINGS = {
    "default_analysis_days": 7,
    "max_content_length": 10000,
    "rate_limit_seconds": 1.0,
    "max_competitors_per_analysis": 10,
    "screenshot_timeout": 30,
    "database_timeout": 10
}

# API Configuration
API_CONFIG = {
    "openai": {
        "model": "gpt-4o",
        "max_tokens": 1000,
        "temperature": 0.3,
        "rate_limit": 1.0
    },
    "slack": {
        "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
        "timeout": 10
    }
}

# Database configuration
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL"),
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600
}

def get_competitor_by_name(name: str) -> Dict[str, Any]:
    """
    Get competitor configuration by name.
    
    Args:
        name: Competitor name to search for
        
    Returns:
        Competitor configuration dictionary or None if not found
    """
    for competitor in COMPETITORS:
        if competitor["name"].lower() == name.lower():
            return competitor
    return None

def get_competitors_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all competitors in a specific category.
    
    Args:
        category: Category to filter by
        
    Returns:
        List of competitor configurations
    """
    return [comp for comp in COMPETITORS if comp.get("category", "").lower() == category.lower()]

def validate_config() -> List[str]:
    """
    Validate application configuration and return any issues.
    
    Returns:
        List of configuration issues (empty if all valid)
    """
    issues = []
    
    # Check required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY environment variable not set")
    
    # Validate competitor configurations
    for competitor in COMPETITORS:
        required_fields = ["name", "url", "platform"]
        for field in required_fields:
            if field not in competitor:
                issues.append(f"Competitor '{competitor.get('name', 'Unknown')}' missing required field: {field}")
    
    return issues
