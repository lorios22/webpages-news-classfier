"""
Value Objects Package

This package contains all value objects used in the news classification domain.
Value objects are immutable objects that represent concepts without identity.
"""

from .score import Score
from .classification import Classification, ClassificationCategory, QualityLevel
from .source import Source, SourceType, CredibilityLevel

__all__ = [
    'Score',
    'Classification',
    'ClassificationCategory', 
    'QualityLevel',
    'Source',
    'SourceType',
    'CredibilityLevel'
] 