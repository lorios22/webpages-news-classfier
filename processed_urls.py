import pandas as pd
import os

def process_urls(excel_path: str, processed_urls_path: str):
    """
    Process URLs from Excel file and update processed URLs list.
    
    Args:
        excel_path (str): Path to Excel file with URLs
        processed_urls_path (str): Path to file containing processed URLs
    """
    try:
        # Read Excel file and get URLs
        df = pd.read_excel(excel_path)
        if 'url' not in df.columns:
            return set()
            
        new_urls = set(df['url'].dropna().tolist())
        
        # Get existing processed URLs
        processed_urls = set()
        if os.path.exists(processed_urls_path):
            with open(processed_urls_path, 'r') as f:
                processed_urls = set(f.read().splitlines())
        
        # Filter and add new URLs
        urls_to_process = new_urls - processed_urls
        with open(processed_urls_path, 'a') as f:
            for url in urls_to_process:
                f.write(url + '\n')
                
        return urls_to_process
        
    except Exception as e:
        print(f"Error processing URLs: {str(e)}")
        return set()