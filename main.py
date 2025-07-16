#!/usr/bin/env python3
"""
Enhanced Crypto & Macro News Pipeline - Main Execution Script

This is the main entry point for the Enhanced Crypto & Macro News Pipeline.
It provides a clean interface to run the comprehensive pipeline system
with automatic archiving and AI-powered analysis.

Usage:
    python main.py

Features:
    - Extracts 120+ crypto and macro articles from 15+ sources
    - Processes through 13 specialized AI agents
    - Generates CSV, JSON, TXT outputs with comprehensive reports
    - Automatic historical archiving with timestamped folders
    - Real-time progress monitoring and error recovery
"""

import asyncio
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    """Main execution function."""
    try:
        print("🚀 Starting Enhanced Crypto & Macro News Pipeline...")
        print("📁 Loading components from organized structure...")

        # Import the enhanced comprehensive pipeline
        from pipelines.enhanced_comprehensive_pipeline import \
            EnhancedComprehensivePipeline

        # Create and run the pipeline
        pipeline = EnhancedComprehensivePipeline(target_articles=120)

        print("✅ Pipeline initialized successfully")
        print("🔄 Starting execution...")

        # Execute the complete pipeline
        asyncio.run(pipeline.run_complete_pipeline())

        print("🎉 Pipeline execution completed successfully!")
        print("📊 Check enhanced_results/ and historical_archives/ for outputs")

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(
            "💡 Make sure all dependencies are installed: pip install -r requirements.txt"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")
        print("📋 Check logs for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
