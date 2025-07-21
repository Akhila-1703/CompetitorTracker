"""
Screenshot comparison module for tracking visual UI changes across competitor websites.
Uses Playwright for screenshot capture and OpenCV for image difference detection.
"""

import os
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Playwright (optional dependency)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - screenshot functionality disabled")

class ScreenshotComparer:
    """Visual diff checker for competitor websites using screenshots."""
    
    def __init__(self, screenshots_dir: str = "screenshots", verbose: bool = False):
        """
        Initialize the screenshot comparer.
        
        Args:
            screenshots_dir: Directory to store screenshots
            verbose: Enable verbose logging
        """
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.verbose = verbose
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed - screenshot features unavailable")
    
    def capture_screenshot(self, url: str, company: str) -> Optional[str]:
        """
        Capture a screenshot of the given URL.
        
        Args:
            url: URL to capture
            company: Company name for filename
            
        Returns:
            Path to saved screenshot or None if failed
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Cannot capture screenshot - Playwright not available")
            return None
        
        try:
            if self.verbose:
                logger.info(f"Capturing screenshot for {company}: {url}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company.lower().replace(' ', '_')}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1280, 'height': 720})
                
                # Navigate to the page
                page.goto(url, timeout=30000)
                
                # Wait for content to load
                page.wait_for_timeout(2000)
                
                # Take screenshot
                page.screenshot(path=str(filepath))
                browser.close()
            
            if self.verbose:
                logger.info(f"Screenshot saved: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error capturing screenshot for {company}: {str(e)}")
            return None
    
    def compare_screenshots(self, image1_path: str, image2_path: str) -> Dict[str, Any]:
        """
        Compare two screenshots and detect differences.
        
        Args:
            image1_path: Path to first image (older)
            image2_path: Path to second image (newer)
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Load images
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None or img2 is None:
                return {
                    'error': 'Failed to load one or both images',
                    'changes_detected': False,
                    'similarity_score': 0.0
                }
            
            # Resize images to same size if needed
            if img1.shape != img2.shape:
                height = min(img1.shape[0], img2.shape[0])
                width = min(img1.shape[1], img2.shape[1])
                img1 = cv2.resize(img1, (width, height))
                img2 = cv2.resize(img2, (width, height))
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate structural similarity
            similarity_score = self._calculate_ssim(gray1, gray2)
            
            # Calculate absolute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # Calculate percentage of changed pixels
            changed_pixels = np.count_nonzero(thresh)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            change_percentage = (changed_pixels / total_pixels) * 100
            
            # Determine if significant changes detected
            changes_detected = change_percentage > 1.0  # More than 1% change
            
            result = {
                'similarity_score': float(similarity_score),
                'change_percentage': float(change_percentage),
                'changes_detected': changes_detected,
                'changed_pixels': int(changed_pixels),
                'total_pixels': int(total_pixels),
                'comparison_timestamp': datetime.now().isoformat()
            }
            
            if self.verbose:
                logger.info(f"Comparison complete: {change_percentage:.2f}% changed, similarity: {similarity_score:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {str(e)}")
            return {
                'error': str(e),
                'changes_detected': False,
                'similarity_score': 0.0
            }
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate Structural Similarity Index (SSIM) between two images.
        
        Args:
            img1: First image array
            img2: Second image array
            
        Returns:
            SSIM score between 0 and 1
        """
        try:
            # Simple SSIM implementation
            mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
            mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
            
            mu1_sq = mu1 * mu1
            mu2_sq = mu2 * mu2
            mu1_mu2 = mu1 * mu2
            
            sigma1_sq = cv2.GaussianBlur(img1 * img1, (11, 11), 1.5) - mu1_sq
            sigma2_sq = cv2.GaussianBlur(img2 * img2, (11, 11), 1.5) - mu2_sq
            sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
            
            c1 = (0.01 * 255) ** 2
            c2 = (0.03 * 255) ** 2
            
            ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
            
            return float(np.mean(ssim_map))
            
        except Exception:
            # Fallback to simple correlation
            return float(np.corrcoef(img1.flatten(), img2.flatten())[0, 1])
    
    def get_latest_screenshot(self, company: str) -> Optional[str]:
        """
        Get the path to the latest screenshot for a company.
        
        Args:
            company: Company name
            
        Returns:
            Path to latest screenshot or None if not found
        """
        try:
            company_pattern = f"{company.lower().replace(' ', '_')}_*.png"
            screenshots = list(self.screenshots_dir.glob(company_pattern))
            
            if not screenshots:
                return None
            
            # Sort by modification time (newest first)
            screenshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return str(screenshots[0])
            
        except Exception as e:
            logger.error(f"Error finding latest screenshot for {company}: {str(e)}")
            return None
    
    def monitor_competitor_changes(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor a competitor for visual changes.
        
        Args:
            competitor: Competitor configuration dictionary
            
        Returns:
            Dictionary with monitoring results
        """
        company = competitor.get('name', 'Unknown')
        url = competitor.get('url', '')
        
        try:
            # Get the latest existing screenshot
            latest_screenshot = self.get_latest_screenshot(company)
            
            # Capture new screenshot
            new_screenshot = self.capture_screenshot(url, company)
            
            if not new_screenshot:
                return {
                    'company': company,
                    'error': 'Failed to capture new screenshot',
                    'changes_detected': False
                }
            
            result = {
                'company': company,
                'new_screenshot': new_screenshot,
                'capture_timestamp': datetime.now().isoformat(),
                'changes_detected': False
            }
            
            # Compare with previous screenshot if available
            if latest_screenshot and latest_screenshot != new_screenshot:
                comparison = self.compare_screenshots(latest_screenshot, new_screenshot)
                result.update(comparison)
                result['previous_screenshot'] = latest_screenshot
            else:
                result['note'] = 'No previous screenshot for comparison'
            
            return result
            
        except Exception as e:
            logger.error(f"Error monitoring {company}: {str(e)}")
            return {
                'company': company,
                'error': str(e),
                'changes_detected': False
            }
    
    def cleanup_old_screenshots(self, days_to_keep: int = 30):
        """
        Clean up old screenshot files.
        
        Args:
            days_to_keep: Number of days of screenshots to keep
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = cutoff_date.timestamp()
            
            deleted_count = 0
            for screenshot in self.screenshots_dir.glob("*.png"):
                if screenshot.stat().st_mtime < cutoff_timestamp:
                    screenshot.unlink()
                    deleted_count += 1
            
            if self.verbose:
                logger.info(f"Cleaned up {deleted_count} old screenshots")
            
        except Exception as e:
            logger.error(f"Error during screenshot cleanup: {str(e)}")

def check_visual_changes(url: str, company: str) -> Dict[str, Any]:
    """
    Convenience function for checking visual changes.
    
    Args:
        url: URL to monitor
        company: Company name
        
    Returns:
        Dictionary with change detection results
    """
    comparer = ScreenshotComparer(verbose=False)
    competitor = {'name': company, 'url': url}
    return comparer.monitor_competitor_changes(competitor)
