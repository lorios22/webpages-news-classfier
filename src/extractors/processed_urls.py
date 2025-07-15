#!/usr/bin/env python3
"""
Processed URLs Manager
=====================

This module handles tracking and managing processed URLs to prevent
duplicate processing and maintain pipeline state.

Features:
- URL tracking and deduplication
- Excel file processing
- Persistent URL state management
- Batch processing capabilities

Author: AI Assistant
Version: 1.0.0
License: MIT
"""

import os
import pandas as pd
from typing import Set, List, Optional
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

def process_urls(excel_file: str = "classified_news/analyzed_results.xlsx", 
                processed_urls_file: str = "urls/processed_urls.txt") -> bool:
    """
    Process URLs from Excel file and mark them as completed.
    
    Args:
        excel_file: Path to Excel file with analyzed results
        processed_urls_file: Path to file tracking processed URLs
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if Excel file exists
        if not os.path.exists(excel_file):
            logger.warning(f"Excel file not found: {excel_file}")
            return False
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        logger.info(f"Processing {len(df)} URLs from {excel_file}")
        
        # Extract URLs from DataFrame
        urls_to_process = []
        for _, row in df.iterrows():
            url = row.get('url', '')
            if url and isinstance(url, str):
                urls_to_process.append(url.strip())
        
        if not urls_to_process:
            logger.warning("No URLs found in Excel file")
            return False
        
        # Load existing processed URLs
        processed_urls = load_processed_urls(processed_urls_file)
        
        # Add new URLs to processed set
        new_urls = 0
        for url in urls_to_process:
            if url not in processed_urls:
                processed_urls.add(url)
                new_urls += 1
        
        # Save updated processed URLs
        save_processed_urls(processed_urls, processed_urls_file)
        
        logger.info(f"✅ Processed {new_urls} new URLs. Total tracked: {len(processed_urls)}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing URLs: {str(e)}")
        return False

def load_processed_urls(processed_urls_file: str) -> Set[str]:
    """
    Load processed URLs from file.
    
    Args:
        processed_urls_file: Path to processed URLs file
        
    Returns:
        Set[str]: Set of processed URLs
    """
    processed_urls = set()
    
    try:
        if os.path.exists(processed_urls_file):
            with open(processed_urls_file, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url:
                        processed_urls.add(url)
            logger.debug(f"Loaded {len(processed_urls)} processed URLs from {processed_urls_file}")
        else:
            logger.debug(f"Processed URLs file not found: {processed_urls_file}")
            
    except Exception as e:
        logger.error(f"Error loading processed URLs: {str(e)}")
        
    return processed_urls

def save_processed_urls(processed_urls: Set[str], processed_urls_file: str) -> bool:
    """
    Save processed URLs to file.
    
    Args:
        processed_urls: Set of processed URLs
        processed_urls_file: Path to processed URLs file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(processed_urls_file), exist_ok=True)
        
        # Save URLs to file
        with open(processed_urls_file, 'w', encoding='utf-8') as f:
            for url in sorted(processed_urls):
                f.write(f"{url}\n")
        
        logger.debug(f"Saved {len(processed_urls)} processed URLs to {processed_urls_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving processed URLs: {str(e)}")
        return False

def is_url_processed(url: str, processed_urls_file: str = "urls/processed_urls.txt") -> bool:
    """
    Check if a URL has been processed.
    
    Args:
        url: URL to check
        processed_urls_file: Path to processed URLs file
        
    Returns:
        bool: True if URL is processed, False otherwise
    """
    processed_urls = load_processed_urls(processed_urls_file)
    return url in processed_urls

def mark_url_as_processed(url: str, processed_urls_file: str = "urls/processed_urls.txt") -> bool:
    """
    Mark a single URL as processed.
    
    Args:
        url: URL to mark as processed
        processed_urls_file: Path to processed URLs file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        processed_urls = load_processed_urls(processed_urls_file)
        processed_urls.add(url)
        return save_processed_urls(processed_urls, processed_urls_file)
        
    except Exception as e:
        logger.error(f"Error marking URL as processed: {str(e)}")
        return False

def get_processed_urls_count(processed_urls_file: str = "urls/processed_urls.txt") -> int:
    """
    Get the count of processed URLs.
    
    Args:
        processed_urls_file: Path to processed URLs file
        
    Returns:
        int: Number of processed URLs
    """
    processed_urls = load_processed_urls(processed_urls_file)
    return len(processed_urls)

def clear_processed_urls(processed_urls_file: str = "urls/processed_urls.txt") -> bool:
    """
    Clear all processed URLs (for testing purposes).
    
    Args:
        processed_urls_file: Path to processed URLs file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(processed_urls_file):
            os.remove(processed_urls_file)
            logger.info(f"Cleared processed URLs file: {processed_urls_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing processed URLs: {str(e)}")
        return False

# Main execution for testing
if __name__ == "__main__":
    import sys
    
    print("🔧 Testing Processed URLs Manager...")
    
    # Test processing URLs
    success = process_urls()
    
    if success:
        count = get_processed_urls_count()
        print(f"✅ Successfully processed URLs. Total tracked: {count}")
    else:
        print("❌ Failed to process URLs")
        sys.exit(1)
    
    print("🎉 Processed URLs Manager test completed!") 