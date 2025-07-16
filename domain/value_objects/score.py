"""
Score Value Object

This module defines the Score value object used to represent
scoring information from AI agents in the classification system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Score:
    """
    Value object representing a score with metadata.

    This immutable object encapsulates scoring information from AI agents,
    including the score value, confidence level, and reasoning.

    Attributes:
        value: Numeric score value (typically 0.1-10.0)
        confidence: Confidence level in the score (0.0-1.0)
        reasoning: Textual explanation for the score
        agent_name: Name of the agent that provided the score
        timestamp: When the score was generated
        metadata: Additional scoring metadata
    """

    value: float
    confidence: float = 1.0
    reasoning: Optional[str] = None
    agent_name: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Validate score values after initialization"""
        # Use object.__setattr__ because dataclass is frozen
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now())

        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        self._validate_score()
        self._validate_confidence()

    def _validate_score(self) -> None:
        """
        Validate score value is within acceptable range.

        Raises:
            ValueError: If score is outside valid range
        """
        if not isinstance(self.value, (int, float)):
            raise ValueError("Score value must be numeric")

        if self.value < 0.1 or self.value > 10.0:
            raise ValueError("Score value must be between 0.1 and 10.0")

    def _validate_confidence(self) -> None:
        """
        Validate confidence level is within acceptable range.

        Raises:
            ValueError: If confidence is outside valid range
        """
        if not isinstance(self.confidence, (int, float)):
            raise ValueError("Confidence must be numeric")

        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Check if this is a high-confidence score.

        Args:
            threshold: Confidence threshold for high confidence

        Returns:
            True if confidence exceeds threshold
        """
        return self.confidence >= threshold

    def is_low_score(self, threshold: float = 3.0) -> bool:
        """
        Check if this is a low score.

        Args:
            threshold: Score threshold for low scores

        Returns:
            True if score is below threshold
        """
        return self.value < threshold

    def is_high_score(self, threshold: float = 8.0) -> bool:
        """
        Check if this is a high score.

        Args:
            threshold: Score threshold for high scores

        Returns:
            True if score exceeds threshold
        """
        return self.value >= threshold

    def get_score_category(self) -> str:
        """
        Get human-readable category for the score.

        Returns:
            String category (Outstanding, Excellent, etc.)
        """
        if self.value >= 9.0:
            return "Outstanding"
        elif self.value >= 8.0:
            return "Excellent"
        elif self.value >= 7.0:
            return "Very Good"
        elif self.value >= 6.0:
            return "Good"
        elif self.value >= 4.0:
            return "Fair"
        elif self.value >= 2.0:
            return "Poor"
        else:
            return "Very Poor"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert score to dictionary representation.

        Returns:
            Dictionary representation of the score
        """
        return {
            "value": self.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "category": self.get_score_category(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Score":
        """
        Create Score instance from dictionary.

        Args:
            data: Dictionary with score data

        Returns:
            Score instance
        """
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()

        return cls(
            value=float(data["value"]),
            confidence=float(data.get("confidence", 1.0)),
            reasoning=data.get("reasoning"),
            agent_name=data.get("agent_name"),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def create_with_agent(
        cls,
        value: float,
        agent_name: str,
        reasoning: str = None,
        confidence: float = 1.0,
        **metadata,
    ) -> "Score":
        """
        Convenience method to create a score with agent information.

        Args:
            value: Score value
            agent_name: Name of the scoring agent
            reasoning: Optional reasoning for the score
            confidence: Confidence in the score
            **metadata: Additional metadata

        Returns:
            Score instance
        """
        return cls(
            value=value,
            confidence=confidence,
            reasoning=reasoning,
            agent_name=agent_name,
            metadata=metadata,
        )

    def __str__(self) -> str:
        """String representation of the score"""
        return f"Score({self.value:.1f}, {self.get_score_category()}, confidence={self.confidence:.2f})"

    def __repr__(self) -> str:
        """Detailed string representation of the score"""
        return (
            f"Score(value={self.value}, confidence={self.confidence}, "
            f"agent_name='{self.agent_name}', category='{self.get_score_category()}')"
        )
