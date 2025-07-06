import os
import logging
import time
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import re

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Slack client
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

def clean_score_string(score_str):
    """Clean and extract first valid float from a string."""
    # Remove any non-numeric characters except decimal points
    # Keep only first occurrence of decimal point
    cleaned = ''
    decimal_found = False
    for c in score_str:
        if c.isdigit():
            cleaned += c
        elif c == '.' and not decimal_found:
            cleaned += c
            decimal_found = True
    
    # Return first valid float or 0.0 if none found
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def safe_slack_text(text, limit=3000):
    """Safely format text for Slack blocks."""
    if not text:
        return ""
    # Remove any null bytes or other invalid characters
    text = ''.join(char for char in text if ord(char) >= 32)
    # Replace problematic characters
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Remove zero-width spaces and other invisible characters
    text = ''.join(c for c in text if c.isprintable() or c.isspace())
    # Ensure text is not empty after cleaning
    return text[:limit] if text.strip() else "No content available"

def validate_blocks(blocks):
    """Validate and clean blocks before sending to Slack."""
    MAX_BLOCKS = 50
    cleaned_blocks = []
    
    for block in blocks[:MAX_BLOCKS]:  # Limit total number of blocks
        try:
            # Ensure block has required type field
            if "type" not in block:
                logger.warning("Skipping block without type")
                continue

            # Deep copy the block to avoid modifying the original
            cleaned_block = json.loads(json.dumps(block))
            
            if cleaned_block["type"] == "section":
                if "text" not in cleaned_block:
                    logger.warning("Skipping section block without text")
                    continue
                if cleaned_block["text"]["type"] == "mrkdwn":
                    cleaned_block["text"]["text"] = safe_slack_text(cleaned_block["text"]["text"], 3000)
                elif cleaned_block["text"]["type"] == "plain_text":
                    cleaned_block["text"]["text"] = safe_slack_text(cleaned_block["text"]["text"], 150)
            
            elif cleaned_block["type"] == "divider":
                cleaned_block = {"type": "divider"}
            
            elif cleaned_block["type"] == "header":
                if "text" not in cleaned_block or "text" not in cleaned_block["text"]:
                    logger.warning("Skipping header block without text")
                    continue
                cleaned_block["text"]["text"] = safe_slack_text(cleaned_block["text"]["text"], 150)
                cleaned_block["text"]["type"] = "plain_text"
            
            elif cleaned_block["type"] == "input":
                # Validate input block structure
                if "label" not in cleaned_block or "element" not in cleaned_block:
                    logger.warning("Skipping invalid input block")
                    continue
                
                # Ensure label is properly formatted
                if isinstance(cleaned_block["label"], dict):
                    cleaned_block["label"]["type"] = "plain_text"
                    cleaned_block["label"]["text"] = safe_slack_text(cleaned_block["label"]["text"], 150)
                
                # Handle different input element types
                if cleaned_block["element"]["type"] == "plain_text_input":
                    if "placeholder" in cleaned_block["element"]:
                        cleaned_block["element"]["placeholder"] = {
                            "type": "plain_text",
                            "text": safe_slack_text(cleaned_block["element"]["placeholder"]["text"], 150)
                        }
                
                elif cleaned_block["element"]["type"] == "number_input":
                    # Ensure min and max values are strings
                    if "min_value" in cleaned_block["element"]:
                        cleaned_block["element"]["min_value"] = str(cleaned_block["element"]["min_value"])
                    if "max_value" in cleaned_block["element"]:
                        cleaned_block["element"]["max_value"] = str(cleaned_block["element"]["max_value"])
                    if "placeholder" in cleaned_block["element"]:
                        cleaned_block["element"]["placeholder"] = {
                            "type": "plain_text",
                            "text": safe_slack_text(cleaned_block["element"]["placeholder"]["text"], 150)
                        }
            
            elif cleaned_block["type"] == "actions":
                if "elements" not in cleaned_block:
                    logger.warning("Skipping actions block without elements")
                    continue
                
                cleaned_elements = []
                for element in cleaned_block["elements"]:
                    if element["type"] == "button":
                        if "text" in element:
                            element["text"] = {
                                "type": "plain_text",
                                "text": safe_slack_text(element["text"]["text"], 75),
                                "emoji": True
                            }
                        if "value" in element:
                            element["value"] = str(element["value"])
                        cleaned_elements.append(element)
                
                cleaned_block["elements"] = cleaned_elements
            
            # Only append block if it's not empty after cleaning
            if cleaned_block:
                cleaned_blocks.append(cleaned_block)
        
        except Exception as e:
            logger.warning(f"Error processing block: {str(e)}")
            continue
    
    return cleaned_blocks

def send_blocks_in_batches(channel_id: str, blocks: list, title: str):
    """
    Divide y envía bloques en grupos de 50 o menos para cumplir con el límite de Slack.
    
    Args:
        channel_id (str): ID del canal de Slack
        blocks (list): Lista completa de bloques a enviar
        title (str): Título para usar como texto fallback
    """
    MAX_BLOCKS_PER_MESSAGE = 50
    total_blocks = len(blocks)
    
    for i in range(0, total_blocks, MAX_BLOCKS_PER_MESSAGE):
        batch = blocks[i:i + MAX_BLOCKS_PER_MESSAGE]
        
        # Agregar indicador de continuación si hay más mensajes
        if i + MAX_BLOCKS_PER_MESSAGE < total_blocks:
            batch.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⬇️ *Continuará en el siguiente mensaje...*"
                }
            })
        
        # Agregar indicador de parte del mensaje
        part_number = (i // MAX_BLOCKS_PER_MESSAGE) + 1
        total_parts = (total_blocks + MAX_BLOCKS_PER_MESSAGE - 1) // MAX_BLOCKS_PER_MESSAGE
        
        if total_parts > 1:
            batch.insert(0, {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📝 *Part {part_number} of {total_parts}*"
                }
            })
        
        try:
            # Validar y limpiar los bloques
            cleaned_batch = validate_blocks(batch)
            
            # Enviar el lote de bloques
            response = client.chat_postMessage(
                channel=channel_id,
                blocks=cleaned_batch,
                text=safe_slack_text(f"{title} (Parte {part_number}/{total_parts})" if total_parts > 1 else title)
            )
            logger.info(f"Successfully posted batch {part_number}/{total_parts}")
            time.sleep(2)  # Pausa entre mensajes
            
        except SlackApiError as e:
            error_msg = str(e.response['error'])
            logger.error(f"Error sending batch {part_number}: {error_msg}")
            if hasattr(e.response, 'data'):
                logger.error(f"Error details: {json.dumps(e.response.data, indent=2)}")

def clear_slack_channel(channel_id: str):
    """
    Deletes all messages in the specified Slack channel.
    
    Args:
        channel_id (str): The ID of the Slack channel to clear
    """
    try:
        # Get channel history
        logger.info(f"Starting to clear channel {channel_id}")
        
        has_more = True
        cursor = None
        
        def delete_with_retry(channel_id, ts, max_retries=3, base_delay=1):
            """Helper function to delete a message with exponential backoff retry"""
            for attempt in range(max_retries):
                try:
                    client.chat_delete(
                        channel=channel_id,
                        ts=ts
                    )
                    return True
                except SlackApiError as e:
                    if e.response['error'] == 'ratelimited':
                        # Get retry_after from headers or use exponential backoff
                        retry_after = float(e.response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                        logger.info(f"Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(retry_after)
                    else:
                        logger.warning(f"Could not delete message {ts}: {str(e)}")
                        return False
            return False
        
        while has_more:
            try:
                # Get messages in batches
                result = client.conversations_history(
                    channel=channel_id,
                    cursor=cursor,
                    limit=100  # Maximum allowed by Slack API
                )
                
                messages = result.get('messages', [])
                
                # Delete each message
                for message in messages:
                    try:
                        # Only delete messages that our bot posted
                        if message.get('bot_id'):
                            success = delete_with_retry(channel_id, message['ts'])
                            if success:
                                # Increased delay between successful deletions
                                time.sleep(1.5)  # Increased from 0.5 to 1.5 seconds
                    except Exception as e:
                        logger.warning(f"Error deleting message {message.get('ts')}: {str(e)}")
                        continue
                
                # Check if there are more messages
                has_more = result['has_more']
                cursor = result.get('response_metadata', {}).get('next_cursor')
                
                if not cursor:
                    has_more = False
                    
                # Add delay between batch requests
                time.sleep(2)  # Add delay between batches
                    
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    # Get retry_after from headers or use default
                    retry_after = float(e.response.headers.get('Retry-After', 30))
                    logger.info(f"Rate limited on batch request. Waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    # Continue the loop to retry this batch
                    continue
                else:
                    logger.error(f"Error getting channel history: {str(e)}")
                    break
                
        logger.info("Finished clearing channel")
        
    except Exception as e:
        logger.error(f"Error clearing channel: {str(e)}")

def safe_parse_agent_content(raw_content, agent_name):
    """
    Safely parses agent content and returns formatted text
    """
    try:
        if not raw_content:
            return None
            
        # Try to parse as dict first
        if isinstance(raw_content, dict):
            content = raw_content.get('content', '')
        else:
            # Try to evaluate string representation
            try:
                parsed = eval(raw_content)
                content = parsed.get('content', '')
            except:
                content = raw_content

        # If content is a string that looks like JSON, try to parse it
        if isinstance(content, str) and content.strip().startswith('{'):
            try:
                content = json.loads(content)
            except:
                pass

        # Format based on content type
        if isinstance(content, dict):
            formatted = []
            for key, value in content.items():
                if isinstance(value, list):
                    formatted.append(f"*{key}:*\n• " + "\n• ".join(str(v) for v in value))
                else:
                    formatted.append(f"*{key}:* {value}")
            return "\n\n".join(formatted)
        else:
            return str(content)
            
    except Exception as e:
        logger.error(f"Error parsing {agent_name} content: {str(e)}")
        return None

def safe_json_loads(data):
    """Safely load JSON data from string or dict."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            try:
                return eval(data)
            except:
                return {}
    return {}

def safe_get_state(raw_data, state_field):
    """Safely extract state from raw agent data."""
    try:
        data = safe_json_loads(raw_data)
        if isinstance(data, dict):
            # Try to get state field directly
            state = data.get(state_field)
            if state:
                # Handle nested JSON string
                if isinstance(state, str):
                    try:
                        return json.loads(state)
                    except json.JSONDecodeError:
                        try:
                            return eval(state)
                        except:
                            return state
                return state
            # Try to get content field
            content = data.get('content')
            if content:
                if isinstance(content, str):
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            return eval(content)
                        except:
                            return content
                return content
        return data
    except Exception as e:
        logger.debug(f"Error processing state {state_field}: {str(e)}")
        return {}

def should_skip_content(row):
    """
    Check if content should be skipped based on various criteria:
    1. Any agent marked it as skip
    2. Missing essential agent data
    3. Incomplete processing - ALL agents must be present
    """
    try:
        # Define ALL required agents based on actual Excel columns
        all_required_agents = [
            'input_preprocessor_raw',
            'summary_agent_raw',
            'context_evaluator_raw',
            'fact_checker_raw',
            'depth_analyzer_raw',
            'relevance_analyzer_raw',
            'structure_analyzer_raw',
            'historical_reflection_raw',
            'score_consolidator_raw',
            'human_reasoning_raw',
            'consensus_agent_raw',
            'reflective_validator_raw',
            # 'metadata_ranking_agent_raw',  # This agent doesn't exist in current Excel
            'validator_raw'
        ]
        
        # Check if ALL agents have processed the content
        missing_agents = []
        for agent in all_required_agents:
            agent_data = row.get(agent, '')
            if not agent_data or str(agent_data).strip() == '' or str(agent_data) == 'nan':
                missing_agents.append(agent.replace('_raw', ''))
        
        if missing_agents:
            logger.info(f"Skipping content due to missing agents: {missing_agents}")
            return True, f"Missing required agents: {', '.join(missing_agents)}"
        
        # Check each agent for skip flags or processing errors
        agents_to_check = [
            ('input_preprocessor_raw', 'preprocessor_state'),
            ('summary_agent_raw', 'summary_state'),
            ('context_evaluator_raw', 'context_evaluator_state'),
            ('fact_checker_raw', 'fact_checker_state'),
            ('depth_analyzer_raw', 'depth_analyzer_state'),
            ('relevance_analyzer_raw', 'relevance_analyzer_state'),
            ('structure_analyzer_raw', 'structure_analyzer_state'),
            ('historical_reflection_raw', 'historical_reflection_state'),
            ('score_consolidator_raw', 'score_consolidator_state'),
            ('human_reasoning_raw', 'human_reasoning_state'),
            ('consensus_agent_raw', 'consensus_state'),
            ('reflective_validator_raw', 'reflective_validator_state'),
            # ('metadata_ranking_agent_raw', 'metadata_ranking_state'),  # Commented out - doesn't exist
            ('validator_raw', 'validator_state')
        ]
        
        for agent_field, state_field in agents_to_check:
            agent_raw = row.get(agent_field, '')
            if agent_raw:
                agent_data = safe_get_state(agent_raw, state_field)
                
                # Check for explicit skip flag
                if isinstance(agent_data, dict):
                    if agent_data.get('skip') == True:
                        skip_reason = agent_data.get('skip_reason', 'Unknown reason')
                        logger.info(f"Skipping content due to {agent_field}: {skip_reason}")
                        return True, f"{agent_field.replace('_raw', '')} skip: {skip_reason}"
                
                # Check for processing errors or invalid states
                if isinstance(agent_data, str) and any(error_indicator in agent_data.lower() for error_indicator in 
                    ['error', 'failed', 'exception', 'invalid', 'unable to process']):
                    logger.info(f"Skipping content due to processing error in {agent_field}")
                    return True, f"Processing error in {agent_field.replace('_raw', '')}"
        
        # Verify summary data is valid (essential for posting)
        summary_raw = row.get('summary_agent_raw', '{}')
        summary_data = safe_get_state(summary_raw, 'summary_state')
        
        if not isinstance(summary_data, dict):
            logger.info("Skipping content due to invalid summary data structure")
            return True, "Invalid summary data structure"
        
        title = summary_data.get('title')
        summary = summary_data.get('summary')
        
        if not title or not summary:
            logger.info("Skipping content due to missing title or summary")
            return True, "Missing title or summary in summary data"
        
        # If we get here, all agents have processed successfully without skip flags
        logger.info("Content passed all agent validation checks - proceeding to post")
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking skip conditions: {str(e)}")
        return True, f"Error in skip check: {str(e)}"

def get_agent_completion_status(row):
    """
    Check which agents have successfully processed the content
    """
    all_agents = [
        'input_preprocessor_raw',
        'summary_agent_raw', 
        'context_evaluator_raw',
        'fact_checker_raw',
        'depth_analyzer_raw',
        'relevance_analyzer_raw',
        'structure_analyzer_raw',
        'historical_reflection_raw',
        'score_consolidator_raw',
        'human_reasoning_raw',
        'consensus_agent_raw',
        'reflective_validator_raw',
        # 'metadata_ranking_agent_raw',  # This agent doesn't exist in current Excel
        'validator_raw'
    ]
    
    completed_agents = []
    missing_agents = []
    
    for agent in all_agents:
        agent_data = row.get(agent, '')
        if agent_data and str(agent_data).strip() != '' and str(agent_data) != 'nan':
            completed_agents.append(agent.replace('_raw', ''))
        else:
            missing_agents.append(agent.replace('_raw', ''))
    
    completion_percentage = (len(completed_agents) / len(all_agents)) * 100
    
    return {
        'completed_agents': completed_agents,
        'missing_agents': missing_agents,
        'completion_percentage': completion_percentage,
        'total_agents': len(all_agents),
        'completed_count': len(completed_agents)
    }

def process_agent_for_display(agent_field, agent_content, completion_status):
    """
    Process agent content for display, returning blocks with complete agent analysis
    """
    try:
        if not agent_content or str(agent_content).strip() == '' or str(agent_content) == 'nan':
            return []
        
        # Check if this agent is in the completed list
        agent_name = agent_field.replace('_raw', '')
        if agent_name not in completion_status['completed_agents']:
            return []
        
        blocks = []
        
        try:
            # Parse the agent content
            content_dict = safe_json_loads(agent_content)
            
            if isinstance(content_dict, dict):
                # Look for state field first
                state_field = agent_field.replace('_raw', '_state')
                state_content = content_dict.get(state_field, '')
                
                if state_content:
                    # Show more complete state content
                    formatted_content = format_complete_state_content(state_content, agent_field)
                    if formatted_content:
                        blocks.append({
                            "type": "section",
                "text": {
                                "type": "mrkdwn",
                                "text": formatted_content[:2900]
                            }
                        })
                else:
                    # Look for other meaningful fields and show more content
                    meaningful_content = extract_complete_agent_content(content_dict, agent_field)
                    if meaningful_content:
                        blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                                "text": meaningful_content[:2900]
                            }
                        })
        else:
                # If content is a string, show it directly with some formatting
                if isinstance(agent_content, str) and len(agent_content) > 50:
                    clean_content = agent_content.replace('\\n', '\n')[:2500]
                    blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                            "text": f"```{clean_content}```"
                        }
                    })
                
        except Exception as e:
            logger.debug(f"Error parsing {agent_field}: {str(e)}")
            # Fallback: show raw content in a code block
            if isinstance(agent_content, str) and len(agent_content) > 20:
                clean_content = str(agent_content)[:2500]
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{clean_content}```"
                    }
                })
        
        return blocks
        
    except Exception as e:
        logger.error(f"Error processing agent {agent_field}: {str(e)}")
        return []

def format_complete_state_content(state_content, agent_field):
    """
    Format state content with better readability and structure
    """
    try:
        if isinstance(state_content, str):
            # Clean and format string content with better structure
            content = state_content.replace('\\n', '\n')
            
            # Remove JSON artifacts
            content = content.replace('{"', '').replace('"}', '').replace('\\"', '"')
            
            # Split into lines and format with better spacing
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            formatted_sections = []
            current_section = []
                
                for line in lines:
                # Skip structural elements but be more permissive
                if (len(line) > 5 and 
                    not line.startswith('---') and
                    not line == '{}' and 
                    not line == '{' and 
                    not line == '}'):
                    
                    # Clean the line
                    clean_line = line.replace('",', '').replace('":', ':').replace('"', '')
                    
                    # Detect different types of content for better formatting
                    if ':' in clean_line and not clean_line.startswith('•'):
                        # This looks like a key-value pair
                        if 'score' in clean_line.lower():
                            formatted_sections.append(f"📊 {clean_line}")
                        elif any(word in clean_line.lower() for word in ['reason', 'explanation', 'justification']):
                            formatted_sections.append(f"💭 {clean_line}")
                        elif 'category' in clean_line.lower() or 'level' in clean_line.lower():
                            formatted_sections.append(f"🏷️ {clean_line}")
                        else:
                            formatted_sections.append(f"• {clean_line}")
                    else:
                        # Regular content
                        if not clean_line.startswith('•'):
                            formatted_sections.append(f"• {clean_line}")
                        else:
                            formatted_sections.append(clean_line)
                    
                    if len(formatted_sections) >= 12:  # Reasonable limit
                            break
                
            return '\n\n'.join(formatted_sections) if formatted_sections else None
            
        elif isinstance(state_content, dict):
            # Format dictionary content with better structure
            formatted_sections = []
            
            # Group by content type for better organization
            scores = {}
            explanations = {}
            other_fields = {}
            
            for key, value in state_content.items():
                key_lower = key.lower()
                if 'score' in key_lower:
                    scores[key] = value
                elif any(word in key_lower for word in ['reason', 'explanation', 'justification', 'assessment']):
                    explanations[key] = value
                else:
                    other_fields[key] = value
            
            # Format scores first
            if scores:
                formatted_sections.append("📊 Scores & Metrics:")
                for key, value in scores.items():
                    clean_key = key.replace('_', ' ').title()
                    if isinstance(value, (int, float)):
                        formatted_sections.append(f"   • {clean_key}: `{value}`")
                    else:
                        formatted_sections.append(f"   • {clean_key}: {str(value)[:100]}")
            
            # Format explanations
            if explanations:
                formatted_sections.append("💭 Analysis & Reasoning:")
                for key, value in explanations.items():
                    clean_key = key.replace('_', ' ').title()
                    if isinstance(value, str) and len(value) > 20:
                        # Format long text with proper line breaks
                        clean_value = value[:400].replace('\\n', '\n')
                        formatted_sections.append(f"   • {clean_key}: {clean_value}")
                        if len(value) > 400:
                            formatted_sections.append("     _(truncated...)_")
            
            # Format other fields
            if other_fields:
                formatted_sections.append("🔍 Additional Details:")
                for key, value in list(other_fields.items())[:6]:  # Limit to 6 items
                    clean_key = key.replace('_', ' ').title()
                    if isinstance(value, (int, float)):
                        formatted_sections.append(f"   • {clean_key}: `{value}`")
                    elif isinstance(value, str) and len(value) < 200:
                        formatted_sections.append(f"   • {clean_key}: {value}")
                    elif isinstance(value, bool):
                        formatted_sections.append(f"   • {clean_key}: {'✅ Yes' if value else '❌ No'}")
                    elif isinstance(value, list) and len(value) < 5:
                        items = ', '.join(str(item)[:50] for item in value)
                        formatted_sections.append(f"   • {clean_key}: {items}")
                    elif isinstance(value, dict):
                        formatted_sections.append(f"   • {clean_key}: {format_compact_dict(value)}")
            
            return '\n\n'.join(formatted_sections) if formatted_sections else None
        
        return None
        
    except Exception as e:
        logger.debug(f"Error formatting complete state content: {str(e)}")
        return None

def format_compact_dict(data, max_items=3):
    """
    Format dictionary in a compact, readable way
    """
    try:
        if not isinstance(data, dict):
            return str(data)[:100]
        
        items = []
        for key, value in list(data.items())[:max_items]:
            clean_key = str(key).replace('_', ' ').title()
            if isinstance(value, (int, float)):
                items.append(f"{clean_key}: `{value}`")
            elif isinstance(value, str) and len(value) < 50:
                items.append(f"{clean_key}: {value}")
            elif isinstance(value, bool):
                items.append(f"{clean_key}: {'✅' if value else '❌'}")
            else:
                items.append(f"{clean_key}: {str(value)[:30]}...")
        
        result = ' | '.join(items)
        if len(data) > max_items:
            result += f" _(+{len(data) - max_items} more)_"
        
        return result
        
    except Exception:
        return str(data)[:100]

def extract_complete_agent_content(content_dict, agent_field):
    """
    Extract and format complete content from agent dictionary with better structure
    """
    try:
        sections = []
        
        # Special handling for different agent types
        if 'fact_checker' in agent_field:
            sections.extend(format_fact_checker_content(content_dict))
        elif 'consensus' in agent_field:
            sections.extend(format_consensus_content(content_dict))
        else:
            sections.extend(format_general_agent_content(content_dict))
        
        return '\n\n'.join(sections[:6]) if sections else None  # Limit to 6 sections
        
    except Exception as e:
        logger.debug(f"Error extracting complete agent content: {str(e)}")
        return None

def format_fact_checker_content(content_dict):
    """
    Special formatting for fact checker agent
    """
    sections = []
    
    if 'claims' in content_dict:
        claims_data = content_dict['claims']
        sections.append("🔍 Fact Check Results:")
        
        if isinstance(claims_data, list):
            for i, claim in enumerate(claims_data[:5]):  # Limit to 5 claims
                if isinstance(claim, dict):
                    text = claim.get('text', 'No text')[:80]
                    veracity = claim.get('veracity', 'UNKNOWN')
                    veracity_icon = '✅' if veracity == 'TRUE' else '❌' if veracity == 'FALSE' else '❓'
                    sections.append(f"   {i+1}. {text} {veracity_icon} _{veracity}_")
    
    # Add other relevant fields
    for key, value in content_dict.items():
        if key in ['credibility_score', 'cred_impact'] and isinstance(value, (str, int, float)):
            clean_key = key.replace('_', ' ').title()
            sections.append(f"📊 {clean_key}: {value}")
    
    return sections

def format_consensus_content(content_dict):
    """
    Special formatting for consensus agent
    """
    sections = []
    
    if 'consensus_state' in content_dict or any('score' in str(k).lower() for k in content_dict.keys()):
        sections.append("🤝 Consensus Analysis:")
        
        # Look for consensus state or score data
        for key, value in content_dict.items():
            if isinstance(value, dict) and ('score' in str(value) or 'consensus' in str(value)):
                formatted_dict = format_compact_dict(value, max_items=4)
                sections.append(f"   • {key.replace('_', ' ').title()}: {formatted_dict}")
            elif 'score' in key.lower() and isinstance(value, (int, float)):
                sections.append(f"   • {key.replace('_', ' ').title()}: `{value}`")
    
    return sections

def format_general_agent_content(content_dict):
    """
    General formatting for other agents
    """
    sections = []
    
    # Group fields by type
    scores = {}
    text_fields = {}
    other_fields = {}
    
    for key, value in content_dict.items():
        if 'score' in key.lower() and isinstance(value, (int, float)):
            scores[key] = value
        elif isinstance(value, str) and len(value) > 20:
            text_fields[key] = value
        else:
            other_fields[key] = value
    
    # Format scores
    if scores:
        sections.append("📊 Scores:")
        for key, value in scores.items():
            clean_key = key.replace('_', ' ').title()
            sections.append(f"   • {clean_key}: `{value}`")
    
    # Format text fields
    if text_fields:
        sections.append("📝 Analysis:")
        for key, value in list(text_fields.items())[:3]:  # Limit to 3 fields
            clean_key = key.replace('_', ' ').title()
            clean_value = value[:300].replace('\\n', ' ')
            sections.append(f"   • {clean_key}: {clean_value}")
            if len(value) > 300:
                sections.append("     _(truncated...)_")
    
    # Format other fields
    if other_fields:
        sections.append("🔍 Details:")
        for key, value in list(other_fields.items())[:3]:  # Limit to 3 fields
            clean_key = key.replace('_', ' ').title()
            if isinstance(value, bool):
                sections.append(f"   • {clean_key}: {'✅ Yes' if value else '❌ No'}")
            elif isinstance(value, (list, dict)):
                sections.append(f"   • {clean_key}: {format_compact_dict(value) if isinstance(value, dict) else str(value)[:100]}")
            else:
                sections.append(f"   • {clean_key}: {str(value)[:100]}")
    
    return sections

def process_preprocessor_content(agent_content):
    """Enhanced preprocessor content processing"""
    blocks = []
    try:
        content_dict = safe_json_loads(agent_content)
        if isinstance(content_dict, dict):
            preprocessor_state_str = content_dict.get('preprocessor_state', '')
            if preprocessor_state_str:
                # Extract and format metadata
                metadata_match = re.search(r'METADATA:\n------------------------------\n(.*?)(?=\n\nCONTENT:)', 
                                        preprocessor_state_str, re.DOTALL)
                if metadata_match:
                    metadata = metadata_match.group(1).strip()
                    blocks.extend([
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*📋 Extracted Metadata:*\n```{metadata[:1000]}```"
                            }
                        }
                    ])
    except Exception as e:
        logger.debug(f"Error processing preprocessor content: {str(e)}")
    
    return blocks

def process_metadata_ranking_content(agent_content):
    """Enhanced metadata ranking content processing"""
    blocks = []
    try:
        content_dict = safe_json_loads(agent_content)
        if isinstance(content_dict, dict):
            metadata_state_str = content_dict.get('metadata_ranking_state', '')
            if metadata_state_str and isinstance(metadata_state_str, str):
                # Extract credibility score
                score_match = re.search(r'"credibility_score":\s*([\d.]+)', metadata_state_str)
                reason_match = re.search(r'"reason":\s*"([^"]+)"', metadata_state_str)
                
                if score_match:
                    score = float(score_match.group(1))
                    score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Credibility Score:* {score_emoji} {score}/10"
                        }
                    })
                
                if reason_match:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Assessment:* {reason_match.group(1)}"
                        }
                    })
    except Exception as e:
        logger.debug(f"Error processing metadata ranking content: {str(e)}")
    
    return blocks

def process_validator_content(agent_content):
    """Enhanced validator content processing"""
    blocks = []
    try:
        # Extract validation report sections
        if isinstance(agent_content, str) and "VALIDATION REPORT" in agent_content:
            parts = agent_content.split("VALIDATION REPORT ----------------")
            if len(parts) > 1:
                content = parts[1].split("\n\n")[0].strip()
                if content:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Validation Summary:*\n{content[:1500]}"
                        }
                    })
    except Exception as e:
        logger.debug(f"Error processing validator content: {str(e)}")
    
    return blocks

def post_stories_to_slack(channel_id: str):
    """
    Posts news content to Slack from Excel file with URL, content, and validation inputs.
    Only posts content that has been processed by ALL agents without skip flags.
    """
    excel_path = "news_classifier_webpages/classified_news/analyzed_results.xlsx"
    
    try:
        # Clear the channel first
        clear_slack_channel(channel_id)
        
        df = pd.read_excel(excel_path)
        logger.info(f"Found {len(df)} rows in Excel file")
        logger.info(f"Excel columns: {df.columns.tolist()}")
        
        # Statistics tracking
        total_rows = len(df)
        processed_count = 0
        skipped_count = 0
        skip_reasons = {}
        
        # Debug: Print first row's summary_agent_raw content
        if len(df) > 0:
            logger.debug("First row summary_agent_raw content:")
            logger.debug(df['summary_agent_raw'].iloc[0])
            logger.debug("Type of summary_agent_raw:")
            logger.debug(type(df['summary_agent_raw'].iloc[0]))
        
        for index, row in df.iterrows():
            try:
                # Check if content should be skipped
                should_skip, skip_reason = should_skip_content(row)
                if should_skip:
                    skipped_count += 1
                    # Track skip reasons for statistics
                    reason_category = skip_reason.split(':')[0] if ':' in skip_reason else skip_reason
                    skip_reasons[reason_category] = skip_reasons.get(reason_category, 0) + 1
                    logger.info(f"Row {index} - SKIPPED: {skip_reason}")
                    continue
                
                logger.info(f"Row {index} - PROCESSING: Content passed all validation checks")
                
                # Get agent completion status
                completion_status = get_agent_completion_status(row)
                logger.info(f"Row {index} - Agent completion: {completion_status['completed_count']}/{completion_status['total_agents']} agents ({completion_status['completion_percentage']:.1f}%)")

                # Process validator content first
                validation_raw = row.get('validator_raw', '')
                validation_data = safe_get_state(validation_raw, 'validator_state')
                
                # Extract score
                score = None
                if validation_data and isinstance(validation_data, dict):
                    score = validation_data.get('final_score')
                
                if score is None and isinstance(validation_raw, str):
                    # Try regex patterns if no score found
                    score_patterns = [
                        r"FINAL SCORE -------------------\nScore:\s*(\d+\.?\d*)",
                        r"MANDATORY ADJUSTMENTS -----------\nAdjusted Score:\s*(\d+\.?\d*)",
                        r"Original Score:\s*(\d+\.?\d*)",
                    ]
                    
                    for pattern in score_patterns:
                        match = re.search(pattern, validation_raw)
                        if match:
                            score_str = match.group(1)
                            score = clean_score_string(score_str)
                            break

                if score is None:
                    score = 0.0
                    logger.info(f"Row {index} - No score found, defaulting to 0.0")

                # Process summary agent content
                summary_raw = row.get('summary_agent_raw', '{}')
                summary_data = safe_get_state(summary_raw, 'summary_state')
                
                title = None
                summary = None
                key_points = []
                entities = []
                statistics = []
                
                if isinstance(summary_data, dict):
                    title = summary_data.get('title')
                    summary = summary_data.get('summary')
                    key_points = summary_data.get('key_points', [])
                    entities = summary_data.get('entities', [])
                    statistics = summary_data.get('statistics', [])

                if not title or not summary:
                    logger.info(f"Row {index} - Skipping due to missing title or summary")
                    continue

                # Extract URL from content field
                url = row.get('url', '')
                if not url:
                    url = "No source URL provided"

                # Extract justification from validation_data
                justification = None
                if validation_data and isinstance(validation_data, str):
                    if 'JUSTIFICATION ----------------\n' in validation_data:
                        justification_parts = validation_data.split('JUSTIFICATION ----------------\n')
                        if len(justification_parts) > 1:
                            justification = justification_parts[1].split('\n\n')[0].strip()

                # Initialize blocks with header
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"📰 {title[:140]}" if title else "📰 No title",
                            "emoji": True
                        }
                    }
                ]

                # Add URL if exists
                if url and url != "No source URL provided":
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🔗 *Source URL*\n{url[:2000]}"
                        }
                    })

                blocks.append({"type": "divider"})

                # Add summary if exists
                if summary:
                    blocks.extend([
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Executive Summary",
                                "emoji": True
                            }
                        },
                        {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                                "text": summary[:2900]
                        }
                        }
                    ])

                # Add key points if they exist
                if key_points:
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📌 Key Points",
                            "emoji": True
                        }
                    })

                    # Format key points nicely
                    for point in key_points[:8]:  # Limit to 8 points
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"• {point}"
                            }
                        })

                # Add entities if they exist
                if entities:
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "👥 Key Entities",
                            "emoji": True
                        }
                    })

                    # Group entities in a single block for better readability
                    entity_text = "\n".join([f"• {entity}" for entity in entities[:8]])
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                            "text": entity_text
                            }
                        })

                # Add statistics if they exist
                if statistics:
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📈 Key Statistics",
                            "emoji": True
                        }
                    })

                    # Group statistics in a single block
                    stats_text = "\n".join([f"• {stat}" for stat in statistics[:8]])
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                            "text": stats_text
                            }
                        })

                blocks.append({"type": "divider"})

                # Add a header for AI analysis
                blocks.extend([
                    {"type": "divider"},
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🤖 Detailed AI Agent Analysis",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Analysis from {completion_status['completed_count']} AI agents that successfully processed this content."
                        }
                    }
                ])

                # Add other agents' analysis with improved formatting similar to Twitter version
                agents_to_process = [
                    ('input_preprocessor_raw', '🔍 Input Preprocessor Analysis'),
                    ('context_evaluator_raw', '📚 Context Evaluation'),
                    ('fact_checker_raw', '✔️ Fact Checking Results'),
                    ('depth_analyzer_raw', '🔬 Depth Analysis'),
                    ('relevance_analyzer_raw', '🎯 Relevance Analysis'),
                    ('structure_analyzer_raw', '🏗️ Structure Analysis'),
                    ('historical_reflection_raw', '📜 Historical Context'),
                    ('score_consolidator_raw', '📊 Score Analysis'),
                    ('human_reasoning_raw', '🧠 Human Reasoning Analysis'),
                    ('consensus_agent_raw', '🤝 Consensus Analysis'),
                    ('reflective_validator_raw', '🔄 Reflective Validation'),
                    ('validator_raw', '🔍 Final Validation')
                ]

                for agent_field, agent_title in agents_to_process:
                    agent_content = row.get(agent_field, '')
                    
                    if agent_content and isinstance(agent_content, str):
                        try:
                            # Add separator before each agent
                            if blocks and blocks[-1]["type"] != "divider":
                                blocks.append({"type": "divider"})

                            # Get agent state using improved processing
                            agent_state = None
                            try:
                                content_dict = safe_json_loads(agent_content)
                                if isinstance(content_dict, dict):
                                    state_field = agent_field.replace('_raw', '_state')
                                    agent_state = content_dict.get(state_field)
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = agent_state
                            except Exception as e:
                                logger.debug(f"Could not parse agent state for {agent_field}: {str(e)}")

                            # Process each agent type with improved formatting
                            if agent_field == 'input_preprocessor_raw':
                                try:
                                    content_dict = safe_json_loads(agent_content)                                    
                                    preprocessor_state = content_dict.get('preprocessor_state', {})
                                    
                                    if preprocessor_state:
                                        # Main Header
                blocks.append({
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                                                "text": "🔍 Input Preprocessor Analysis",
                        "emoji": True
                    }
                })
                
                                        # Check if content was skipped
                                        if preprocessor_state.get('skip', False):
                                            skip_reason = preprocessor_state.get('skip_reason', 'Unknown reason')
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "⚠️ *Content Status*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Status: Skipped\nReason: {skip_reason}"
                                                    }
                                                }
                                            ])
                                        else:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "✅ *Content Status*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "Status: Successfully processed"
                                                    }
                                                }
                                            ])
                                        
                                        # Content preview section
                                        cleaned_content = preprocessor_state.get('cleaned_content', '')
                                        if cleaned_content:
                                            blocks.extend([
                                                {
                                                    "type": "header",
                                                    "text": {
                                                        "type": "plain_text",
                                                        "text": "📄 Processed Content Preview",
                                                        "emoji": True
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": cleaned_content[:1500] + "..." if len(cleaned_content) > 1500 else cleaned_content
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing input preprocessor: {str(e)}")
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                                            "text": f"*Error processing input preprocessor:* {str(e)}"
                                        }
                                    })

                            elif agent_field == 'context_evaluator_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "📚 Context Evaluation",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'context_score' in agent_state:
                                            score = agent_state['context_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Context Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Quality Category
                                        if 'quality_category' in agent_state:
                                            category = agent_state['quality_category']
                                            category_emoji = "🏆" if "Excellent" in category else "✨" if "Good" in category else "📝"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{category_emoji} *Quality Assessment*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Category: {category}"
                                                    }
                                                }
                                            ])
                                        
                                        # Detailed Analysis
                                        if 'reasoning' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Detailed Analysis*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['reasoning'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing context_evaluator: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing context evaluator: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'fact_checker_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "✔️ Fact Checking Results",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Credibility Score
                                        if 'credibility_score' in agent_state:
                                            score = agent_state['credibility_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Credibility Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Claims Analysis
                                        if 'claims' in agent_state and agent_state['claims']:
                                            blocks.append({
                                                "type": "section",
                                                "text": {
                                                    "type": "mrkdwn",
                                                    "text": "🔍 *Claims Analysis*"
                                                }
                                            })
                                            
                                            for i, claim in enumerate(agent_state['claims'][:5], 1):  # Limit to 5 claims
                                                if isinstance(claim, dict):
                                                    text = claim.get('text', 'No text')[:100]
                                                    veracity = claim.get('veracity', 'UNKNOWN')
                                                    veracity_icon = '✅' if veracity == 'TRUE' else '❌' if veracity == 'FALSE' else '❓'
                                                    
                                                    blocks.append({
                                                        "type": "section",
                                                        "text": {
                                                            "type": "mrkdwn",
                                                            "text": f"   {i}. {text} {veracity_icon} _{veracity}_"
                                                        }
                                                    })
                                        
                                        # Impact Analysis
                                        if 'cred_impact' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Impact Analysis*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['cred_impact'][:1000]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing fact_checker: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing fact checker: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'depth_analyzer_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🔬 Depth Analysis",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'depth_score' in agent_state:
                                            score = agent_state['depth_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Depth Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Justification
                                        if 'justification' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Analysis Details*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['justification'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing depth_analyzer: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing depth analyzer: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'relevance_analyzer_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🎯 Relevance Analysis",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'relevance_score' in agent_state:
                                            score = agent_state['relevance_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Relevance Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Explanation
                                        if 'explanation' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Relevance Analysis*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['explanation'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing relevance_analyzer: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing relevance analyzer: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'structure_analyzer_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🏗️ Structure Analysis",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'structure_score' in agent_state:
                                            score = agent_state['structure_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Structure Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Explanation
                                        if 'explanation' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Structure Analysis*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['explanation'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing structure_analyzer: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing structure analyzer: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'historical_reflection_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "📜 Historical Context",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'historical_score' in agent_state:
                                            score = agent_state['historical_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Historical Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Pattern Analysis
                                        if 'pattern_analysis' in agent_state:
                                            pattern = agent_state['pattern_analysis']
                                            if isinstance(pattern, dict):
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📈 *Pattern Analysis*"
                                                    }
                                                })
                                                
                                                for key, value in pattern.items():
                                                    if key in ['trend_alignment', 'consistency']:
                                                        blocks.append({
                                                            "type": "section",
                                                            "text": {
                                                                "type": "mrkdwn",
                                                                "text": f"   • {key.replace('_', ' ').title()}: {value}"
                                                            }
                                                        })
                                        
                                        # Adjustment Rationale
                                        if 'adjustment_rationale' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Analysis Rationale*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['adjustment_rationale'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing historical_reflection: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing historical reflection: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'human_reasoning_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🧠 Human Reasoning Analysis",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score Section
                                        if 'human_score' in agent_state:
                                            score = agent_state['human_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Human Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Reasoning breakdown
                                        if 'reasoning' in agent_state:
                                            reasoning = agent_state['reasoning']
                                            if isinstance(reasoning, dict):
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📊 *Quality Metrics*"
                                                    }
                                                })
                                                
                                                for key, value in reasoning.items():
                                                    if key in ['readability', 'practical_value', 'engagement', 'trust']:
                                                        blocks.append({
                                                            "type": "section",
                                                            "text": {
                                                                "type": "mrkdwn",
                                                                "text": f"   • {key.replace('_', ' ').title()}: {value}"
                                                            }
                                                        })
                                        
                                        # Explanation
                                        if 'explanation' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Detailed Explanation*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['explanation'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing human_reasoning: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing human reasoning: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'score_consolidator_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "📊 Score Consolidation",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Raw Score
                                        if 'raw_consolidated_score' in agent_state:
                                            score = float(agent_state['raw_consolidated_score'])
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Raw Consolidated Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        # Warnings
                                        if 'warnings' in agent_state and agent_state['warnings']:
                                            blocks.append({
                                                "type": "section",
                                                "text": {
                                                    "type": "mrkdwn",
                                                    "text": "⚠️ *Warnings*"
                                                }
                                            })
                                            
                                            for warning in agent_state['warnings']:
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"   • {warning}"
                                                    }
                                                })
                                        
                                        # Human Review Required
                                        if 'requires_human_review' in agent_state:
                                            review_needed = agent_state['requires_human_review']
                                            review_emoji = "🚨" if review_needed else "✅"
                                            review_text = "Required" if review_needed else "Not Required"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{review_emoji} *Human Review*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Status: {review_text}"
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing score_consolidator: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing score consolidator: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'consensus_agent_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🤝 Consensus Analysis",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Scores Section
                                        blocks.append({
                                            "type": "section",
                                            "text": {
                                                "type": "mrkdwn",
                                                "text": "📊 *Overall Scores*"
                                            }
                                        })
                                        
                                        score_fields = ['human_score', 'weighted_score', 'score_difference']
                                        for field in score_fields:
                                            if field in agent_state:
                                                value = agent_state[field]
                                                if field == 'score_difference':
                                                    diff_emoji = "⚠️" if value > 1 else "✅"
                                                    blocks.append({
                                                        "type": "section",
                                                        "text": {
                                                            "type": "mrkdwn",
                                                            "text": f"   • {field.replace('_', ' ').title()}: {diff_emoji} {value:.2f}"
                                                        }
                                                    })
                                                else:
                                                    blocks.append({
                                                        "type": "section",
                                                        "text": {
                                                            "type": "mrkdwn",
                                                            "text": f"   • {field.replace('_', ' ').title()}: `{value}/10`"
                                                        }
                                                    })
                                        
                                        # Divergence Status
                                        if 'has_significant_divergence' in agent_state:
                                            status = agent_state['has_significant_divergence']
                                            status_emoji = "⚠️" if status else "✅"
                                            status_text = "Significant divergence detected" if status else "Scores are consistent"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "🔍 *Divergence Status*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{status_emoji} {status_text}"
                                                    }
                                                }
                                            ])
                                        
                                        # Sub-scores
                                        if 'sub_scores' in agent_state:
                                            blocks.append({
                                                "type": "section",
                                                "text": {
                                                    "type": "mrkdwn",
                                                    "text": "📈 *Detailed Sub-scores*"
                                                }
                                            })
                                            
                                            sub_scores = agent_state['sub_scores']
                                            for category, score in sub_scores.items():
                                                score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"   • {category.title()}: {score_emoji} `{score}/10`"
                                                    }
                                                })
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing consensus_agent: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing consensus agent: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'reflective_validator_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🔄 Reflective Validation",
                                            "emoji": True
                                        }
                                    })
                                    
                                    if isinstance(agent_state, str):
                                        try:
                                            agent_state = json.loads(agent_state)
                                        except:
                                            agent_state = {}
                                    
                                    if isinstance(agent_state, dict):
                                        # Score and Validation Result
                                        if 'reflective_score' in agent_state:
                                            score = agent_state['reflective_score']
                                            score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{score_emoji} *Reflective Score*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Score: `{score}/10`"
                                                    }
                                                }
                                            ])
                                        
                                        if 'validation_result' in agent_state:
                                            result = agent_state['validation_result']
                                            result_emoji = "✅" if result == "pass" else "❌"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{result_emoji} *Validation Result*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"Result: {result.title()}"
                                                    }
                                                }
                                            ])
                                        
                                        # Recommendations
                                        if 'recommendations' in agent_state and agent_state['recommendations']:
                                            blocks.append({
                                                "type": "section",
                                                "text": {
                                                    "type": "mrkdwn",
                                                    "text": "💡 *Recommendations*"
                                                }
                                            })
                                            
                                            for recommendation in agent_state['recommendations']:
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"   • {recommendation}"
                                                    }
                                                })
                                        
                                        # Score Rationale
                                        if 'score_rationale' in agent_state:
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "📝 *Score Rationale*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": agent_state['score_rationale'][:1200]
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing reflective_validator: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing reflective validator: {str(e)}"
                                        }
                                    })

                            elif agent_field == 'validator_raw':
                                try:
                                    # Main Header
                                    blocks.append({
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🔍 Final Validation",
                                            "emoji": True
                                        }
                                    })
                                    
                                    content_dict = safe_json_loads(agent_content)                                    
                                    validator_state = content_dict.get('validator_state', {})
                                    
                                    if isinstance(validator_state, dict):
                                        # Final Score
                                        score_fields = ['human_score', 'weighted_score']
                                        for field in score_fields:
                                            if field in validator_state:
                                                score = validator_state[field]
                                                score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                                
                                                blocks.extend([
                                                    {
                                                        "type": "section",
                                                        "text": {
                                                            "type": "mrkdwn",
                                                            "text": f"{score_emoji} *{field.replace('_', ' ').title()}*"
                                                        }
                                                    },
                                                    {
                                                        "type": "section",
                                                        "text": {
                                                            "type": "mrkdwn",
                                                            "text": f"Score: `{score}/10`"
                                                        }
                                                    }
                                                ])
                                        
                                        # Sub-scores
                                        if 'sub_scores' in validator_state:
                                            blocks.append({
                                                "type": "section",
                                                "text": {
                                                    "type": "mrkdwn",
                                                    "text": "📈 *Detailed Sub-scores*"
                                                }
                                            })
                                            
                                            sub_scores = validator_state['sub_scores']
                                            for category, score in sub_scores.items():
                                                score_emoji = "⭐" if score >= 8 else "✨" if score >= 6 else "📊"
                                                blocks.append({
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"   • {category.title()}: {score_emoji} `{score}/10`"
                                                    }
                                                })
                                        
                                        # Divergence Status
                                        if 'has_significant_divergence' in validator_state:
                                            status = validator_state['has_significant_divergence']
                                            status_emoji = "⚠️" if status else "✅"
                                            status_text = "Significant divergence detected" if status else "Scores are consistent"
                                            
                                            blocks.extend([
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": "🔍 *Divergence Status*"
                                                    }
                                                },
                                                {
                                                    "type": "section",
                                                    "text": {
                                                        "type": "mrkdwn",
                                                        "text": f"{status_emoji} {status_text}"
                                                    }
                                                }
                                            ])
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing validator: {str(e)}")
                                    blocks.append({
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": f"Error processing validator: {str(e)}"
                                        }
                                    })

                        except Exception as e:
                            logger.warning(f"Could not process {agent_field}: {str(e)}")
                            continue

                blocks.append({"type": "divider"})

                # Add AI analysis if score or justification exists
                if score or justification:
                    # Main Header for AI Analysis
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🔍 Final AI Analysis Results",
                            "emoji": True
                        }
                    })
                    
                    blocks.append({"type": "divider"})
                    
                    # Format validation report sections
                    if isinstance(validation_data, str):
                        # Validation Report Section
                        if "VALIDATION REPORT" in validation_data:
                            parts = validation_data.split("VALIDATION REPORT ----------------")
                            if len(parts) > 1:
                                content = parts[1].split("\n\n")[0].strip()
                                # Split content into individual lines
                                content_lines = content.split("\n")
                                
                                blocks.extend([
                                    {
                                        "type": "header",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "📋 Validation Report",
                                            "emoji": True
                                        }
                                    }
                                ])
                                
                                # Add each line as a separate block
                                for line in content_lines:
                                    if line.strip():
                                        blocks.append({
                                            "type": "section",
                                            "text": {
                                                "type": "mrkdwn",
                                                "text": line.strip()
                                            }
                                        })
                                        blocks.append({"type": "divider"})
                    
                    blocks.append({"type": "divider"})

                blocks.append({"type": "divider"})

                # Add human validation section
                blocks.extend([
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "✍️ Human Validation",
                            "emoji": True
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📝 Assessment Instructions",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Please provide your detailed assessment of this content below. Consider all aspects analyzed by the agents above."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "input",
                        "block_id": "score_block",
                        "label": {
                            "type": "plain_text",
                            "text": "📊 Evaluation Score (0.0-10.0)",
                            "emoji": True
                        },
                        "element": {
                            "type": "number_input",
                            "is_decimal_allowed": True,
                            "action_id": "user_score",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Enter a score between 0.0-10.0",
                                "emoji": True
                            },
                            "min_value": "0.0",
                            "max_value": "10.0"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "justification_block",
                        "label": {
                            "type": "plain_text",
                            "text": "📝 Detailed Justification",
                            "emoji": True
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True,
                            "action_id": "user_justification",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Please provide your detailed reasoning and analysis, including strengths, weaknesses, and overall assessment...",
                                "emoji": True
                            }
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "actions",
                        "block_id": "actions_block",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "✅ Submit Evaluation",
                                    "emoji": True
                                },
                                "style": "primary",
                                "value": "submit_validation",
                                "action_id": "submit_user_validation"
                            }
                        ]
                    }
                ])
                        
                # Post single message with all content
                try:
                    # Validate and clean blocks before sending
                    cleaned_blocks = validate_blocks(blocks)
                    
                    # Log block count and types for debugging
                    logger.debug(f"Sending {len(cleaned_blocks)} blocks to Slack")
                    block_types = [block.get('type') for block in cleaned_blocks]
                    logger.debug(f"Block types: {block_types}")
                    
                    # Usar la nueva función para enviar los bloques en lotes
                    send_blocks_in_batches(
                        channel_id=channel_id,
                        blocks=blocks,  # Usar los bloques originales, no los cleaned_blocks
                        title=safe_slack_text(title[:150] if title else "No title")
                    )
                    logger.info(f"Row {index} - Successfully posted to Slack")
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    continue
                
            except Exception as e:
                logger.error(f"Error processing row {index}: {str(e)}")
                continue
        
        # Print final statistics
        logger.info("="*60)
        logger.info("FINAL PROCESSING STATISTICS")
        logger.info("="*60)
        logger.info(f"Total rows in Excel: {total_rows}")
        logger.info(f"Successfully processed and posted: {processed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Success rate: {(processed_count/total_rows)*100:.1f}%")
        
        if skip_reasons:
            logger.info("\nSkip reasons breakdown:")
            for reason, count in skip_reasons.items():
                logger.info(f"  - {reason}: {count} rows")
        
        logger.info("="*60)
                
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")