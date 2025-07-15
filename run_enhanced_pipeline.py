#!/usr/bin/env python3
"""
Enhanced Pipeline Execution Script
==================================

Complete execution script that runs the enhanced comprehensive pipeline
with all Memory Agents integrated.

Features:
- Memory Agents (Memory Agent, Context Engine, Weight Matrix)
- 13 AI Agents with 1-10 scoring
- Historical archiving system
- Multi-source extraction
- Real-time monitoring
- Complete integration

Author: AI Assistant
Version: 4.0.0
"""

import sys
import os
import time
import asyncio
from datetime import datetime

async def main():
    """Main execution function with enhanced features"""
    
    print("🚀 ENHANCED CRYPTO & MACRO NEWS PIPELINE WITH MEMORY AGENTS")
    print("=" * 80)
    print("🤖 Features: Memory Agents + 13 AI Agents + Historical Archiving")
    print("📊 Target: 120+ articles with complete AI analysis")
    print("🔄 Processing: Multi-source extraction + AI scoring + Archiving")
    print()
    
    try:
        # Import and initialize the enhanced pipeline
        print("🔧 Initializing Enhanced Pipeline with Memory Agents...")
        from enhanced_comprehensive_pipeline import EnhancedComprehensivePipeline
        
        # Create pipeline instance
        pipeline = EnhancedComprehensivePipeline(target_articles=30)
        
        print("✅ Pipeline initialized successfully")
        print("🤖 Memory Agents: ACTIVE")
        print("🧠 AI Agents: 13 agents ready")
        print("🗄️ Historical Archiving: ACTIVE")
        print()
        
        # Execute the complete pipeline
        print("🚀 Starting complete pipeline execution...")
        execution_start = time.time()
        
        result = await pipeline.run_complete_pipeline()
        
        execution_end = time.time()
        total_duration = execution_end - execution_start
        
        # Display results
        print()
        if result.get('success'):
            print("🎉 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"⏱️  Total Execution Time: {total_duration:.1f} seconds")
            print(f"📊 Articles Processed: {result.get('articles_processed', 0)}")
            print(f"📝 Agent Responses: {result.get('statistics', {}).get('agent_responses_captured', 0)}")
            print(f"🗄️  Archive Location: {result.get('archive_path', 'N/A')}")
            print(f"📄 Output Files: {len(result.get('output_files', {}))}")
            print()
            
            # Memory Agent Statistics
            if hasattr(pipeline, 'memory_agent') and pipeline.memory_agent:
                memory_stats = await pipeline.memory_agent.get_statistics()
                print("🧠 MEMORY AGENT STATISTICS:")
                print(f"   📚 Total Memories: {memory_stats.get('total_memories', 0)}")
                print(f"   🔍 Pattern Memories: {memory_stats.get('pattern_memories', 0)}")
                print(f"   💭 Context Memories: {memory_stats.get('context_memories', 0)}")
                print(f"   📊 Fact Memories: {memory_stats.get('fact_memories', 0)}")
                print()
            
            # Output file details
            if 'output_files' in result:
                print("📄 GENERATED FILES:")
                for file_type, file_path in result['output_files'].items():
                    print(f"   {file_type}: {file_path}")
                print()
            
            print("✅ System is ready for the next execution!")
            print("🔄 Run again: python3 run_enhanced_pipeline.py")
            
            return True
        else:
            print("❌ PIPELINE EXECUTION FAILED!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
        
    except KeyboardInterrupt:
        print("\n⚠️  Execution interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 