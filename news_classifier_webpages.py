import os 
from dotenv import load_dotenv
import json

from extract_slack_urls import extract_slack_urls
from webscrapping import process_urls_and_extract_content
from agents_process import process_top_stories
# from news_classifier_agents import graph  # Commented out due to syntax error
from processed_urls import process_urls
from post_classified_news import post_stories_to_slack
from clean_folders_move_file import clean_processed_folders, move_file

from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Slack channel ids
channel_id = os.getenv("SLACK_CHANNEL_ID_WEBSCRAPPER")
channel_id_to_post = os.getenv("SLACK_CHANNEL_ID_TO_POST_CLASSIFIED_NEWS_WEBPAGES")

# Paths to the files and folders 
excel_path = "news_classifier_webpages/classified_news/analyzed_results.xlsx"
historical_excel_path = "news_classifier_webpages/historical_classified_news"
processed_urls_path= "news_classifier_webpages/urls/processed_urls.txt"
urls_file = "news_classifier_webpages/urls/slack_channel_links_extracted.txt"
output_dir = "news_classifier_webpages/results"

#urls = extract_slack_urls(channel_id, urls_file, processed_urls_path, limit=1000)

#process_urls_and_extract_content(urls_file,output_dir)

process_top_stories(graph)

#process_urls(excel_path, processed_urls_path)

#post_stories_to_slack(channel_id_to_post)

#move_file(excel_path, historical_excel_path)

#clean_processed_folders()