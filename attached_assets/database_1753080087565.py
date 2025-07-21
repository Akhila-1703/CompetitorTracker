"""
Database module for Competitor Intelligence Dashboard.
Handles PostgreSQL operations for storing and retrieving analysis data.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class CompetitorAnalysis(Base):
    """Table for storing competitor analysis results."""
    __tablename__ = 'competitor_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_name = Column(String(255), nullable=False)
    analysis_date = Column(DateTime, default=datetime.now)
    summary_bullets = Column(JSON)
    strategic_insight = Column(Text)
    confidence_level = Column(String(50))
    momentum_score = Column(Integer, default=0)
    categories = Column(JSON)
    impact_score = Column(Integer, default=50)
    raw_content = Column(Text)
    content_length = Column(Integer, default=0)
    url = Column(String(500))
    platform = Column(String(100))
    analysis_period_start = Column(DateTime)
    analysis_period_end = Column(DateTime)

class TrendAnalysis(Base):
    """Table for storing trend analysis data."""
    __tablename__ = 'trend_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_date = Column(DateTime, default=datetime.now)
    dominant_trend = Column(String(255))
    trend_description = Column(Text)
    companies_count = Column(Integer, default=0)
    trend_data = Column(JSON)

class ScreenshotComparison(Base):
    """Table for storing screenshot comparison results."""
    __tablename__ = 'screenshot_comparisons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_name = Column(String(255), nullable=False)
    capture_date = Column(DateTime, default=datetime.now)
    url = Column(String(500))
    current_screenshot_path = Column(String(500))
    previous_screenshot_path = Column(String(500))
    has_changes = Column(Boolean, default=False)
    change_percentage = Column(Float, default=0.0)
    diff_image_path = Column(String(500))
    comparison_metadata = Column(JSON)

class CompetitorConfig(Base):
    """Table for storing competitor configurations."""
    __tablename__ = 'competitor_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    platform = Column(String(100), nullable=False)
    description = Column(Text)
    homepage_url = Column(String(500))
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        """Initialize database connection."""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def save_competitor_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """
        Save competitor analysis to database.
        
        Args:
            analysis_data: Analysis data dictionary
            
        Returns:
            ID of saved analysis record
        """
        session = self.get_session()
        try:
            analysis = CompetitorAnalysis(
                competitor_name=analysis_data.get('competitor'),
                summary_bullets=analysis_data.get('summary_bullets', []),
                strategic_insight=analysis_data.get('strategic_insight'),
                confidence_level=analysis_data.get('confidence_level'),
                momentum_score=analysis_data.get('momentum_score', 0),
                categories=analysis_data.get('categories', []),
                impact_score=analysis_data.get('impact_score', 50),
                raw_content=analysis_data.get('raw_content', ''),
                content_length=analysis_data.get('content_length', 0),
                url=analysis_data.get('url'),
                platform=analysis_data.get('platform'),
                analysis_period_start=analysis_data.get('analysis_period', {}).get('start'),
                analysis_period_end=analysis_data.get('analysis_period', {}).get('end')
            )
            
            session.add(analysis)
            session.commit()
            
            analysis_id = analysis.id
            logger.info(f"Saved competitor analysis for {analysis_data.get('competitor')} with ID {analysis_id}")
            return analysis_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving competitor analysis: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_trend_analysis(self, trend_data: Dict[str, Any]) -> int:
        """
        Save trend analysis to database.
        
        Args:
            trend_data: Trend analysis data
            
        Returns:
            ID of saved trend record
        """
        session = self.get_session()
        try:
            trend = TrendAnalysis(
                dominant_trend=trend_data.get('dominant_trend'),
                trend_description=trend_data.get('description'),
                companies_count=trend_data.get('companies_count', 0),
                trend_data=trend_data.get('raw_data', {})
            )
            
            session.add(trend)
            session.commit()
            
            trend_id = trend.id
            logger.info(f"Saved trend analysis with ID {trend_id}")
            return trend_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving trend analysis: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_screenshot_comparison(self, comparison_data: Dict[str, Any]) -> int:
        """
        Save screenshot comparison to database.
        
        Args:
            comparison_data: Screenshot comparison data
            
        Returns:
            ID of saved comparison record
        """
        session = self.get_session()
        try:
            comparison = ScreenshotComparison(
                competitor_name=comparison_data.get('company'),
                url=comparison_data.get('url'),
                current_screenshot_path=comparison_data.get('current_screenshot'),
                previous_screenshot_path=comparison_data.get('previous_screenshot'),
                has_changes=comparison_data.get('has_changes', False),
                change_percentage=comparison_data.get('change_percentage', 0.0),
                diff_image_path=comparison_data.get('diff_image'),
                comparison_metadata=comparison_data.get('metadata', {})
            )
            
            session.add(comparison)
            session.commit()
            
            comparison_id = comparison.id
            logger.info(f"Saved screenshot comparison for {comparison_data.get('company')} with ID {comparison_id}")
            return comparison_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving screenshot comparison: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_recent_analyses(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent competitor analyses.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of analysis dictionaries
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.analysis_date >= cutoff_date)\
                .order_by(CompetitorAnalysis.analysis_date.desc())\
                .limit(limit)\
                .all()
            
            results = []
            for analysis in analyses:
                results.append({
                    'id': analysis.id,
                    'competitor': analysis.competitor_name,
                    'summary_bullets': analysis.summary_bullets,
                    'strategic_insight': analysis.strategic_insight,
                    'confidence_level': analysis.confidence_level,
                    'momentum_score': analysis.momentum_score,
                    'categories': analysis.categories,
                    'impact_score': analysis.impact_score,
                    'analysis_date': analysis.analysis_date.isoformat(),
                    'url': analysis.url,
                    'platform': analysis.platform,
                    'content_length': analysis.content_length
                })
            
            logger.info(f"Retrieved {len(results)} recent analyses")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving recent analyses: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_competitor_history(self, competitor_name: str, days: int = 90) -> List[Dict[str, Any]]:
        """
        Get historical analyses for a specific competitor.
        
        Args:
            competitor_name: Name of the competitor
            days: Number of days to look back
            
        Returns:
            List of historical analysis data
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.competitor_name == competitor_name)\
                .filter(CompetitorAnalysis.analysis_date >= cutoff_date)\
                .order_by(CompetitorAnalysis.analysis_date.desc())\
                .all()
            
            results = []
            for analysis in analyses:
                results.append({
                    'id': analysis.id,
                    'analysis_date': analysis.analysis_date.isoformat(),
                    'momentum_score': analysis.momentum_score,
                    'confidence_level': analysis.confidence_level,
                    'impact_score': analysis.impact_score,
                    'summary_bullets': analysis.summary_bullets,
                    'strategic_insight': analysis.strategic_insight
                })
            
            logger.info(f"Retrieved {len(results)} historical analyses for {competitor_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving competitor history: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_momentum_trends(self, days: int = 30) -> Dict[str, List[Dict]]:
        """
        Get momentum score trends for all competitors.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary mapping competitor names to momentum trend data
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.analysis_date >= cutoff_date)\
                .order_by(CompetitorAnalysis.competitor_name, CompetitorAnalysis.analysis_date)\
                .all()
            
            trends = {}
            for analysis in analyses:
                if analysis.competitor_name not in trends:
                    trends[analysis.competitor_name] = []
                
                trends[analysis.competitor_name].append({
                    'date': analysis.analysis_date.isoformat(),
                    'momentum_score': analysis.momentum_score,
                    'impact_score': analysis.impact_score
                })
            
            logger.info(f"Retrieved momentum trends for {len(trends)} competitors")
            return trends
            
        except Exception as e:
            logger.error(f"Error retrieving momentum trends: {str(e)}")
            return {}
        finally:
            session.close()
    
    def save_competitor_config(self, config_data: Dict[str, Any]) -> int:
        """
        Save or update competitor configuration.
        
        Args:
            config_data: Competitor configuration data
            
        Returns:
            ID of saved configuration
        """
        session = self.get_session()
        try:
            # Check if competitor already exists
            existing = session.query(CompetitorConfig)\
                .filter(CompetitorConfig.name == config_data['name'])\
                .first()
            
            if existing:
                # Update existing
                existing.url = config_data.get('url', existing.url)
                existing.platform = config_data.get('platform', existing.platform)
                existing.description = config_data.get('description', existing.description)
                existing.homepage_url = config_data.get('homepage_url', existing.homepage_url)
                existing.category = config_data.get('category', existing.category)
                existing.is_active = config_data.get('is_active', existing.is_active)
                existing.updated_date = datetime.now()
                
                config_id = existing.id
            else:
                # Create new
                config = CompetitorConfig(
                    name=config_data['name'],
                    url=config_data['url'],
                    platform=config_data['platform'],
                    description=config_data.get('description'),
                    homepage_url=config_data.get('homepage_url'),
                    category=config_data.get('category'),
                    is_active=config_data.get('is_active', True)
                )
                
                session.add(config)
                session.flush()
                config_id = config.id
            
            session.commit()
            logger.info(f"Saved competitor config for {config_data['name']} with ID {config_id}")
            return config_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving competitor config: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_active_competitors(self) -> List[Dict[str, Any]]:
        """
        Get all active competitor configurations.
        
        Returns:
            List of active competitor configurations
        """
        session = self.get_session()
        try:
            configs = session.query(CompetitorConfig)\
                .filter(CompetitorConfig.is_active == True)\
                .order_by(CompetitorConfig.name)\
                .all()
            
            results = []
            for config in configs:
                results.append({
                    'id': config.id,
                    'name': config.name,
                    'url': config.url,
                    'platform': config.platform,
                    'description': config.description,
                    'homepage_url': config.homepage_url,
                    'category': config.category,
                    'created_date': config.created_date.isoformat(),
                    'updated_date': config.updated_date.isoformat()
                })
            
            logger.info(f"Retrieved {len(results)} active competitors")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving active competitors: {str(e)}")
            return []
        finally:
            session.close()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data from the database.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Delete old analyses
            deleted_analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.analysis_date < cutoff_date)\
                .delete()
            
            # Delete old trend analyses
            deleted_trends = session.query(TrendAnalysis)\
                .filter(TrendAnalysis.analysis_date < cutoff_date)\
                .delete()
            
            # Delete old screenshot comparisons
            deleted_screenshots = session.query(ScreenshotComparison)\
                .filter(ScreenshotComparison.capture_date < cutoff_date)\
                .delete()
            
            session.commit()
            
            logger.info(f"Cleaned up {deleted_analyses} analyses, {deleted_trends} trends, {deleted_screenshots} screenshots older than {days_to_keep} days")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old data: {str(e)}")
            raise
        finally:
            session.close()

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database():
    """Initialize database with default competitors."""
    try:
        db = get_db_manager()
        
        # Default competitors from config
        from config import COMPETITOR_CONFIGS
        
        for name, config in COMPETITOR_CONFIGS.items():
            try:
                db.save_competitor_config({
                    'name': name,
                    'url': config['url'],
                    'platform': config['platform'],
                    'description': config['description'],
                    'homepage_url': config.get('homepage_url'),
                    'category': config.get('category'),
                    'is_active': True
                })
            except Exception as e:
                logger.warning(f"Could not save config for {name}: {str(e)}")
        
        logger.info("Database initialized with default competitors")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise