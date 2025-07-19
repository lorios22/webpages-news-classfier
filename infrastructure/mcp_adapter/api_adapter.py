#!/usr/bin/env python3
"""
API Adapter for MCP Migration
=============================

This adapter allows gradual migration from direct API calls to MCP without
breaking existing functionality. It provides backward compatibility while
enabling MCP features.

Usage:
    # Instead of direct API calls:
    from infrastructure.mcp_adapter.api_adapter import APIAdapter

    adapter = APIAdapter(use_mcp=True)  # or False for direct APIs
    result = await adapter.classify_article(content, title, source)

Features:
- Backward compatibility with existing code
- Seamless switching between MCP and direct APIs
- Configuration-based selection
- Fallback mechanisms
- Performance monitoring
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIAdapter:
    """
    Unified API adapter that can use MCP or direct APIs.

    This class provides the same interface as existing code but can
    route requests through MCP server or direct APIs based on configuration.
    """

    def __init__(self, use_mcp: bool = None, mcp_server_url: str = "http://localhost:3000", fallback_to_direct: bool = True):
        """
        Initialize the API adapter.

        Args:
            use_mcp: Whether to use MCP server (None = auto-detect)
            mcp_server_url: MCP server URL
            fallback_to_direct: Whether to fallback to direct APIs if MCP fails
        """
        self.use_mcp = use_mcp if use_mcp is not None else self._should_use_mcp()
        self.mcp_server_url = mcp_server_url
        self.fallback_to_direct = fallback_to_direct

        # Direct API clients (existing code compatibility)
        self._init_direct_apis()

        # MCP client
        self.mcp_client = None
        if self.use_mcp:
            self._init_mcp_client()

    def _should_use_mcp(self) -> bool:
        """Auto-detect whether to use MCP based on environment."""
        return os.getenv("USE_MCP", "false").lower() == "true"

    def _init_direct_apis(self):
        """Initialize direct API clients (existing functionality)."""
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=openai_api_key)
                logger.info("✅ Direct OpenAI API initialized")
            else:
                self.llm = None
                logger.warning("⚠️ OpenAI API key not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize direct APIs: {e}")
            self.llm = None

    def _init_mcp_client(self):
        """Initialize MCP client."""
        try:
            # This would be replaced with actual MCP client
            self.mcp_client = httpx.AsyncClient()
            logger.info(f"✅ MCP client initialized: {self.mcp_server_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP client: {e}")
            self.mcp_client = None
            if not self.fallback_to_direct:
                raise

    async def _call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call MCP tool and return result."""
        try:
            if not self.mcp_client:
                raise Exception("MCP client not initialized")

            response = await self.mcp_client.post(f"{self.mcp_server_url}/tools/{tool_name}", json=kwargs, timeout=60.0)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"MCP tool error: {response.status_code}")

        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            if self.fallback_to_direct:
                logger.info("🔄 Falling back to direct API")
                return {"error": str(e), "fallback": True}
            else:
                raise

    # ===========================================
    # AI Agent Methods (compatible with existing code)
    # ===========================================

    async def ai_agent_classify(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        AI agent classification compatible with existing NewsClassifierAgents.
        """
        if self.use_mcp and self.mcp_client:
            try:
                result = await self._call_mcp_tool(
                    "ai_agent_classify", model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
                )

                if not result.get("fallback"):
                    return result
            except Exception as e:
                logger.warning(f"MCP call failed, using direct API: {e}")

        # Direct API call (existing functionality)
        try:
            if not self.llm:
                return {"error": "No AI model available"}

            # Convert messages to LangChain format
            lc_messages = [HumanMessage(content=msg["content"]) for msg in messages if msg.get("role") == "user"]

            response = await self.llm.ainvoke(lc_messages)

            return {"success": True, "response": response.content, "model": model, "method": "direct_api"}
        except Exception as e:
            logger.error(f"Direct AI API error: {e}")
            return {"error": str(e)}

    async def classify_news_article(
        self, article_content: str, article_title: str, source: str, use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Complete news article classification using 13-agent pipeline.

        This method is compatible with existing pipeline code.
        """
        if self.use_mcp and self.mcp_client:
            try:
                result = await self._call_mcp_tool(
                    "classify_news_article",
                    article_content=article_content,
                    article_title=article_title,
                    source=source,
                    use_memory=use_memory,
                )

                if not result.get("fallback"):
                    return result
            except Exception as e:
                logger.warning(f"MCP classification failed, using direct method: {e}")

        # Direct classification (existing functionality)
        return await self._direct_classify_article(article_content, article_title, source, use_memory)

    async def _direct_classify_article(
        self, article_content: str, article_title: str, source: str, use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Direct article classification using existing logic.

        This maintains compatibility with existing NewsClassifierAgents.
        """
        try:
            # Import existing agents (maintains backward compatibility)
            from src.agents.news_classifier_agents import NewsClassifierAgents

            # Use existing classification logic
            classifier = NewsClassifierAgents()

            # Create article object compatible with existing code
            article = {
                "title": article_title,
                "content": article_content,
                "source": source,
                "url": "",  # Not needed for classification
                "published_date": "",  # Not needed for classification
            }

            # Process through existing agent pipeline
            result = await classifier.process_article_async(article)

            return {
                "success": True,
                "article_title": article_title,
                "source": source,
                "final_score": result.get("final_score", 6.0),
                "agent_results": result.get("agent_responses", {}),
                "method": "direct_agents",
            }

        except Exception as e:
            logger.error(f"Direct classification error: {e}")
            return {"error": str(e), "article_title": article_title, "method": "direct_agents"}

    # ===========================================
    # RSS Feed Methods
    # ===========================================

    async def fetch_rss_feed(self, url: str, source_name: str, max_articles: int = 50) -> Dict[str, Any]:
        """
        Fetch RSS feed compatible with existing extractor.
        """
        if self.use_mcp and self.mcp_client:
            try:
                result = await self._call_mcp_tool(
                    "fetch_rss_feed", url=url, source_name=source_name, max_articles=max_articles
                )

                if not result.get("fallback"):
                    return result
            except Exception as e:
                logger.warning(f"MCP RSS fetch failed, using direct method: {e}")

        # Direct RSS fetching (existing functionality)
        return await self._direct_fetch_rss(url, source_name, max_articles)

    async def _direct_fetch_rss(self, url: str, source_name: str, max_articles: int = 50) -> Dict[str, Any]:
        """
        Direct RSS fetching using existing logic.
        """
        try:
            # Import existing extractor
            from src.extractors.enhanced_crypto_macro_extractor import EnhancedCryptoMacroExtractor

            extractor = EnhancedCryptoMacroExtractor()

            # Use existing RSS processing logic
            response = extractor.safe_request(url)
            if not response:
                return {"error": f"Failed to fetch {url}"}

            import feedparser

            feed = feedparser.parse(response.text)

            articles = []
            for entry in feed.entries[:max_articles]:
                article = {
                    "title": getattr(entry, "title", "No title"),
                    "link": getattr(entry, "link", ""),
                    "description": getattr(entry, "description", ""),
                    "published": getattr(entry, "published", ""),
                    "source": source_name,
                }
                articles.append(article)

            return {
                "success": True,
                "source": source_name,
                "articles_count": len(articles),
                "articles": articles,
                "method": "direct_rss",
            }

        except Exception as e:
            logger.error(f"Direct RSS fetch error: {e}")
            return {"error": str(e), "url": url}

    # ===========================================
    # Web Scraping Methods
    # ===========================================

    async def scrape_web_content(self, url: str, timeout: int = 30, use_anti_blocking: bool = True) -> Dict[str, Any]:
        """
        Web scraping compatible with existing scraper.
        """
        if self.use_mcp and self.mcp_client:
            try:
                result = await self._call_mcp_tool(
                    "scrape_web_content", url=url, timeout=timeout, use_anti_blocking=use_anti_blocking
                )

                if not result.get("fallback"):
                    return result
            except Exception as e:
                logger.warning(f"MCP scraping failed, using direct method: {e}")

        # Direct scraping (existing functionality)
        return await self._direct_scrape_content(url, timeout, use_anti_blocking)

    async def _direct_scrape_content(self, url: str, timeout: int = 30, use_anti_blocking: bool = True) -> Dict[str, Any]:
        """
        Direct web scraping using existing logic.
        """
        try:
            # Import existing extractor
            from src.extractors.enhanced_crypto_macro_extractor import EnhancedCryptoMacroExtractor

            extractor = EnhancedCryptoMacroExtractor()

            # Use existing scraping logic
            response = extractor.safe_request(url, timeout=timeout)
            if not response:
                return {"error": f"Failed to scrape {url}"}

            # Extract content using existing logic
            content = extractor.extract_article_content(response.text, url)

            return {
                "success": True,
                "url": url,
                "content": content.get("content", ""),
                "title": content.get("title", ""),
                "method": "direct_scraping",
            }

        except Exception as e:
            logger.error(f"Direct scraping error: {e}")
            return {"error": str(e), "url": url}

    # ===========================================
    # Configuration and Health Methods
    # ===========================================

    async def health_check(self) -> Dict[str, Any]:
        """Health check for adapter and underlying services."""
        health = {"adapter": "healthy", "use_mcp": self.use_mcp, "services": {}}

        if self.use_mcp and self.mcp_client:
            try:
                result = await self._call_mcp_tool("health_check")
                health["services"]["mcp"] = "healthy" if result.get("success") else "unhealthy"
            except:
                health["services"]["mcp"] = "unhealthy"

        # Check direct APIs
        if self.llm:
            try:
                test_messages = [{"role": "user", "content": "test"}]
                result = await self.ai_agent_classify(test_messages, max_tokens=5)
                health["services"]["direct_ai"] = "healthy" if result.get("success") else "unhealthy"
            except:
                health["services"]["direct_ai"] = "unhealthy"
        else:
            health["services"]["direct_ai"] = "not_configured"

        return health

    def switch_to_mcp(self):
        """Switch to MCP mode."""
        self.use_mcp = True
        if not self.mcp_client:
            self._init_mcp_client()
        logger.info("✅ Switched to MCP mode")

    def switch_to_direct(self):
        """Switch to direct API mode."""
        self.use_mcp = False
        logger.info("✅ Switched to direct API mode")

    async def close(self):
        """Close all connections."""
        if self.mcp_client:
            await self.mcp_client.aclose()


# ===========================================
# Global Adapter Instance (Singleton Pattern)
# ===========================================

_global_adapter = None


def get_api_adapter(**kwargs) -> APIAdapter:
    """Get global API adapter instance (singleton)."""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = APIAdapter(**kwargs)
    return _global_adapter


async def set_global_adapter_mode(use_mcp: bool):
    """Set global adapter mode."""
    adapter = get_api_adapter()
    if use_mcp:
        adapter.switch_to_mcp()
    else:
        adapter.switch_to_direct()


# ===========================================
# Backward Compatibility Wrapper Functions
# ===========================================


async def classify_article_unified(
    article_content: str, article_title: str, source: str, use_memory: bool = True
) -> Dict[str, Any]:
    """
    Unified article classification function.

    This function can replace existing classification calls without
    changing the interface.
    """
    adapter = get_api_adapter()
    return await adapter.classify_news_article(article_content, article_title, source, use_memory)


async def fetch_rss_unified(url: str, source_name: str, max_articles: int = 50) -> Dict[str, Any]:
    """
    Unified RSS fetching function.
    """
    adapter = get_api_adapter()
    return await adapter.fetch_rss_feed(url, source_name, max_articles)


async def scrape_content_unified(url: str, timeout: int = 30, use_anti_blocking: bool = True) -> Dict[str, Any]:
    """
    Unified web scraping function.
    """
    adapter = get_api_adapter()
    return await adapter.scrape_web_content(url, timeout, use_anti_blocking)
