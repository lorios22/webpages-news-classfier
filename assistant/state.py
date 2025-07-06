import operator
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ClassifierState:
    content: str  # Original content
    content_types: Dict[str, str] = field(default_factory=dict)  # Content types
    
    fact_checker_state: Dict = field(default_factory=dict)  # Fact checker results
    depth_analyzer_state: Dict = field(default_factory=dict)  # Depth analysis results 
    relevance_analyzer_state: Dict = field(default_factory=dict)  # Relevance analysis results
    structure_analyzer_state: Dict = field(default_factory=dict)  # Structure analysis results
    historical_reflection_state: Dict = field(default_factory=dict)  # Historical reflection results
    summary_state: Dict = field(default_factory=dict)  # Summary agent results
    preprocessor_state: Dict = field(default_factory=dict)  # Input preprocessor results
    context_evaluator_state: Dict = field(default_factory=dict)  # Context evaluator results
    score_consolidator_state: Dict = field(default_factory=dict)  # Score consolidator results
    human_reasoning_state: Dict = field(default_factory=dict)  # Human reasoning results
    consensus_state: Dict = field(default_factory=dict)  # Consensus agent results
    reflective_validator_state: Dict = field(default_factory=dict)  # Reflective validator results
    validator_state: Dict = field(default_factory=dict)  # Final validator results

