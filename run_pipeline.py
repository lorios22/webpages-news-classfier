#!/usr/bin/env python3
"""
Enhanced Pipeline Runner - Alternative Execution Interface

This script provides an enhanced execution interface with additional
configuration options and better user experience.

Usage:
    python run_pipeline.py

Features:
    - Enhanced configuration options
    - Better error handling and user feedback
    - Parameter validation and monitoring
    - Graceful execution scenarios handling
"""

import asyncio
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    """Main execution function using enhanced runner."""
    try:
        print("🚀 Enhanced Pipeline Runner")
        print("📁 Loading enhanced execution interface...")

        # Import and run the enhanced pipeline runner
        from pipelines.run_enhanced_pipeline import main as run_enhanced_main

        print("✅ Enhanced runner loaded successfully")

        # Execute using the enhanced runner (async function)
        asyncio.run(run_enhanced_main())

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Runner Error: {e}")
        print("📋 Check logs for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
