import os 
import shutil
from datetime import datetime

def move_file(source_path, dest_path):
    """Move a file from source path to destination path with unique timestamp"""
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(dest_path, exist_ok=True)
        
        # Get filename from source
        source_filename = os.path.basename(source_path)
        filename_no_ext = os.path.splitext(source_filename)[0]
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{filename_no_ext}_{timestamp}.xlsx"
        new_dest_path = os.path.join(dest_path, new_filename)
        
        # If file exists, increment counter until unique name found
        counter = 1
        while os.path.exists(new_dest_path):
            new_filename = f"{filename_no_ext}_{timestamp}_{counter}.xlsx"
            new_dest_path = os.path.join(dest_path, new_filename)
            counter += 1
            
        # Copy file to destination path
        shutil.copy2(source_path, new_dest_path)
        print(f"Successfully copied file from {source_path} to {new_dest_path}")
        
        # Also copy to root historical folder
        root_historical = "historical_classified_news"
        os.makedirs(root_historical, exist_ok=True)
        root_dest = os.path.join(root_historical, new_filename)
        shutil.copy2(source_path, root_dest)
        print(f"Successfully copied file to root historical folder: {root_dest}")
        
    except Exception as e:
        print(f"Error copying file: {e}")

def clean_processed_folders():
    """Remove all files from directories including .xlsx files"""
    dirs_to_clean = [
        "news_classifier_webpages/classified_news",
        "news_classifier_webpages/results"
    ]
    
    for directory in dirs_to_clean:
        try:
            # Si el directorio existe, elimínalo completamente
            if os.path.exists(directory):
                shutil.rmtree(directory)
            
            # Crea el directorio nuevamente
            os.makedirs(directory)
            print(f"Directory {directory} cleaned and recreated successfully")
            
        except Exception as e:
            print(f"Error cleaning directory {directory}: {e}")