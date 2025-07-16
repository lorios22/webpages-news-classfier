"""
Classify Article Use Case

This module contains the main use case for classifying news articles.
It orchestrates the entire classification pipeline including preprocessing,
AI agent analysis, scoring, and final classification.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from application.services.ai_classification_service import AIClassificationService
from application.services.content_processing_service import ContentProcessingService
from application.services.duplicate_detection_service import DuplicateDetectionService
from application.services.scoring_service import ScoringService
from domain.entities import Article, ArticleStatus
from domain.value_objects import Classification, Score, Source
from infrastructure.external_services.fin_service import FINService

logger = logging.getLogger(__name__)


class ClassifyArticleUseCase:
    """
    Use case for classifying news articles through the complete AI pipeline.

    This use case orchestrates the entire article classification process:
    1. Content preprocessing and validation
    2. Duplicate detection
    3. AI agent analysis
    4. Score consolidation
    5. Final classification

    Attributes:
        duplicate_service: Service for detecting duplicate articles
        content_service: Service for content processing and cleaning
        ai_service: Service for AI agent classification
        scoring_service: Service for score consolidation
        fin_service: Service for financial intelligence data
    """

    def __init__(
        self,
        duplicate_service: DuplicateDetectionService,
        content_service: ContentProcessingService,
        ai_service: AIClassificationService,
        scoring_service: ScoringService,
        fin_service: FINService,
    ):
        self.duplicate_service = duplicate_service
        self.content_service = content_service
        self.ai_service = ai_service
        self.scoring_service = scoring_service
        self.fin_service = fin_service

    async def execute(self, article: Article) -> Article:
        """
        Execute the complete article classification pipeline.

        Args:
            article: Article entity to classify

        Returns:
            Classified article with results

        Raises:
            Exception: If classification fails
        """
        try:
            logger.info(f"Starting classification for article: {article.id}")
            article.status = ArticleStatus.PROCESSING

            # Step 1: Preprocess and validate content
            article = await self._preprocess_content(article)
            if article.status == ArticleStatus.SKIPPED:
                return article

            # Step 2: Check for duplicates
            article = await self._check_duplicates(article)
            if article.status == ArticleStatus.SKIPPED:
                return article

            # Step 3: Run AI classification pipeline
            article = await self._run_ai_classification(article)
            if article.status == ArticleStatus.ERROR:
                return article

            # Step 4: Consolidate scores and create final classification
            article = await self._consolidate_classification(article)

            # Step 5: Store in duplicate detection memory
            await self._store_for_duplicate_detection(article)

            logger.info(f"Classification completed for article: {article.id}")
            return article

        except Exception as e:
            logger.error(f"Classification failed for article {article.id}: {str(e)}")
            article.mark_as_error(str(e))
            return article

    async def _preprocess_content(self, article: Article) -> Article:
        """
        Preprocess article content and check if it should be skipped.

        Args:
            article: Article to preprocess

        Returns:
            Preprocessed article
        """
        try:
            # Clean and structure content
            cleaned_content = self.content_service.clean_content(article.content)

            # Check content length and quality
            if not self.content_service.validate_content_length(cleaned_content):
                article.mark_as_skipped("Content too short (minimum 50 words required)")
                return article

            # Check for spam with enhanced detection
            spam_result = self.content_service.check_spam_with_override(cleaned_content)
            if spam_result.should_skip:
                article.mark_as_skipped(spam_result.reason)
                return article

            # Truncate long content if necessary
            if article.is_long_content():
                cleaned_content = self.content_service.truncate_content(cleaned_content)
                article.metadata["content_truncated"] = True

            # Update article with cleaned content
            article.content = cleaned_content
            article.metadata.update(
                {
                    "original_length": len(article.content),
                    "cleaned_length": len(cleaned_content),
                    "preprocessing_completed": datetime.now().isoformat(),
                }
            )

            return article

        except Exception as e:
            logger.error(f"Content preprocessing failed: {str(e)}")
            article.mark_as_error(f"Content preprocessing failed: {str(e)}")
            return article

    async def _check_duplicates(self, article: Article) -> Article:
        """
        Check if article is a duplicate of previously processed content.

        Args:
            article: Article to check

        Returns:
            Article with duplicate check results
        """
        try:
            is_duplicate, duplicate_id = await self.duplicate_service.is_duplicate(article.content, article.url)

            if is_duplicate:
                article.mark_as_skipped(f"Duplicate content (matches {duplicate_id})")
                article.metadata.update({"is_duplicate": True, "duplicate_id": duplicate_id})

            return article

        except Exception as e:
            logger.error(f"Duplicate detection failed: {str(e)}")
            # Don't fail the entire process for duplicate detection errors
            logger.warning("Continuing without duplicate detection")
            return article

    async def _run_ai_classification(self, article: Article) -> Article:
        """
        Run the complete AI classification pipeline.

        Args:
            article: Article to classify

        Returns:
            Article with AI classification results
        """
        try:
            # Get source information and FIN data
            source = Source.from_url(article.url)
            article.source = source

            fin_data = await self.fin_service.get_comprehensive_analysis(article.content, article.url)
            article.metadata["fin_analysis"] = fin_data

            # Run all AI agents in the pipeline
            classification_results = await self.ai_service.classify_article(article, fin_data)

            # Store agent responses and scores
            for agent_name, result in classification_results.items():
                article.add_agent_response(agent_name, result.get("response"))
                if "score" in result:
                    score = Score.create_with_agent(
                        value=result["score"],
                        agent_name=agent_name,
                        reasoning=result.get("reasoning"),
                        confidence=result.get("confidence", 1.0),
                    )
                    article.add_score(agent_name, score)

            return article

        except Exception as e:
            logger.error(f"AI classification failed: {str(e)}")
            article.mark_as_error(f"AI classification failed: {str(e)}")
            return article

    async def _consolidate_classification(self, article: Article) -> Article:
        """
        Consolidate individual scores into final classification.

        Args:
            article: Article with individual scores

        Returns:
            Article with final classification
        """
        try:
            # Consolidate scores using scoring service
            final_score = self.scoring_service.consolidate_scores(article.scores)

            # Generate summary and rationale
            summary = self._generate_summary(article)
            rationale = self._generate_rationale(article, final_score)

            # Calculate confidence based on score consistency
            confidence = self.scoring_service.calculate_confidence(article.scores)

            # Create final classification
            classification = Classification.create_from_score(
                final_score=final_score,
                summary=summary,
                rationale=rationale,
                sub_scores={name: score.value for name, score in article.scores.items()},
                confidence=confidence,
                fin_enhanced=True,
                source_credibility=(article.source.credibility_score if article.source else None),
            )

            article.set_classification(classification)
            return article

        except Exception as e:
            logger.error(f"Score consolidation failed: {str(e)}")
            article.mark_as_error(f"Score consolidation failed: {str(e)}")
            return article

    async def _store_for_duplicate_detection(self, article: Article) -> None:
        """
        Store article in duplicate detection memory for future checks.

        Args:
            article: Classified article to store
        """
        try:
            if article.status == ArticleStatus.CLASSIFIED:
                article_id = await self.duplicate_service.add_content(article.content, article.url)
                article.metadata["duplicate_detection_id"] = article_id
                logger.debug(f"Article stored for duplicate detection: {article_id}")
        except Exception as e:
            logger.warning(f"Failed to store article for duplicate detection: {str(e)}")
            # Don't fail the process for this

    def _generate_summary(self, article: Article) -> str:
        """
        Generate a summary of the article based on agent responses.

        Args:
            article: Article with agent responses

        Returns:
            Generated summary
        """
        # Try to get summary from summary agent first
        summary_response = article.agent_responses.get("summary_agent")
        if summary_response and isinstance(summary_response, dict):
            return summary_response.get("summary", article.title)

        # Fallback to title if no summary available
        return article.title

    def _generate_rationale(self, article: Article, final_score: float) -> str:
        """
        Generate rationale for the classification based on agent scores and reasoning.

        Args:
            article: Article with classification results
            final_score: Final consolidated score

        Returns:
            Generated rationale
        """
        rationale_parts = [f"Final score: {final_score:.1f}/10.0"]

        # Add key agent insights
        key_agents = ["context_evaluator", "fact_checker", "human_reasoning"]
        for agent in key_agents:
            score = article.get_score_by_agent(agent)
            if score and score.reasoning:
                rationale_parts.append(f"{agent}: {score.reasoning}")

        # Add FIN analysis if available
        fin_data = article.metadata.get("fin_analysis", {})
        if fin_data:
            source_cred = fin_data.get("source_credibility", {})
            if source_cred:
                rationale_parts.append(f"Source credibility: {source_cred.get('source_credibility', 'N/A')}/100")

        return " | ".join(rationale_parts)

    def get_classification_stats(self, articles: List[Article]) -> Dict[str, Any]:
        """
        Get statistics about a batch of classified articles.

        Args:
            articles: List of classified articles

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_articles": len(articles),
            "classified": 0,
            "skipped": 0,
            "errors": 0,
            "duplicates": 0,
            "average_score": 0.0,
            "score_distribution": {},
            "content_types": {},
            "source_types": {},
        }

        total_score = 0.0
        classified_count = 0

        for article in articles:
            # Count by status
            if article.status == ArticleStatus.CLASSIFIED:
                stats["classified"] += 1
                if article.classification:
                    total_score += article.classification.final_score
                    classified_count += 1

                    # Score distribution
                    category = article.classification.category.value
                    stats["score_distribution"][category] = stats["score_distribution"].get(category, 0) + 1

            elif article.status == ArticleStatus.SKIPPED:
                stats["skipped"] += 1
                if article.is_duplicate():
                    stats["duplicates"] += 1
            elif article.status == ArticleStatus.ERROR:
                stats["errors"] += 1

            # Content types
            content_type = article.content_type.value
            stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1

            # Source types
            if article.source:
                source_type = article.source.source_type.value
                stats["source_types"][source_type] = stats["source_types"].get(source_type, 0) + 1

        # Calculate average score
        if classified_count > 0:
            stats["average_score"] = round(total_score / classified_count, 2)

        return stats
