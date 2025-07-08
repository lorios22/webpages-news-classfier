"""
Unit tests for Article entity.

This module tests the Article entity's business logic, validation,
and behavior according to domain-driven design principles.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from domain.entities import Article, ArticleStatus, ContentType
from domain.value_objects import Score, Classification, Source


class TestArticleEntity:
    """Test suite for Article entity"""
    
    def test_article_creation_valid(self):
        """Test successful article creation with valid data"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="This is a test article with sufficient content to pass validation."
        )
        
        assert article.id == "test-123"
        assert article.url == "https://example.com/article"
        assert article.title == "Test Article"
        assert article.status == ArticleStatus.PENDING
        assert isinstance(article.created_at, datetime)
        assert article.processed_at is None
    
    def test_article_creation_invalid_id(self):
        """Test article creation fails with invalid ID"""
        with pytest.raises(ValueError, match="Article ID is required"):
            Article(
                id="",
                url="https://example.com/article",
                title="Test Article",
                content="Valid content here."
            )
    
    def test_article_creation_invalid_url(self):
        """Test article creation fails with invalid URL"""
        with pytest.raises(ValueError, match="Article URL is required"):
            Article(
                id="test-123",
                url="",
                title="Test Article",
                content="Valid content here."
            )
    
    def test_article_creation_invalid_title(self):
        """Test article creation fails with invalid title"""
        with pytest.raises(ValueError, match="Article title is required"):
            Article(
                id="test-123",
                url="https://example.com/article",
                title="",
                content="Valid content here."
            )
    
    def test_article_creation_invalid_content(self):
        """Test article creation fails with invalid content"""
        with pytest.raises(ValueError, match="Article content must be at least 10 characters"):
            Article(
                id="test-123",
                url="https://example.com/article",
                title="Test Article",
                content="Short"
            )
    
    def test_content_type_detection_news(self):
        """Test automatic content type detection for news articles"""
        article = Article(
            id="test-123",
            url="https://reuters.com/article",
            title="Breaking News",
            content="This is breaking news that was announced today by the company."
        )
        
        assert article.content_type == ContentType.NEWS_ARTICLE
    
    def test_content_type_detection_press_release(self):
        """Test automatic content type detection for press releases"""
        article = Article(
            id="test-123",
            url="https://businesswire.com/article",
            title="Company Announcement",
            content="LONDON, January 8, 2025 -- Business Wire -- This is a press release announcement."
        )
        
        assert article.content_type == ContentType.PRESS_RELEASE
    
    def test_content_type_detection_blog(self):
        """Test automatic content type detection for blog posts"""
        article = Article(
            id="test-123",
            url="https://example.com/blog/post",
            title="My Thoughts",
            content="In this blog post, I want to share my thoughts on the author's perspective."
        )
        
        assert article.content_type == ContentType.BLOG_POST
    
    def test_add_score_valid(self):
        """Test adding a valid score to article"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        score = Score.create_with_agent(
            value=7.5,
            agent_name="fact_checker",
            reasoning="High credibility content"
        )
        
        article.add_score("fact_checker", score)
        
        assert "fact_checker" in article.scores
        assert article.scores["fact_checker"].value == 7.5
        assert article.scores["fact_checker"].agent_name == "fact_checker"
    
    def test_add_score_invalid(self):
        """Test adding an invalid score fails"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        with pytest.raises(ValueError, match="Score must be a Score instance"):
            article.add_score("test_agent", "invalid_score")
    
    def test_add_agent_response(self):
        """Test adding agent response"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        response = {"analysis": "Good content", "confidence": 0.8}
        article.add_agent_response("context_evaluator", response)
        
        assert "context_evaluator" in article.agent_responses
        assert article.agent_responses["context_evaluator"] == response
    
    def test_set_classification(self):
        """Test setting classification updates status and timestamp"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        classification = Classification.create_from_score(
            final_score=7.5,
            summary="Good article",
            rationale="Well-written and informative"
        )
        
        article.set_classification(classification)
        
        assert article.classification == classification
        assert article.status == ArticleStatus.CLASSIFIED
        assert article.processed_at is not None
    
    def test_set_classification_invalid(self):
        """Test setting invalid classification fails"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        with pytest.raises(ValueError, match="Classification must be a Classification instance"):
            article.set_classification("invalid_classification")
    
    def test_mark_as_skipped(self):
        """Test marking article as skipped"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        reason = "Content too short"
        article.mark_as_skipped(reason)
        
        assert article.status == ArticleStatus.SKIPPED
        assert article.metadata["skip_reason"] == reason
        assert article.processed_at is not None
    
    def test_mark_as_error(self):
        """Test marking article as error"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        error = "Processing failed"
        article.mark_as_error(error)
        
        assert article.status == ArticleStatus.ERROR
        assert article.metadata["error"] == error
        assert article.processed_at is not None
    
    def test_get_final_score_with_classification(self):
        """Test getting final score when classification exists"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        classification = Classification.create_from_score(
            final_score=8.2,
            summary="Excellent article",
            rationale="High-quality content"
        )
        article.set_classification(classification)
        
        assert article.get_final_score() == 8.2
    
    def test_get_final_score_without_classification(self):
        """Test getting final score when no classification exists"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        assert article.get_final_score() is None
    
    def test_get_score_by_agent(self):
        """Test getting score by specific agent"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        score = Score.create_with_agent(
            value=6.8,
            agent_name="depth_analyzer",
            reasoning="Moderate technical depth"
        )
        article.add_score("depth_analyzer", score)
        
        retrieved_score = article.get_score_by_agent("depth_analyzer")
        assert retrieved_score == score
        assert retrieved_score.value == 6.8
        
        # Test non-existent agent
        assert article.get_score_by_agent("non_existent") is None
    
    def test_is_duplicate(self):
        """Test duplicate detection flag"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing."
        )
        
        # Initially not a duplicate
        assert not article.is_duplicate()
        
        # Mark as duplicate
        article.metadata["is_duplicate"] = True
        assert article.is_duplicate()
    
    def test_word_count(self):
        """Test word count calculation"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="This is a test article with exactly ten words here."
        )
        
        assert article.get_word_count() == 10
    
    def test_character_count(self):
        """Test character count calculation"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Hello World"
        )
        
        assert article.get_character_count() == 11
    
    def test_is_long_content(self):
        """Test long content detection"""
        # Short content
        short_article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Short content here."
        )
        assert not short_article.is_long_content()
        
        # Long content
        long_content = "Very long content. " * 1000  # Creates ~19,000 characters
        long_article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content=long_content
        )
        assert long_article.is_long_content()
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="Test Article",
            content="Valid content for testing.",
            description="Test description"
        )
        
        # Add some scores and classification
        score = Score.create_with_agent(value=7.0, agent_name="test_agent")
        article.add_score("test_agent", score)
        
        classification = Classification.create_from_score(
            final_score=7.0,
            summary="Good article",
            rationale="Well-written"
        )
        article.set_classification(classification)
        
        article_dict = article.to_dict()
        
        assert article_dict["id"] == "test-123"
        assert article_dict["url"] == "https://example.com/article"
        assert article_dict["title"] == "Test Article"
        assert article_dict["description"] == "Test description"
        assert article_dict["status"] == "classified"
        assert "scores" in article_dict
        assert "classification" in article_dict
        assert "word_count" in article_dict
        assert "character_count" in article_dict
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        article_data = {
            "id": "test-123",
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "Valid content for testing.",
            "description": "Test description",
            "status": "pending",
            "content_type": "news_article",
            "created_at": "2025-01-08T10:00:00",
            "metadata": {"test_key": "test_value"},
            "scores": {},
            "agent_responses": {}
        }
        
        article = Article.from_dict(article_data)
        
        assert article.id == "test-123"
        assert article.url == "https://example.com/article"
        assert article.title == "Test Article"
        assert article.description == "Test description"
        assert article.status == ArticleStatus.PENDING
        assert article.content_type == ContentType.NEWS_ARTICLE
        assert article.metadata["test_key"] == "test_value"
    
    def test_string_representations(self):
        """Test string representations"""
        article = Article(
            id="test-123",
            url="https://example.com/article",
            title="A Very Long Article Title That Should Be Truncated in String Representation",
            content="Valid content for testing."
        )
        
        str_repr = str(article)
        assert "test-123" in str_repr
        assert "pending" in str_repr
        assert len(str_repr) < 200  # Should be concise
        
        repr_str = repr(article)
        assert "test-123" in repr_str
        assert "https://example.com/article" in repr_str
        assert "news_article" in repr_str 