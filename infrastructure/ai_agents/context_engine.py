"""
Advanced Context Engineering System
Implements context budgeting, zones, and optimization for AI agents
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import tiktoken


class ContextZone(Enum):
    """Context zones for different types of content"""

    SYSTEM = "system"
    CORE_CONTENT = "core_content"
    MEMORY_CONTEXT = "memory_context"
    HISTORICAL_PATTERNS = "historical_patterns"
    RULES_AND_CONSTRAINTS = "rules_and_constraints"
    OUTPUT_FORMAT = "output_format"
    WORKING_MEMORY = "working_memory"


class Priority(Enum):
    """Priority levels for context elements"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ContextElement:
    """Individual context element with metadata"""

    content: str
    zone: ContextZone
    priority: Priority
    token_count: int
    importance_score: float = 0.5  # 0.0-1.0
    compressible: bool = True
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = self._count_tokens(self.content)

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except:
            # Fallback estimation
            return len(text.split()) * 1.3


@dataclass
class ContextBudget:
    """Context budget configuration"""

    total_tokens: int = 16000  # Default for GPT-4
    system_reserve: int = 1000
    output_reserve: int = 1000
    available_tokens: int = field(init=False)

    def __post_init__(self):
        self.available_tokens = (
            self.total_tokens - self.system_reserve - self.output_reserve
        )


class ContextEngine:
    """
    Advanced context engineering system with intelligent budget management

    Features:
    - Context zone management with priorities
    - Dynamic content compression and truncation
    - Memory-aware context assembly
    - Token budget optimization
    - Context bleed prevention
    - Multi-article page handling
    """

    def __init__(self, default_budget: ContextBudget = None):
        self.budget = default_budget or ContextBudget()
        self.context_elements: List[ContextElement] = []
        self.encoding = self._get_encoding()

        # Context zone configurations
        self.zone_configs = {
            ContextZone.SYSTEM: {"max_ratio": 0.15, "compressible": False},
            ContextZone.CORE_CONTENT: {"max_ratio": 0.50, "compressible": True},
            ContextZone.MEMORY_CONTEXT: {"max_ratio": 0.15, "compressible": True},
            ContextZone.HISTORICAL_PATTERNS: {"max_ratio": 0.10, "compressible": True},
            ContextZone.RULES_AND_CONSTRAINTS: {
                "max_ratio": 0.05,
                "compressible": False,
            },
            ContextZone.OUTPUT_FORMAT: {"max_ratio": 0.03, "compressible": False},
            ContextZone.WORKING_MEMORY: {"max_ratio": 0.02, "compressible": True},
        }

    def _get_encoding(self):
        """Get tiktoken encoding"""
        try:
            return tiktoken.encoding_for_model("gpt-4")
        except:
            return tiktoken.get_encoding("cl100k_base")

    def add_context_element(
        self,
        content: str,
        zone: ContextZone,
        priority: Priority = Priority.MEDIUM,
        importance_score: float = 0.5,
        compressible: bool = True,
        tags: List[str] = None,
    ) -> ContextElement:
        """Add a context element to the context"""
        element = ContextElement(
            content=content,
            zone=zone,
            priority=priority,
            token_count=len(self.encoding.encode(content)),
            importance_score=importance_score,
            compressible=compressible,
            tags=tags or [],
        )

        self.context_elements.append(element)
        return element

    def build_optimized_context(
        self,
        target_content: str,
        memory_context: List[str] = None,
        agent_id: str = None,
    ) -> Dict[str, Any]:
        """Build optimized context within budget constraints"""

        # Add core content
        self.add_context_element(
            target_content,
            ContextZone.CORE_CONTENT,
            Priority.CRITICAL,
            importance_score=1.0,
            compressible=True,
        )

        # Add memory context if provided
        if memory_context and agent_id:
            memory_content = self._build_memory_context(memory_context, agent_id)
            if memory_content:
                self.add_context_element(
                    memory_content,
                    ContextZone.MEMORY_CONTEXT,
                    Priority.HIGH,
                    importance_score=0.8,
                )

        # Calculate current token usage
        total_tokens = sum(element.token_count for element in self.context_elements)

        # Optimize if over budget
        if total_tokens > self.budget.available_tokens:
            self._optimize_context()

        return self._assemble_final_context()

    def _build_memory_context(self, memory_context: List[str], agent_id: str) -> str:
        """Build memory context from agent's persistent memory"""
        if not memory_context:
            return ""

        # Limit memory context to prevent overwhelming
        max_memory_items = 5
        sorted_memory = sorted(memory_context, key=len, reverse=True)[:max_memory_items]

        memory_section = "RELEVANT CONTEXT FROM PREVIOUS ANALYSIS:\n"
        for i, memory in enumerate(sorted_memory, 1):
            memory_section += f"{i}. {memory}\n"

        return memory_section

    def _optimize_context(self):
        """Optimize context to fit within budget"""
        # Step 1: Remove low-priority, low-importance elements
        self.context_elements = [
            elem
            for elem in self.context_elements
            if not (elem.priority == Priority.LOW and elem.importance_score < 0.3)
        ]

        # Step 2: Compress compressible elements
        for element in self.context_elements:
            if element.compressible and element.zone != ContextZone.CORE_CONTENT:
                element.content = self._compress_text(element.content, 0.7)
                element.token_count = len(self.encoding.encode(element.content))

        # Step 3: Apply zone-based budgets
        self._apply_zone_budgets()

        # Step 4: Final truncation if still over budget
        total_tokens = sum(element.token_count for element in self.context_elements)
        if total_tokens > self.budget.available_tokens:
            self._emergency_truncation()

    def _compress_text(self, text: str, compression_ratio: float) -> str:
        """Compress text by removing less important sentences"""
        sentences = text.split(". ")
        if len(sentences) <= 2:
            return text

        target_sentences = max(2, int(len(sentences) * compression_ratio))

        # Simple heuristic: keep sentences with numbers, proper nouns, and key terms
        scored_sentences = []
        for sentence in sentences:
            score = 0
            score += len(re.findall(r"\d+", sentence)) * 2  # Numbers
            score += len(re.findall(r"[A-Z][a-z]+", sentence))  # Proper nouns
            score += len(sentence.split())  # Length bonus
            scored_sentences.append((sentence, score))

        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        selected_sentences = [s[0] for s in scored_sentences[:target_sentences]]

        return ". ".join(selected_sentences) + ("." if not text.endswith(".") else "")

    def _apply_zone_budgets(self):
        """Apply budget constraints per context zone"""
        zone_elements = {}
        for element in self.context_elements:
            if element.zone not in zone_elements:
                zone_elements[element.zone] = []
            zone_elements[element.zone].append(element)

        # Apply zone-specific budgets
        for zone, elements in zone_elements.items():
            zone_config = self.zone_configs.get(zone, {"max_ratio": 0.1})
            max_tokens = int(self.budget.available_tokens * zone_config["max_ratio"])

            current_tokens = sum(elem.token_count for elem in elements)

            if current_tokens > max_tokens:
                # Sort by importance and priority
                elements.sort(key=lambda x: (x.priority.value, -x.importance_score))

                # Keep elements within budget
                running_total = 0
                kept_elements = []

                for element in elements:
                    if running_total + element.token_count <= max_tokens:
                        kept_elements.append(element)
                        running_total += element.token_count
                    elif zone_config.get("compressible", True):
                        # Try to compress and fit
                        needed_compression = (
                            1 - (max_tokens - running_total) / element.token_count
                        )
                        if needed_compression < 0.8:  # Don't over-compress
                            element.content = self._compress_text(
                                element.content, 1 - needed_compression
                            )
                            element.token_count = len(
                                self.encoding.encode(element.content)
                            )
                            kept_elements.append(element)
                            running_total += element.token_count
                        break

                # Update context_elements
                self.context_elements = [
                    elem for elem in self.context_elements if elem.zone != zone
                ]
                self.context_elements.extend(kept_elements)

    def _emergency_truncation(self):
        """Emergency truncation as last resort"""
        # Sort all elements by priority and importance
        self.context_elements.sort(
            key=lambda x: (x.priority.value, -x.importance_score)
        )

        running_total = 0
        kept_elements = []

        for element in self.context_elements:
            if running_total + element.token_count <= self.budget.available_tokens:
                kept_elements.append(element)
                running_total += element.token_count
            else:
                break

        self.context_elements = kept_elements

    def _assemble_final_context(self) -> Dict[str, Any]:
        """Assemble the final optimized context"""
        # Group by zone
        zone_content = {}
        for element in self.context_elements:
            if element.zone not in zone_content:
                zone_content[element.zone] = []
            zone_content[element.zone].append(element.content)

        # Build context in logical order
        context_parts = []

        # System context
        if ContextZone.SYSTEM in zone_content:
            context_parts.extend(zone_content[ContextZone.SYSTEM])

        # Rules and constraints
        if ContextZone.RULES_AND_CONSTRAINTS in zone_content:
            context_parts.extend(zone_content[ContextZone.RULES_AND_CONSTRAINTS])

        # Memory context
        if ContextZone.MEMORY_CONTEXT in zone_content:
            context_parts.extend(zone_content[ContextZone.MEMORY_CONTEXT])

        # Historical patterns
        if ContextZone.HISTORICAL_PATTERNS in zone_content:
            context_parts.extend(zone_content[ContextZone.HISTORICAL_PATTERNS])

        # Core content
        if ContextZone.CORE_CONTENT in zone_content:
            context_parts.extend(zone_content[ContextZone.CORE_CONTENT])

        # Working memory
        if ContextZone.WORKING_MEMORY in zone_content:
            context_parts.extend(zone_content[ContextZone.WORKING_MEMORY])

        # Output format
        if ContextZone.OUTPUT_FORMAT in zone_content:
            context_parts.extend(zone_content[ContextZone.OUTPUT_FORMAT])

        final_context = "\n\n".join(context_parts)
        final_token_count = len(self.encoding.encode(final_context))

        return {
            "context": final_context,
            "token_count": final_token_count,
            "budget_utilization": final_token_count / self.budget.available_tokens,
            "zones_used": list(zone_content.keys()),
            "optimization_applied": final_token_count
            < sum(elem.token_count for elem in self.context_elements),
        }

    def detect_context_bleed(self, content: str) -> Dict[str, Any]:
        """Detect potential context bleed in multi-article pages"""
        # Look for multiple article indicators
        article_indicators = [
            r"(?:published|posted|updated).*\d{4}",  # Dates
            r"by\s+[A-Z][a-z]+\s+[A-Z][a-z]+",  # Author names
            r"share\s+this\s+article",  # Social sharing
            r"related\s+articles?",  # Related content
            r"more\s+from\s+[A-Z]",  # More from author/category
        ]

        indicator_matches = []
        for pattern in article_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            indicator_matches.extend(matches)

        # Check for abrupt topic changes
        paragraphs = content.split("\n\n")
        topic_changes = 0

        for i in range(1, len(paragraphs)):
            if len(paragraphs[i]) > 50:  # Substantial paragraph
                # Simple heuristic: check for topic discontinuity
                prev_words = set(paragraphs[i - 1].lower().split())
                curr_words = set(paragraphs[i].lower().split())

                overlap = len(prev_words.intersection(curr_words))
                union = len(prev_words.union(curr_words))

                if union > 0 and overlap / union < 0.1:  # Low overlap
                    topic_changes += 1

        bleed_score = len(indicator_matches) * 0.3 + topic_changes * 0.2

        return {
            "bleed_detected": bleed_score > 1.0,
            "bleed_score": bleed_score,
            "indicators_found": len(indicator_matches),
            "topic_changes": topic_changes,
            "confidence": min(1.0, bleed_score / 3.0),
        }

    def clean_multi_article_content(self, content: str) -> str:
        """Clean content to remove context bleed from multi-article pages"""
        bleed_analysis = self.detect_context_bleed(content)

        if not bleed_analysis["bleed_detected"]:
            return content

        # Split content into sections
        sections = content.split("\n\n")

        # Keep only the main article (usually the first substantial section)
        main_content = []
        content_started = False

        for section in sections:
            if len(section.strip()) < 20:  # Skip short sections
                continue

            # Check if this looks like article navigation or sidebar
            if re.search(r"(menu|navigation|sidebar|footer|header)", section.lower()):
                continue

            # Check for social media or sharing buttons
            if re.search(r"(share|tweet|facebook|linkedin|subscribe)", section.lower()):
                continue

            # Start of main content detected
            if not content_started and len(section) > 100:
                content_started = True

            if content_started:
                main_content.append(section)

                # Stop if we hit another article
                if len(main_content) > 5 and re.search(
                    r"related\s+articles?|more\s+stories", section.lower()
                ):
                    break

        return "\n\n".join(main_content)

    def reset(self):
        """Reset context engine for new content"""
        self.context_elements = []


# Global context engine instance
context_engine = ContextEngine()


def get_context_engine() -> ContextEngine:
    """Get the global context engine instance"""
    return context_engine
