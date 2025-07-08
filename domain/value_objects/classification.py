"""
Classification Value Object

This module defines the Classification value object used to represent
the final classification result for news articles.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ClassificationCategory(Enum):
    """Enumeration of classification categories"""
    OUTSTANDING = "Outstanding"
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    VERY_POOR = "Very Poor"


class QualityLevel(Enum):
    """Enumeration of quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Classification:
    """
    Value object representing the final classification result for an article.
    
    This immutable object encapsulates the final classification decision,
    including scores, reasoning, and quality assessment.
    
    Attributes:
        final_score: Final consolidated score (0.1-10.0)
        category: Classification category (Outstanding, Excellent, etc.)
        quality_level: Overall quality level (high, medium, low)
        summary: Brief summary of the article
        rationale: Detailed reasoning for the classification
        confidence: Confidence in the classification (0.0-1.0)
        sub_scores: Individual scores from different agents
        warnings: Any warnings or concerns about the classification
        timestamp: When the classification was made
        metadata: Additional classification metadata
    """
    
    final_score: float
    category: ClassificationCategory
    quality_level: QualityLevel
    summary: str
    rationale: str
    confidence: float = 1.0
    sub_scores: Dict[str, float] = None
    warnings: List[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values and validate classification"""
        # Use object.__setattr__ because dataclass is frozen
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())
        
        if self.sub_scores is None:
            object.__setattr__(self, 'sub_scores', {})
        
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
        
        self._validate_classification()
        self._validate_consistency()
    
    def _validate_classification(self) -> None:
        """
        Validate classification values.
        
        Raises:
            ValueError: If classification values are invalid
        """
        if not isinstance(self.final_score, (int, float)):
            raise ValueError("Final score must be numeric")
        
        if self.final_score < 0.1 or self.final_score > 10.0:
            raise ValueError("Final score must be between 0.1 and 10.0")
        
        if not isinstance(self.confidence, (int, float)):
            raise ValueError("Confidence must be numeric")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if not self.summary or len(self.summary.strip()) < 10:
            raise ValueError("Summary must be at least 10 characters")
        
        if not self.rationale or len(self.rationale.strip()) < 20:
            raise ValueError("Rationale must be at least 20 characters")
    
    def _validate_consistency(self) -> None:
        """Validate consistency between score, category, and quality level"""
        expected_category = self._score_to_category(self.final_score)
        if self.category != expected_category:
            # Add warning instead of raising error for flexibility
            warnings_list = list(self.warnings)
            warnings_list.append(
                f"Category '{self.category.value}' may not match score {self.final_score:.1f} "
                f"(expected '{expected_category.value}')"
            )
            object.__setattr__(self, 'warnings', warnings_list)
        
        expected_quality = self._score_to_quality(self.final_score)
        if self.quality_level != expected_quality:
            warnings_list = list(self.warnings)
            warnings_list.append(
                f"Quality level '{self.quality_level.value}' may not match score {self.final_score:.1f} "
                f"(expected '{expected_quality.value}')"
            )
            object.__setattr__(self, 'warnings', warnings_list)
    
    @staticmethod
    def _score_to_category(score: float) -> ClassificationCategory:
        """Convert score to appropriate category"""
        if score >= 8.6:
            return ClassificationCategory.OUTSTANDING
        elif score >= 7.6:
            return ClassificationCategory.EXCELLENT
        elif score >= 6.6:
            return ClassificationCategory.VERY_GOOD
        elif score >= 5.1:
            return ClassificationCategory.GOOD
        elif score >= 3.1:
            return ClassificationCategory.FAIR
        elif score >= 2.1:
            return ClassificationCategory.POOR
        else:
            return ClassificationCategory.VERY_POOR
    
    @staticmethod
    def _score_to_quality(score: float) -> QualityLevel:
        """Convert score to appropriate quality level"""
        if score >= 7.0:
            return QualityLevel.HIGH
        elif score >= 4.0:
            return QualityLevel.MEDIUM
        else:
            return QualityLevel.LOW
    
    def is_high_quality(self) -> bool:
        """
        Check if this is a high-quality classification.
        
        Returns:
            True if quality level is high
        """
        return self.quality_level == QualityLevel.HIGH
    
    def is_low_quality(self) -> bool:
        """
        Check if this is a low-quality classification.
        
        Returns:
            True if quality level is low
        """
        return self.quality_level == QualityLevel.LOW
    
    def has_warnings(self) -> bool:
        """
        Check if classification has any warnings.
        
        Returns:
            True if there are warnings
        """
        return len(self.warnings) > 0
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Check if this is a high-confidence classification.
        
        Args:
            threshold: Confidence threshold
            
        Returns:
            True if confidence exceeds threshold
        """
        return self.confidence >= threshold
    
    def get_score_breakdown(self) -> Dict[str, Any]:
        """
        Get a breakdown of the scoring.
        
        Returns:
            Dictionary with score breakdown information
        """
        return {
            "final_score": self.final_score,
            "category": self.category.value,
            "quality_level": self.quality_level.value,
            "sub_scores": self.sub_scores,
            "score_range": self._get_score_range(),
            "percentile": self._get_percentile()
        }
    
    def _get_score_range(self) -> str:
        """Get the score range for the current category"""
        score_ranges = {
            ClassificationCategory.OUTSTANDING: "8.6-10.0",
            ClassificationCategory.EXCELLENT: "7.6-8.5",
            ClassificationCategory.VERY_GOOD: "6.6-7.5",
            ClassificationCategory.GOOD: "5.1-6.5",
            ClassificationCategory.FAIR: "3.1-5.0",
            ClassificationCategory.POOR: "2.1-3.0",
            ClassificationCategory.VERY_POOR: "0.1-2.0"
        }
        return score_ranges.get(self.category, "Unknown")
    
    def _get_percentile(self) -> int:
        """Get approximate percentile for the score"""
        # Rough percentile mapping based on score
        if self.final_score >= 9.0:
            return 95
        elif self.final_score >= 8.0:
            return 85
        elif self.final_score >= 7.0:
            return 75
        elif self.final_score >= 6.0:
            return 60
        elif self.final_score >= 5.0:
            return 50
        elif self.final_score >= 4.0:
            return 30
        elif self.final_score >= 3.0:
            return 15
        else:
            return 5
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert classification to dictionary representation.
        
        Returns:
            Dictionary representation of the classification
        """
        return {
            "final_score": self.final_score,
            "category": self.category.value,
            "quality_level": self.quality_level.value,
            "summary": self.summary,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "sub_scores": self.sub_scores,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "score_breakdown": self.get_score_breakdown()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Classification':
        """
        Create Classification instance from dictionary.
        
        Args:
            data: Dictionary with classification data
            
        Returns:
            Classification instance
        """
        category = ClassificationCategory(data["category"])
        quality_level = QualityLevel(data["quality_level"])
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        
        return cls(
            final_score=float(data["final_score"]),
            category=category,
            quality_level=quality_level,
            summary=data["summary"],
            rationale=data["rationale"],
            confidence=float(data.get("confidence", 1.0)),
            sub_scores=data.get("sub_scores", {}),
            warnings=data.get("warnings", []),
            timestamp=timestamp,
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def create_from_score(cls, final_score: float, summary: str, rationale: str,
                         sub_scores: Dict[str, float] = None, confidence: float = 1.0,
                         **metadata) -> 'Classification':
        """
        Create classification automatically from score.
        
        Args:
            final_score: Final score value
            summary: Article summary
            rationale: Classification rationale
            sub_scores: Individual agent scores
            confidence: Confidence in classification
            **metadata: Additional metadata
            
        Returns:
            Classification instance with auto-derived category and quality
        """
        category = cls._score_to_category(final_score)
        quality_level = cls._score_to_quality(final_score)
        
        return cls(
            final_score=final_score,
            category=category,
            quality_level=quality_level,
            summary=summary,
            rationale=rationale,
            confidence=confidence,
            sub_scores=sub_scores or {},
            metadata=metadata
        )
    
    def __str__(self) -> str:
        """String representation of the classification"""
        return f"Classification({self.final_score:.1f}, {self.category.value}, {self.quality_level.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the classification"""
        return (f"Classification(final_score={self.final_score}, category='{self.category.value}', "
                f"quality_level='{self.quality_level.value}', confidence={self.confidence})") 