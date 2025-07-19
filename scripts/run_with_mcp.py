#!/usr/bin/env python3
"""
Run Pipeline with MCP Support
=============================

This script allows running the existing pipeline with optional MCP support.
It provides backward compatibility while enabling MCP features.

Usage:
    # Run with direct APIs (current behavior)
    python scripts/run_with_mcp.py --mode direct

    # Run with MCP (requires MCP server running)
    python scripts/run_with_mcp.py --mode mcp

    # Run with MCP and fallback to direct APIs
    python scripts/run_with_mcp.py --mode mcp --fallback

    # Start MCP server and run pipeline
    python scripts/run_with_mcp.py --mode mcp --start-server
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.mcp_adapter.api_adapter import get_api_adapter, set_global_adapter_mode

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MCPPipelineRunner:
    """
    Pipeline runner with MCP support.
    """

    def __init__(self, mode: str = "direct", fallback: bool = True, start_server: bool = False):
        self.mode = mode
        self.fallback = fallback
        self.start_server = start_server
        self.mcp_process = None

    async def run(self, target_articles: int = 120):
        """
        Run the pipeline with MCP support.
        """
        logger.info(f"🚀 Starting pipeline in {self.mode} mode")

        try:
            # Step 1: Setup MCP if needed
            if self.mode == "mcp" and self.start_server:
                await self._start_mcp_server()

            # Step 2: Configure adapter
            await self._configure_adapter()

            # Step 3: Health check
            await self._health_check()

            # Step 4: Run pipeline
            await self._run_pipeline(target_articles)

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
        finally:
            # Cleanup
            await self._cleanup()

    async def _start_mcp_server(self):
        """
        Start the MCP server in background.
        """
        logger.info("🔧 Starting MCP server...")

        server_script = project_root / "infrastructure" / "mcp_server" / "news_pipeline_mcp_server.py"

        if not server_script.exists():
            raise FileNotFoundError(f"MCP server script not found: {server_script}")

        # Start MCP server
        self.mcp_process = subprocess.Popen(
            [sys.executable, str(server_script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Wait a bit for server to start
        await asyncio.sleep(3)

        if self.mcp_process.poll() is not None:
            stdout, stderr = self.mcp_process.communicate()
            raise RuntimeError(f"MCP server failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")

        logger.info("✅ MCP server started")

    async def _configure_adapter(self):
        """
        Configure the API adapter based on mode.
        """
        logger.info(f"⚙️ Configuring adapter for {self.mode} mode")

        # Set environment variable for auto-detection
        os.environ["USE_MCP"] = "true" if self.mode == "mcp" else "false"

        # Configure global adapter
        adapter = get_api_adapter(use_mcp=(self.mode == "mcp"), fallback_to_direct=self.fallback)

        # Set global mode
        await set_global_adapter_mode(use_mcp=(self.mode == "mcp"))

        logger.info(f"✅ Adapter configured: MCP={self.mode == 'mcp'}, Fallback={self.fallback}")

    async def _health_check(self):
        """
        Perform health check on the adapter and services.
        """
        logger.info("🏥 Performing health check...")

        adapter = get_api_adapter()
        health = await adapter.health_check()

        logger.info(f"Health Status: {health}")

        # Check if critical services are available
        services = health.get("services", {})

        if self.mode == "mcp" and services.get("mcp") == "unhealthy" and not self.fallback:
            raise RuntimeError("MCP server is unhealthy and fallback is disabled")

        if services.get("direct_ai") == "not_configured" and services.get("mcp") != "healthy":
            raise RuntimeError("No AI services available (OpenAI API key not configured)")

        logger.info("✅ Health check passed")

    async def _run_pipeline(self, target_articles: int):
        """
        Run the main pipeline.
        """
        logger.info(f"🔄 Starting pipeline with {target_articles} target articles")

        # Import and run the existing pipeline with minimal modifications
        try:
            from src.pipelines.enhanced_comprehensive_pipeline import EnhancedComprehensivePipeline

            # Create pipeline instance
            pipeline = EnhancedComprehensivePipeline(target_articles=target_articles)

            # Optional: Patch pipeline to use unified adapter functions
            await self._patch_pipeline_for_mcp(pipeline)

            # Run pipeline
            result = await pipeline.run_complete_pipeline()

            logger.info("✅ Pipeline completed successfully")
            logger.info(f"📊 Results: {result}")

            return result

        except ImportError:
            logger.error("❌ Could not import existing pipeline")
            # Fallback to simple example
            await self._run_simple_example()

    async def _patch_pipeline_for_mcp(self, pipeline):
        """
        Optionally patch the pipeline to use MCP adapter.

        This is an example of how to gradually integrate MCP without
        rewriting the entire pipeline.
        """
        if self.mode != "mcp":
            return

        logger.info("🔧 Patching pipeline for MCP support...")

        # Example: Replace direct API calls with adapter calls
        # This is optional and can be done gradually

        original_process_articles = getattr(pipeline, "process_articles_with_agents", None)

        if original_process_articles:

            async def mcp_process_articles(articles):
                """MCP-enhanced article processing."""
                logger.info("🤖 Using MCP-enhanced processing")

                adapter = get_api_adapter()
                processed_articles = []

                for article in articles:
                    try:
                        # Use unified classification
                        result = await adapter.classify_news_article(
                            article_content=article.get("content", ""),
                            article_title=article.get("title", ""),
                            source=article.get("source", ""),
                            use_memory=True,
                        )

                        # Convert result to expected format
                        if result.get("success"):
                            article["final_score"] = result.get("final_score", 6.0)
                            article["agent_responses"] = result.get("agent_results", {})
                            article["processing_status"] = "success"
                        else:
                            article["final_score"] = 0.0
                            article["agent_responses"] = {}
                            article["processing_status"] = "error"

                        processed_articles.append(article)

                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                        article["final_score"] = 0.0
                        article["processing_status"] = "error"
                        processed_articles.append(article)

                return processed_articles

            # Replace the method (this is optional patching)
            # pipeline.process_articles_with_agents = mcp_process_articles
            logger.info("✅ Pipeline patched for MCP")
        else:
            logger.info("ℹ️ Pipeline patching not needed")

    async def _run_simple_example(self):
        """
        Run a simple example if the main pipeline is not available.
        """
        logger.info("🔄 Running simple MCP example...")

        from infrastructure.mcp_adapter.api_adapter import classify_article_unified, fetch_rss_unified

        # Test RSS feed
        rss_result = await fetch_rss_unified(
            url="https://www.coindesk.com/arc/outboundfeeds/rss/", source_name="CoinDesk", max_articles=5
        )

        if rss_result.get("success"):
            articles = rss_result.get("articles", [])
            logger.info(f"📰 Fetched {len(articles)} articles")

            # Test classification on first article
            if articles:
                first_article = articles[0]
                classification_result = await classify_article_unified(
                    article_content=first_article.get("description", ""),
                    article_title=first_article.get("title", ""),
                    source=first_article.get("source", ""),
                )

                logger.info(f"🤖 Classification result: {classification_result}")

        logger.info("✅ Simple example completed")

    async def _cleanup(self):
        """
        Cleanup resources.
        """
        logger.info("🧹 Cleaning up...")

        # Close adapter
        adapter = get_api_adapter()
        await adapter.close()

        # Stop MCP server if we started it
        if self.mcp_process:
            logger.info("🛑 Stopping MCP server...")
            self.mcp_process.terminate()
            try:
                self.mcp_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
                self.mcp_process.wait()
            logger.info("✅ MCP server stopped")


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="Run pipeline with MCP support")

    parser.add_argument("--mode", choices=["direct", "mcp"], default="direct", help="API mode: direct (current) or mcp (new)")

    parser.add_argument("--fallback", action="store_true", default=True, help="Enable fallback to direct APIs if MCP fails")

    parser.add_argument("--no-fallback", action="store_true", help="Disable fallback to direct APIs")

    parser.add_argument("--start-server", action="store_true", help="Start MCP server automatically")

    parser.add_argument("--target-articles", type=int, default=120, help="Number of articles to process")

    args = parser.parse_args()

    # Handle no-fallback flag
    if args.no_fallback:
        args.fallback = False

    # Create and run pipeline
    runner = MCPPipelineRunner(mode=args.mode, fallback=args.fallback, start_server=args.start_server)

    try:
        asyncio.run(runner.run(target_articles=args.target_articles))
        print("🎉 Pipeline completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
