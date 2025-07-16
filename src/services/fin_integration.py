import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse


class FINIntegration:
    """
    Financial Intelligence Network (FIN) integration for news article analysis.
    Provides credibility scoring, sentiment analysis, and market impact assessment.
    """

    def __init__(self):
        # Mock credibility scores for different domains
        self.domain_credibility = {
            "reuters.com": 95,
            "bloomberg.com": 94,
            "wsj.com": 93,
            "ft.com": 92,
            "cnbc.com": 85,
            "yahoo.com": 80,
            "marketwatch.com": 82,
            "coindesk.com": 85,
            "cointelegraph.com": 75,
            "decrypt.co": 80,
            "theblock.co": 83,
            "kitco.com": 75,
            "infosecurity-magazine.com": 80,
            "cryptomarketsreport.com": 70,
            "finance.yahoo.com": 82,
            "businesswire.com": 90,  # Press releases are factual
            "default": 60,  # Unknown domains
        }

        # Market impact keywords
        self.high_impact_keywords = [
            "etf",
            "sec",
            "regulation",
            "bitcoin",
            "ethereum",
            "blackrock",
            "fidelity",
            "federal reserve",
            "interest rate",
            "inflation",
            "gdp",
            "earnings",
            "ipo",
            "merger",
            "acquisition",
            "bankruptcy",
            "lawsuit",
        ]

        self.medium_impact_keywords = [
            "trading",
            "investment",
            "market",
            "price",
            "volume",
            "analysis",
            "forecast",
            "prediction",
            "crypto",
            "blockchain",
            "defi",
        ]

        # Sentiment keywords
        self.positive_keywords = [
            "gain",
            "rise",
            "surge",
            "jump",
            "rally",
            "bull",
            "bullish",
            "optimistic",
            "growth",
            "increase",
            "profit",
            "success",
            "breakthrough",
            "positive",
        ]

        self.negative_keywords = [
            "fall",
            "drop",
            "crash",
            "decline",
            "bear",
            "bearish",
            "pessimistic",
            "loss",
            "decrease",
            "plunge",
            "collapse",
            "negative",
            "concern",
            "worry",
        ]

    def get_domain_credibility(self, url: str) -> int:
        """Get credibility score for a domain"""
        try:
            domain = urlparse(url).netloc.lower()
            return self.domain_credibility.get(
                domain, self.domain_credibility["default"]
            )
        except:
            return self.domain_credibility["default"]

    def analyze_sentiment(self, content: str) -> Dict:
        """Analyze sentiment of the content"""
        content_lower = content.lower()

        positive_count = sum(
            1 for keyword in self.positive_keywords if keyword in content_lower
        )
        negative_count = sum(
            1 for keyword in self.negative_keywords if keyword in content_lower
        )

        if positive_count > negative_count:
            sentiment = "bullish"
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = "bearish"
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = "neutral"
            confidence = 0.65

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
        }

    def assess_market_impact(self, content: str) -> str:
        """Assess potential market impact"""
        content_lower = content.lower()

        high_impact_count = sum(
            1 for keyword in self.high_impact_keywords if keyword in content_lower
        )
        medium_impact_count = sum(
            1 for keyword in self.medium_impact_keywords if keyword in content_lower
        )

        if high_impact_count >= 2:
            return "high"
        elif high_impact_count >= 1 or medium_impact_count >= 3:
            return "medium"
        else:
            return "low"

    def count_crypto_mentions(self, content: str) -> int:
        """Count cryptocurrency mentions"""
        crypto_keywords = [
            "bitcoin",
            "ethereum",
            "crypto",
            "blockchain",
            "btc",
            "eth",
            "defi",
            "nft",
        ]
        content_lower = content.lower()
        return sum(1 for keyword in crypto_keywords if keyword in content_lower)

    def analyze_article(self, url: str, content: str, title: str = "") -> Dict:
        """
        Comprehensive analysis of an article.

        Args:
            url: Article URL
            content: Article content
            title: Article title

        Returns:
            Dictionary with analysis results
        """
        full_text = f"{title} {content}"

        # Get domain credibility
        domain_credibility = self.get_domain_credibility(url)

        # Analyze sentiment
        sentiment_analysis = self.analyze_sentiment(full_text)

        # Assess market impact
        market_impact = self.assess_market_impact(full_text)

        # Count crypto mentions
        crypto_mentions = self.count_crypto_mentions(full_text)

        # Calculate overall credibility score
        base_score = domain_credibility

        # Adjust based on sentiment confidence
        sentiment_adjustment = (sentiment_analysis["confidence"] - 0.5) * 10

        # Final credibility score
        final_credibility = min(100, max(0, base_score + sentiment_adjustment))

        return {
            "source_credibility": {
                "source_credibility": domain_credibility,
                "domain": urlparse(url).netloc,
                "classification": (
                    "news_outlet" if domain_credibility > 80 else "unknown"
                ),
            },
            "sentiment_analysis": {
                "sentiment": sentiment_analysis["sentiment"],
                "confidence": sentiment_analysis["confidence"],
                "market_impact": market_impact,
                "crypto_mentions": crypto_mentions,
                "sentiment_scores": {
                    "positive": sentiment_analysis["positive_indicators"],
                    "negative": sentiment_analysis["negative_indicators"],
                    "neutral": 1 if sentiment_analysis["sentiment"] == "neutral" else 0,
                },
            },
            "fact_check": {
                "fact_check_score": int(final_credibility),
                "classification": (
                    "verified" if final_credibility > 70 else "unverified"
                ),
                "timestamp": datetime.now().isoformat(),
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "fin_version": "1.0.0",
        }


# Create global instance
fin_integration = FINIntegration()

# Export for other modules
__all__ = ["fin_integration", "FINIntegration"]
