"""
Article Entity - Core Domain Model

This module defines the Article entity, which represents a news article
in the classification system with all its properties and business rules.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects.classification import Classification
from ..value_objects.score import Score
from ..value_objects.source import Source


class ArticleStatus(Enum):
    """Enumeration of possible article processing statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    SKIPPED = "skipped"
    ERROR = "error"


class ContentType(Enum):
    """Enumeration of supported content types"""
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    PRESS_RELEASE = "press_release"
    RESEARCH_PAPER = "research_paper"
    OPINION = "opinion"
    UNKNOWN = "unknown"


@dataclass
class Article:
    """
    Core Article entity representing a news article with all its classification data.
    
    This entity encapsulates the business logic for article classification,
    including content processing, scoring, and validation rules.
    
    Attributes:
        id: Unique identifier for the article
        url: Source URL of the article
        title: Article title
        content: Main article content
        description: Article description/summary
        source: Source information (domain, credibility, etc.)
        classification: Classification result
        scores: Individual and consolidated scores
        status: Current processing status
        content_type: Type of content (news, blog, etc.)
        created_at: Timestamp when article was created
        processed_at: Timestamp when article was processed
        metadata: Additional metadata
        agent_responses: Responses from individual AI agents
    """
    
    id: str
    url: str
    title: str
    content: str
    description: Optional[str] = None
    source: Optional[Source] = None
    classification: Optional[Classification] = None
    scores: Dict[str, Score] = field(default_factory=dict)
    status: ArticleStatus = ArticleStatus.PENDING
    content_type: ContentType = ContentType.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_responses: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate article data after initialization"""
        self._validate_required_fields()
        self._set_content_type()
    
    def _validate_required_fields(self) -> None:
        """
        Validate that required fields are present and valid.
        
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not self.id or not self.id.strip():
            raise ValueError("Article ID is required")
        
        if not self.url or not self.url.strip():
            raise ValueError("Article URL is required")
        
        if not self.title or not self.title.strip():
            raise ValueError("Article title is required")
        
        if not self.content or len(self.content.strip()) < 10:
            raise ValueError("Article content must be at least 10 characters")
    
    def _set_content_type(self) -> None:
        """Automatically determine content type based on content and metadata"""
        content_lower = self.content.lower()
        
        if any(indicator in content_lower for indicator in ["press release", "business wire", "pr newswire"]):
            self.content_type = ContentType.PRESS_RELEASE
        elif any(indicator in content_lower for indicator in ["research", "study", "analysis", "report"]):
            self.content_type = ContentType.RESEARCH_PAPER
        elif any(indicator in content_lower for indicator in ["opinion", "editorial", "commentary"]):
            self.content_type = ContentType.OPINION
        elif any(indicator in content_lower for indicator in ["blog", "post", "author:"]):
            self.content_type = ContentType.BLOG_POST
        elif any(indicator in content_lower for indicator in ["news", "breaking", "reported", "announced"]):
            self.content_type = ContentType.NEWS_ARTICLE
        else:
            self.content_type = ContentType.UNKNOWN
    
    def add_score(self, agent_name: str, score: Score) -> None:
        """
        Add a score from a specific agent.
        
        Args:
            agent_name: Name of the agent providing the score
            score: Score object with value and metadata
        """
        if not isinstance(score, Score):
            raise ValueError("Score must be a Score instance")
        
        self.scores[agent_name] = score
    
    def add_agent_response(self, agent_name: str, response: Any) -> None:
        """
        Add a response from a specific agent.
        
        Args:
            agent_name: Name of the agent
            response: Response data from the agent
        """
        self.agent_responses[agent_name] = response
    
    def set_classification(self, classification: Classification) -> None:
        """
        Set the final classification for the article.
        
        Args:
            classification: Classification result
        """
        if not isinstance(classification, Classification):
            raise ValueError("Classification must be a Classification instance")
        
        self.classification = classification
        self.status = ArticleStatus.CLASSIFIED
        self.processed_at = datetime.now()
    
    def mark_as_skipped(self, reason: str) -> None:
        """
        Mark article as skipped with a reason.
        
        Args:
            reason: Reason why the article was skipped
        """
        self.status = ArticleStatus.SKIPPED
        self.metadata["skip_reason"] = reason
        self.processed_at = datetime.now()
    
    def mark_as_error(self, error: str) -> None:
        """
        Mark article as having an error during processing.
        
        Args:
            error: Error message
        """
        self.status = ArticleStatus.ERROR
        self.metadata["error"] = error
        self.processed_at = datetime.now()
    
    def get_final_score(self) -> Optional[float]:
        """
        Get the final consolidated score.
        
        Returns:
            Final score value or None if not available
        """
        if self.classification:
            return self.classification.final_score
        return None
    
    def get_score_by_agent(self, agent_name: str) -> Optional[Score]:
        """
        Get score from a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Score object or None if not found
        """
        return self.scores.get(agent_name)
    
    def is_duplicate(self) -> bool:
        """
        Check if article was marked as duplicate.
        
        Returns:
            True if article is a duplicate
        """
        return self.metadata.get("is_duplicate", False)
    
    def get_word_count(self) -> int:
        """
        Get word count of the article content.
        
        Returns:
            Number of words in content
        """
        return len(self.content.split())
    
    def get_character_count(self) -> int:
        """
        Get character count of the article content.
        
        Returns:
            Number of characters in content
        """
        return len(self.content)
    
    def is_long_content(self, threshold: int = 12000) -> bool:
        """
        Check if article content is considered long.
        
        Args:
            threshold: Character count threshold for long content
            
        Returns:
            True if content exceeds threshold
        """
        return self.get_character_count() > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert article to dictionary representation.
        
        Returns:
            Dictionary representation of the article
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "description": self.description,
            "source": self.source.to_dict() if self.source else None,
            "classification": self.classification.to_dict() if self.classification else None,
            "scores": {name: score.to_dict() for name, score in self.scores.items()},
            "status": self.status.value,
            "content_type": self.content_type.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "metadata": self.metadata,
            "agent_responses": self.agent_responses,
            "word_count": self.get_word_count(),
            "character_count": self.get_character_count()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """
        Create Article instance from dictionary.
        
        Args:
            data: Dictionary with article data
            
        Returns:
            Article instance
        """
        # Convert string enums back to enum values
        status = ArticleStatus(data.get("status", "pending"))
        content_type = ContentType(data.get("content_type", "unknown"))
        
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now()
        processed_at = datetime.fromisoformat(data.get("processed_at")) if data.get("processed_at") else None
        
        # Create scores
        scores = {}
        for name, score_data in data.get("scores", {}).items():
            scores[name] = Score.from_dict(score_data)
        
        # Create source and classification if present
        source = Source.from_dict(data["source"]) if data.get("source") else None
        classification = Classification.from_dict(data["classification"]) if data.get("classification") else None
        
        return cls(
            id=data["id"],
            url=data["url"],
            title=data["title"],
            content=data["content"],
            description=data.get("description"),
            source=source,
            classification=classification,
            scores=scores,
            status=status,
            content_type=content_type,
            created_at=created_at,
            processed_at=processed_at,
            metadata=data.get("metadata", {}),
            agent_responses=data.get("agent_responses", {})
        )
    
    def __str__(self) -> str:
        """String representation of the article"""
        return f"Article(id={self.id}, title='{self.title[:50]}...', status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the article"""
        return (f"Article(id={self.id}, url={self.url}, title='{self.title}', "
                f"status={self.status.value}, content_type={self.content_type.value})") 