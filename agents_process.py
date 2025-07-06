import os
import json
from typing import List
import pandas as pd

def process_top_stories(graph):
    # Change directory path to the results folder
    results_dir = "news_classifier_webpages/results/"
    
    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        results = []
        
        for json_file in json_files:
            file_path = os.path.join(results_dir, json_file)
            print(f"\nProcessing File: {json_file}")
            
            try:
                # Read JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    json_data = json.load(file)
                    
                    # Extract content from the JSON structure
                    content_data = json_data.get('content', {})
                    url = content_data.get('url', '')
                    title = content_data.get('title', '')
                    description = content_data.get('description', '')
                    main_content = content_data.get('content', '')
                    
                    # Combine all content for analysis
                    full_content = f"""
                    Title: {title}
                    Description: {description}
                    Content: {main_content}
                    """

                    # Create initial state with content and content type
                    initial_state = {
                        "content": full_content,
                        "content_types": ["text"]
                    }

                    # Process with graph
                    responses = graph.stream(initial_state)
                    
                    result = {
                        "url": url,
                        "title": title,
                        "description": description,
                        "content": main_content,
                        "source_file": json_file
                    }
                    
                    # Process each agent's response
                    for response in responses:
                        if "__end__" not in response:
                            for agent_name, agent_output in response.items():
                                # Store raw agent output for all agents
                                result[f"{agent_name}_raw"] = str(agent_output)
                                print(f"\n{agent_name} Response processed")
                    
                    results.append(result)
                    
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")
                results.append({
                    "filename": json_file,
                    "error": str(e)
                })
                continue
                
            print("=" * 80)

        # Save results to Excel
        df = pd.DataFrame(results)
        output_excel = "news_classifier_webpages/classified_news/analyzed_results.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"\nAnalysis results saved to {output_excel}")
        
    except Exception as e:
        print(f"Critical error: {str(e)}")
        if results:
            pd.DataFrame(results).to_excel("error_recovery.xlsx", index=False)