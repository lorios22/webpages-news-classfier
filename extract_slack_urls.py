import logging
import os
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to show INFO level messages in console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Slack client instance using bot token
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def extract_slack_urls(channel_id, output_file, processed_urls_path, limit):
    """
    Extracts and saves unique URLs from a Slack channel that are not in processed_urls.txt.
    
    Parameters:
        channel_id (str): ID of the Slack channel to extract URLs from
        output_file (str): Path to save new URLs
        limit (int): Maximum number of messages to review
        
    Returns:
        set: Set of new unique URLs found in the channel
    """
    try:
        # Get processed URLs
        processed_urls = set()
        if os.path.exists(processed_urls_path):
            with open(processed_urls_path, 'r', encoding='utf-8') as f:
                processed_urls = set(f.read().splitlines())

        # Get messages from channel
        response = client.conversations_history(channel=channel_id, limit=limit)
        messages = response["messages"]
        new_urls = set()

        # Extract URLs from messages
        for msg in messages:
            if 'text' in msg:
                for url in re.findall(r'(https?://[^\s]+)', msg['text']):
                    if "novatide" not in url and url not in processed_urls:
                        new_urls.add(url)
            
            if 'attachments' in msg:
                for attachment in msg['attachments']:
                    if 'from_url' in attachment:
                        url = attachment['from_url']
                        if "novatide" not in url and url not in processed_urls:
                            new_urls.add(url)

        # Save only new URLs to file
        with open(output_file, 'w', encoding='utf-8') as file:
            for url in new_urls:
                file.write(url + '\n')
                
        logger.info(f"Extracted and saved {len(new_urls)} new unique URLs from channel {channel_id}")
        return new_urls

    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return set()
    except Exception as e:
        logger.error(f"Error extracting URLs: {str(e)}")
        return set()

# Example usage:
# urls = extract_slack_urls("CHANNEL_ID", "output_file.txt", limit=100)