"""
Database management for the Competitor Intelligence Dashboard.
Handles PostgreSQL data persistence using SQLAlchemy ORM.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class CompetitorAnalysis(Base):
    """Model for storing competitor analysis results."""
    __tablename__ = 'competitor_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_name = Column(String(255), nullable=False)
    summary_data = Column(JSON, nullable=False)
    raw_content = Column(Text)
    content_hash = Column(String(64))
    impact_score = Column(Integer)
    confidence_level = Column(String(50))
    categories = Column(JSON)
    used_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrendAnalysis(Base):
    """Model for storing trend analysis results."""
    __tablename__ = 'trend_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_period = Column(String(100))
    trending_categories = Column(JSON)
    average_impact = Column(Integer)
    total_competitors = Column(Integer)
    analysis_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScreenshotComparison(Base):
    """Model for storing screenshot comparison results."""
    __tablename__ = 'screenshot_comparisons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    competitor_name = Column(String(255), nullable=False)
    screenshot_path = Column(String(500))
    comparison_result = Column(JSON)
    changes_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class CompetitorConfig(Base):
    """Model for storing competitor configurations."""
    __tablename__ = 'competitor_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    platform = Column(String(100))
    description = Column(Text)
    homepage = Column(String(500))
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    """Database manager for competitor intelligence data."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise ValueError("Database URL is required. Set DATABASE_URL environment variable.")
        
        try:
            self.engine = create_engine(database_url, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def save_analysis(self, competitor_name: str, summary_data: Dict[str, Any], raw_content: str = None) -> bool:
        """
        Save competitor analysis to database.
        
        Args:
            competitor_name: Name of the competitor
            summary_data: Analysis summary dictionary
            raw_content: Raw changelog content
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Create content hash for deduplication
            content_hash = None
            if raw_content:
                import hashlib
                content_hash = hashlib.sha256(raw_content.encode('utf-8')).hexdigest()
            
            analysis = CompetitorAnalysis(
                competitor_name=competitor_name,
                summary_data=summary_data,
                raw_content=raw_content,
                content_hash=content_hash,
                impact_score=summary_data.get('impact_score'),
                confidence_level=summary_data.get('confidence_level'),
                categories=summary_data.get('categories', []),
                used_fallback=summary_data.get('used_fallback_content', False)
            )
            
            session.add(analysis)
            session.commit()
            session.close()
            
            logger.info(f"Analysis saved for {competitor_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving analysis: {str(e)}")
            if session:
                session.rollback()
                session.close()
            return False
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            if session:
                session.close()
            return False
    
    def get_recent_analyses(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent competitor analyses.
        
        Args:
            limit: Maximum number of results
            days: Number of days to look back
            
        Returns:
            List of analysis dictionaries
        """
        try:
            session = self.SessionLocal()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.created_at >= cutoff_date)\
                .order_by(CompetitorAnalysis.created_at.desc())\
                .limit(limit)\
                .all()
            
            results = []
            for analysis in analyses:
                results.append({
                    'id': analysis.id,
                    'competitor': analysis.competitor_name,
                    'summary_data': analysis.summary_data,
                    'impact_score': analysis.impact_score,
                    'confidence_level': analysis.confidence_level,
                    'categories': analysis.categories,
                    'used_fallback': analysis.used_fallback,
                    'created_at': analysis.created_at.isoformat()
                })
            
            session.close()
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving recent analyses: {str(e)}")
            if session:
                session.close()
            return []
    
    def save_trend_analysis(self, period: str, trending_categories: List[str], 
                          avg_impact: float, total_competitors: int, analysis_data: Dict[str, Any]) -> bool:
        """
        Save trend analysis results.
        
        Args:
            period: Analysis period description
            trending_categories: List of trending category names
            avg_impact: Average impact score
            total_competitors: Total number of competitors analyzed
            analysis_data: Full analysis data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            trend = TrendAnalysis(
                analysis_period=period,
                trending_categories=trending_categories,
                average_impact=int(avg_impact),
                total_competitors=total_competitors,
                analysis_data=analysis_data
            )
            
            session.add(trend)
            session.commit()
            session.close()
            
            logger.info(f"Trend analysis saved for period: {period}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trend analysis: {str(e)}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_competitor_history(self, competitor_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get analysis history for a specific competitor.
        
        Args:
            competitor_name: Name of the competitor
            days: Number of days to look back
            
        Returns:
            List of historical analyses
        """
        try:
            session = self.SessionLocal()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.competitor_name == competitor_name)\
                .filter(CompetitorAnalysis.created_at >= cutoff_date)\
                .order_by(CompetitorAnalysis.created_at.desc())\
                .all()
            
            results = []
            for analysis in analyses:
                results.append({
                    'created_at': analysis.created_at.isoformat(),
                    'impact_score': analysis.impact_score,
                    'confidence_level': analysis.confidence_level,
                    'categories': analysis.categories,
                    'summary_data': analysis.summary_data
                })
            
            session.close()
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving competitor history: {str(e)}")
            if session:
                session.close()
            return []
    
    def save_screenshot_comparison(self, competitor_name: str, screenshot_path: str, 
                                 comparison_result: Dict[str, Any], changes_detected: bool) -> bool:
        """
        Save screenshot comparison results.
        
        Args:
            competitor_name: Name of the competitor
            screenshot_path: Path to screenshot file
            comparison_result: Comparison analysis results
            changes_detected: Whether changes were detected
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            screenshot = ScreenshotComparison(
                competitor_name=competitor_name,
                screenshot_path=screenshot_path,
                comparison_result=comparison_result,
                changes_detected=changes_detected
            )
            
            session.add(screenshot)
            session.commit()
            session.close()
            
            logger.info(f"Screenshot comparison saved for {competitor_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving screenshot comparison: {str(e)}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old analysis data.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            session = self.SessionLocal()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old analyses
            deleted_analyses = session.query(CompetitorAnalysis)\
                .filter(CompetitorAnalysis.created_at < cutoff_date)\
                .delete()
            
            # Clean up old trends
            deleted_trends = session.query(TrendAnalysis)\
                .filter(TrendAnalysis.created_at < cutoff_date)\
                .delete()
            
            # Clean up old screenshots
            deleted_screenshots = session.query(ScreenshotComparison)\
                .filter(ScreenshotComparison.created_at < cutoff_date)\
                .delete()
            
            session.commit()
            session.close()
            
            logger.info(f"Cleanup completed: {deleted_analyses} analyses, {deleted_trends} trends, {deleted_screenshots} screenshots deleted")
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {str(e)}")
            if session:
                session.rollback()
                session.close()
