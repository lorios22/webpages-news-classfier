# AI-Powered News Classifier for Web Pages

## Overview

This is an advanced multi-agent AI system designed to automatically classify and analyze news content from web pages. The system extracts URLs from Slack channels, scrapes web content, processes it through multiple specialized AI agents, and posts the classified results back to Slack.

## Architecture

### 🏗️ System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Slack Channel  │───▶│  URL Extraction │───▶│  Web Scraping   │
│   (Input)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Slack Channel  │◀───│  Results Post   │◀───│  Multi-Agent    │
│   (Output)      │    │                 │    │  Classification │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🤖 Multi-Agent Classification Pipeline

The system employs a sophisticated multi-agent architecture where each agent specializes in different aspects of content analysis:

1. **Input Preprocessor**: Cleans and structures raw web content
2. **Context Evaluator**: Assesses overall content quality and determines if analysis should continue
3. **Fact Checker**: Verifies factual claims and assesses credibility
4. **Depth Analyzer**: Evaluates technical complexity and content depth
5. **Relevance Analyzer**: Determines content relevance to target audience
6. **Structure Analyzer**: Assesses content organization and presentation
7. **Historical Reflection**: Compares content against historical patterns
8. **Human Reasoning**: Applies human-like reasoning and judgment
9. **Reflective Validator**: Performs self-validation and quality checks
10. **Score Consolidator**: Combines all agent scores into final ratings
11. **Consensus Agent**: Reaches final classification consensus
12. **Validator**: Performs final validation and quality assurance

## File Structure

```
news_classifier_webpages/
├── news_classifier_webpages.py     # Main orchestration script
├── extract_slack_urls.py           # Slack URL extraction
├── webscrapping.py                 # Web content scraping (Playwright)
├── agents_process.py               # Agent processing coordinator
├── news_classifier_agents.py       # Multi-agent classification system
├── post_classified_news.py         # Slack results posting
├── processed_urls.py               # URL processing utilities
├── clean_folders_move_file.py      # File management utilities
├── assistant/                      # Agent configuration and prompts
│   ├── configuration.py           # System configuration
│   ├── state.py                   # Agent state management
│   ├── prompts.py                 # AI agent prompts
│   └── utils.py                   # Utility functions
├── results/                       # JSON results from web scraping
├── classified_news/               # Excel output files
├── historical_classified_news/    # Historical results archive
├── urls/                          # URL files
├── improvements/                  # System enhancement documentation
└── documentation/                 # System documentation
```

## Key Features

### 🔍 Web Content Extraction
- **Playwright-based scraping**: Handles dynamic content and JavaScript-heavy sites
- **Smart content extraction**: Focuses on main article content while filtering out ads and navigation
- **Error handling**: Robust error handling with retry mechanisms
- **Content cleaning**: Removes HTML tags, excess whitespace, and irrelevant elements

### 🧠 Multi-Agent AI Classification
- **Specialized agents**: Each agent focuses on specific aspects of content analysis
- **Configurable scoring**: Flexible scoring system with customizable thresholds
- **Quality filters**: Early termination for low-quality content to save resources
- **Comprehensive analysis**: Covers credibility, depth, relevance, structure, and more

### 📊 Advanced Scoring System
- **Context Score**: Overall content quality (0.1-10.0)
- **Credibility Score**: Factual accuracy and trustworthiness (1.0-10.0)
- **Depth Score**: Technical complexity and thoroughness (1.0-10.0)
- **Relevance Score**: Relevance to target audience (1.0-10.0)
- **Structure Score**: Content organization and presentation (1.0-10.0)
- **Consolidated Score**: Final weighted score combining all metrics

### 🔄 Slack Integration
- **Automated URL extraction**: Pulls URLs from designated Slack channels
- **Duplicate prevention**: Tracks processed URLs to avoid reprocessing
- **Rich result formatting**: Posts detailed analysis results with interactive elements
- **Error reporting**: Comprehensive error logging and reporting

## Installation

### Prerequisites
- Python 3.8+
- Playwright browser dependencies
- OpenAI API key
- Slack Bot Token

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news_classifier_webpages
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Environment configuration**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   SLACK_BOT_TOKEN=your_slack_bot_token
   SLACK_CHANNEL_ID_WEBSCRAPPER=your_source_channel_id
   SLACK_CHANNEL_ID_TO_POST_CLASSIFIED_NEWS_WEBPAGES=your_target_channel_id
   ```

4. **Slack Bot Setup**
   - Create a Slack app and bot
   - Add required permissions:
     - `channels:history`
     - `chat:write`
     - `files:write`
   - Install the bot to your workspace

## Usage

### Manual Execution

Run the main pipeline:
```bash
python news_classifier_webpages.py
```

### Pipeline Components

The main script coordinates the following steps:

1. **Extract URLs from Slack**
   ```python
   urls = extract_slack_urls(channel_id, urls_file, processed_urls_path, limit=1000)
   ```

2. **Scrape web content**
   ```python
   process_urls_and_extract_content(urls_file, output_dir)
   ```

3. **Run AI classification**
   ```python
   process_top_stories(graph)
   ```

4. **Post results to Slack**
   ```python
   post_stories_to_slack(channel_id_to_post)
   ```

5. **Clean up and archive**
   ```python
   move_file(excel_path, historical_excel_path)
   clean_processed_folders()
   ```

### Configuration

Modify `assistant/configuration.py` to adjust:
- AI model selection
- Processing parameters
- Scoring thresholds

## Output

### Excel Reports
The system generates comprehensive Excel reports with:
- Original content metadata
- Individual agent scores and reasoning
- Consolidated ratings
- Classification categories
- Processing timestamps

### Slack Posts
Results are posted to Slack with:
- Article summaries
- Score breakdowns
- Interactive elements for feedback
- Error notifications

## Monitoring and Maintenance

### Logging
- Comprehensive logging throughout the pipeline
- Error tracking and reporting
- Performance monitoring

### File Management
- Automatic archiving of historical results
- Cleanup of temporary files
- Duplicate URL prevention

### Quality Assurance
- Multi-level validation
- Content quality filters
- Error recovery mechanisms

## Customization

### Adding New Agents
1. Create agent function in `news_classifier_agents.py`
2. Add to the StateGraph workflow
3. Update state management in `assistant/state.py`
4. Add prompts in `assistant/prompts.py`

### Modifying Scoring
- Adjust scoring ranges in agent prompts
- Modify consolidation logic in `score_consolidator`
- Update classification thresholds in `get_classification`

### Custom Content Filters
- Modify preprocessing filters in `input_preprocessor`
- Add custom spam detection rules
- Adjust content length requirements

## Troubleshooting

### Common Issues

1. **Playwright setup**: Ensure browsers are installed with `playwright install`
2. **API rate limits**: Implement delays between requests
3. **Memory usage**: Process large batches in chunks
4. **Slack API errors**: Check token permissions and rate limits

### Performance Optimization

- Batch processing for large URL sets
- Caching of processed content
- Parallel processing where possible
- Resource monitoring and cleanup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:
- Check the documentation in the `documentation/` folder
- Review the troubleshooting section
- Submit issues through the repository's issue tracker

---

**Note**: This system is designed for educational and research purposes. Ensure compliance with website terms of service and rate limiting when scraping content. 