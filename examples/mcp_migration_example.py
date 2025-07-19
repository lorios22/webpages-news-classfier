#!/usr/bin/env python3
"""
MCP Migration Example
====================

This example shows how to migrate from direct APIs to MCP without
breaking existing functionality. The migration can be done gradually
and switched on/off with configuration.

Run this example to see how the adapter works with both MCP and direct APIs.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from infrastructure.mcp_adapter.api_adapter import (
    APIAdapter,
    classify_article_unified,
    fetch_rss_unified,
    get_api_adapter,
    scrape_content_unified,
    set_global_adapter_mode,
)


async def main():
    """
    Demonstrate MCP migration capabilities.
    """
    print("🚀 MCP Migration Example")
    print("=" * 50)

    # ===========================================
    # Example 1: Direct API Usage (Current)
    # ===========================================

    print("\n📌 Example 1: Direct API Mode (Current)")
    print("-" * 30)

    # Configure adapter for direct APIs (current behavior)
    adapter = APIAdapter(use_mcp=False, fallback_to_direct=True)

    # Health check
    health = await adapter.health_check()
    print(f"🏥 Health Status: {health}")

    # Test AI classification
    print("\n🤖 Testing AI Classification (Direct API):")
    ai_result = await adapter.ai_agent_classify(
        messages=[{"role": "user", "content": "Classify this test message"}], max_tokens=50
    )
    print(f"✅ AI Result: {ai_result.get('success', False)} - Method: {ai_result.get('method', 'unknown')}")

    # Test RSS feed
    print("\n📰 Testing RSS Feed (Direct API):")
    rss_result = await adapter.fetch_rss_feed(
        url="https://www.coindesk.com/arc/outboundfeeds/rss/", source_name="CoinDesk", max_articles=3
    )
    print(f"✅ RSS Result: {rss_result.get('success', False)} - Articles: {rss_result.get('articles_count', 0)}")

    # ===========================================
    # Example 2: MCP Mode (Future)
    # ===========================================

    print("\n📌 Example 2: MCP Mode (Future)")
    print("-" * 30)

    # Switch to MCP mode (this would use MCP server if running)
    adapter.switch_to_mcp()

    # Test the same operations with MCP (will fallback to direct APIs if MCP not running)
    print("\n🤖 Testing AI Classification (MCP Mode):")
    ai_result_mcp = await adapter.ai_agent_classify(
        messages=[{"role": "user", "content": "Classify this test message via MCP"}], max_tokens=50
    )
    print(f"✅ AI Result: {ai_result_mcp.get('success', False)} - Method: {ai_result_mcp.get('method', 'unknown')}")

    # ===========================================
    # Example 3: Unified Functions (Recommended)
    # ===========================================

    print("\n📌 Example 3: Unified Functions (Recommended)")
    print("-" * 30)

    # These functions provide the same interface but can switch between MCP and direct APIs
    print("\n🔄 Testing Unified Classification:")

    # Simulate a real article classification
    sample_article = {
        "title": "Bitcoin Reaches New All-Time High as Institutional Adoption Grows",
        "content": """
        Bitcoin has reached a new all-time high of $120,000 as institutional adoption
        continues to accelerate. Major corporations and investment funds are increasingly
        adding Bitcoin to their portfolios as a hedge against inflation and economic
        uncertainty. The cryptocurrency market has shown remarkable resilience and growth
        throughout the year, with Bitcoin leading the charge.
        """,
        "source": "example_news",
    }

    unified_result = await classify_article_unified(
        article_content=sample_article["content"], article_title=sample_article["title"], source=sample_article["source"]
    )

    print(f"✅ Classification Result:")
    print(f"   Success: {unified_result.get('success', False)}")
    print(f"   Score: {unified_result.get('final_score', 'N/A')}")
    print(f"   Method: {unified_result.get('method', 'unknown')}")

    # ===========================================
    # Example 4: Existing Code Integration
    # ===========================================

    print("\n📌 Example 4: Existing Code Integration")
    print("-" * 30)

    # Show how existing pipeline code can be minimally modified
    await demonstrate_existing_code_integration()

    # ===========================================
    # Example 5: Performance Comparison
    # ===========================================

    print("\n📌 Example 5: Performance Comparison")
    print("-" * 30)

    await performance_comparison()

    # Cleanup
    await adapter.close()
    print("\n✅ Migration example completed!")


async def demonstrate_existing_code_integration():
    """
    Show how existing code can be modified minimally to support MCP.
    """

    # Original code pattern (still works):
    print("🔧 Original Code Pattern:")
    try:
        from src.agents.news_classifier_agents import NewsClassifierAgents

        print("   ✅ Existing agents still accessible")
    except ImportError:
        print("   ⚠️ Existing agents not available in this example")

    # New unified pattern (recommended):
    print("🔧 New Unified Pattern:")

    # Instead of:
    # classifier = NewsClassifierAgents()
    # result = await classifier.process_article_async(article)

    # Use:
    adapter = get_api_adapter()
    result = await adapter.classify_news_article(
        article_content="Sample content", article_title="Sample title", source="sample_source"
    )
    print(f"   ✅ Unified classification available: {result.get('success', False)}")


async def performance_comparison():
    """
    Compare performance between direct APIs and MCP.
    """

    # Test data
    test_message = {"role": "user", "content": "Quick test"}

    adapter = get_api_adapter()

    # Test direct API performance
    adapter.switch_to_direct()
    start_time = datetime.now()

    direct_result = await adapter.ai_agent_classify(messages=[test_message], max_tokens=10)

    direct_time = (datetime.now() - start_time).total_seconds()

    # Test MCP performance (with fallback)
    adapter.switch_to_mcp()
    start_time = datetime.now()

    mcp_result = await adapter.ai_agent_classify(messages=[test_message], max_tokens=10)

    mcp_time = (datetime.now() - start_time).total_seconds()

    print(f"📊 Performance Comparison:")
    print(f"   Direct API: {direct_time:.2f}s - Success: {direct_result.get('success', False)}")
    print(f"   MCP Mode:   {mcp_time:.2f}s - Success: {mcp_result.get('success', False)}")

    if direct_result.get("success") and mcp_result.get("success"):
        overhead = ((mcp_time - direct_time) / direct_time) * 100
        print(f"   MCP Overhead: {overhead:.1f}%")


# ===========================================
# Configuration Examples
# ===========================================


def show_configuration_examples():
    """
    Show different ways to configure the adapter.
    """

    print("⚙️ Configuration Examples:")

    # 1. Environment-based configuration
    print("1. Environment-based (recommended):")
    print("   export USE_MCP=true")
    print("   export MCP_SERVER_URL=http://localhost:3000")

    # 2. Code-based configuration
    print("2. Code-based:")
    print("   adapter = APIAdapter(use_mcp=True)")

    # 3. Runtime switching
    print("3. Runtime switching:")
    print("   await set_global_adapter_mode(use_mcp=True)")

    # 4. Fallback configuration
    print("4. With fallback (production recommended):")
    print("   adapter = APIAdapter(use_mcp=True, fallback_to_direct=True)")


# ===========================================
# Migration Strategies
# ===========================================


def show_migration_strategies():
    """
    Show different migration strategies.
    """

    print("🔄 Migration Strategies:")

    print("1. 🐢 Gradual Migration (Recommended):")
    print("   - Start with USE_MCP=false")
    print("   - Test MCP server separately")
    print("   - Switch components one by one")
    print("   - Enable fallback_to_direct=true")

    print("2. 🚀 Full Migration:")
    print("   - Deploy MCP server")
    print("   - Switch all components at once")
    print("   - Monitor performance closely")

    print("3. 🔀 Hybrid Approach:")
    print("   - Use MCP for new features")
    print("   - Keep direct APIs for critical paths")
    print("   - Migrate based on performance")


if __name__ == "__main__":
    print("📋 Configuration Examples:")
    show_configuration_examples()

    print("\n📋 Migration Strategies:")
    show_migration_strategies()

    print("\n🚀 Running Live Examples:")
    asyncio.run(main())
