"""
Screenshot comparison module for tracking visual UI changes across competitor sites.
Uses Playwright for screenshot capture and OpenCV for image difference detection.
"""

import os
import asyncio
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging
from PIL import Image, ImageDraw
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Screenshot comparison features will be disabled.")

class ScreenshotComparer:
    """Handles screenshot capture and comparison for UI change detection."""
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """Initialize the screenshot comparer."""
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.viewport_size = {"width": 1920, "height": 1080}
        self.diff_threshold = 0.1  # Percentage difference threshold for change detection
    
    async def capture_screenshot_async(self, url: str, filename: str) -> Optional[str]:
        """
        Capture a screenshot of the given URL using Playwright.
        
        Args:
            url: URL to capture
            filename: Output filename
            
        Returns:
            Path to saved screenshot or None if failed
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available for screenshots")
            return None
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport=self.viewport_size,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                page = await context.new_page()
                
                # Navigate to URL with timeout
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # Take screenshot
                screenshot_path = self.screenshot_dir / filename
                await page.screenshot(path=str(screenshot_path), full_page=True)
                
                await browser.close()
                
                logger.info(f"Screenshot captured: {screenshot_path}")
                return str(screenshot_path)
                
        except Exception as e:
            logger.error(f"Error capturing screenshot for {url}: {str(e)}")
            return None
    
    def capture_screenshot(self, url: str, filename: str) -> Optional[str]:
        """
        Synchronous wrapper for screenshot capture.
        
        Args:
            url: URL to capture
            filename: Output filename
            
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            return asyncio.run(self.capture_screenshot_async(url, filename))
        except Exception as e:
            logger.error(f"Error in async screenshot capture: {str(e)}")
            return None
    
    def compare_images(self, image1_path: str, image2_path: str) -> Dict[str, any]:
        """
        Compare two images and detect differences.
        
        Args:
            image1_path: Path to first image (previous)
            image2_path: Path to second image (current)
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Load images
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None or img2 is None:
                return {"error": "Could not load one or both images"}
            
            # Resize images to same dimensions if needed
            if img1.shape != img2.shape:
                height = min(img1.shape[0], img2.shape[0])
                width = min(img1.shape[1], img2.shape[1])
                img1 = cv2.resize(img1, (width, height))
                img2 = cv2.resize(img2, (width, height))
            
            # Calculate difference
            diff = cv2.absdiff(img1, img2)
            
            # Convert to grayscale for analysis
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Calculate percentage of pixels that changed
            total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
            changed_pixels = np.count_nonzero(gray_diff > 30)  # Threshold for significant change
            change_percentage = (changed_pixels / total_pixels) * 100
            
            # Detect if significant changes occurred
            has_changes = change_percentage > self.diff_threshold
            
            # Create difference visualization
            diff_image_path = None
            if has_changes:
                diff_image_path = self._create_diff_visualization(img1, img2, diff)
            
            return {
                "has_changes": has_changes,
                "change_percentage": round(change_percentage, 2),
                "changed_pixels": changed_pixels,
                "total_pixels": total_pixels,
                "diff_image_path": diff_image_path,
                "threshold_used": self.diff_threshold
            }
            
        except Exception as e:
            logger.error(f"Error comparing images: {str(e)}")
            return {"error": str(e)}
    
    def _create_diff_visualization(self, img1: np.ndarray, img2: np.ndarray, diff: np.ndarray) -> str:
        """
        Create a visualization showing the differences between two images.
        
        Args:
            img1: First image
            img2: Second image  
            diff: Difference image
            
        Returns:
            Path to difference visualization image
        """
        try:
            # Create a mask for significant differences
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            mask = gray_diff > 30
            
            # Create highlighted diff image
            result = img2.copy()
            result[mask] = [0, 0, 255]  # Highlight differences in red
            
            # Save difference visualization
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_filename = f"diff_{timestamp}.png"
            diff_path = self.screenshot_dir / diff_filename
            
            cv2.imwrite(str(diff_path), result)
            
            return str(diff_path)
            
        except Exception as e:
            logger.error(f"Error creating diff visualization: {str(e)}")
            return None
    
    def capture_and_compare(self, url: str, company_name: str) -> Dict[str, any]:
        """
        Capture a new screenshot and compare with the previous one.
        
        Args:
            url: URL to capture
            company_name: Name of the company (for file naming)
            
        Returns:
            Dictionary with comparison results and screenshot paths
        """
        try:
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_filename = f"{company_name.lower()}_{timestamp}.png"
            
            # Find previous screenshot
            previous_screenshots = sorted([
                f for f in self.screenshot_dir.glob(f"{company_name.lower()}_*.png")
                if f.name != current_filename
            ])
            
            # Capture new screenshot
            current_path = self.capture_screenshot(url, current_filename)
            if not current_path:
                return {"error": "Failed to capture screenshot"}
            
            result = {
                "company": company_name,
                "current_screenshot": current_path,
                "captured_at": datetime.now().isoformat(),
                "url": url
            }
            
            # Compare with previous screenshot if available
            if previous_screenshots:
                previous_path = str(previous_screenshots[-1])  # Most recent previous screenshot
                result["previous_screenshot"] = previous_path
                
                comparison = self.compare_images(previous_path, current_path)
                result.update(comparison)
                
                if comparison.get("diff_image_path"):
                    result["diff_image"] = comparison["diff_image_path"]
            else:
                result["has_changes"] = False
                result["note"] = "No previous screenshot available for comparison"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in capture_and_compare: {str(e)}")
            return {"error": str(e)}
    
    def batch_capture_and_compare(self, urls_and_companies: list) -> Dict[str, Dict]:
        """
        Capture and compare screenshots for multiple companies.
        
        Args:
            urls_and_companies: List of tuples (url, company_name)
            
        Returns:
            Dictionary mapping company names to comparison results
        """
        results = {}
        
        for url, company_name in urls_and_companies:
            logger.info(f"Processing screenshots for {company_name}")
            result = self.capture_and_compare(url, company_name)
            results[company_name] = result
        
        return results
    
    def cleanup_old_screenshots(self, keep_days: int = 30):
        """
        Clean up screenshots older than specified days.
        
        Args:
            keep_days: Number of days to keep screenshots
        """
        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            
            for screenshot_file in self.screenshot_dir.glob("*.png"):
                if screenshot_file.stat().st_mtime < cutoff_date:
                    screenshot_file.unlink()
                    logger.info(f"Deleted old screenshot: {screenshot_file}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up screenshots: {str(e)}")
    
    def get_screenshot_base64(self, image_path: str) -> Optional[str]:
        """
        Convert screenshot to base64 for web display.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string or None if failed
        """
        try:
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{base64_data}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return None

def create_mock_comparison_result() -> Dict[str, any]:
    """
    Create a mock comparison result for testing when Playwright is not available.
    """
    return {
        "has_changes": False,
        "change_percentage": 0.0,
        "changed_pixels": 0,
        "total_pixels": 2073600,  # 1920x1080
        "diff_image_path": None,
        "note": "Playwright not available - screenshot comparison disabled"
    }
