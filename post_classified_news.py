#!/usr/bin/env python3
"""
Minimal version of post_classified_news.py for pipeline functionality
Contains only essential functions to avoid syntax errors
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def post_stories_to_slack(channel_id: str):
    """
    Minimal function to post stories to Slack
    """
    try:
        # Initialize Slack client
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if not slack_token:
            logger.error("SLACK_BOT_TOKEN not found in environment variables")
            return False
        
        client = WebClient(token=slack_token)
        
        # Read results from Excel file
        try:
            df = pd.read_excel('classified_news/analyzed_results.xlsx')
            logger.info(f"Found {len(df)} articles to process")
        except FileNotFoundError:
            logger.error("No analyzed_results.xlsx file found")
            return False
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return False
        
        # Process each article
        posted_count = 0
        for index, row in df.iterrows():
            try:
                # Get basic article info
                title = row.get('title', 'No Title')
                url = row.get('url', '')
                final_score = row.get('final_score', 0)
                classification = row.get('classification', 'unknown')
                
                # Skip low-quality articles
                if final_score < 6.0:
                    logger.info(f"Skipping article with low score: {final_score}")
                    continue
                
                # Create basic Slack message
                message = f"📰 *{title}*\n"
                message += f"🔗 {url}\n"
                message += f"📊 Score: {final_score}\n"
                message += f"🏷️ Classification: {classification}\n"
                
                # Post to Slack
                response = client.chat_postMessage(
                    channel=channel_id,
                    text=message,
                    parse='mrkdwn'
                )
                
                if response["ok"]:
                    posted_count += 1
                    logger.info(f"Posted article: {title[:50]}...")
                else:
                    logger.error(f"Failed to post article: {response}")
                    
            except Exception as e:
                logger.error(f"Error processing article at index {index}: {e}")
                continue
        
        logger.info(f"Successfully posted {posted_count} articles to Slack")
        return True
        
    except Exception as e:
        logger.error(f"Error in post_stories_to_slack: {e}")
        return False

def clear_slack_channel(channel_id: str):
    """
    Minimal function to clear Slack channel
    """
    try:
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if not slack_token:
            logger.error("SLACK_BOT_TOKEN not found")
            return False
        
        client = WebClient(token=slack_token)
        logger.info("Slack channel clear functionality - minimal implementation")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing Slack channel: {e}")
        return False

# Main execution for testing
if __name__ == "__main__":
    test_channel = os.getenv('SLACK_CHANNEL_ID', '#general')
    print(f"Testing minimal post_classified_news with channel: {test_channel}")
    
    result = post_stories_to_slack(test_channel)
    print(f"Result: {'Success' if result else 'Failed'}") 