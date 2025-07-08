import re
import json
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

class FINIntegration:
    """
    Mock FIN (Financial Intelligence Network) integration for news article analysis.
    Provides credibility scoring and sentiment analysis.
    """
    
    def __init__(self):
        # Mock credibility scores for different domains
        self.domain_credibility = {
            'reuters.com': 95,
            'bloomberg.com': 94,
            'wsj.com': 93,
            'ft.com': 92,
            'cnbc.com': 85,
            'yahoo.com': 80,
            'marketwatch.com': 82,
            'coindesk.com': 85,
            'cointelegraph.com': 75,
            'decrypt.co': 80,
            'theblock.co': 83,
            'kitco.com': 75,
            'infosecurity-magazine.com': 80,
            'cryptomarketsreport.com': 70,
            'finance.yahoo.com': 82,
            'businesswire.com': 90,  # Press releases are factual
            'default': 60  # Unknown domains
        }
        
        # Market impact keywords
        self.high_impact_keywords = [
            'etf', 'sec', 'regulation', 'bitcoin', 'ethereum', 'blackrock', 'fidelity',
            'federal reserve', 'interest rate', 'inflation', 'gdp', 'earnings',
            'ipo', 'merger', 'acquisition', 'bankruptcy', 'lawsuit'
        ]
        
        self.medium_impact_keywords = [
            'trading', 'investment', 'market', 'price', 'volume', 'analysis',
            'forecast', 'prediction', 'crypto', 'blockchain', 'defi'
        ]
    
    def get_source_credibility(self, url: str = None, domain: str = None) -> Dict:
        """
        Get credibility score for a news source.
        """
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
        
        if domain:
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            credibility_score = self.domain_credibility.get(domain, self.domain_credibility['default'])
            
            # Adjust based on domain characteristics
            if 'press' in domain or 'wire' in domain:
                credibility_score += 5  # Press releases are typically factual
            elif 'blog' in domain or 'medium.com' in domain:
                credibility_score -= 10  # Blogs are less reliable
            elif '.gov' in domain or '.edu' in domain:
                credibility_score = 95  # Government and educational sources
            
            # Ensure score is within bounds
            credibility_score = max(0, min(100, credibility_score))
            
            return {
                'source_credibility': credibility_score,
                'domain': domain,
                'classification': self._classify_credibility(credibility_score)
            }
        
        return {
            'source_credibility': 60,
            'domain': 'unknown',
            'classification': 'unknown'
        }
    
    def _classify_credibility(self, score: int) -> str:
        """Classify credibility score into categories."""
        if score >= 90:
            return 'premier'
        elif score >= 80:
            return 'established'
        elif score >= 70:
            return 'reliable'
        elif score >= 60:
            return 'moderate'
        else:
            return 'questionable'
    
    def analyze_sentiment(self, content: str) -> Dict:
        """
        Analyze sentiment and market impact of content.
        """
        content_lower = content.lower()
        
        # Simple sentiment analysis based on keywords
        positive_keywords = [
            'surge', 'rally', 'bullish', 'growth', 'increase', 'rise', 'gain',
            'positive', 'optimistic', 'breakthrough', 'success', 'approval',
            'adoption', 'institutional', 'milestone', 'record', 'high'
        ]
        
        negative_keywords = [
            'crash', 'dump', 'bearish', 'decline', 'fall', 'drop', 'loss',
            'negative', 'pessimistic', 'concern', 'worry', 'ban', 'restriction',
            'hack', 'scam', 'fraud', 'regulation', 'crackdown', 'low'
        ]
        
        neutral_keywords = [
            'analysis', 'report', 'study', 'data', 'information', 'update',
            'news', 'announcement', 'statement', 'development', 'technical'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
        neutral_count = sum(1 for keyword in neutral_keywords if keyword in content_lower)
        
        # Determine sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = 'bullish'
            confidence = min(0.9, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = 'bearish'
            confidence = min(0.9, 0.5 + (negative_count * 0.1))
        else:
            sentiment = 'neutral'
            confidence = min(0.8, 0.6 + (neutral_count * 0.05))
        
        # Determine market impact
        high_impact_count = sum(1 for keyword in self.high_impact_keywords if keyword in content_lower)
        medium_impact_count = sum(1 for keyword in self.medium_impact_keywords if keyword in content_lower)
        
        if high_impact_count >= 2:
            market_impact = 'high'
        elif high_impact_count >= 1 or medium_impact_count >= 3:
            market_impact = 'medium'
        else:
            market_impact = 'low'
        
        # Count crypto mentions
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
            'blockchain', 'defi', 'nft', 'token', 'altcoin', 'stablecoin'
        ]
        
        crypto_mentions = sum(1 for keyword in crypto_keywords if keyword in content_lower)
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'market_impact': market_impact,
            'crypto_mentions': crypto_mentions,
            'sentiment_scores': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        }
    
    def fact_check_enhancement(self, content: str) -> Dict:
        """
        Enhance fact-checking with FIN data.
        """
        # Mock fact-checking enhancement
        fact_check_score = 85  # Default score
        
        # Adjust based on content characteristics
        if 'according to' in content.lower() or 'sources say' in content.lower():
            fact_check_score += 5  # Attribution increases credibility
        
        if 'rumor' in content.lower() or 'allegedly' in content.lower():
            fact_check_score -= 10  # Speculative language decreases credibility
        
        if re.search(r'\d{4}-\d{2}-\d{2}', content):  # Contains dates
            fact_check_score += 3  # Specific dates increase credibility
        
        if re.search(r'\$[\d,]+', content):  # Contains monetary figures
            fact_check_score += 3  # Specific figures increase credibility
        
        # Ensure score is within bounds
        fact_check_score = max(0, min(100, fact_check_score))
        
        return {
            'fact_check_score': fact_check_score,
            'classification': 'verified' if fact_check_score >= 80 else 'likely_accurate' if fact_check_score >= 60 else 'unverified',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_comprehensive_analysis(self, content: str, url: str = None) -> Dict:
        """
        Get comprehensive FIN analysis combining all features.
        """
        source_cred = self.get_source_credibility(url)
        sentiment = self.analyze_sentiment(content)
        fact_check = self.fact_check_enhancement(content)
        
        return {
            'source_credibility': source_cred,
            'sentiment_analysis': sentiment,
            'fact_check': fact_check,
            'analysis_timestamp': datetime.now().isoformat(),
            'fin_version': '1.0.0'
        }

# Global instance
fin_integration = FINIntegration() 