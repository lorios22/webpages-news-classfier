import traceback
from playwright.sync_api import sync_playwright, Page, BrowserContext, Browser, TimeoutError
from pathlib import Path
from typing import Optional, Dict, List
import time
import re
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def process_urls_and_extract_content(input_file, output_dir):
    """
    Read URLs from a file and extract content from each webpage, saving results to individual files.
    """    
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Read URLs from file
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(urls)} URLs to process")
        
        with sync_playwright() as playwright:
            # Launch browser with additional options
            browser = playwright.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Create context with additional options
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                accept_downloads=True,
                ignore_https_errors=True,
                java_script_enabled=True,
                bypass_csp=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            )
            
            for i, url in enumerate(urls, 1):
                try:
                    print(f"\nProcessing URL {i}/{len(urls)}: {url}")
                    
                    # Create new page for each URL
                    page = context.new_page()
                    
                    try:
                        # First try with domcontentloaded
                        response = page.goto(
                            url, 
                            wait_until="domcontentloaded",
                            timeout=15000
                        )
                        
                        if not response:
                            print(f"Failed to load {url}, skipping...")
                            continue
                            
                        # Wait for content to be available
                        page.wait_for_selector('body', timeout=5000)
                        
                        # Try to scroll to load lazy content
                        page.evaluate("""
                            window.scrollTo(0, document.body.scrollHeight);
                            new Promise((resolve) => setTimeout(resolve, 2000));
                        """)
                        
                        # Extract content
                        content = page.evaluate('''() => {
                            function getVisibleText(element) {
                                if (!element) return '';
                                const style = window.getComputedStyle(element);
                                if (style.display === 'none' || style.visibility === 'hidden') return '';
                                
                                let text = '';
                                for (let child of element.childNodes) {
                                    if (child.nodeType === 3) { // Text node
                                        text += child.textContent.trim() + ' ';
                                    } else if (child.nodeType === 1) { // Element node
                                        text += getVisibleText(child) + ' ';
                                    }
                                }
                                return text.trim();
                            }
                            
                            // Get main content
                            const article = document.querySelector('article') || 
                                         document.querySelector('main') || 
                                         document.querySelector('.content') ||
                                         document.querySelector('.article-content');
                                         
                            const mainContent = article ? getVisibleText(article) : getVisibleText(document.body);
                            
                            // Get metadata
                            const title = document.title;
                            const description = document.querySelector('meta[name="description"]')?.content || 
                                             document.querySelector('meta[property="og:description"]')?.content || '';
                            
                            return {
                                title: title,
                                description: description,
                                content: mainContent,
                                url: window.location.href
                            }
                        }''')
                        
                        if not content['content'].strip():
                            raise Exception("No content extracted")
                        
                        # Create filename with sequential numbering
                        output_file = os.path.join(output_dir, f"url_{i}.json")
                        
                        # Save content
                        result = {
                            'source_url': url,
                            'extraction_time': datetime.now().isoformat(),
                            'content': content
                        }
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=4, ensure_ascii=False)
                            
                        print(f"Content saved to: {output_file}")
                        
                    except Exception as e:
                        print(f"Error processing URL {url}: {str(e)}")
                        
                finally:
                    page.close()
                    time.sleep(1)  # Reduced delay between requests
            
            context.close()
            browser.close()
            
        return {
            "status": "success",
            "message": f"Processed {len(urls)} URLs"
        }
        
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }