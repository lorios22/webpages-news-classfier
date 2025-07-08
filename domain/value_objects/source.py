"""
Source Value Object

This module defines the Source value object used to represent
information about news sources in the classification system.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse


class SourceType(Enum):
    """Enumeration of source types"""
    NEWS_OUTLET = "news_outlet"
    BLOG = "blog"
    PRESS_RELEASE = "press_release"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"


class CredibilityLevel(Enum):
    """Enumeration of credibility levels"""
    PREMIER = "premier"          # 90-100
    ESTABLISHED = "established"  # 80-89
    RELIABLE = "reliable"        # 70-79
    MODERATE = "moderate"        # 60-69
    QUESTIONABLE = "questionable"  # 0-59


@dataclass(frozen=True)
class Source:
    """
    Value object representing a news source with credibility information.
    
    This immutable object encapsulates source information including
    domain, credibility scoring, and source classification.
    
    Attributes:
        domain: Source domain (e.g., "reuters.com")
        url: Full URL of the source
        credibility_score: Numeric credibility score (0-100)
        credibility_level: Categorical credibility level
        source_type: Type of source (news outlet, blog, etc.)
        bias_score: Political/ideological bias score (-100 to 100)
        reputation_score: Overall reputation score (0-100)
        verified: Whether the source is verified/authenticated
        metadata: Additional source metadata
        last_updated: When source information was last updated
    """
    
    domain: str
    url: str
    credibility_score: int = 60
    credibility_level: CredibilityLevel = CredibilityLevel.MODERATE
    source_type: SourceType = SourceType.UNKNOWN
    bias_score: int = 0
    reputation_score: int = 60
    verified: bool = False
    metadata: Dict[str, Any] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        """Initialize default values and validate source information"""
        # Use object.__setattr__ because dataclass is frozen
        if self.last_updated is None:
            object.__setattr__(self, 'last_updated', datetime.now())
        
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
        
        self._validate_source()
        self._set_credibility_level()
        self._set_source_type()
    
    def _validate_source(self) -> None:
        """
        Validate source information.
        
        Raises:
            ValueError: If source information is invalid
        """
        if not self.domain or not self.domain.strip():
            raise ValueError("Domain is required")
        
        if not self.url or not self.url.strip():
            raise ValueError("URL is required")
        
        if not isinstance(self.credibility_score, int):
            raise ValueError("Credibility score must be an integer")
        
        if self.credibility_score < 0 or self.credibility_score > 100:
            raise ValueError("Credibility score must be between 0 and 100")
        
        if not isinstance(self.bias_score, int):
            raise ValueError("Bias score must be an integer")
        
        if self.bias_score < -100 or self.bias_score > 100:
            raise ValueError("Bias score must be between -100 and 100")
        
        if not isinstance(self.reputation_score, int):
            raise ValueError("Reputation score must be an integer")
        
        if self.reputation_score < 0 or self.reputation_score > 100:
            raise ValueError("Reputation score must be between 0 and 100")
    
    def _set_credibility_level(self) -> None:
        """Set credibility level based on credibility score"""
        if self.credibility_score >= 90:
            level = CredibilityLevel.PREMIER
        elif self.credibility_score >= 80:
            level = CredibilityLevel.ESTABLISHED
        elif self.credibility_score >= 70:
            level = CredibilityLevel.RELIABLE
        elif self.credibility_score >= 60:
            level = CredibilityLevel.MODERATE
        else:
            level = CredibilityLevel.QUESTIONABLE
        
        object.__setattr__(self, 'credibility_level', level)
    
    def _set_source_type(self) -> None:
        """Determine source type based on domain and URL patterns"""
        domain_lower = self.domain.lower()
        url_lower = self.url.lower()
        
        # Government sources
        if domain_lower.endswith('.gov') or domain_lower.endswith('.mil'):
            source_type = SourceType.GOVERNMENT
        # Academic sources
        elif domain_lower.endswith('.edu') or 'university' in domain_lower or 'college' in domain_lower:
            source_type = SourceType.ACADEMIC
        # Press releases
        elif any(pr in domain_lower for pr in ['businesswire', 'prnewswire', 'marketwatch']):
            source_type = SourceType.PRESS_RELEASE
        # Social media
        elif any(sm in domain_lower for sm in ['twitter', 'facebook', 'linkedin', 'reddit']):
            source_type = SourceType.SOCIAL_MEDIA
        # Blogs
        elif any(blog in domain_lower for blog in ['blog', 'medium', 'substack']) or '/blog/' in url_lower:
            source_type = SourceType.BLOG
        # News outlets (major domains)
        elif any(news in domain_lower for news in [
            'reuters', 'bloomberg', 'wsj', 'ft.com', 'cnn', 'bbc', 'cnbc',
            'coindesk', 'cointelegraph', 'theblock', 'decrypt'
        ]):
            source_type = SourceType.NEWS_OUTLET
        else:
            source_type = SourceType.UNKNOWN
        
        object.__setattr__(self, 'source_type', source_type)
    
    def is_high_credibility(self, threshold: int = 80) -> bool:
        """
        Check if source has high credibility.
        
        Args:
            threshold: Credibility threshold
            
        Returns:
            True if credibility score exceeds threshold
        """
        return self.credibility_score >= threshold
    
    def is_low_credibility(self, threshold: int = 60) -> bool:
        """
        Check if source has low credibility.
        
        Args:
            threshold: Credibility threshold
            
        Returns:
            True if credibility score is below threshold
        """
        return self.credibility_score < threshold
    
    def is_biased(self, threshold: int = 30) -> bool:
        """
        Check if source shows significant bias.
        
        Args:
            threshold: Bias threshold (absolute value)
            
        Returns:
            True if absolute bias score exceeds threshold
        """
        return abs(self.bias_score) >= threshold
    
    def get_bias_direction(self) -> str:
        """
        Get the direction of bias.
        
        Returns:
            String indicating bias direction ("left", "right", "center")
        """
        if self.bias_score > 10:
            return "right"
        elif self.bias_score < -10:
            return "left"
        else:
            return "center"
    
    def is_premium_source(self) -> bool:
        """
        Check if this is a premium/premier news source.
        
        Returns:
            True if source is premier level
        """
        return self.credibility_level == CredibilityLevel.PREMIER
    
    def get_trust_score(self) -> float:
        """
        Calculate overall trust score combining credibility and reputation.
        
        Returns:
            Combined trust score (0.0-10.0)
        """
        # Weight credibility more heavily than reputation
        combined = (self.credibility_score * 0.7) + (self.reputation_score * 0.3)
        return round(combined / 10, 1)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert source to dictionary representation.
        
        Returns:
            Dictionary representation of the source
        """
        return {
            "domain": self.domain,
            "url": self.url,
            "credibility_score": self.credibility_score,
            "credibility_level": self.credibility_level.value,
            "source_type": self.source_type.value,
            "bias_score": self.bias_score,
            "reputation_score": self.reputation_score,
            "verified": self.verified,
            "metadata": self.metadata,
            "last_updated": self.last_updated.isoformat(),
            "trust_score": self.get_trust_score(),
            "bias_direction": self.get_bias_direction()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """
        Create Source instance from dictionary.
        
        Args:
            data: Dictionary with source data
            
        Returns:
            Source instance
        """
        credibility_level = CredibilityLevel(data.get("credibility_level", "moderate"))
        source_type = SourceType(data.get("source_type", "unknown"))
        last_updated = datetime.fromisoformat(data.get("last_updated")) if data.get("last_updated") else datetime.now()
        
        return cls(
            domain=data["domain"],
            url=data["url"],
            credibility_score=int(data.get("credibility_score", 60)),
            credibility_level=credibility_level,
            source_type=source_type,
            bias_score=int(data.get("bias_score", 0)),
            reputation_score=int(data.get("reputation_score", 60)),
            verified=bool(data.get("verified", False)),
            metadata=data.get("metadata", {}),
            last_updated=last_updated
        )
    
    @classmethod
    def from_url(cls, url: str, credibility_score: int = None) -> 'Source':
        """
        Create Source instance from URL with automatic domain extraction.
        
        Args:
            url: Source URL
            credibility_score: Optional credibility score override
            
        Returns:
            Source instance
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Default credibility mapping for known domains
        default_credibility = {
            'reuters.com': 95,
            'bloomberg.com': 94,
            'wsj.com': 93,
            'ft.com': 92,
            'bbc.com': 90,
            'cnbc.com': 85,
            'coindesk.com': 85,
            'cointelegraph.com': 75,
            'businesswire.com': 90,
            'prnewswire.com': 88
        }
        
        final_credibility = credibility_score or default_credibility.get(domain, 60)
        
        return cls(
            domain=domain,
            url=url,
            credibility_score=final_credibility
        )
    
    def __str__(self) -> str:
        """String representation of the source"""
        return f"Source({self.domain}, {self.credibility_level.value}, score={self.credibility_score})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the source"""
        return (f"Source(domain='{self.domain}', credibility_score={self.credibility_score}, "
                f"credibility_level='{self.credibility_level.value}', source_type='{self.source_type.value}')") 