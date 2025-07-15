#!/usr/bin/env python3
"""
Enhanced Comprehensive Crypto & Macro News Pipeline
===================================================

Complete pipeline that extracts crypto and macroeconomic news from multiple sources
and processes them through an enhanced AI agent system with 1-10 scoring.
Includes automatic historical archiving system.

Features:
- Enhanced crypto/macro news extraction with anti-blocking
- 13 specialized AI agents with 1-10 scoring system
- Comprehensive English output (CSV, JSON, TXT)
- Advanced duplicate detection and quality filtering
- Real-time progress monitoring
- Detailed agent response capture
- Automatic historical archiving

Target Output:
- 100+ high-quality crypto/macro articles
- Complete agent analysis with 1-10 scores
- Professional CSV/JSON/TXT reports
- Comprehensive agent response summaries
- Clean directory management with historical archiving

Author: AI Assistant
Version: 3.1.0
License: MIT
"""

import os
import sys
import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import warnings

# Suppress specific warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Local imports
from srcextractors.enhanced_crypto_macro_extractor import EnhancedCryptoMacroExtractor
from srcservices.historical_archive_manager import HistoricalArchiveManager
from srcservices.duplicate_detection import DuplicateDetector
from srcagents.news_classifier_agents import NewsClassifierAgents

# Try to import memory agents
try:
    from src.infrastructure.ai_agents.memory_agent import MemoryAgent
    from src.infrastructure.ai_agents.context_engine import ContextEngine
    from src.infrastructure.ai_agents.weight_matrix import WeightMatrix
    memory_agents_available = True
except ImportError:
    memory_agents_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_comprehensive_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedComprehensivePipeline:
    def __init__(self, target_articles: int = 30, output_dir: str = "enhanced_results"):
        """Initialize the Enhanced Comprehensive Pipeline with Memory Agents"""
        
        # Basic configuration
        self.target_articles = target_articles
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize core components
        self.extractor = EnhancedCryptoMacroExtractor()
        self.archive_manager = HistoricalArchiveManager()
        self.duplicate_detector = DuplicateDetector()
        self.agent_graph = NewsClassifierAgents()
        
        # Initialize Memory Agents if available
        if memory_agents_available:
            try:
                self.memory_agent = MemoryAgent()
                self.context_engine = ContextEngine()
                self.weight_matrix = WeightMatrix()
                logger.info("🤖 Memory Agents activated: Memory Agent, Context Engine, Weight Matrix")
            except Exception as e:
                logger.warning(f"⚠️ Memory Agents initialization failed: {e}")
                self.memory_agent = None
                self.context_engine = None
                self.weight_matrix = None
        else:
            self.memory_agent = None
            self.context_engine = None
            self.weight_matrix = None
        
        # Statistics tracking
        self.stats = {
            'execution_start': None,
            'extraction_start': None,
            'extraction_end': None,
            'processing_start': None,
            'processing_end': None,
            'archiving_start': None,
            'archiving_end': None,
            'articles_extracted': 0,
            'articles_processed': 0,
            'articles_with_errors': 0,
            'crypto_articles': 0,
            'macro_articles': 0,
            'average_quality_score': 0.0,
            'average_relevance_score': 0.0,
            'agent_responses_captured': 0,
            'files_archived': 0
        }
        
        # Cleanup summary
        self.cleanup_summary = {}
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(exist_ok=True)
        
        logger.info("🚀 Enhanced Comprehensive Pipeline initialized")
        logger.info(f"📊 Target articles: {self.target_articles}")
        logger.info(f"📁 Output directory: {self.output_dir}")
        logger.info(f"⏰ Timestamp: {self.timestamp}")

    async def run_complete_pipeline(self) -> Dict[str, Any]:
        """Run the complete enhanced pipeline with all phases"""
        
        try:
            self.stats['execution_start'] = datetime.now()
            
            logger.info("🚀 STARTING ENHANCED COMPREHENSIVE PIPELINE WITH ARCHIVING")
            logger.info("=" * 80)
            
            # Phase 1: Pre-execution cleanup and archiving
            logger.info("🗄️ Performing pre-execution cleanup and archiving")
            self.cleanup_summary = self.archive_manager.pre_execution_cleanup()
            
            # Phase 2: Enhanced News Extraction
            logger.info("🔍 Phase 1: Enhanced News Extraction")
            logger.info("=" * 80)
            
            self.stats['extraction_start'] = datetime.now()
            articles = self.extractor.extract_all_articles(target_count=self.target_articles)
            self.stats['extraction_end'] = datetime.now()
            
            if not articles:
                raise Exception("No articles extracted")
            
            logger.info(f"✅ Successfully extracted {len(articles)} articles")
            
            # Update statistics
            self.stats['articles_extracted'] = len(articles)
            self.stats['crypto_articles'] = sum(1 for a in articles if a.get('category') == 'crypto')
            self.stats['macro_articles'] = sum(1 for a in articles if a.get('category') == 'macro')
            
            logger.info(f"📊 Breakdown: {self.stats['crypto_articles']} crypto, {self.stats['macro_articles']} macro")
            
            # Phase 3: Enhanced AI Agent Processing with Memory Agents
            logger.info("🧠 Phase 2: Enhanced AI Agent Processing with Memory Agents")
            logger.info("=" * 80)
            
            self.stats['processing_start'] = datetime.now()
            processed_articles = await self.process_articles_with_agents(articles)
            self.stats['processing_end'] = datetime.now()
            
            processing_duration = (self.stats['processing_end'] - self.stats['processing_start']).total_seconds()
            logger.info(f"🎉 AI Agent Processing completed in {processing_duration:.1f} seconds")
            logger.info(f"📊 Articles processed: {len(processed_articles)}")
            logger.info(f"❌ Articles with errors: {self.stats['articles_with_errors']}")
            
            # Memory Agent Summary
            if self.memory_agent:
                try:
                    memory_stats = self.memory_agent.get_statistics()
                    logger.info(f"🤖 Memory Agents: {memory_stats.get('total_memories', 0)} memories stored")
                except Exception as e:
                    logger.warning(f"Memory agent statistics failed: {e}")
                    logger.info("🤖 Memory Agents: Statistics unavailable")
            
            # Phase 4: Generate Comprehensive Outputs
            logger.info("📊 Phase 3: Generating Comprehensive Outputs")
            logger.info("=" * 80)
            
            output_files = await self.generate_comprehensive_outputs(processed_articles)
            logger.info("✅ All output files generated successfully")
            
            # Phase 5: Archive Results
            logger.info("🗄️ Phase 4: Archiving Results to Historical Storage")
            logger.info("=" * 80)
            
            self.stats['archiving_start'] = datetime.now()
            archive_path = self.archive_manager.archive_results(self.output_dir)
            self.stats['archiving_end'] = datetime.now()
            
            if archive_path:
                logger.info(f"✅ Results successfully archived to: {archive_path}")
                self.stats['files_archived'] = len(output_files)
                logger.info(f"📦 Archived files: {self.stats['files_archived']}")
                logger.info(f"📂 {self.output_dir}/ is now clean and ready for next execution")
            
            # Final Statistics
            total_duration = (datetime.now() - self.stats['execution_start']).total_seconds()
            success_rate = ((len(processed_articles) - self.stats['articles_with_errors']) / len(processed_articles)) * 100 if processed_articles else 0
            
            logger.info("🎉 ENHANCED PIPELINE WITH ARCHIVING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"📊 Articles processed: {len(processed_articles)}")
            logger.info(f"⏱️ Total execution time: {total_duration:.1f} seconds")
            logger.info(f"📈 Success rate: {success_rate:.1f}%")
            logger.info(f"📁 Output files: {len(output_files)}")
            logger.info(f"🤖 Agent responses captured: {self.stats['agent_responses_captured']}")
            logger.info(f"🗄️ Results archived to: {archive_path.split('/')[-1] if archive_path else 'N/A'}")
            logger.info(f"📂 {self.output_dir}/ is clean for next execution")
            
            return {
                'success': True,
                'articles_processed': len(processed_articles),
                'total_duration': total_duration,
                'success_rate': success_rate,
                'output_files': output_files,
                'archive_path': archive_path,
                'statistics': self.stats
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'statistics': self.stats
            }

    async def process_articles_with_agents(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process articles through AI agents with enhanced memory integration"""
        
        processed_articles = []
        
        for i, article in enumerate(articles, 1):
            try:
                logger.info(f"🔄 Processing article {i}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
                
                # CONTEXT ENGINE INTEGRATION - Enhanced context preparation
                if self.context_engine:
                    try:
                        context_analysis = self.context_engine.analyze_context(
                            article['content'],
                            article.get('category', 'unknown')
                        )
                        article['context_analysis'] = context_analysis
                    except Exception as e:
                        logger.warning(f"Context engine analysis failed: {e}")
                
                # WEIGHT MATRIX INTEGRATION - Get optimal weights
                if self.weight_matrix:
                    try:
                        optimal_weights = self.weight_matrix.get_optimal_configuration()
                        article['weight_configuration'] = optimal_weights
                    except Exception as e:
                        logger.warning(f"Weight matrix configuration failed: {e}")
                
                # Process through agent graph with enhanced context
                try:
                    # Process article through all agents
                    processed_result = await self.agent_graph.process_article(article)
                    
                    # Update article with processed results
                    article.update(processed_result)
                    
                    # Extract key scores for easier access
                    article['agent_scores'] = article.get('agent_scores', {})
                    
                    # MEMORY AGENT INTEGRATION - Store processing results
                    if self.memory_agent:
                        try:
                            self.memory_agent.store_processing_result(
                                article_id=article.get('url', f'article_{i}'),
                                content_preview=article['content'][:500],
                                agent_scores=article['agent_scores'],
                                processing_metadata={
                                    'timestamp': datetime.now().isoformat(),
                                    'category': article.get('category', 'unknown'),
                                    'source': article.get('source', 'unknown')
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Memory agent storage failed: {e}")
                    
                    # WEIGHT MATRIX INTEGRATION - Update with results
                    if self.weight_matrix:
                        try:
                            self.weight_matrix.update_with_results(
                                article_category=article.get('category', 'unknown'),
                                agent_scores=article['agent_scores'],
                                final_score=article['agent_scores'].get('overall_score', 0)
                            )
                        except Exception as e:
                            logger.warning(f"Weight matrix update failed: {e}")
                    
                    self.stats['agent_responses_captured'] += len(article.get('ai_responses', {}))
                    
                except Exception as agent_error:
                    logger.error(f"❌ Error processing article {i} through agents: {agent_error}")
                    self.stats['articles_with_errors'] += 1
                    
                    # Add error information to article
                    article['processing_error'] = str(agent_error)
                    article['agent_scores'] = {
                        'context_score': 0,
                        'credibility_score': 0,
                        'depth_score': 0,
                        'relevance_score': 0,
                        'structure_score': 0,
                        'historical_score': 0,
                        'reflective_score': 0,
                        'human_reasoning_score': 0,
                        'overall_score': 0
                    }
                
                processed_articles.append(article)
                self.stats['articles_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing article {i}: {e}")
                self.stats['articles_with_errors'] += 1
                
                # Add minimal article info for consistency
                article['processing_error'] = str(e)
                article['agent_scores'] = {}
                processed_articles.append(article)
        
        return processed_articles

    async def generate_comprehensive_outputs(self, processed_articles: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate comprehensive output files with enhanced formatting"""
        
        output_files = {}
        
        try:
            # 1. Enhanced CSV Output
            csv_data = []
            for article in processed_articles:
                row = {
                    'title': article.get('title', ''),
                    'url': article['url'],
                    'published_date': article.get('published_date', ''),
                    'quality_score': article.get('quality_score', 0),
                    'relevance_score': article.get('relevance_score', 0),
                    'description': article.get('description', '')[:200],  # Truncate for CSV
                    'content_preview': article['content'][:300] if article['content'] else '',  # Preview
                    'agent_count': article.get('agent_count', 0),
                    'processing_status': 'success' if 'ai_responses' in article and 'error' not in article['ai_responses'] else 'error'
                }
                
                # Add agent scores
                agent_scores = article.get('agent_scores', {})
                row.update({
                    'context_score': agent_scores.get('context_score', 0),
                    'credibility_score': agent_scores.get('credibility_score', 0),
                    'depth_score': agent_scores.get('depth_score', 0),
                    'relevance_agent_score': agent_scores.get('relevance_score', 0),
                    'human_reasoning_score': agent_scores.get('human_reasoning_score', 0),
                    'overall_agent_score': agent_scores.get('overall_score', 0)
                })
                
                csv_data.append(row)
            
            # Save CSV
            csv_file = f"{self.output_dir}/enhanced_results_{self.timestamp}.csv"
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            output_files['csv'] = csv_file
            logger.info(f"📄 Enhanced CSV created: {csv_file} ({len(csv_data)} rows)")
            
            # 2. Complete JSON Output
            json_file = f"{self.output_dir}/enhanced_results_{self.timestamp}.json"
            json_data = {
                'metadata': {
                    'generation_timestamp': datetime.now().isoformat(),
                    'pipeline_version': '3.1.0',
                    'total_articles': len(processed_articles),
                    'processing_duration_seconds': (
                        self.stats['processing_end'] - self.stats['processing_start']
                    ).total_seconds() if self.stats['processing_end'] and self.stats['processing_start'] else 0,
                    'extraction_duration_seconds': (
                        self.stats['extraction_end'] - self.stats['extraction_start']
                    ).total_seconds() if self.stats['extraction_end'] and self.stats['extraction_start'] else 0,
                    'ai_agents_used': 13,
                    'target_articles': self.target_articles,
                    'historical_archiving': True
                },
                'statistics': self.stats,
                'cleanup_summary': self.cleanup_summary,
                'articles': processed_articles
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            
            output_files['json'] = json_file
            logger.info(f"📄 Complete JSON created: {json_file}")
            
            # 3. Human-Readable Text Output
            txt_file = f"{self.output_dir}/enhanced_results_{self.timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write("ENHANCED CRYPTO & MACRO NEWS ANALYSIS RESULTS\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Articles: {len(processed_articles)}\n")
                f.write(f"Crypto Articles: {self.stats['crypto_articles']}\n")
                f.write(f"Macro Articles: {self.stats['macro_articles']}\n")
                f.write(f"Processing Errors: {self.stats['articles_with_errors']}\n\n")
                
                for i, article in enumerate(processed_articles, 1):
                    f.write(f"ARTICLE {i}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Title: {article.get('title', 'N/A')}\n")
                    f.write(f"Source: {article.get('source', 'N/A')}\n")
                    f.write(f"Category: {article.get('category', 'N/A')}\n")
                    f.write(f"Published: {article.get('published_date', 'N/A')}\n")
                    f.write(f"URL: {article.get('url', 'N/A')}\n")
                    
                    # Agent scores
                    agent_scores = article.get('agent_scores', {})
                    if agent_scores:
                        f.write(f"Overall Score: {agent_scores.get('overall_score', 0):.1f}/10\n")
                        f.write(f"Context: {agent_scores.get('context_score', 0):.1f}/10\n")
                        f.write(f"Credibility: {agent_scores.get('credibility_score', 0):.1f}/10\n")
                        f.write(f"Depth: {agent_scores.get('depth_score', 0):.1f}/10\n")
                        f.write(f"Relevance: {agent_scores.get('relevance_score', 0):.1f}/10\n")
                    
                    f.write(f"Content Preview: {article.get('content', '')[:200]}...\n")
                    f.write("\n")
            
            output_files['txt'] = txt_file
            logger.info(f"📄 Human-readable TXT created: {txt_file}")
            
            # 4. Agent Responses Summary
            agent_summary_file = f"{self.output_dir}/agent_responses_summary_{self.timestamp}.txt"
            with open(agent_summary_file, 'w', encoding='utf-8') as f:
                f.write("AI AGENT RESPONSES SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Articles Processed: {len(processed_articles)}\n")
                f.write(f"Total Agent Responses: {self.stats['agent_responses_captured']}\n")
                f.write(f"Average Responses per Article: {self.stats['agent_responses_captured'] / len(processed_articles) if processed_articles else 0:.1f}\n\n")
                
                for i, article in enumerate(processed_articles, 1):
                    ai_responses = article.get('ai_responses', {})
                    if ai_responses:
                        f.write(f"Article {i}: {article.get('title', 'N/A')[:50]}...\n")
                        f.write(f"Agent Responses: {len(ai_responses)}\n")
                        f.write(f"Agents: {', '.join(ai_responses.keys())}\n")
                        f.write("-" * 40 + "\n")
            
            output_files['agent_summary'] = agent_summary_file
            logger.info(f"📄 Agent responses summary created: {agent_summary_file}")
            
            # 5. Pipeline Report
            report_file = f"{self.output_dir}/pipeline_report_{self.timestamp}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# Enhanced Crypto & Macro News Pipeline Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Pipeline Version:** 3.1.0\n")
                f.write(f"**Target Articles:** {self.target_articles}\n\n")
                
                f.write("## Execution Statistics\n\n")
                f.write(f"- **Total Articles:** {len(processed_articles)}\n")
                f.write(f"- **Crypto Articles:** {self.stats['crypto_articles']}\n")
                f.write(f"- **Macro Articles:** {self.stats['macro_articles']}\n")
                f.write(f"- **Processing Errors:** {self.stats['articles_with_errors']}\n")
                f.write(f"- **Success Rate:** {((len(processed_articles) - self.stats['articles_with_errors']) / len(processed_articles)) * 100:.1f}%\n\n")
                
                f.write("## Performance Metrics\n\n")
                extraction_time = (self.stats['extraction_end'] - self.stats['extraction_start']).total_seconds() if self.stats['extraction_end'] and self.stats['extraction_start'] else 0
                processing_time = (self.stats['processing_end'] - self.stats['processing_start']).total_seconds() if self.stats['processing_end'] and self.stats['processing_start'] else 0
                
                f.write(f"- **Extraction Time:** {extraction_time:.1f} seconds\n")
                f.write(f"- **Processing Time:** {processing_time:.1f} seconds\n")
                f.write(f"- **Total Execution Time:** {(datetime.now() - self.stats['execution_start']).total_seconds():.1f} seconds\n")
                f.write(f"- **Articles per Second:** {len(processed_articles) / processing_time if processing_time > 0 else 0:.2f}\n\n")
                
                f.write("## Memory Agent Statistics\n\n")
                if self.memory_agent:
                    memory_stats = await self.memory_agent.get_statistics()
                    f.write(f"- **Total Memories:** {memory_stats.get('total_memories', 0)}\n")
                    f.write(f"- **Pattern Memories:** {memory_stats.get('pattern_memories', 0)}\n")
                    f.write(f"- **Context Memories:** {memory_stats.get('context_memories', 0)}\n")
                    f.write(f"- **Fact Memories:** {memory_stats.get('fact_memories', 0)}\n")
                else:
                    f.write("- **Memory Agents:** Not available\n")
                
                f.write("\n## Output Files\n\n")
                for file_type, file_path in output_files.items():
                    f.write(f"- **{file_type.upper()}:** `{file_path}`\n")
            
            output_files['report'] = report_file
            logger.info(f"📄 Pipeline report created: {report_file}")
            
            return output_files
            
        except Exception as e:
            logger.error(f"❌ Error generating outputs: {e}")
            return {}

    def _extract_agent_scores(self, agent_responses: Dict[str, Any]) -> Dict[str, float]:
        """Extract agent scores from responses for easier access"""
        
        scores = {}
        
        # Score mappings
        score_mappings = {
            'context_evaluator': 'context_score',
            'fact_checker': 'credibility_score',
            'depth_analyzer': 'depth_score',
            'relevance_analyzer': 'relevance_score',
            'structure_analyzer': 'structure_score',
            'historical_reflection': 'historical_score',
            'reflective_validator': 'reflective_score',
            'human_reasoning': 'human_reasoning_score'
        }
        
        for agent_name, score_key in score_mappings.items():
            if agent_name in agent_responses:
                response = agent_responses[agent_name]
                if isinstance(response, dict):
                    # Try to extract score from various possible locations
                    score = response.get(score_key, 0)
                    if score == 0:
                        score = response.get(f"{agent_name}_score", 0)
                    scores[score_key] = float(score) if score else 0.0
                else:
                    scores[score_key] = 0.0
        
        # Calculate overall score (weighted average)
        if scores:
            weights = {
                'context_score': 0.15,
                'credibility_score': 0.20,
                'depth_score': 0.15,
                'relevance_score': 0.15,
                'structure_score': 0.10,
                'historical_score': 0.05,
                'reflective_score': 0.10,
                'human_reasoning_score': 0.10
            }
            
            weighted_sum = sum(scores.get(key, 0) * weight for key, weight in weights.items())
            scores['overall_score'] = weighted_sum
        
        return scores

# Main execution
async def main():
    """Main execution function"""
    
    try:
        # Initialize pipeline
        pipeline = EnhancedComprehensivePipeline(target_articles=30)
        
        # Run complete pipeline
        result = await pipeline.run_complete_pipeline()
        
        if result['success']:
            print("\n🎉 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"⏱️  Total Execution Time: {result['total_duration']:.1f} seconds")
            print(f"📊 Articles Processed: {result['articles_processed']}")
            print(f"📝 Agent Responses: {result['statistics']['agent_responses_captured']}")
            print(f"🗄️  Archive Location: {result['archive_path'].split('/')[-1] if result['archive_path'] else 'N/A'}")
            print(f"📄 Output Files: {len(result['output_files'])}")
            
            # Memory Agent Statistics
            if pipeline.memory_agent:
                memory_stats = await pipeline.memory_agent.get_statistics()
                print(f"\n🧠 MEMORY AGENT STATISTICS:")
                print(f"   📚 Total Memories: {memory_stats.get('total_memories', 0)}")
                print(f"   🔍 Pattern Memories: {memory_stats.get('pattern_memories', 0)}")
                print(f"   💭 Context Memories: {memory_stats.get('context_memories', 0)}")
                print(f"   📊 Fact Memories: {memory_stats.get('fact_memories', 0)}")
            
            # Output files
            print(f"\n📄 GENERATED FILES:")
            for file_type, file_path in result['output_files'].items():
                print(f"   {file_type}: {file_path}")
            
            print(f"\n✅ System is ready for the next execution!")
            print(f"🔄 Run again: python3 run_enhanced_pipeline.py")
            
        else:
            print(f"\n❌ PIPELINE EXECUTION FAILED!")
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        logger.error(f"Critical error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 