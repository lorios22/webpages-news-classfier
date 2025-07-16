#!/usr/bin/env python3
"""
Pipeline Monitoring Script

Real-time monitoring interface for the Enhanced Crypto & Macro News Pipeline.
Provides live status updates, progress tracking, and system health monitoring.

Usage:
    python monitor.py

Features:
    - Real-time pipeline status monitoring
    - Article extraction progress tracking
    - AI agent processing status
    - Archive operations monitoring
    - Error tracking and reporting
    - System resource monitoring
"""

import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    """Main monitoring function."""
    try:
        print("📊 Starting Pipeline Monitor...")
        print("🔍 Loading monitoring components...")

        # Import the enhanced monitor
        from monitoring.enhanced_monitor import main as monitor_main

        print("✅ Monitor initialized successfully")
        print("📈 Starting real-time monitoring...")

        # Start monitoring
        monitor_main()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(
            "💡 Make sure all dependencies are installed: pip install -r requirements.txt"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Monitor Error: {e}")
        print("📋 Check logs for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
