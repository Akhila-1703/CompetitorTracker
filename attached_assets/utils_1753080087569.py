"""
Utility functions for the Competitor Intelligence Dashboard.
Includes data persistence, file handling, and helper functions.
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory for persistence
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def save_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save analysis data to persistent storage.
    
    Args:
        data: Data dictionary to save
        filename: Optional custom filename
        
    Returns:
        Path to saved file
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.json"
        
        filepath = DATA_DIR / filename
        
        # Ensure data is JSON serializable
        serializable_data = make_json_serializable(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise

def load_data(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load analysis data from persistent storage.
    
    Args:
        filename: Name of file to load
        
    Returns:
        Data dictionary or None if not found/error
    """
    try:
        filepath = DATA_DIR / filename
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Data loaded from {filepath}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None

def load_historical_data(days_back: int = 30) -> Optional[Dict[str, Any]]:
    """
    Load the most recent historical analysis data.
    
    Args:
        days_back: Number of days to look back for data
        
    Returns:
        Most recent analysis data or None if not found
    """
    try:
        # Get all analysis files
        analysis_files = list(DATA_DIR.glob("analysis_*.json"))
        
        if not analysis_files:
            return None
        
        # Sort by modification time (newest first)
        analysis_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Load the most recent file
        most_recent = analysis_files[0]
        return load_data(most_recent.name)
        
    except Exception as e:
        logger.error(f"Error loading historical data: {str(e)}")
        return None

def save_screenshot(image_data: bytes, company: str, timestamp: Optional[datetime] = None) -> str:
    """
    Save screenshot data to file.
    
    Args:
        image_data: Raw image bytes
        company: Company name
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        Path to saved screenshot
    """
    try:
        if not timestamp:
            timestamp = datetime.now()
        
        # Create screenshots directory
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{company.lower().replace(' ', '_')}_{timestamp_str}.png"
        filepath = screenshots_dir / filename
        
        # Save image data
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving screenshot: {str(e)}")
        raise

def make_json_serializable(obj: Any) -> Any:
    """
    Convert an object to JSON serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON serializable version of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # For other types, try to convert to string
        try:
            return str(obj)
        except:
            return None

def hash_content(content: str) -> str:
    """
    Generate a hash for content to detect changes.
    
    Args:
        content: Content to hash
        
    Returns:
        SHA256 hash of the content
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def clean_company_name(name: str) -> str:
    """
    Clean company name for use in filenames and identifiers.
    
    Args:
        name: Raw company name
        
    Returns:
        Cleaned company name
    """
    # Remove special characters and convert to lowercase
    cleaned = ''.join(c for c in name if c.isalnum() or c in [' ', '-', '_'])
    cleaned = cleaned.strip().lower().replace(' ', '_')
    return cleaned

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        filepath: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "extension": path.suffix,
            "is_file": path.is_file(),
            "is_directory": path.is_dir()
        }
        
    except Exception as e:
        return {"error": str(e)}

def cleanup_old_data(days_to_keep: int = 30):
    """
    Clean up old analysis data files.
    
    Args:
        days_to_keep: Number of days of data to keep
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.timestamp()
        
        # Clean up analysis files
        for file in DATA_DIR.glob("analysis_*.json"):
            if file.stat().st_mtime < cutoff_timestamp:
                file.unlink()
                logger.info(f"Deleted old analysis file: {file}")
        
        # Clean up screenshots
        screenshots_dir = Path("screenshots")
        if screenshots_dir.exists():
            for file in screenshots_dir.glob("*.png"):
                if file.stat().st_mtime < cutoff_timestamp:
                    file.unlink()
                    logger.info(f"Deleted old screenshot: {file}")
        
        logger.info(f"Cleanup completed - kept data from last {days_to_keep} days")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def export_to_csv(data: List[Dict[str, Any]], filename: str) -> str:
    """
    Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        filename: Output filename
        
    Returns:
        Path to exported CSV file
    """
    try:
        import pandas as pd
        
        df = pd.DataFrame(data)
        filepath = DATA_DIR / f"{filename}.csv"
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Data exported to CSV: {filepath}")
        return str(filepath)
        
    except ImportError:
        logger.error("Pandas not available for CSV export")
        raise
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise

def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL appears valid, False otherwise
    """
    try:
        from urllib.parse import urlparse
        
        result = urlparse(url)
        return all([result.scheme, result.netloc])
        
    except Exception:
        return False

def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name or empty string if invalid
    """
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        return parsed.netloc
        
    except Exception:
        return ""

def format_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format ISO timestamp string to readable format.
    
    Args:
        timestamp: ISO timestamp string
        format_str: Output format string
        
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime(format_str)
    except Exception:
        return timestamp

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def create_backup(source_dir: str = "data", backup_name: Optional[str] = None) -> str:
    """
    Create a backup of data directory.
    
    Args:
        source_dir: Directory to backup
        backup_name: Optional backup name
        
    Returns:
        Path to backup file
    """
    try:
        import shutil
        
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = f"{backup_name}.zip"
        
        # Create zip archive
        shutil.make_archive(backup_name, 'zip', source_dir)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise

def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging.
    
    Returns:
        Dictionary with system information
    """
    try:
        import platform
        import sys
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "data_directory": str(DATA_DIR.absolute()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}
