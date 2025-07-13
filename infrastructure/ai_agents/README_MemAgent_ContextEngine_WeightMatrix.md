# Advanced AI Agent Systems - Implementation Guide

This document describes the three new advanced systems implemented to complete the "Web-News Classifier: Last-Mile MVP Fix" requirements.

## 🧠 MemAgent - Persistent Memory System

### Overview
Letta-style persistent memory system that allows agents to maintain context and learn from previous interactions across sessions.

### Features
- **Long-term Memory Storage**: SQLite-based persistent storage
- **Memory Types**: fact, pattern, context, preference
- **Relevance Scoring**: 0.0-1.0 scoring for memory importance
- **Memory Decay**: Automatic cleanup of expired memories
- **Agent Isolation**: Each agent maintains separate memory space

### Usage Example
```python
from infrastructure.ai_agents.memory_agent import get_memory_agent

memory_agent = get_memory_agent()

# Store a memory
memory_id = memory_agent.store_memory(
    agent_id="fact_checker",
    content="Article showed false statistics about crypto adoption",
    memory_type="pattern",
    relevance_score=0.9,
    tags=["false_stats", "crypto"],
    expires_in_days=90
)

# Retrieve memories
memories = memory_agent.retrieve_memories(
    agent_id="fact_checker",
    memory_type="pattern",
    limit=5,
    min_relevance=0.5
)

# Search memories
relevant_memories = memory_agent.search_memories(
    agent_id="fact_checker",
    query="false statistics crypto",
    limit=3
)
```

### Memory Types
- **fact**: Verified factual information
- **pattern**: Recurring patterns in content or scoring
- **context**: Contextual information for better understanding
- **preference**: Agent-specific preferences and configurations

### Integration Points
- **Input Preprocessor**: Stores context bleed patterns
- **Consensus Agent**: Stores scoring divergence patterns
- **All Agents**: Can store and retrieve relevant memories

## 🎯 ContextEngine - Advanced Context Management

### Overview
Intelligent context budgeting and optimization system that manages token limits, prevents context bleed, and optimizes prompt construction.

### Features
- **Context Zones**: Organized context areas with priorities
- **Token Budget Management**: Intelligent token allocation
- **Content Compression**: Dynamic text compression when needed
- **Context Bleed Detection**: Multi-article page handling
- **Memory Integration**: Incorporates agent memories into context

### Context Zones
1. **SYSTEM** (15% budget, non-compressible): Core system instructions
2. **CORE_CONTENT** (50% budget, compressible): Main article content
3. **MEMORY_CONTEXT** (15% budget, compressible): Agent memories
4. **HISTORICAL_PATTERNS** (10% budget, compressible): Historical context
5. **RULES_AND_CONSTRAINTS** (5% budget, non-compressible): Rules
6. **OUTPUT_FORMAT** (3% budget, non-compressible): Output format
7. **WORKING_MEMORY** (2% budget, compressible): Temporary context

### Usage Example
```python
from infrastructure.ai_agents.context_engine import get_context_engine, ContextZone, Priority

context_engine = get_context_engine()

# Add context elements
context_engine.add_context_element(
    content="Article content here...",
    zone=ContextZone.CORE_CONTENT,
    priority=Priority.CRITICAL,
    importance_score=1.0
)

# Build optimized context
context_result = context_engine.build_optimized_context(
    target_content=article_content,
    memory_context=agent_memories,
    agent_id="fact_checker"
)

# Check for context bleed
bleed_analysis = context_engine.detect_context_bleed(webpage_content)
if bleed_analysis["bleed_detected"]:
    cleaned_content = context_engine.clean_multi_article_content(webpage_content)
```

### Context Bleed Detection
Automatically detects and handles:
- Multiple article indicators (dates, authors, sharing buttons)
- Abrupt topic changes
- Navigation and sidebar content
- Social media content

## ⚖️ WeightMatrix - Dynamic Scoring Optimization

### Overview
Advanced weight matrix system for dynamic agent scoring with content-type specific configurations and performance tracking.

### Features
- **Content-Type Specific Weights**: Different weights for different content types
- **Scenario-Based Optimization**: Fact-heavy, depth-focused, human-centric scenarios
- **Performance Tracking**: Logs human vs AI score differences
- **A/B Testing Support**: Multiple configurations with performance comparison
- **Learning System**: Optimizes weights based on historical performance

### Weight Configurations

#### Default Configuration
```
context_evaluator: 15%
fact_checker: 20%
depth_analyzer: 10%
relevance_analyzer: 10%
structure_analyzer: 10%
historical_reflection: 5%
human_reasoning: 20%
reflective_validator: 10%
```

#### Fact-Heavy Configuration
```
context_evaluator: 10%
fact_checker: 35%  ← Increased
depth_analyzer: 10%
relevance_analyzer: 10%
structure_analyzer: 5%
historical_reflection: 5%
human_reasoning: 15%
reflective_validator: 10%
```

#### Technical-Optimized Configuration
```
context_evaluator: 10%
fact_checker: 20%
depth_analyzer: 35%  ← Increased
relevance_analyzer: 10%
structure_analyzer: 15%  ← Increased
historical_reflection: 5%
human_reasoning: 3%   ← Decreased
reflective_validator: 2%
```

### Usage Example
```python
from infrastructure.ai_agents.weight_matrix import get_weight_matrix, ContentType, ScenarioType

weight_matrix = get_weight_matrix()

# Get optimal configuration
optimal_config = weight_matrix.get_optimal_configuration(
    content_type=ContentType.NEWS_ARTICLE,
    scenario=ScenarioType.FACT_HEAVY
)

# Use weights in scoring
weights = optimal_config.to_dict()
weighted_score = (
    context_score * weights["context_evaluator"] +
    fact_score * weights["fact_checker"] +
    # ... other scores
)

# Log performance for optimization
weight_matrix.log_performance(
    config_name=optimal_config.name,
    human_score=8.5,
    ai_score=8.2,
    content_type=ContentType.NEWS_ARTICLE,
    metadata={"content_length": 1500}
)
```

### Content Types
- `NEWS_ARTICLE`: Standard news content
- `BLOG_POST`: Blog and opinion content
- `RESEARCH_PAPER`: Academic and research content
- `SOCIAL_MEDIA`: Social media posts
- `PRESS_RELEASE`: Corporate announcements
- `TECHNICAL_DOC`: Technical documentation
- `OPINION_PIECE`: Editorial content

### Scenario Types
- `DEFAULT`: Balanced configuration
- `FACT_HEAVY`: Prioritizes fact-checking
- `DEPTH_FOCUSED`: Emphasizes technical depth
- `RELEVANCE_PRIORITIZED`: Focus on relevance
- `HUMAN_CENTRIC`: Prioritizes human reasoning
- `CONSENSUS_BALANCED`: Balanced consensus approach

## 🔄 Integration Overview

### System Integration Flow
1. **Input Preprocessor**: Uses ContextEngine for bleed detection and MemAgent for pattern storage
2. **Content Analysis**: All agents can access memories and use optimized context
3. **Consensus Agent**: Uses WeightMatrix for dynamic scoring and logs performance
4. **Learning Loop**: System continuously learns and optimizes based on performance

### Database Storage
- **MemAgent**: `infrastructure/ai_agents/agent_memory.db`
- **WeightMatrix**: `infrastructure/ai_agents/weight_matrix.db`
- **ContextEngine**: In-memory with SQLite backing for persistence

### Performance Monitoring
- Automatic logging of human vs AI score differences
- Weight configuration performance tracking
- Memory usage and relevance scoring
- Context optimization metrics

## 🚀 Getting Started

### 1. Initialization
The systems are automatically initialized when imported:
```python
# All systems are auto-imported in news_classifier_agents.py
from infrastructure.ai_agents.memory_agent import get_memory_agent
from infrastructure.ai_agents.context_engine import get_context_engine
from infrastructure.ai_agents.weight_matrix import get_weight_matrix
```

### 2. Configuration
Systems work out-of-the-box with sensible defaults, but can be customized:
```python
# Custom context budget
from infrastructure.ai_agents.context_engine import ContextBudget
custom_budget = ContextBudget(total_tokens=32000, system_reserve=2000)

# Custom weight configuration
from infrastructure.ai_agents.weight_matrix import WeightConfiguration
custom_weights = WeightConfiguration(
    fact_checker=0.30,  # Increased fact checking
    human_reasoning=0.25,  # Increased human reasoning
    # ... other weights (must sum to 1.0)
)
```

### 3. Monitoring
View system performance and analytics:
```python
# Memory statistics
memory_stats = memory_agent.get_agent_memory_stats("fact_checker")

# Weight matrix analytics
performance_analytics = weight_matrix.get_performance_analytics()

# Context usage metrics
context_result = context_engine.build_optimized_context(content)
print(f"Budget utilization: {context_result['budget_utilization']:.1%}")
```

## 📊 Benefits Achieved

### 1. Enhanced Spam Filter ✅
- **MemAgent**: Stores spam detection patterns across sessions
- **ContextEngine**: Prevents context bleed from affecting spam detection
- **Result**: Fewer false positives, better pattern recognition

### 2. Context Bleed Prevention ✅
- **ContextEngine**: Automatic multi-article page detection and cleaning
- **MemAgent**: Learns from bleed patterns to improve detection
- **Result**: Cleaner content analysis, reduced noise

### 3. Dynamic Weight Optimization ✅
- **WeightMatrix**: Content-type specific weight configurations
- **Performance Learning**: Continuous optimization based on human feedback
- **Result**: Better alignment between human and AI scores

### 4. Persistent Learning ✅
- **MemAgent**: Long-term memory across sessions
- **Pattern Recognition**: Learns from scoring divergences and content patterns
- **Result**: Improving accuracy over time

## 🔧 Troubleshooting

### Common Issues

1. **Memory Database Lock**
   - Solution: Ensure proper database connection cleanup
   - Check: SQLite database permissions

2. **Context Budget Overflow**
   - Solution: Adjust ContextBudget parameters
   - Check: Content length and complexity

3. **Weight Configuration Errors**
   - Solution: Ensure weights sum to 1.0
   - Check: WeightConfiguration validation

### Performance Optimization

1. **Memory Cleanup**: Regular cleanup of expired memories
2. **Context Compression**: Adjust compression ratios for performance
3. **Weight Learning**: Allow sufficient data for weight optimization

This implementation completes all requirements from the "Web-News Classifier: Last-Mile MVP Fix" memo, providing a robust, learning system with persistent memory, intelligent context management, and dynamic optimization capabilities. 