#!/usr/bin/env python3
"""
Full Pipeline Execution Script

This script runs the complete news classification pipeline when all tests pass.
It coordinates the entire process from URL extraction to results posting.
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from extract_slack_urls import extract_slack_urls
from webscrapping import process_urls_and_extract_content
from agents_process import process_top_stories
from post_classified_news import post_stories_to_slack
from clean_folders_move_file import clean_processed_folders, move_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Executes the complete news classification pipeline.
    
    This class orchestrates the entire process:
    1. Run tests to ensure system health
    2. Extract URLs from Slack
    3. Scrape web content
    4. Run AI classification
    5. Post results to Slack
    6. Clean up and archive
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            "start_time": self.start_time.isoformat(),
            "stages": {},
            "errors": [],
            "warnings": []
        }
        
        # Configuration
        self.config = self._load_config()
        self._validate_environment()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            "slack_channel_source": os.getenv("SLACK_CHANNEL_ID_WEBSCRAPPER"),
            "slack_channel_target": os.getenv("SLACK_CHANNEL_ID_TO_POST_CLASSIFIED_NEWS_WEBPAGES"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "max_urls": int(os.getenv("MAX_URLS_TO_PROCESS", "1000")),
            "run_tests": os.getenv("RUN_TESTS_FIRST", "true").lower() == "true",
            "cleanup_after": os.getenv("CLEANUP_AFTER_EXECUTION", "true").lower() == "true"
        }
    
    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = [
            "SLACK_CHANNEL_ID_WEBSCRAPPER",
            "SLACK_CHANNEL_ID_TO_POST_CLASSIFIED_NEWS_WEBPAGES",
            "OPENAI_API_KEY",
            "SLACK_BOT_TOKEN"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def run_tests(self) -> bool:
        """
        Run the test suite to ensure system health.
        
        Returns:
            True if all tests pass, False otherwise
        """
        logger.info("🧪 Running test suite to validate system health...")
        stage_start = time.time()
        
        try:
            # Run MVP fixes tests
            result = subprocess.run(
                [sys.executable, "test_mvp_fixes.py"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if result.returncode != 0:
                logger.error("❌ MVP tests failed!")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                self.stats["errors"].append("MVP tests failed")
                return False
            
            logger.info("✅ All tests passed successfully!")
            self.stats["stages"]["tests"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "message": "All tests passed"
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running tests: {str(e)}")
            self.stats["errors"].append(f"Test execution error: {str(e)}")
            return False
    
    def extract_urls(self) -> List[str]:
        """
        Extract URLs from Slack channel.
        
        Returns:
            List of extracted URLs
        """
        logger.info("📥 Extracting URLs from Slack channel...")
        stage_start = time.time()
        
        try:
            urls_file = "urls/slack_channel_links_extracted.txt"
            processed_urls_path = "urls/processed_urls.txt"
            
            # Ensure directories exist
            Path("urls").mkdir(exist_ok=True)
            
            urls = extract_slack_urls(
                self.config["slack_channel_source"],
                urls_file,
                processed_urls_path,
                limit=self.config["max_urls"]
            )
            
            logger.info(f"✅ Extracted {len(urls)} new URLs")
            self.stats["stages"]["url_extraction"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "urls_extracted": len(urls),
                "message": f"Extracted {len(urls)} URLs"
            }
            return urls
            
        except Exception as e:
            logger.error(f"❌ Error extracting URLs: {str(e)}")
            self.stats["errors"].append(f"URL extraction error: {str(e)}")
            return []
    
    def scrape_content(self, urls: List[str]) -> int:
        """
        Scrape content from extracted URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Number of successfully scraped articles
        """
        if not urls:
            logger.warning("⚠️ No URLs to scrape")
            return 0
        
        logger.info(f"🕷️ Scraping content from {len(urls)} URLs...")
        stage_start = time.time()
        
        try:
            urls_file = "urls/slack_channel_links_extracted.txt"
            output_dir = "results"
            
            # Ensure directories exist
            Path(output_dir).mkdir(exist_ok=True)
            
            process_urls_and_extract_content(urls_file, output_dir)
            
            # Count scraped files
            scraped_files = list(Path(output_dir).glob("*.json"))
            scraped_count = len(scraped_files)
            
            logger.info(f"✅ Successfully scraped {scraped_count} articles")
            self.stats["stages"]["content_scraping"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "articles_scraped": scraped_count,
                "message": f"Scraped {scraped_count} articles"
            }
            return scraped_count
            
        except Exception as e:
            logger.error(f"❌ Error scraping content: {str(e)}")
            self.stats["errors"].append(f"Content scraping error: {str(e)}")
            return 0
    
    def classify_articles(self, scraped_count: int) -> Dict[str, Any]:
        """
        Run AI classification on scraped articles.
        
        Args:
            scraped_count: Number of scraped articles
            
        Returns:
            Classification results and statistics
        """
        if scraped_count == 0:
            logger.warning("⚠️ No articles to classify")
            return {}
        
        logger.info(f"🤖 Classifying {scraped_count} articles with AI agents...")
        stage_start = time.time()
        
        try:
            # Import the graph after ensuring all dependencies are available
            from news_classifier_agents import graph
            
            results = process_top_stories(graph)
            
            logger.info("✅ AI classification completed successfully")
            
            # Get classification statistics
            excel_path = "classified_news/analyzed_results.xlsx"
            stats = self._get_classification_stats(excel_path)
            
            self.stats["stages"]["ai_classification"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "classification_stats": stats,
                "message": f"Classified {scraped_count} articles"
            }
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error in AI classification: {str(e)}")
            self.stats["errors"].append(f"AI classification error: {str(e)}")
            return {}
    
    def post_results(self, classification_stats: Dict[str, Any]) -> bool:
        """
        Post classification results to Slack.
        
        Args:
            classification_stats: Statistics from classification
            
        Returns:
            True if posting successful, False otherwise
        """
        if not classification_stats:
            logger.warning("⚠️ No classification results to post")
            return False
        
        logger.info("📤 Posting classification results to Slack...")
        stage_start = time.time()
        
        try:
            post_stories_to_slack(self.config["slack_channel_target"])
            
            logger.info("✅ Results posted to Slack successfully")
            self.stats["stages"]["results_posting"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "message": "Results posted to Slack"
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting results: {str(e)}")
            self.stats["errors"].append(f"Results posting error: {str(e)}")
            return False
    
    def cleanup_and_archive(self) -> None:
        """Clean up temporary files and archive results"""
        if not self.config["cleanup_after"]:
            logger.info("🧹 Cleanup disabled, skipping...")
            return
        
        logger.info("🧹 Cleaning up and archiving results...")
        stage_start = time.time()
        
        try:
            # Move Excel results to historical folder
            excel_path = "classified_news/analyzed_results.xlsx"
            historical_excel_path = "historical_classified_news"
            
            if Path(excel_path).exists():
                move_file(excel_path, historical_excel_path)
            
            # Clean processed folders
            clean_processed_folders()
            
            logger.info("✅ Cleanup and archiving completed")
            self.stats["stages"]["cleanup"] = {
                "duration": time.time() - stage_start,
                "status": "success",
                "message": "Cleanup completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
            self.stats["warnings"].append(f"Cleanup error: {str(e)}")
    
    def _get_classification_stats(self, excel_path: str) -> Dict[str, Any]:
        """Get statistics from classification results"""
        try:
            if not Path(excel_path).exists():
                return {"message": "No results file found"}
            
            # Basic file stats
            file_size = Path(excel_path).stat().st_size
            return {
                "results_file_size": file_size,
                "results_file_exists": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not get classification stats: {str(e)}")
            return {"error": str(e)}
    
    def execute_full_pipeline(self) -> bool:
        """
        Execute the complete pipeline.
        
        Returns:
            True if pipeline completed successfully, False otherwise
        """
        logger.info("🚀 Starting full news classification pipeline...")
        logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        try:
            # Stage 1: Run tests (if enabled)
            if self.config["run_tests"]:
                if not self.run_tests():
                    logger.error("❌ Pipeline aborted due to test failures")
                    return False
            else:
                logger.info("⏭️ Skipping tests as requested")
            
            # Stage 2: Extract URLs
            urls = self.extract_urls()
            if not urls:
                logger.warning("⚠️ No new URLs found, pipeline completed with no work")
                return True
            
            # Stage 3: Scrape content
            scraped_count = self.scrape_content(urls)
            if scraped_count == 0:
                logger.error("❌ No content scraped, aborting pipeline")
                return False
            
            # Stage 4: Classify articles
            classification_stats = self.classify_articles(scraped_count)
            
            # Stage 5: Post results
            self.post_results(classification_stats)
            
            # Stage 6: Cleanup
            self.cleanup_and_archive()
            
            # Final statistics
            end_time = datetime.now()
            total_duration = (end_time - self.start_time).total_seconds()
            
            self.stats.update({
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "status": "completed_successfully" if not self.stats["errors"] else "completed_with_errors"
            })
            
            logger.info(f"🎉 Pipeline completed successfully in {total_duration:.1f} seconds")
            logger.info(f"📊 Final statistics: {json.dumps(self.stats, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical pipeline error: {str(e)}")
            self.stats["errors"].append(f"Critical error: {str(e)}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        return self.stats.copy()


def main():
    """Main entry point"""
    try:
        executor = PipelineExecutor()
        success = executor.execute_full_pipeline()
        
        # Write stats to file
        stats_file = f"pipeline_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(executor.get_pipeline_stats(), f, indent=2)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 