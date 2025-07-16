"""
Value Objects Package

This package contains all value objects used in the news classification domain.
Value objects are immutable objects that represent concepts without identity.
"""

from .classification import (Classification, ClassificationCategory,
                             QualityLevel)
from .score import Score
from .source import CredibilityLevel, Source, SourceType

__all__ = [
    "Score",
    "Classification",
    "ClassificationCategory",
    "QualityLevel",
    "Source",
    "SourceType",
    "CredibilityLevel",
]
