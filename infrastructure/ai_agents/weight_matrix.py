"""
Weight Matrix System for AI Agent Scoring
Dynamic weight configuration and optimization for multi-agent classification
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ContentType(Enum):
    """Content types with different scoring profiles"""

    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    RESEARCH_PAPER = "research_paper"
    SOCIAL_MEDIA = "social_media"
    PRESS_RELEASE = "press_release"
    TECHNICAL_DOC = "technical_doc"
    OPINION_PIECE = "opinion_piece"


class ScenarioType(Enum):
    """Scoring scenarios with different weight preferences"""

    DEFAULT = "default"
    FACT_HEAVY = "fact_heavy"
    DEPTH_FOCUSED = "depth_focused"
    RELEVANCE_PRIORITIZED = "relevance_prioritized"
    HUMAN_CENTRIC = "human_centric"
    CONSENSUS_BALANCED = "consensus_balanced"


@dataclass
class WeightConfiguration:
    """Weight configuration for different agents"""

    context_evaluator: float = 0.15
    fact_checker: float = 0.20
    depth_analyzer: float = 0.10
    relevance_analyzer: float = 0.10
    structure_analyzer: float = 0.10
    historical_reflection: float = 0.05
    human_reasoning: float = 0.20
    reflective_validator: float = 0.10

    # Metadata
    name: str = "default"
    description: str = "Default weight configuration"
    content_type: Optional[ContentType] = None
    scenario_type: ScenarioType = ScenarioType.DEFAULT
    created_at: datetime = field(default_factory=datetime.now)
    performance_score: float = 0.0  # Track performance for optimization

    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = (
            self.context_evaluator
            + self.fact_checker
            + self.depth_analyzer
            + self.relevance_analyzer
            + self.structure_analyzer
            + self.historical_reflection
            + self.human_reasoning
            + self.reflective_validator
        )

        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format"""
        return {
            "context_evaluator": self.context_evaluator,
            "fact_checker": self.fact_checker,
            "depth_analyzer": self.depth_analyzer,
            "relevance_analyzer": self.relevance_analyzer,
            "structure_analyzer": self.structure_analyzer,
            "historical_reflection": self.historical_reflection,
            "human_reasoning": self.human_reasoning,
            "reflective_validator": self.reflective_validator,
        }


class WeightMatrix:
    """
    Advanced weight matrix system for dynamic agent scoring

    Features:
    - Content-type specific weight configurations
    - Scenario-based weight optimization
    - Performance tracking and learning
    - A/B testing for weight configurations
    - Historical weight performance analysis
    """

    def __init__(self, db_path: str = "infrastructure/ai_agents/weight_matrix.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._load_default_configurations()

        self.current_config: WeightConfiguration = self.get_configuration("default")
        self.performance_history: List[Dict] = []

    def _init_database(self):
        """Initialize SQLite database for weight configurations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weight_configs (
                    name TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    content_type TEXT,
                    scenario_type TEXT,
                    performance_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    last_used TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT,
                    content_type TEXT,
                    human_score REAL,
                    ai_score REAL,
                    score_difference REAL,
                    timestamp TEXT,
                    metadata TEXT
                )
            """
            )

    def _load_default_configurations(self):
        """Load default weight configurations for different scenarios"""
        default_configs = {
            "default": WeightConfiguration(
                name="default",
                description="Balanced configuration for general content",
                scenario_type=ScenarioType.DEFAULT,
            ),
            "fact_heavy": WeightConfiguration(
                context_evaluator=0.10,
                fact_checker=0.35,
                depth_analyzer=0.10,
                relevance_analyzer=0.10,
                structure_analyzer=0.05,
                historical_reflection=0.05,
                human_reasoning=0.15,
                reflective_validator=0.10,
                name="fact_heavy",
                description="Prioritizes fact-checking and credibility",
                scenario_type=ScenarioType.FACT_HEAVY,
            ),
            "depth_focused": WeightConfiguration(
                context_evaluator=0.10,
                fact_checker=0.15,
                depth_analyzer=0.30,
                relevance_analyzer=0.15,
                structure_analyzer=0.10,
                historical_reflection=0.05,
                human_reasoning=0.10,
                reflective_validator=0.05,
                name="depth_focused",
                description="Emphasizes technical depth and analysis",
                scenario_type=ScenarioType.DEPTH_FOCUSED,
            ),
            "human_centric": WeightConfiguration(
                context_evaluator=0.10,
                fact_checker=0.15,
                depth_analyzer=0.05,
                relevance_analyzer=0.15,
                structure_analyzer=0.10,
                historical_reflection=0.05,
                human_reasoning=0.35,
                reflective_validator=0.05,
                name="human_centric",
                description="Prioritizes human-like reasoning and readability",
                scenario_type=ScenarioType.HUMAN_CENTRIC,
            ),
            "news_optimized": WeightConfiguration(
                context_evaluator=0.20,
                fact_checker=0.25,
                depth_analyzer=0.05,
                relevance_analyzer=0.20,
                structure_analyzer=0.10,
                historical_reflection=0.05,
                human_reasoning=0.10,
                reflective_validator=0.05,
                name="news_optimized",
                description="Optimized for news articles",
                content_type=ContentType.NEWS_ARTICLE,
                scenario_type=ScenarioType.DEFAULT,
            ),
            "technical_optimized": WeightConfiguration(
                context_evaluator=0.10,
                fact_checker=0.20,
                depth_analyzer=0.35,
                relevance_analyzer=0.10,
                structure_analyzer=0.15,
                historical_reflection=0.05,
                human_reasoning=0.03,
                reflective_validator=0.02,
                name="technical_optimized",
                description="Optimized for technical documentation",
                content_type=ContentType.TECHNICAL_DOC,
                scenario_type=ScenarioType.DEPTH_FOCUSED,
            ),
        }

        for config_name, config in default_configs.items():
            self.save_configuration(config)

    def save_configuration(self, config: WeightConfiguration):
        """Save a weight configuration to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO weight_configs 
                (name, config_json, content_type, scenario_type, 
                 performance_score, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    config.name,
                    json.dumps(asdict(config), default=str),
                    config.content_type.value if config.content_type else None,
                    config.scenario_type.value,
                    config.performance_score,
                    config.created_at.isoformat(),
                    datetime.now().isoformat(),
                ),
            )

    def get_configuration(self, name: str) -> Optional[WeightConfiguration]:
        """Retrieve a weight configuration by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT config_json FROM weight_configs WHERE name = ?
            """,
                (name,),
            )
            row = cursor.fetchone()

        if row:
            config_data = json.loads(row[0])
            # Handle datetime deserialization
            if "created_at" in config_data and isinstance(config_data["created_at"], str):
                config_data["created_at"] = datetime.fromisoformat(config_data["created_at"])

            # Handle enum deserialization
            if config_data.get("content_type"):
                try:
                    config_data["content_type"] = ContentType(config_data["content_type"])
                except ValueError:
                    config_data["content_type"] = None
            if config_data.get("scenario_type"):
                try:
                    config_data["scenario_type"] = ScenarioType(config_data["scenario_type"])
                except ValueError:
                    config_data["scenario_type"] = ScenarioType.DEFAULT

            return WeightConfiguration(**config_data)
        return None

    def get_optimal_configuration(
        self,
        content_type: Optional[ContentType] = None,
        scenario: Optional[ScenarioType] = None,
    ) -> WeightConfiguration:
        """Get the optimal configuration based on content type and scenario"""

        # First, try to find exact match
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT name, performance_score FROM weight_configs WHERE 1=1"
            params = []

            if content_type:
                query += " AND content_type = ?"
                params.append(content_type.value)

            if scenario:
                query += " AND scenario_type = ?"
                params.append(scenario.value)

            query += " ORDER BY performance_score DESC, usage_count DESC LIMIT 1"

            cursor = conn.execute(query, params)
            row = cursor.fetchone()

        if row:
            config = self.get_configuration(row[0])
            if config:
                return config

        # Fallback to scenario-based selection
        if scenario:
            scenario_configs = {
                ScenarioType.FACT_HEAVY: "fact_heavy",
                ScenarioType.DEPTH_FOCUSED: "depth_focused",
                ScenarioType.HUMAN_CENTRIC: "human_centric",
            }
            config_name = scenario_configs.get(scenario, "default")
            config = self.get_configuration(config_name)
            if config:
                return config

        # Fallback to content type specific
        if content_type:
            type_configs = {
                ContentType.NEWS_ARTICLE: "news_optimized",
                ContentType.TECHNICAL_DOC: "technical_optimized",
            }
            config_name = type_configs.get(content_type, "default")
            config = self.get_configuration(config_name)
            if config:
                return config

        # Final fallback to default
        return self.get_configuration("default")

    def log_performance(
        self,
        config_name: str,
        human_score: float,
        ai_score: float,
        content_type: Optional[ContentType] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Log performance data for a configuration"""
        score_difference = abs(human_score - ai_score)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_logs 
                (config_name, content_type, human_score, ai_score, 
                 score_difference, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    config_name,
                    content_type.value if content_type else None,
                    human_score,
                    ai_score,
                    score_difference,
                    datetime.now().isoformat(),
                    json.dumps(metadata or {}),
                ),
            )

            # Update configuration performance score
            conn.execute(
                """
                UPDATE weight_configs 
                SET performance_score = (
                    SELECT AVG(10.0 - score_difference) 
                    FROM performance_logs 
                    WHERE config_name = ?
                ),
                usage_count = usage_count + 1,
                last_used = ?
                WHERE name = ?
            """,
                (config_name, datetime.now().isoformat(), config_name),
            )

    def optimize_weights(
        self,
        target_content_type: Optional[ContentType] = None,
        learning_rate: float = 0.1,
    ) -> WeightConfiguration:
        """Optimize weights based on performance history"""

        # Get performance data
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT config_name, human_score, ai_score, score_difference
                FROM performance_logs 
                WHERE 1=1
            """
            params = []

            if target_content_type:
                query += " AND content_type = ?"
                params.append(target_content_type.value)

            query += " ORDER BY timestamp DESC LIMIT 100"

            cursor = conn.execute(query, params)
            performance_data = cursor.fetchall()

        if len(performance_data) < 10:  # Need minimum data for optimization
            return self.get_optimal_configuration(target_content_type)

        # Analyze patterns in score differences
        best_config = None
        best_performance = float("inf")

        config_performances = {}
        for row in performance_data:
            config_name = row[0]
            score_diff = row[3]

            if config_name not in config_performances:
                config_performances[config_name] = []
            config_performances[config_name].append(score_diff)

        # Find best performing configuration
        for config_name, diffs in config_performances.items():
            avg_diff = np.mean(diffs)
            if avg_diff < best_performance:
                best_performance = avg_diff
                best_config = config_name

        if best_config:
            base_config = self.get_configuration(best_config)
            if base_config:
                # Create optimized version
                optimized_config = WeightConfiguration(
                    context_evaluator=base_config.context_evaluator,
                    fact_checker=base_config.fact_checker,
                    depth_analyzer=base_config.depth_analyzer,
                    relevance_analyzer=base_config.relevance_analyzer,
                    structure_analyzer=base_config.structure_analyzer,
                    historical_reflection=base_config.historical_reflection,
                    human_reasoning=base_config.human_reasoning,
                    reflective_validator=base_config.reflective_validator,
                    name=f"optimized_{target_content_type.value if target_content_type else 'general'}",
                    description=f"Optimized configuration based on performance data",
                    content_type=target_content_type,
                    performance_score=10.0 - best_performance,
                )

                self.save_configuration(optimized_config)
                return optimized_config

        return self.get_optimal_configuration(target_content_type)

    def get_weight_recommendations(self, content_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Get weight recommendations based on content analysis"""

        # Base weights
        weights = self.current_config.to_dict()

        # Adjust based on content characteristics
        if content_analysis.get("technical_complexity", "low") == "high":
            # Increase depth analyzer weight for technical content
            weights["depth_analyzer"] = min(0.25, weights["depth_analyzer"] * 1.5)
            weights["fact_checker"] = min(0.30, weights["fact_checker"] * 1.2)
            weights["human_reasoning"] = max(0.05, weights["human_reasoning"] * 0.7)

        if content_analysis.get("credibility_concerns", False):
            # Increase fact checker weight for suspicious content
            weights["fact_checker"] = min(0.40, weights["fact_checker"] * 1.8)
            weights["context_evaluator"] = min(0.25, weights["context_evaluator"] * 1.4)

        if content_analysis.get("content_length", 0) < 500:
            # Adjust for short content
            weights["structure_analyzer"] = max(0.05, weights["structure_analyzer"] * 0.6)
            weights["human_reasoning"] = min(0.30, weights["human_reasoning"] * 1.3)

        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        return weights

    def set_current_configuration(self, config_name: str):
        """Set the current active configuration"""
        config = self.get_configuration(config_name)
        if config:
            self.current_config = config
        else:
            raise ValueError(f"Configuration '{config_name}' not found")

    def list_configurations(self) -> List[Dict[str, Any]]:
        """List all available configurations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT name, content_type, scenario_type, performance_score, usage_count
                FROM weight_configs
                ORDER BY performance_score DESC
            """
            )

            configs = []
            for row in cursor.fetchall():
                configs.append(
                    {
                        "name": row[0],
                        "content_type": row[1],
                        "scenario_type": row[2],
                        "performance_score": row[3],
                        "usage_count": row[4],
                    }
                )

            return configs

    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get analytics on weight configuration performance"""
        with sqlite3.connect(self.db_path) as conn:
            # Overall statistics
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_evaluations,
                    AVG(score_difference) as avg_difference,
                    MIN(score_difference) as min_difference,
                    MAX(score_difference) as max_difference
                FROM performance_logs
            """
            )
            overall_stats = cursor.fetchone()

            # Per-configuration statistics
            cursor = conn.execute(
                """
                SELECT 
                    config_name,
                    COUNT(*) as usage_count,
                    AVG(score_difference) as avg_difference,
                    AVG(human_score) as avg_human_score,
                    AVG(ai_score) as avg_ai_score
                FROM performance_logs
                GROUP BY config_name
                ORDER BY avg_difference ASC
            """
            )
            config_stats = cursor.fetchall()

        return {
            "overall": {
                "total_evaluations": overall_stats[0],
                "average_difference": overall_stats[1],
                "min_difference": overall_stats[2],
                "max_difference": overall_stats[3],
            },
            "configurations": [
                {
                    "name": row[0],
                    "usage_count": row[1],
                    "avg_difference": row[2],
                    "avg_human_score": row[3],
                    "avg_ai_score": row[4],
                }
                for row in config_stats
            ],
        }


# Global weight matrix instance
weight_matrix = WeightMatrix()


def get_weight_matrix() -> WeightMatrix:
    """Get the global weight matrix instance"""
    return weight_matrix
