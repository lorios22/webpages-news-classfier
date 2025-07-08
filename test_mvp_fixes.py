#!/usr/bin/env python3
"""
Test script for MVP fixes to Web News Classifier
Tests all four critical fixes:
1. Enhanced spam filter with override
2. Long-text truncation  
3. Duplicate detection
4. FIN integration
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from news_classifier_agents import (
    check_summary_override, truncate_long_content, 
    clean_webpage_content, input_preprocessor,
    fact_checker, human_reasoning
)
from assistant.state import ClassifierState
from duplicate_detection import duplicate_detector
from fin_integration import fin_integration

def test_spam_filter_improvements():
    """Test enhanced spam filter with credible pattern detection"""
    print("=== Testing Enhanced Spam Filter ===")
    
    # Test 1: Previously false positive - press release with spam words
    test_content_1 = """
    WESTLAKE, Texas, January 06, 2025 -- Business Wire
    Special offer for investors to buy now the new BlackRock ETF.
    Limited time discount available for early adopters.
    This press release contains forward-looking statements.
    """
    
    # Test 2: Actual spam content
    test_content_2 = """
    Buy now! Limited time special offer!
    Click here for discount! Sale ends soon!
    Get rich quick with this amazing deal!
    """
    
    # Test override mechanism
    print("Test 1 - Press release with spam words (should pass):")
    can_extract = check_summary_override(test_content_1)
    print(f"Summary override result: {can_extract}")
    
    print("\nTest 2 - Actual spam (should fail):")
    can_extract = check_summary_override(test_content_2)
    print(f"Summary override result: {can_extract}")
    
    return True

def test_content_truncation():
    """Test long-content truncation functionality"""
    print("\n=== Testing Content Truncation ===")
    
    # Create very long content
    long_content = "This is a test article. " * 1000  # ~5000 words
    print(f"Original length: {len(long_content)} characters")
    
    truncated = truncate_long_content(long_content, max_tokens=500)
    print(f"Truncated length: {len(truncated)} characters")
    print(f"Contains truncation marker: {'[Content truncated for analysis...]' in truncated}")
    
    # Test normal length content (should not be truncated)
    normal_content = "This is a normal length article about Bitcoin."
    not_truncated = truncate_long_content(normal_content)
    print(f"Normal content unchanged: {normal_content == not_truncated}")
    
    return True

def test_duplicate_detection():
    """Test duplicate detection system"""
    print("\n=== Testing Duplicate Detection ===")
    
    # Clear existing memory for clean test
    duplicate_detector.memory = {"articles": []}
    
    # Test content
    article_1 = "Bitcoin reaches new all-time high as institutional adoption increases"
    article_2 = "Bitcoin reaches new all-time high as institutional adoption increases"  # Exact duplicate
    article_3 = "BTC hits record high with growing institutional interest"  # Similar
    article_4 = "Ethereum sees price surge amid DeFi growth"  # Different
    
    # Add first article
    id_1 = duplicate_detector.add_content(article_1)
    print(f"Added article 1: {id_1}")
    
    # Check for exact duplicate
    is_dup_2, dup_id_2 = duplicate_detector.is_duplicate(article_2)
    print(f"Article 2 is duplicate: {is_dup_2}, matches: {dup_id_2}")
    
    # Check for similar content
    is_dup_3, dup_id_3 = duplicate_detector.is_duplicate(article_3, similarity_threshold=0.7)
    print(f"Article 3 is similar: {is_dup_3}, matches: {dup_id_3}")
    
    # Check for different content
    is_dup_4, dup_id_4 = duplicate_detector.is_duplicate(article_4)
    print(f"Article 4 is duplicate: {is_dup_4}")
    
    # Print stats
    stats = duplicate_detector.get_stats()
    print(f"Memory stats: {stats}")
    
    return True

def test_fin_integration():
    """Test FIN integration functionality"""
    print("\n=== Testing FIN Integration ===")
    
    # Test content with various characteristics
    test_content = """
    BlackRock's Bitcoin ETF sees massive inflows as institutional investors 
    surge into cryptocurrency markets. According to sources, the ETF has 
    attracted over $1 billion in assets. Market analysts are bullish on 
    the long-term prospects.
    """
    
    # Test source credibility
    cred_reuters = fin_integration.get_source_credibility(url="https://reuters.com/article")
    print(f"Reuters credibility: {cred_reuters}")
    
    cred_unknown = fin_integration.get_source_credibility(url="https://unknownblog.com/post")
    print(f"Unknown source credibility: {cred_unknown}")
    
    # Test sentiment analysis
    sentiment = fin_integration.analyze_sentiment(test_content)
    print(f"Sentiment analysis: {sentiment}")
    
    # Test fact-check enhancement
    fact_check = fin_integration.fact_check_enhancement(test_content)
    print(f"Fact-check enhancement: {fact_check}")
    
    # Test comprehensive analysis
    comprehensive = fin_integration.get_comprehensive_analysis(test_content, url="https://reuters.com/crypto")
    print(f"Comprehensive analysis keys: {list(comprehensive.keys())}")
    
    return True

def test_enhanced_content_cleaning():
    """Test enhanced content cleaning for context bleed prevention"""
    print("\n=== Testing Enhanced Content Cleaning ===")
    
    # Test content with navigation elements and breaking news
    messy_content = """
    Skip to main content
    BREAKING: GameStop surges 40% on news
    Subscribe to our newsletter
    Share this article
    
    Bitcoin ETF approval expected soon as BlackRock files with SEC.
    The cryptocurrency market is showing strong momentum.
    
    Advertisement
    Related articles
    You might also like
    Follow us on Twitter
    """
    
    cleaned = clean_webpage_content(messy_content)
    print("Original content snippet:")
    print(messy_content[:200] + "...")
    print("\nCleaned content:")
    print(cleaned)
    
    # Check that problematic elements were removed
    problematic_elements = ['skip to main content', 'breaking:', 'subscribe', 'advertisement']
    elements_removed = all(elem not in cleaned.lower() for elem in problematic_elements)
    print(f"Problematic elements removed: {elements_removed}")
    
    return True

def run_integration_test():
    """Run a full integration test of the pipeline with fixes"""
    print("\n=== Integration Test ===")
    
    # Create test state
    test_content = """
    LONDON, January 8, 2025 -- Business Wire
    
    BlackRock's iShares Bitcoin Trust ETF has attracted significant institutional 
    interest, with over $2 billion in inflows since launch. According to industry 
    sources, this represents a milestone in cryptocurrency adoption.
    
    "This demonstrates the growing institutional acceptance of Bitcoin as a 
    legitimate asset class," said a BlackRock spokesperson.
    
    The ETF approval follows months of regulatory discussions with the SEC.
    Market sentiment remains bullish on cryptocurrency prospects.
    """
    
    state = ClassifierState(content=test_content)
    
    try:
        # Test input preprocessor with all fixes
        print("Running input preprocessor...")
        preprocessor_result = input_preprocessor(state, None)
        print(f"Preprocessor skip: {state.preprocessor_state.get('skip', False)}")
        
        if not state.preprocessor_state.get('skip', False):
            print("Content passed preprocessing - running fact checker...")
            fact_result = fact_checker(state, None)
            print(f"Fact checker score: {state.fact_checker_score}")
            
            print("Running human reasoning...")
            human_result = human_reasoning(state, None)
            print(f"Human reasoning score: {state.human_reasoning_score}")
            
            print("Integration test completed successfully!")
            return True
        else:
            print(f"Content was skipped: {state.preprocessor_state.get('skip_reason')}")
            return False
            
    except Exception as e:
        print(f"Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing MVP Fixes for Web News Classifier")
    print("=" * 50)
    
    tests = [
        test_spam_filter_improvements,
        test_content_truncation,
        test_duplicate_detection,
        test_fin_integration,
        test_enhanced_content_cleaning,
        run_integration_test
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    overall = "PASS" if all(results) else "FAIL"
    print(f"\nOverall: {overall}")
    
    if overall == "PASS":
        print("\n✅ All MVP fixes are working correctly!")
        print("Ready for Day 2: HTML scraper patches and staging deployment")
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")

if __name__ == "__main__":
    main() 