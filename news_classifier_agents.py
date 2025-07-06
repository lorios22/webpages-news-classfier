import json
from typing import Dict, List, Optional
from typing_extensions import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
import re

from assistant.configuration import Configuration
from assistant.state import ClassifierState
from assistant.prompts import (input_preprocessor_instructions, context_evaluator_instructions,
                             fact_checker_instructions, depth_analyzer_instructions,
                             relevance_analyzer_instructions, structure_analyzer_instructions,
                             historical_reflection_instructions, consolidation_instructions,
                             human_reasoning_instructions, consensus_instructions,
                             reflective_validator_instructions, validator_instructions,
                             metadata_ranking_instructions, summary_instructions)
from assistant.utils import (clean_and_structure_content, load_classification_rules, 
                           verify_claim, extract_claims, consolidate_score, 
                           human_like_adjustment)

def summary_agent(state: ClassifierState, config: RunnableConfig):
    """Generate a concise summary and title of the webpage content"""
    
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="o3-mini")
    
    # Extract raw content from state
    raw_content = state.content
    
    result = llm.invoke([
        SystemMessage(content=summary_instructions),
        HumanMessage(content=raw_content)
    ])
    
    # Store result in summary_state and agent_responses
    state.summary_state = result.content
    state.agent_responses = getattr(state, 'agent_responses', {})
    state.agent_responses['summary_agent'] = result.content

    return {
        "summary_state": state.summary_state,
        "agent_responses": state.agent_responses
    }

def clean_webpage_content(content: str) -> str:
    """
    Cleans webpage content by removing unnecessary elements and formatting.
    """
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove common webpage elements
    content = re.sub(r'cookie[s]? policy|privacy policy|terms of service|accept cookies', '', content, flags=re.IGNORECASE)
    
    # Remove URLs
    content = re.sub(r'https?://\S+', '', content)
    
    return content.strip()

def input_preprocessor(state: ClassifierState, config: RunnableConfig):
    """Clean and structure raw webpage input"""
    
    # Extract raw content from state
    raw_content = state.content
    
    # Clean the webpage content
    cleaned_content = clean_webpage_content(raw_content)
    
    # Apply pre-filters to determine if content should be skipped
    should_skip = False
    skip_reason = None
    
    # Check minimum content length
    if len(cleaned_content.split()) < 50:
        should_skip = True
        skip_reason = "Content too short (minimum 50 words required)"
        print(f"\nSkipping content - {skip_reason}")
    
    # Check for spam indicators
    spam_indicators = ['buy now', 'click here', 'limited time', 'special offer', 'discount', 'sale']
    if any(indicator in cleaned_content.lower() for indicator in spam_indicators):
        should_skip = True
        skip_reason = "Spam indicators detected in content"
        print(f"\nSkipping content - {skip_reason}")
    
    # If content should be skipped, return early with skip flag
    if should_skip:
        preprocessor_state = {
            "skip": True,
            "skip_reason": skip_reason,
            "cleaned_content": cleaned_content
        }
        state.preprocessor_state = preprocessor_state
        state.agent_responses = getattr(state, 'agent_responses', {})
        state.agent_responses['input_preprocessor'] = preprocessor_state
    return {
            "preprocessor_state": state.preprocessor_state,
            "agent_responses": state.agent_responses
        }
    
    print("\nContent passed preprocessor filters - continuing with analysis")
    
    # If content passes filters, return cleaned and structured data
    preprocessor_state = {
        "skip": False,
        "cleaned_content": cleaned_content
    }
    state.preprocessor_state = preprocessor_state
    state.agent_responses = getattr(state, 'agent_responses', {})
    state.agent_responses['input_preprocessor'] = preprocessor_state
    return {
        "preprocessor_state": state.preprocessor_state,
        "agent_responses": state.agent_responses
    }

def context_evaluator(state: ClassifierState, config: RunnableConfig):
    """
    Evaluates the webpage's overall quality and context.
    Provides an initial quality score and determines if further analysis is needed.
    """
    # Extract preprocessed content from state
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
        
    # Load classification rules
    rules = load_classification_rules()
    
    # Create a streamlined prompt for GPT-3.5
    context_evaluator_prompt = f"""You are a webpage content evaluator. Evaluate the content's overall quality (0.1–10.0) per these guidelines:

1. Assess accuracy/truthfulness:
   - Is the information factual and verifiable?
   - Are claims supported by evidence?
   - Does it avoid misleading statements?

2. Assess intent:
   - Is the primary purpose to inform or mislead?
   - Is there a clear informational value?
   - Does it avoid clickbait or sensationalism?

3. Assess context completeness:
   - Does it provide sufficient context?
   - Is it self-contained or does it rely on external knowledge?
   - Does it avoid vague or incomplete information?

Use these categories as reference:
- Extremely Poor (0.1-2.0): Misinformation, scams, completely false
- Very Poor (2.1-3.0): Highly misleading, poor quality
- Fair (3.1-5.0): Basic information, some accuracy issues
- Good (5.1-6.5): Reliable information, minor issues
- Very Good (6.6-7.5): High-quality information
- Excellent (7.6-8.5): Exceptional quality, well-researched
- Outstanding (8.6-10.0): Definitive source, comprehensive

Output a JSON with:
1. "context_score": A number between 0.1 and 10.0
2. "reasoning": Brief explanation of the score
3. "quality_category": One of the categories above
4. "should_continue": true/false (set to false if score < 3.0)
"""
    
    llm = ChatOpenAI(model="o3-mini")
    
    result = llm.invoke([
        SystemMessage(content=context_evaluator_prompt),
        HumanMessage(content=content)
    ])
    
    # Parse the result to get the context score
    try:
        result_dict = json.loads(result.content)
        context_score = float(result_dict.get("context_score", 5.0))
        should_continue = result_dict.get("should_continue", True)
        
        if context_score < 3.0:
            should_continue = False
    
    state.context_evaluator_state = result.content
        
        if not should_continue:
            state.skip_further_analysis = True
            state.skip_reason = f"Low context score: {context_score}"
            
    except Exception as e:
        print(f"Error parsing context evaluator result: {e}")
        context_score = 5.0
        state.context_evaluator_state = result.content
        state.skip_further_analysis = False
    
    return {
        "context_evaluator_state": state.context_evaluator_state,
        "skip_further_analysis": getattr(state, 'skip_further_analysis', False),
        "skip_reason": getattr(state, 'skip_reason', None)
    }

def fact_checker(state: ClassifierState, config: RunnableConfig):
    """
    Verifies factual claims in the webpage content using GPT-4.
    Identifies false or misleading claims and assesses their impact on credibility.
    """
    # Extract preprocessed content
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
    
    # Load classification rules
    rules = load_classification_rules()
    
    fact_checker_prompt = """You are a fact-checking expert. Verify factual claims in the webpage content.

Identify and verify each factual claim:
- Label FALSE claims that are inaccurate
- Label TRUE claims that are supported
- Label UNVERIFIED claims that cannot be verified

Format response as JSON:
{
  "claims": [
    {"text": "claim text", "veracity": "TRUE/FALSE/UNVERIFIED"}
  ],
  "cred_impact": "How findings affect credibility",
  "credibility_score": number between 1.0 and 10.0
}
"""
    
    llm = ChatOpenAI(model="gpt-4")
    
    result = llm.invoke([
        SystemMessage(content=fact_checker_prompt),
        HumanMessage(content=content)
    ])
    
    state.fact_checker_state = result.content

    try:
        result_dict = json.loads(result.content)
        credibility_score = float(result_dict.get("credibility_score", 5.0))
        state.fact_checker_score = credibility_score
    except Exception as e:
        print(f"Error parsing fact checker result: {e}")
        state.fact_checker_score = 5.0

    return {
        "fact_checker_state": state.fact_checker_state,
        "fact_checker_score": getattr(state, 'fact_checker_score', 5.0)
    }

def depth_analyzer(state: ClassifierState, config: RunnableConfig):
    """
    Analyzes the technical depth and complexity of the webpage content.
    """
    # Extract preprocessed content
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
        
    depth_analyzer_prompt = """You are a technical content analyzer. Rate the depth and complexity (1-10):
1 = very superficial
5 = moderate technical discussion
10 = highly technical analysis

Consider:
- Technical terminology usage
- Concept complexity
- Analysis depth
- Data/statistics presence
- Discussion thoroughness

Format as JSON:
{
  "depth_score": number between 1 and 10,
  "justification": "Brief explanation"
}
"""
    
    llm = ChatOpenAI(model="o3-mini")
    
    result = llm.invoke([
        SystemMessage(content=depth_analyzer_prompt),
        HumanMessage(content=content)
    ])
    
    state.depth_analyzer_state = result.content

    try:
        result_dict = json.loads(result.content)
        depth_score = float(result_dict.get("depth_score", 5.0))
        state.depth_analyzer_score = depth_score
    except Exception as e:
        print(f"Error parsing depth analyzer result: {e}")
        state.depth_analyzer_score = 5.0

    return {
        "depth_analyzer_state": state.depth_analyzer_state,
        "depth_analyzer_score": getattr(state, 'depth_analyzer_score', 5.0)
    }

def relevance_analyzer(state: ClassifierState, config: RunnableConfig):
    """
    Analyzes the relevance and impact of the webpage content.
    Returns a direct relevance score from 1-10.
    """
    # Extract preprocessed content
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
    
    relevance_analyzer_prompt = """You are a content relevance analyzer. Rate the significance and impact of this webpage content on a scale of 1-10.

Consider:
- Is this major news/information? (9-10 points)
- Does it affect many users/readers? (7-8 points) 
- Is it about significant developments? (6-7 points)
- Is it timely and important? (5-6 points)
- Is it minor or personal opinion? (1-4 points)

Format as JSON:
{
  "relevance_score": number between 1.0 and 10.0,
  "explanation": "Brief explanation of the score"
}
"""
    
    llm = ChatOpenAI(model="o3-mini")
    
    result = llm.invoke([
        SystemMessage(content=relevance_analyzer_prompt),
        HumanMessage(content=content)
    ])
    
    state.relevance_analyzer_state = result.content
    
    try:
        result_dict = json.loads(result.content)
        relevance_score = float(result_dict.get("relevance_score", 5.0))
        state.relevance_analyzer_score = relevance_score
        
    except Exception as e:
        print(f"Error parsing relevance analyzer result: {e}")
        state.relevance_analyzer_score = 5.0
    
    return {
        "relevance_analyzer_state": state.relevance_analyzer_state,
        "relevance_analyzer_score": getattr(state, 'relevance_analyzer_score', 5.0)
    }

def structure_analyzer(state: ClassifierState, config: RunnableConfig):
    """
    Analyzes the writing quality and structure of the webpage content.
    """
    # Extract preprocessed content
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
    
    # Apply programmatic checks
    structure_score = 7.0  # Default score
    
    # Check for unusual capitalization
    if content.isupper() or (sum(1 for c in content if c.isupper()) / len(content) > 0.7):
        structure_score = min(structure_score, 5.0)
    
    # Check for excessive punctuation
    if content.count('!') > 3 or content.count('?') > 3:
        structure_score = min(structure_score, 5.0)
    
    structure_analyzer_prompt = """You are a writing quality analyzer. Evaluate clarity and structure.

Consider:
- Logical organization
- Clear language
- Appropriate formatting
- Grammar and phrasing
- Professional tone

Format as JSON:
{
  "structure_score": number between 1 and 10,
  "explanation": "Brief explanation"
}
"""
    
    llm = ChatOpenAI(model="o3-mini")
    
    result = llm.invoke([
        SystemMessage(content=structure_analyzer_prompt),
        HumanMessage(content=content)
    ])
    
    state.structure_analyzer_state = result.content
    
    try:
        result_dict = json.loads(result.content)
        llm_structure_score = float(result_dict.get("structure_score", 7.0))
        final_structure_score = min(llm_structure_score, structure_score)
        state.structure_analyzer_score = final_structure_score
    except Exception as e:
        print(f"Error parsing structure analyzer result: {e}")
        state.structure_analyzer_score = structure_score

    return {
        "structure_analyzer_state": state.structure_analyzer_state,
        "structure_analyzer_score": getattr(state, 'structure_analyzer_score', 7.0)
    }

def historical_reflection(state: ClassifierState, config: RunnableConfig):
    # Compare with historical patterns
    #configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="o3-mini")
    
    # Load classification rules
    rules = load_classification_rules()
    
    # Combine cleaned content with rules for LLM analysis
    combined_content = f"""
    Cleaned Content:
    {state.preprocessor_state}
    
    Classification Rules:
    {rules}
    """
    
    result = llm.invoke([
        SystemMessage(content=historical_reflection_instructions),
        HumanMessage(content=combined_content)
    ])
    
    state.historical_reflection_state = result.content

    return {
        "historical_reflection_state": state.historical_reflection_state
    }

def human_reasoning(state: ClassifierState, config: RunnableConfig):
    """
    Applies human-like reasoning to evaluate content quality and relevance
    """
    llm = ChatOpenAI(model="o3-mini")
        
    # Get cleaned content
    preprocessor_state = state.preprocessor_state
    if not preprocessor_state:
        content = state.content
    else:
        content = preprocessor_state.get('cleaned_content', state.content)
    
    human_reasoning_prompt = """You are a human evaluator. Rate this content's quality and value from 1-10:

Consider:
- Readability and clarity
- Practical value to readers
- Engagement level
- Trustworthiness
- Overall quality

Format as JSON:
{
    "human_score": number between 1.0 and 10.0,
    "reasoning": {
        "readability": "high|medium|low",
        "practical_value": "high|medium|low",
        "engagement": "high|medium|low",
        "trust": "high|medium|low"
    },
    "explanation": "Brief explanation of score"
}
"""
    
    result = llm.invoke([
        SystemMessage(content=human_reasoning_prompt),
        HumanMessage(content=content)
    ])
    
    try:
        result_dict = json.loads(result.content)
        human_score = float(result_dict.get("human_score", 5.0))
        state.human_reasoning_score = human_score
    except Exception as e:
        print(f"Error parsing human reasoning result: {e}")
        state.human_reasoning_score = 5.0
    
    state.human_reasoning_state = result.content
    
    return {
        "human_reasoning_state": state.human_reasoning_state,
        "human_reasoning_score": state.human_reasoning_score
    }
    
def reflective_validator(state: ClassifierState, config: RunnableConfig):
    # Validate results through reflection
    #configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="o3-mini")
    
    # Load classification rules
    rules = load_classification_rules()
    
    # Combine cleaned content with rules for LLM analysis
    combined_content = f"""
    Cleaned Content:
    {state.preprocessor_state}
    
    Classification Rules:
    {rules}
    """
    
    result = llm.invoke([
        SystemMessage(content=reflective_validator_instructions),
        HumanMessage(content=combined_content)
    ])
    
    state.reflective_validator_state = result.content
    
    return {
        "reflective_validator_state": state.reflective_validator_state
    }
    

def score_consolidator(state: ClassifierState, config: RunnableConfig):
    # Consolidate all scores
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="o3-mini") 
    
    # Load classification rules
    rules = load_classification_rules()
    
    # Clean and structure the raw content
    cleaned_content = clean_and_structure_content(state.content)
    
    # Combine cleaned content with rules for LLM analysis
    combined_content = f"""
    Cleaned Content:
    {cleaned_content}
    
    Classification Rules:
    {rules}
    """
    
    result = llm.invoke([
        SystemMessage(content=consolidation_instructions),
        HumanMessage(content=combined_content)
    ])
    
    def extract_context_evaluator(content_str: str) -> float:
        try:
            # Buscar el patrón "historical_adjustment": "+X.X" o "-X.X"
            match = re.search(r'"final_score":\s*"([+-]?\d*\.?\d*)"', content_str)
            if match:
                print("Match found:", match.group(1))
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
    
    def extract_credibility(content_str: str) -> float:
        try:
        # Buscar el patrón "credibility": "X.X"
            print("This is the content", content_str)
            match = re.search(r'"credibility":\s*"(\d+\.?\d*)"', content_str)
            if match:
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_depth_score(content_str: str) -> float:
        try:
        # Buscar el patrón "credibility": "X.X"
            match = re.search(r'"depth_score":\s*"(\d+\.?\d*)"', content_str)
            if match:
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
             
    def extract_relevance_score(content_str: str) -> float:
        try:
        # Buscar el patrón "credibility": "X.X"
            match = re.search(r'"relevance_score":\s*"(\d+\.?\d*)"', content_str)
            if match:
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_structure_score(content_str: str) -> float:
        try:
        # Buscar el patrón "credibility": "X.X"
            match = re.search(r'"structure_score":\s*"(\d+\.?\d*)"', content_str)
            if match:
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_historical_adjustment(content_str: str) -> float:
        try:
            # Buscar el patrón "historical_adjustment": "+X.X" o "-X.X"
            match = re.search(r'"historical_adjustment":\s*"([+-]?\d*\.?\d*)"', content_str)
            if match:
                print("Match found:", match.group(1))
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_human_reasoning(content_str: str) -> float:
        try:
            # Buscar el patrón "historical_adjustment": "+X.X" o "-X.X"
            match = re.search(r'"final_score":\s*"([+-]?\d*\.?\d*)"', content_str)
            if match:
                print("Match found:", match.group(1))
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_reflective_validator(content_str: str) -> float:
        try:
            # Buscar el patrón "historical_adjustment": "+X.X" o "-X.X"
            match = re.search(r'"suggested_adjustment":\s*"([+-]?\d*\.?\d*)"', content_str)
            if match:
                print("Match found:", match.group(1))
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
    def extract_reflective_validator(content_str: str) -> float:
        try:
            # Buscar el patrón "historical_adjustment": "+X.X" o "-X.X"
            match = re.search(r'"suggested_adjustment":\s*"([+-]?\d*\.?\d*)"', content_str)
            if match:
                print("Match found:", match.group(1))
                return float(match.group(1))
            return 5.0  # valor por defecto
        except:
            return 5.0  # valor por defecto en caso de error
        
        
    context_evaluator = extract_context_evaluator(str(state.context_evaluator_state))
    credibility_score = extract_credibility(str(state.fact_checker_state))
    depth_score = extract_depth_score(str(state.depth_analyzer_state))
    relevance_score = extract_relevance_score(str(state.relevance_analyzer_state)) 
    structure_score = extract_structure_score(str(state.structure_analyzer_state))
    historical_adjustment = extract_historical_adjustment(str(state.historical_reflection_state))
    human_reasoning= extract_human_reasoning(str(state.human_reasoning_state))
    reflective_validator = extract_reflective_validator(str(state.reflective_validator_state))
    
    agent_outputs = {
        "context_evaluator": context_evaluator, 
        "fact_check": credibility_score,  
        "depth_analysis": depth_score,
        "relevance_assessment": relevance_score,
        "structure_analysis": structure_score,
        "historical_reflection": historical_adjustment,
        "human_reasoning": human_reasoning,
        "reflective_validator": reflective_validator,
    }

    # Use consolidate_score to validate and combine scores
    state.score_consolidator_state = consolidate_score(agent_outputs)
    
    return  {
        "score_consolidator_state": state.score_consolidator_state
    }

def consensus_agent(state: ClassifierState, config: RunnableConfig):
    """
    Calculates consensus from all analysis components.
    """
    try:
        # Extract the Human Reasoning score
        human_score = 5.0
        if hasattr(state, 'human_reasoning_state'):
            try:
                human_dict = json.loads(state.human_reasoning_state)
                human_score = float(human_dict.get("human_score", 5.0))
                print(f"Human score extracted: {human_score}")
            except Exception as e:
                print(f"Error parsing human_reasoning_state: {e}")
                pass
            
        # Context evaluator score
        context_score = 5.0
        if hasattr(state, 'context_evaluator_state'):
            try:
                context_dict = json.loads(state.context_evaluator_state)
                context_score = float(context_dict.get("context_score", 5.0))
                print(f"Context score extracted: {context_score}")
            except Exception as e:
                print(f"Error parsing context_evaluator_state: {e}")
                pass
        
        # Fact checker score
        fact_score = 5.0
        if hasattr(state, 'fact_checker_state'):
            try:
                fact_dict = json.loads(state.fact_checker_state)
                fact_score = float(fact_dict.get("credibility_score", 5.0))
                print(f"Fact score extracted: {fact_score}")
            except Exception as e:
                print(f"Error parsing fact_checker_state: {e}")
                pass
        
        # Depth score
        depth_score = 5.0
        if hasattr(state, 'depth_analyzer_state'):
            try:
                depth_dict = json.loads(state.depth_analyzer_state)
                depth_score = float(depth_dict.get("depth_score", 5.0))
                print(f"Depth score extracted: {depth_score}")
            except Exception as e:
                print(f"Error parsing depth_analyzer_state: {e}")
                pass
        
        # Relevance score - parse from JSON state
        relevance_score = 5.0
        if hasattr(state, 'relevance_analyzer_state'):
            try:
                relevance_dict = json.loads(state.relevance_analyzer_state)
                relevance_score = float(relevance_dict.get("relevance_score", 5.0))
                print(f"Relevance score extracted: {relevance_score}")
            except Exception as e:
                print(f"Error parsing relevance_analyzer_state: {e}")
                pass
            
        # Structure score
        structure_score = 5.0
        if hasattr(state, 'structure_analyzer_state'):
            try:
                structure_dict = json.loads(state.structure_analyzer_state)
                structure_score = float(structure_dict.get("structure_score", 5.0))
                print(f"Structure score extracted: {structure_score}")
            except Exception as e:
                print(f"Error parsing structure_analyzer_state: {e}")
                pass

        # Reflective validator score
        reflective_score = 5.0
        if hasattr(state, 'reflective_validator_state'):
            try:
                reflective_dict = json.loads(state.reflective_validator_state)
                reflective_score = float(reflective_dict.get("reflective_score", 5.0))
                print(f"Reflective score extracted: {reflective_score}")
            except Exception as e:
                print(f"Error parsing reflective_validator_state: {e}")
                pass
        
        # Define weights for each component
        weights = {
            "context": 0.15,
            "fact": 0.2,
            "depth": 0.1,
            "relevance": 0.1,
            "structure": 0.1,
            "human": 0.2,
            "reflective": 0.15
        }
        
        # Calculate weighted average
        weighted_score = (
            context_score * weights["context"] +
            fact_score * weights["fact"] +
            depth_score * weights["depth"] +
            relevance_score * weights["relevance"] +
            structure_score * weights["structure"] +
            human_score * weights["human"] +
            reflective_score * weights["reflective"]
        )
        
        # Clamp to valid range
        weighted_score = max(0.1, min(10.0, weighted_score))
        
        # Calculate difference between human score and weighted average
        score_difference = abs(human_score - weighted_score)
        
        # Flag if there's a significant divergence (more than 2 points)
        has_significant_divergence = score_difference > 2.0
        
        # Create the result
        result = {
            "human_score": human_score,
            "weighted_score": weighted_score,
            "score_difference": score_difference,
            "has_significant_divergence": has_significant_divergence,
            "sub_scores": {
                "context": context_score,
                "fact": fact_score,
                "depth": depth_score,
                "relevance": relevance_score,
                "structure": structure_score,
                "human": human_score,
                "reflective": reflective_score
            }
        }
        
        # Store in state
        state.consensus_state = result
        
        # Log warning if there's a significant divergence
        if has_significant_divergence:
            print(f"WARNING: Significant divergence between human score ({human_score}) and weighted average ({weighted_score})")
        
        print(f"Final consensus scores: {result['sub_scores']}")
        
    except Exception as e:
        print(f"Error in consensus calculation: {e}")
        # If calculation fails, use default values
        result = {
            "human_score": 5.0,
            "weighted_score": 5.0,
            "score_difference": 0.0,
            "has_significant_divergence": False,
            "sub_scores": {}
        }
        state.consensus_state = result
    
    return {
        "consensus_state": state.consensus_state
    }

def validator(state: ClassifierState, config: RunnableConfig):
    """
    Final validation of results and format checking.
    """
    if not hasattr(state, 'consensus_state') or not isinstance(state.consensus_state, dict):
        default_result = {
            "final_score": 5.0,
            "classification": "Fair",
            "summary": "No summary available",
            "rationale": "No rationale available",
            "sub_scores": {}
        }
        state.validator_state = default_result
        return {
            "validator_state": state.validator_state
        }
    
    result = state.consensus_state
    
    # Validate result structure
    validation_errors = []
    
    required_fields = {
        "human_score": float,
        "weighted_score": float,
        "score_difference": float,
        "has_significant_divergence": bool,
        "sub_scores": dict
    }
    
    for field, field_type in required_fields.items():
        if field not in result:
            validation_errors.append(f"Missing {field} field")
        elif not isinstance(result[field], field_type):
            validation_errors.append(f"{field} has wrong type")
    
    if validation_errors:
        print(f"Validation errors: {', '.join(validation_errors)}")
        default_result = {
            "final_score": 5.0,
            "classification": "Fair",
            "summary": "No summary available",
            "rationale": "No rationale available",
            "sub_scores": {},
            "validation_errors": validation_errors
        }
        
        try:
            if "weighted_score" in result:
                score = float(result["weighted_score"])
                if 0.1 <= score <= 10.0:
                    default_result["final_score"] = score
                    default_result["classification"] = get_classification(score)
        except:
            pass
        
        state.validator_state = default_result
    else:
        state.validator_state = result
    
    return {
        "validator_state": state.validator_state
    }
    
def get_classification(score: float) -> str:
    """Helper function to get classification label from score."""
    if score >= 8.6: return "Outstanding"
    elif score >= 7.6: return "Excellent"
    elif score >= 6.6: return "Very Good"
    elif score >= 5.1: return "Good"
    elif score >= 3.1: return "Fair"
    elif score >= 2.1: return "Very Poor"
    else: return "Extremely Poor"

def should_skip_content(state: ClassifierState) -> str:
    """Router function for content skipping decision."""
    if isinstance(state.preprocessor_state, dict) and state.preprocessor_state.get('skip', False):
        return 'skip'
    return 'process'

def should_skip_further_analysis(state: ClassifierState) -> str:
    """Router function for further analysis decision."""
    if getattr(state, 'skip_further_analysis', False):
        return 'skip'
    return 'continue'

# Build graph
builder = StateGraph(ClassifierState)

# Add nodes
builder.add_node("summary_agent", summary_agent)
builder.add_node("input_preprocessor", input_preprocessor)
builder.add_node("context_evaluator", context_evaluator)
builder.add_node("fact_checker", fact_checker)
builder.add_node("depth_analyzer", depth_analyzer)
builder.add_node("relevance_analyzer", relevance_analyzer)
builder.add_node("structure_analyzer", structure_analyzer)
builder.add_node("historical_reflection", historical_reflection)
builder.add_node("score_consolidator", score_consolidator)
builder.add_node("human_reasoning", human_reasoning)
builder.add_node("consensus_agent", consensus_agent)
builder.add_node("reflective_validator", reflective_validator)
builder.add_node("validator", validator)

# Add edges with conditional routing
builder.add_edge(START, "summary_agent")
builder.add_edge("summary_agent", "input_preprocessor")

# Add conditional routing after preprocessor
builder.add_conditional_edges(
    "input_preprocessor",
    should_skip_content,
    {
        "skip": END,
        "process": "context_evaluator"
    }
)

# Add conditional routing after context evaluator
builder.add_conditional_edges(
    "context_evaluator",
    should_skip_further_analysis,
    {
        "skip": END,
        "continue": "fact_checker"
    }
)

# Add remaining edges
builder.add_edge("fact_checker", "depth_analyzer")
builder.add_edge("depth_analyzer", "relevance_analyzer")
builder.add_edge("relevance_analyzer", "structure_analyzer")
builder.add_edge("structure_analyzer", "historical_reflection")
builder.add_edge("historical_reflection", "reflective_validator")
builder.add_edge("reflective_validator", "human_reasoning")
builder.add_edge("human_reasoning", "score_consolidator")
builder.add_edge("score_consolidator", "consensus_agent")
builder.add_edge("consensus_agent", "validator")
builder.add_edge("validator", END)

graph = builder.compile()

## Example news content
#news_content = """
#TWEET URL:
#==================================================
#https://x.com/lookonchain/status/1882966799433835000?s=46&t=QXHlGY8b4Tg3q3ouS77o_A
#
#TWEET CONTENT:
#==================================================
#Trump's World Liberty(
#@worldlibertyfi
#) bought another 3,001 $ETH($10M) and 95 $WBTC($10M).
#
#Since Nov 30, 2024, #WorldLiberty has bought:
#
#49,879 $ETH($170M) at $3,407;
#647 $WBTC($68.5M) at $105,983;
#40.72M $TRX($10M) at $0.25.
#256,315 $LINK($6.7M) at $26.14;
#19,399 $AAVE($6.7M) at $345.38;
#5.78M $ENA($5.45M) at $0.94;
#134,216 $ONDO($250K) at $1.86.
#https://intel.arkm.com/explorer/entity/worldlibertyfi…
#
#URL ANALYSIS:
#==================================================
#
#URL 1: https://intel.arkm.com/explorer/entity/worldlibertyfi…
#Content:
#Arkham Market Data Dashboard Alerts Visualizer Exchange More Profile Points Private Labels Login Sign Up Something went wrong. ALL NETWORKS Create Alert + Visualize Something went wrong. Visualize PORTFOLIO HOLDINGS BY CHAIN PORTFOLIO ARCHIVE ASSET PRICE HOLDINGS VALUE ASSET PRICE HOLDINGS VALUE BALANCES HISTORY TOKEN BALANCES HISTORY PROFIT & LOSS 1W 1M 3M ALL EXCHANGE USAGE TOP COUNTERPARTIES DEPOSITS WITHDRAWALS USD ≥ $1.00 SOLANA : Show Owner Account TRANSFERS SWAPS INFLOW OUTFLOW Something went wrong. ARKHAM FILTERS USD ≥ $1.00 SOLANA : Show Owner Account TRANSFERS SWAPS ALL TX Something went wrong. ARKHAM BORROWS & LOANS Net Value $0.00 +0.00% Largest Positions PLATFORM USD VALUE POSITIONS NETWORK EXCHANGE USAGE TOP COUNTERPARTIES DEPOSITS WITHDRAWALS Back to Top ARKHAM support@arkm.com - ARKHAM INTELLIGENCE - © 2025 - terms of service - privacy CHAT ROOM: cookie settings we use cookies to improve our product and your experience on our website. you can opt out of cookies here, or in the settings tab. accept cookies customize
#"""
#
## Create initial state with the news content
#initial_state = {
#    "content": news_content,
#    "content_types": ["text"] # Initialize with content type
#}
#
## Process the news through the graph
#responses = graph.stream(initial_state)
#
#for response in responses: 
#    print(response)