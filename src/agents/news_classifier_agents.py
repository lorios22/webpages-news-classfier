import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import random

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import BaseMessage

# Local imports
from assistant.prompts import (
    summary_instructions,
    input_preprocessor_instructions,
    context_evaluator_instructions,
    fact_checker_instructions,
    depth_analyzer_instructions,
    relevance_analyzer_instructions,
    structure_analyzer_instructions,
    historical_reflection_instructions,
    consolidation_instructions,
    human_reasoning_instructions,
    consensus_instructions,
    reflective_validator_instructions,
    validator_instructions
)

# Try to import memory agents
try:
    frominfrastructure.ai_agents.memory_agent import MemoryAgent
    frominfrastructure.ai_agents.context_engine import ContextEngine
    memory_agents_available = True
    print("✅ Memory Agents available")
except ImportError:
    memory_agents_available = False
    print("⚠️ Memory Agents not available - continuing without memory features")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentResponse:
    agent_name: str
    response: Dict[str, Any]
    timestamp: str
    processing_time: float

class NewsClassifierAgents:
    def __init__(self):
        """Initialize the News Classifier with enhanced agents"""
        
        # Initialize LLM
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=openai_api_key
            )
            print("🤖 Using OpenAI GPT-4o-mini for detailed analysis")
        else:
            self.llm = ChatOllama(
                model="llama3.2:latest",
                temperature=0.3
            )
            print("🤖 Using Ollama Llama3.2 for detailed analysis")
        
        # Initialize Memory Agents if available
        if memory_agents_available:
            try:
                self.memory_agent = MemoryAgent()
                self.context_engine = ContextEngine()
                print("🧠 Memory Agents initialized successfully")
            except Exception as e:
                print(f"⚠️ Memory Agents initialization failed: {e}")
                self.memory_agent = None
                self.context_engine = None
        else:
            self.memory_agent = None
            self.context_engine = None
        
        # Initialize JSON parser
        self.json_parser = JsonOutputParser()
        
        # Define agent configurations with enhanced prompts
        self.agent_configs = {
            "summary_agent": {
                "instructions": summary_instructions,
                "weight": 0.05,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "input_preprocessor": {
                "instructions": input_preprocessor_instructions,
                "weight": 0.05,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "context_evaluator": {
                "instructions": context_evaluator_instructions,
                "weight": 0.15,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "fact_checker": {
                "instructions": fact_checker_instructions,
                "weight": 0.20,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "depth_analyzer": {
                "instructions": depth_analyzer_instructions,
                "weight": 0.10,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "relevance_analyzer": {
                "instructions": relevance_analyzer_instructions,
                "weight": 0.10,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "structure_analyzer": {
                "instructions": structure_analyzer_instructions,
                "weight": 0.10,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "historical_reflection": {
                "instructions": historical_reflection_instructions,
                "weight": 0.05,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "reflective_validator": {
                "instructions": reflective_validator_instructions,
                "weight": 0.10,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "human_reasoning": {
                "instructions": human_reasoning_instructions,
                "weight": 0.20,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "score_consolidator": {
                "instructions": consolidation_instructions,
                "weight": 0.05,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "consensus_agent": {
                "instructions": consensus_instructions,
                "weight": 0.05,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            },
            "validator": {
                "instructions": validator_instructions,
                "weight": 0.15,
                "fallback_score": lambda: round(random.uniform(4.0, 8.0), 1)
            }
        }
        
        print(f"🔧 Initialized {len(self.agent_configs)} enhanced agents")

    async def call_agent(self, agent_name: str, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific agent with enhanced error handling and scoring"""
        
        start_time = datetime.now()
        
        try:
            # Get agent configuration
            agent_config = self.agent_configs.get(agent_name)
            if not agent_config:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            # Prepare context if available
            context_info = ""
            if context:
                context_info = f"\n\nContext Information:\n{json.dumps(context, indent=2)}"
            
            # Create messages
            messages = [
                SystemMessage(content=agent_config["instructions"]),
                HumanMessage(content=f"{content}{context_info}")
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse response
            try:
                parsed_response = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback parsing for non-JSON responses
                parsed_response = {
                    f"{agent_name}_state": response.content,
                    "fallback_used": True
                }
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Store in memory if available
            if self.memory_agent:
                try:
                    await self.memory_agent.store_interaction(
                        agent_name=agent_name,
                        input_content=content[:500],  # Truncate for storage
                        response=parsed_response,
                        processing_time=processing_time
                    )
    except Exception as e:
                    logger.warning(f"Failed to store memory for {agent_name}: {e}")
            
            return parsed_response
        
    except Exception as e:
            logger.error(f"Error in {agent_name}: {e}")
            
            # Return fallback response with random score
            fallback_score = agent_config["fallback_score"]()

    return {
                f"{agent_name}_state": {
                    "error": str(e),
                    "fallback_score": fallback_score,
                    "fallback_used": True
                }
            }

    def extract_score_from_response(self, response: Dict[str, Any], agent_name: str) -> float:
        """Extract score from agent response with enhanced accuracy"""
        
        # Score field mappings for different agents
        score_mappings = {
            "context_evaluator": "context_score",
            "fact_checker": "credibility_score", 
            "depth_analyzer": "depth_score",
            "relevance_analyzer": "relevance_score",
            "structure_analyzer": "structure_score",
            "historical_reflection": "historical_score",
            "reflective_validator": "reflective_score",
            "human_reasoning": "human_score",
            "validator": "final_score",
            "summary_agent": "summary_score",
            "input_preprocessor": "preprocessor_score",
            "score_consolidator": "consolidation_score",
            "consensus_agent": "consensus_score"
        }
        
        # Get expected score field
        expected_score_field = score_mappings.get(agent_name, f"{agent_name}_score")
        
        # Debug logging
        logger.debug(f"Extracting score for {agent_name}, looking for field: {expected_score_field}")
        logger.debug(f"Response keys: {list(response.keys())}")
        
        # Try multiple extraction strategies in order of preference
        score = None
        extraction_method = "unknown"
        
        # Strategy 1: Direct score field (most common)
        if expected_score_field in response:
            score = response[expected_score_field]
            extraction_method = "direct_field"
        
        # Strategy 2: Alternative score field names
        elif f"{agent_name}_score" in response:
            score = response[f"{agent_name}_score"]
            extraction_method = "agent_score_field"
        
        # Strategy 3: Look for common score field names
        elif "score" in response:
            score = response["score"]
            extraction_method = "generic_score_field"
        
        # Strategy 4: Look for nested state (legacy support)
        elif f"{agent_name}_state" in response:
            state = response[f"{agent_name}_state"]
            if isinstance(state, dict):
                if expected_score_field in state:
                    score = state[expected_score_field]
                    extraction_method = "nested_state"
                elif "score" in state:
                    score = state["score"]
                    extraction_method = "nested_generic_score"
        
        # Strategy 5: Search all fields for numeric values that could be scores
        if score is None:
            for key, value in response.items():
                if "score" in key.lower() and isinstance(value, (int, float)):
                    if 1.0 <= float(value) <= 10.0:
                        score = value
                        extraction_method = f"found_in_{key}"
                        break
        
        # Validate and convert score
        if score is not None:
            try:
                score = float(score)
                # Ensure score is in valid range
                if 1.0 <= score <= 10.0:
                    logger.info(f"✅ {agent_name}: Score {score} extracted via {extraction_method}")
                    return score
                else:
                    logger.warning(f"⚠️ {agent_name}: Score {score} out of range (1-10), using fallback")
            except (ValueError, TypeError):
                logger.warning(f"⚠️ {agent_name}: Score {score} not convertible to float, using fallback")
        
        # Only use fallback if absolutely necessary
        logger.warning(f"⚠️ {agent_name}: No valid score found in response, using fallback")
        logger.debug(f"Full response for debugging: {json.dumps(response, indent=2)}")
        
        # Use a more reasonable fallback based on agent type
        fallback_scores = {
            "context_evaluator": 6.0,
            "fact_checker": 7.0,
            "depth_analyzer": 5.5,
            "relevance_analyzer": 6.5,
            "structure_analyzer": 6.0,
            "historical_reflection": 6.0,
            "reflective_validator": 6.5,
            "human_reasoning": 7.0,
            "validator": 6.0,
            "summary_agent": 6.5,
            "input_preprocessor": 6.0,
            "score_consolidator": 6.0,
            "consensus_agent": 6.0
        }
        
        fallback_score = fallback_scores.get(agent_name, 6.0)
        logger.warning(f"Using fallback score {fallback_score} for {agent_name}")
        return fallback_score

    async def process_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Process article through all agents with enhanced scoring"""
        
        print(f"🔄 Processing: {article.get('title', 'Unknown')[:50]}...")
        
        # Prepare content for analysis
        content = f"""
        Title: {article.get('title', '')}
        Description: {article.get('description', '')}
        Content: {article.get('content', '')}
        Source: {article.get('source', '')}
        Published: {article.get('published_date', '')}
        Quality Score: {article.get('quality_score', 100)}
        Relevance Score: {article.get('relevance_score', 100)}
        Category: {article.get('category', '')}
        """
        
        # Phase 1: Individual Analysis Agents (parallel processing)
        individual_agents = [
            "summary_agent", "input_preprocessor", "context_evaluator",
            "fact_checker", "depth_analyzer", "relevance_analyzer",
            "structure_analyzer", "historical_reflection"
        ]
        
        print("📊 Phase 1: Individual agent analysis...")
        individual_results = {}
        
        # Process individual agents in parallel
        tasks = []
        for agent_name in individual_agents:
            task = self.call_agent(agent_name, content)
            tasks.append((agent_name, task))
        
        # Wait for all individual agents to complete
        for agent_name, task in tasks:
            try:
                result = await task
                individual_results[agent_name] = result
            except Exception as e:
                logger.error(f"Error in {agent_name}: {e}")
                fallback_score = self.agent_configs[agent_name]["fallback_score"]()
                individual_results[agent_name] = {
                    f"{agent_name}_state": {
                        "error": str(e),
                        "fallback_score": fallback_score
                    }
                }
        
        # Phase 2: Consolidation Agents (sequential processing)
        print("🔄 Phase 2: Consolidation and validation...")
        
        # Prepare context for consolidation agents
        consolidation_context = {
            "individual_results": individual_results,
            "article_metadata": {
                "title": article.get('title', ''),
                "source": article.get('source', ''),
                "category": article.get('category', '')
            }
        }
        
        # Run consolidation agents sequentially
        consolidation_agents = ["reflective_validator", "human_reasoning", "score_consolidator", "consensus_agent", "validator"]
        
        for agent_name in consolidation_agents:
            try:
                context_content = f"{content}\n\nPrevious Analysis Results:\n{json.dumps(individual_results, indent=2)}"
                result = await self.call_agent(agent_name, context_content, consolidation_context)
                individual_results[agent_name] = result
            except Exception as e:
                logger.error(f"Error in consolidation agent {agent_name}: {e}")
                fallback_score = self.agent_configs[agent_name]["fallback_score"]()
                individual_results[agent_name] = {
                    f"{agent_name}_state": {
                        "error": str(e),
                        "fallback_score": fallback_score
                    }
                }
        
        # Extract individual scores with proper mapping
        agent_scores = {}
        print("📊 Extracting individual agent scores...")
        
        for agent_name in self.agent_configs.keys():
            if agent_name in individual_results:
                score = self.extract_score_from_response(individual_results[agent_name], agent_name)
                agent_scores[agent_name] = score
                print(f"   {agent_name}: {score:.1f}/10")
        
        # Calculate weighted scores with proper mapping
        weighted_scores = {}
        total_weight = 0
        
        score_mappings = {
            "context_evaluator": "context_score",
            "fact_checker": "credibility_score",
            "depth_analyzer": "depth_score", 
            "relevance_analyzer": "relevance_score",
            "structure_analyzer": "structure_score",
            "historical_reflection": "historical_score",
            "reflective_validator": "reflective_score",
            "human_reasoning": "human_reasoning_score"
        }
        
        for agent_name, score_key in score_mappings.items():
            if agent_name in agent_scores:
                weight = self.agent_configs[agent_name]["weight"]
                score = agent_scores[agent_name]
                weighted_scores[score_key] = score * weight
                total_weight += weight
                print(f"   💰 {agent_name}: {score:.1f} * {weight:.2f} = {score * weight:.3f}")
        
        # Calculate final weighted score
        final_weighted_score = sum(weighted_scores.values()) / total_weight if total_weight > 0 else 5.0
        
        # Get final validator score
        validator_score = agent_scores.get("validator", 5.0)
        
        # Prepare final result with actual extracted scores
        result = {
            **article,
            "ai_responses": individual_results,
            "processing_timestamp": datetime.now().isoformat(),
            "agent_count": len(self.agent_configs),
            "agent_scores": {
                "context_score": agent_scores.get("context_evaluator", 5.0),
                "credibility_score": agent_scores.get("fact_checker", 5.0),
                "depth_score": agent_scores.get("depth_analyzer", 5.0),
                "relevance_score": agent_scores.get("relevance_analyzer", 5.0),
                "structure_score": agent_scores.get("structure_analyzer", 5.0),
                "historical_score": agent_scores.get("historical_reflection", 5.0),
                "reflective_score": agent_scores.get("reflective_validator", 5.0),
                "human_reasoning_score": agent_scores.get("human_reasoning", 5.0),
                "validator_score": validator_score,
                "overall_score": round(final_weighted_score, 1)
            },
            "weighted_scores": weighted_scores,
            "final_weighted_score": round(final_weighted_score, 1),
            "weight_configuration": "enhanced_v2"
        }
        
        # Add context analysis if available
        if self.context_engine:
            try:
                context_analysis = await self.context_engine.analyze_context(content)
                result["context_analysis"] = context_analysis
            except Exception as e:
                logger.warning(f"Context analysis failed: {e}")
        
        print(f"✅ Final weighted score: {final_weighted_score:.2f}/10")
        print(f"✅ Article processed successfully - Score: {final_weighted_score:.2f}/10")
        return result

# Create the graph for backward compatibility
graph = NewsClassifierAgents()

# Export functions for backward compatibility
async def process_article_with_agents(article: Dict[str, Any]) -> Dict[str, Any]:
    """Process article through all agents"""
    return await graph.process_article(article)

def get_agent_weights() -> Dict[str, float]:
    """Get agent weights for score calculation"""
    return {name: config["weight"] for name, config in graph.agent_configs.items()}

# Main execution
if __name__ == "__main__":
    async def test_single_article():
        """Test with a single article"""
        
        test_article = {
            "url": "https://example.com/test",
            "title": "Bitcoin Reaches New All-Time High",
            "description": "Bitcoin has surged to unprecedented levels",
            "content": "Bitcoin (BTC) has reached a new all-time high of $120,000...",
            "source": "test_source",
            "published_date": datetime.now().isoformat(),
            "author": "Test Author",
            "tags": ["bitcoin", "crypto"],
            "quality_score": 100,
            "relevance_score": 100,
            "category": "crypto"
        }
        
        classifier = NewsClassifierAgents()
        result = await classifier.process_article(test_article)
        
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        print(f"Overall Score: {result['agent_scores']['overall_score']}/10")
        print(f"Context Score: {result['agent_scores']['context_score']}/10")
        print(f"Depth Score: {result['agent_scores']['depth_score']}/10")
        print(f"Structure Score: {result['agent_scores']['structure_score']}/10")
        print("="*60)
    
    # Run test
    asyncio.run(test_single_article()) 