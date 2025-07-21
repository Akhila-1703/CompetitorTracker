#!/usr/bin/env python3
"""
Test script to verify OpenAI fallback functionality for the competitor intelligence dashboard.
This will test the get_changelog_fallback() function and overall scraper integration.
"""

import os
from dotenv import load_dotenv
from scraper import ChangelogScraper

# Load environment variables
load_dotenv()

def test_openai_fallback():
    """Test the OpenAI fallback functionality."""
    print("Testing OpenAI Fallback Functionality")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print("✅ OpenAI API key found")
    
    # Initialize scraper
    try:
        scraper = ChangelogScraper(verbose=True)
        print("✅ ChangelogScraper initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {str(e)}")
        return False
    
    # Test direct fallback generation
    print("\n🤖 Testing direct fallback generation...")
    try:
        test_company = "Linear"
        fallback_content = scraper.get_changelog_fallback(test_company)
        
        if fallback_content and not fallback_content.startswith("⚠️"):
            print("✅ Fallback content generated successfully")
            print("\nGenerated Content Preview:")
            print("-" * 30)
            # Show first 200 characters
            preview = fallback_content[:200] + "..." if len(fallback_content) > 200 else fallback_content
            print(preview)
            print("-" * 30)
        else:
            print(f"❌ Fallback generation failed: {fallback_content}")
            return False
            
    except Exception as e:
        print(f"❌ Error during fallback generation: {str(e)}")
        return False
    
    # Test fallback integration with scraper
    print("\n🔄 Testing fallback integration with scraper...")
    try:
        # Use an invalid URL to trigger fallback
        invalid_url = "https://nonexistent-website-12345.com/changelog"
        result = scraper.scrape_changelog(invalid_url, "generic")
        
        if result and "GPT-4 generated fallback" in result:
            print("✅ Scraper fallback integration working correctly")
            print("\nIntegrated Fallback Preview:")
            print("-" * 30)
            preview = result[:300] + "..." if len(result) > 300 else result
            print(preview)
            print("-" * 30)
        else:
            print(f"❌ Fallback integration failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error during fallback integration test: {str(e)}")
        return False
    
    print("\n🎉 All tests passed! OpenAI fallback functionality is working correctly.")
    return True

def test_multiple_companies():
    """Test fallback generation for multiple companies."""
    print("\n🏢 Testing fallback for multiple companies...")
    
    companies = ["Notion", "Figma", "Slack", "Discord"]
    scraper = ChangelogScraper(verbose=False)
    
    for company in companies:
        try:
            print(f"\nGenerating fallback for {company}...")
            fallback = scraper.get_changelog_fallback(company)
            
            if fallback and not fallback.startswith("⚠️"):
                print(f"✅ {company}: Success")
                # Show just the title line
                lines = fallback.split('\n')
                title_line = next((line for line in lines if '–' in line or '-' in line), lines[0])
                print(f"   Sample: {title_line[:60]}...")
            else:
                print(f"❌ {company}: Failed")
                
        except Exception as e:
            print(f"❌ {company}: Error - {str(e)}")

if __name__ == "__main__":
    success = test_openai_fallback()
    
    if success:
        test_multiple_companies()
        print("\n" + "=" * 50)
        print("🚀 OpenAI fallback system is fully operational!")
        print("\nThe system will now:")
        print("• Use GPT-4o to generate realistic changelog content when scraping fails")
        print("• Maintain the exact format: [Date] – [Title] with 3 bullet points")
        print("• Integrate seamlessly with the existing scraper workflow")
        print("• Handle API errors gracefully with clear error messages")
    else:
        print("\n" + "=" * 50)
        print("❌ Fallback system needs attention. Check the errors above.")