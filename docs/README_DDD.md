# Web News Classifier - Domain-Driven Design Architecture

## 🏗️ Architecture Overview

This document describes the Domain-Driven Design (DDD) architecture implemented for the Web News Classifier system. The system has been completely restructured to follow DDD principles, ensuring better maintainability, testability, and scalability.

## 📁 Project Structure

```
webpages-news-classfier/
├── domain/                          # Core business logic
│   ├── entities/                    # Domain entities with identity
│   │   ├── __init__.py
│   │   └── article.py              # Core Article entity
│   ├── value_objects/               # Immutable value objects
│   │   ├── __init__.py
│   │   ├── classification.py       # Classification result
│   │   ├── score.py                # Agent score
│   │   └── source.py               # News source information
│   ├── repositories/                # Domain repository interfaces
│   │   └── article_repository.py   # Article persistence interface
│   └── services/                    # Domain services
│       └── classification_service.py # Business logic services
│
├── application/                     # Application logic layer
│   ├── use_cases/                   # Application use cases
│   │   ├── classify_article.py     # Main classification use case
│   │   └── bulk_classify.py        # Batch processing use case
│   ├── services/                    # Application services
│   │   ├── duplicate_detection_service.py
│   │   ├── content_processing_service.py
│   │   ├── ai_classification_service.py
│   │   └── scoring_service.py
│   └── dto/                         # Data transfer objects
│       └── classification_request.py
│
├── infrastructure/                  # External concerns
│   ├── web_scraping/               # Web scraping implementations
│   │   └── playwright_scraper.py
│   ├── ai_agents/                  # AI agent implementations
│   │   ├── openai_agents.py
│   │   └── agent_coordinator.py
│   ├── slack/                      # Slack integration
│   │   └── slack_client.py
│   ├── persistence/                # Data persistence
│   │   ├── json_repository.py
│   │   └── excel_exporter.py
│   └── external_services/          # External APIs
│       └── fin_service.py
│
├── presentation/                    # Presentation layer
│   ├── api/                        # REST API endpoints
│   │   └── classification_api.py
│   ├── cli/                        # Command-line interface
│   │   └── cli_runner.py
│   └── web/                        # Web interface (future)
│
├── shared/                         # Shared utilities
│   ├── utils/                      # Common utilities
│   ├── config/                     # Configuration management
│   └── exceptions/                 # Custom exceptions
│
├── tests/                          # Test suites
│   ├── unit/                       # Unit tests
│   │   ├── domain/                 # Domain layer tests
│   │   ├── application/            # Application layer tests
│   │   └── infrastructure/         # Infrastructure tests
│   ├── integration/                # Integration tests
│   └── e2e/                        # End-to-end tests
│
├── scripts/                        # Utility scripts
│   ├── run_full_pipeline.py       # Complete pipeline execution
│   ├── staging_smoke_tests.py     # Staging environment tests
│   └── deployment_monitor.py      # Production monitoring
│
└── .github/                        # CI/CD pipeline
    └── workflows/
        └── ci-cd.yml               # GitHub Actions workflow
```

## 🎯 Domain-Driven Design Principles

### 1. Domain Layer (Core Business Logic)

The domain layer contains the core business entities, value objects, and business rules:

#### **Entities**
- **Article**: Main aggregate root representing a news article with identity and lifecycle
- Contains business logic for content validation, status management, and classification

#### **Value Objects**
- **Score**: Immutable object representing AI agent scores with validation
- **Classification**: Final classification result with category and quality assessment  
- **Source**: News source information with credibility scoring

#### **Key Business Rules**
- Articles must have valid content (minimum 10 characters)
- Scores must be between 0.1 and 10.0 with confidence levels
- Classifications automatically determine categories based on scores
- Source credibility affects overall assessment

### 2. Application Layer (Use Cases & Services)

Orchestrates domain logic and coordinates between layers:

#### **Main Use Cases**
- **ClassifyArticleUseCase**: Complete classification pipeline
- **BulkClassifyUseCase**: Batch processing of multiple articles

#### **Application Services**
- **DuplicateDetectionService**: Prevents reprocessing of duplicate content
- **ContentProcessingService**: Handles content cleaning and validation
- **AIClassificationService**: Coordinates AI agent analysis
- **ScoringService**: Consolidates individual agent scores

### 3. Infrastructure Layer (Technical Concerns)

Implements technical details and external integrations:

#### **Web Scraping**
- Playwright-based scraping with error handling
- Content cleaning and extraction

#### **AI Agents**
- OpenAI GPT integration for classification
- Multi-agent pipeline with specialized roles

#### **External Services**
- FIN (Financial Intelligence Network) integration
- Slack API for notifications and data input

#### **Persistence**
- JSON-based storage for results
- Excel export for analysis
- Duplicate detection memory

### 4. Presentation Layer (Interfaces)

Provides different interfaces to the system:

#### **API**: RESTful endpoints for external integration
#### **CLI**: Command-line interface for operations
#### **Web**: Future web interface (placeholder)

## 🔄 CI/CD Pipeline

### Automated Pipeline Stages

1. **Code Quality & Security**
   - Black code formatting
   - isort import organization  
   - flake8 linting
   - Bandit security scanning
   - MyPy type checking

2. **Testing** (Multi-Python versions: 3.9, 3.10, 3.11)
   - MVP fixes validation
   - Unit tests with coverage
   - Integration tests
   - End-to-end tests

3. **Performance Testing**
   - Load testing with Locust
   - Memory profiling
   - Performance regression detection

4. **Deployment**
   - **Staging**: Automatic deployment on `develop` branch
   - **Production**: Blue-green deployment on `main` branch
   - Health checks and monitoring
   - Automatic rollback on failure

5. **Security Scanning** (Daily)
   - Trivy vulnerability scanning
   - Dependency security checks
   - SARIF report generation

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.9+ required
python --version

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID_WEBSCRAPPER=source_channel_id
SLACK_CHANNEL_ID_TO_POST_CLASSIFIED_NEWS_WEBPAGES=target_channel_id

# Optional
MAX_URLS_TO_PROCESS=1000
RUN_TESTS_FIRST=true
CLEANUP_AFTER_EXECUTION=true
```

### Running the System

#### 1. Run Tests First
```bash
# Run MVP validation tests
python test_mvp_fixes.py

# Run full test suite
pytest tests/ -v --cov=domain --cov=application --cov=infrastructure
```

#### 2. Execute Full Pipeline
```bash
# Run complete pipeline (if tests pass)
python scripts/run_full_pipeline.py
```

#### 3. Manual Steps
```bash
# 1. Extract URLs from Slack
python extract_slack_urls.py

# 2. Scrape content
python webscrapping.py

# 3. Classify articles
python agents_process.py

# 4. Post results
python post_classified_news.py
```

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Domain entity behavior
   - Value object validation
   - Business logic verification
   - Service functionality

2. **Integration Tests** (`tests/integration/`)
   - Component interaction
   - Database operations
   - External API integration
   - Pipeline coordination

3. **End-to-End Tests** (`tests/e2e/`)
   - Complete workflow validation
   - Real environment testing
   - User scenario simulation

### Test Execution

```bash
# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest tests/e2e/ -v                     # E2E tests only

# Run with coverage
pytest --cov=domain --cov=application --cov-report=html

# Run performance tests
pytest tests/performance/ -v
```

## 📊 Monitoring & Observability

### Key Metrics

- **Processing Rate**: Articles processed per hour
- **Classification Accuracy**: Score alignment with editorial review
- **Error Rate**: Failed classifications vs. total attempts
- **Duplicate Detection**: False positive/negative rates
- **Performance**: Response times and resource usage

### Logging

The system uses structured logging with different levels:

```python
# Example usage
import logging
logger = logging.getLogger(__name__)

logger.info("Article classification started", extra={
    "article_id": article.id,
    "url": article.url,
    "stage": "preprocessing"
})
```

### Health Checks

Production health checks monitor:
- API endpoint availability
- Database connectivity
- External service status
- Classification pipeline health

## 🔒 Security Considerations

### Implemented Security Measures

1. **Input Validation**
   - All user inputs validated at domain level
   - URL and content sanitization
   - Parameter validation

2. **Dependency Management**
   - Regular security scanning with Bandit and Safety
   - Automated dependency updates
   - Vulnerability monitoring

3. **API Security**
   - Environment variable protection
   - Secure token handling
   - Rate limiting (future)

4. **Data Protection**
   - Sensitive data handling protocols
   - Secure configuration management
   - Audit logging

## 🔧 Deployment & Operations

### Staging Environment

- **Branch**: `develop`
- **URL**: `https://staging.news-classifier.example.com`
- **Purpose**: Pre-production testing and validation

### Production Environment

- **Branch**: `main` 
- **URL**: `https://news-classifier.example.com`
- **Strategy**: Blue-green deployment with 5-minute monitoring
- **Rollback**: Automatic on health check failure

### Deployment Commands

```bash
# Deploy to staging (automatic on develop push)
git push origin develop

# Deploy to production (automatic on main push)
git push origin main

# Manual rollback
python scripts/rollback.py --environment=production
```

## 📈 Performance Optimization

### Current Optimizations

1. **Concurrency**: Async processing for I/O operations
2. **Caching**: Duplicate detection memory and FIN data caching
3. **Content Truncation**: Prevents token limit issues
4. **Batch Processing**: Efficient handling of multiple articles

### Performance Targets

- **Classification Time**: < 30 seconds per article
- **Throughput**: 100+ articles per hour
- **Memory Usage**: < 512MB steady state
- **Error Rate**: < 5% classification failures

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Verify environment variables
   echo $OPENAI_API_KEY
   echo $SLACK_BOT_TOKEN
   ```

2. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=/path/to/project
   ```

3. **Test Failures**
   ```bash
   # Run with verbose output
   python test_mvp_fixes.py -v
   ```

4. **Pipeline Execution Issues**
   ```bash
   # Check logs
   tail -f pipeline.log
   
   # Check stats
   cat pipeline_stats_*.json
   ```

### Debug Mode

Enable debug logging:

```bash
export DEBUG=true
python scripts/run_full_pipeline.py
```

## 🤝 Contributing

### Development Workflow

1. **Branch**: Create feature branch from `develop`
2. **Develop**: Follow DDD principles and add tests
3. **Test**: Ensure all tests pass locally
4. **PR**: Create pull request to `develop`
5. **Review**: Code review and CI/CD validation
6. **Merge**: Automatic deployment to staging

### Code Standards

- **Formatting**: Black with 127 character line length
- **Imports**: isort for consistent import organization
- **Type Hints**: MyPy for static type checking
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Minimum 80% code coverage

## 📚 Additional Documentation

- [API Documentation](docs/api/)
- [Architecture Decisions](docs/architecture/)
- [Deployment Guide](docs/deployment/)
- [Agent Prompts Documentation](documentation/Agent_Prompts_Documentation.md)
- [MVP Implementation Summary](Day_1_MVP_Summary.md)

## 📞 Support

For questions, issues, or contributions:

1. **Issues**: Create GitHub issue with detailed description
2. **Discussions**: Use GitHub Discussions for questions
3. **Emergency**: Contact system administrators directly

---

*This documentation reflects the DDD architecture implementation completed in Day 1 MVP fixes with comprehensive CI/CD integration.* 