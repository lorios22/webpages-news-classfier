import logging
import re
from typing import Dict, List, Union

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_and_structure_content(content: str) -> Dict:
    """
    Cleans and structures raw web content by removing HTML tags, normalizing text,
    and extracting metadata.
    """
    try:
        # Use BeautifulSoup to clean HTML
        soup = BeautifulSoup(content, "html.parser")

        # Extract potential metadata
        title = soup.title.string if soup.title else ""

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get clean text
        text = soup.get_text(separator="\n", strip=True)

        # Normalize whitespace
        text = " ".join(text.split())

        # Basic structure detection
        is_news_article = any(indicator in text.lower() for indicator in ["news", "report", "announced"])
        is_blog_post = any(indicator in text.lower() for indicator in ["blog", "opinion", "thoughts"])

        return {
            "cleaned_content": text,
            "metadata": {
                "title": title,
                "content_type": ("news_article" if is_news_article else "blog_post" if is_blog_post else "unknown"),
                "estimated_length": len(text.split()),
            },
        }
    except Exception as e:
        return {"error": f"Failed to process content: {str(e)}"}


def load_classification_rules() -> str:
    """Load the current classification rules from the specified documents."""
    try:
        rules = []

        # Load first rules document
        rules_path1 = "improvements/Definitions of Key Judgment Terms For Crypto News Article Classification System.txt"
        with open(rules_path1, "r", encoding="utf-8") as f:
            rules.append(f.read())

        # Execute the function right away
        result = "\n\n".join(rules)
        return result

    except Exception as e:
        print("Error loading rules:", str(e))
        return f"Failed to load rules: {str(e)}"


def transcribe_audio_video(url: str) -> Dict:
    """
    Transcribes audio/video content from a given URL.

    Args:
        url: URL of the audio/video content

    Returns:
        Dict containing transcription and metadata
    """
    try:
        # Placeholder for actual transcription logic
        return {
            "metadata": {
                "url": url,
                "date": "",
                "duration": "",
                "poster": "",
                "technical": {},
            },
            "transcript": [{"timestamp": "00:00:00", "content": "", "type": "speech", "notes": ""}],
            "technical_log": [],
        }
    except Exception as e:
        return {"error": str(e)}


# Create fact verification tools
def verify_claim(claim: str) -> Dict:
    """Verify a factual claim against trusted sources."""
    try:
        # Here you would integrate with fact-checking APIs or databases
        # For now, we'll use a simple implementation
        return {
            "verified": True,  # or False
            "confidence": 0.8,
            "source": "Example Source",
            "notes": "Verification details would go here",
        }
    except Exception as e:
        return {"verified": False, "error": str(e)}


def extract_claims(text: str) -> List[str]:
    """Extract factual claims from text for verification."""
    try:
        # Implementation would parse text and identify claims
        # For now, return a simple structure
        return ["Claim 1", "Claim 2"]
    except Exception as e:
        logger.warning(f"Failed to extract claims: {e}")
        return []


class ScoringPitfallsValidator:
    """
    Validates scores against common classification pitfalls and edge cases.
    """

    def __init__(self):
        self.score_boundaries = {
            "misinformation": {
                (
                    1,
                    2,
                ): "Distinguish between completely false (1) and partially misleading (2)",
                (2, 3): "Distinguish between misleading and speculative content",
            },
            "basic_content": {
                (4, 5): "Distinguish between listing facts (4) and basic analysis (5)",
                (5, 6): "Distinguish between basic context and actual technical depth",
            },
            "analysis_depth": {
                (6, 7): "Distinguish between moderate and substantial analysis",
                (7, 8): "Distinguish between good analysis and innovative insights",
            },
            "excellence": {
                (8, 9): "Distinguish between excellent and industry-leading",
                (9, 10): "Distinguish between industry-leading and transformative",
            },
        }

        self.content_type_limits = {
            "tweet": 5.5,
            "blog_post": 8.0,
            "research_paper": 10.0,
            "news_article": 7.0,
        }

    def validate_score_transition(self, score: float, agent_outputs: Dict) -> Dict:
        """
        Validates if the score properly considers common transition pitfalls and content type limits.
        """
        warnings = []
        content_type = agent_outputs.get("content_metadata", {}).get("type", "blog_post")

        # Check content type limits
        type_limit = self.content_type_limits.get(content_type, 7.0)
        if score > type_limit:
            warnings.append(f"{content_type} score exceeding typical limit of {type_limit}")

        # Check depth vs score alignment
        if isinstance(agent_outputs["depth_analysis"], dict):
            depth_level = agent_outputs["depth_analysis"].get("depth_level")
            if depth_level == "basic" and score > 5.0:
                warnings.append("Basic depth content scored too high")

        # Check technical analysis requirements
        if score >= 7.0:
            if isinstance(agent_outputs["depth_analysis"], dict):
                if not agent_outputs["depth_analysis"].get("technical_elements"):
                    warnings.append("High score without technical depth justification")

        # Check innovation requirements for top scores
        if score >= 9.0:
            if isinstance(agent_outputs["relevance_assessment"], dict):
                if not agent_outputs["relevance_assessment"].get("industry_changing"):
                    warnings.append("Top score without industry-changing impact")

        return {
            "score": score,
            "warnings": warnings,
            "requires_review": len(warnings) > 0,
        }

    def get_boundary_guidance(self, score: float) -> str:
        """
        Returns specific guidance for score boundary cases.
        """
        for category, boundaries in self.score_boundaries.items():
            for (lower, upper), guidance in boundaries.items():
                if lower - 0.2 <= score <= upper + 0.2:
                    return f"{guidance} (Current score: {score:.1f})"
        return "Score not in boundary area"


def consolidate_score(agent_outputs: Dict) -> Dict:
    """
    Consolidates and validates decimal scores from multiple agents into a final classification score.

    Args:
        agent_outputs (Dict): Dictionary containing outputs from all analysis agents
            including fact checks, depth analysis, relevance assessment, etc.

    Returns:
        Dict: Contains final_score, warnings, and review status with decimal precision
    """
    validator = ScoringPitfallsValidator()
    print("this is the output", agent_outputs)
    # Extract decimal scores from agent outputs
    context_evaluator = float(agent_outputs["context_evaluator"])
    credibility_score = float(agent_outputs["fact_check"])
    depth_score = float(agent_outputs["depth_analysis"])
    relevance_score = float(agent_outputs["relevance_assessment"])
    structure_score = float(agent_outputs["structure_analysis"])
    historical_adjustment = float(agent_outputs["historical_reflection"])
    human_reasoning = float(agent_outputs["human_reasoning"])
    reflective_validator = float(agent_outputs["reflective_validator"])

    # Calculate weighted average including all scores
    raw_score = (
        context_evaluator * 0.1
        + credibility_score * 0.2
        + depth_score * 0.2
        + relevance_score * 0.1
        + structure_score * 0.1
        + human_reasoning * 0.1
        + reflective_validator * 0.1
    )

    # Apply historical adjustment (capped at ±1.5)
    adjusted_score = raw_score + max(min(historical_adjustment, 1.5), -1.5)
    # Validate against common pitfalls
    validation_result = validator.validate_score_transition(adjusted_score, agent_outputs)

    if validation_result["requires_review"]:
        guidance = validator.get_boundary_guidance(adjusted_score)
        return {
            "raw_consolidated_score": f"{adjusted_score:.1f}",
            "warnings": validation_result["warnings"],
            "guidance": guidance,
            "requires_human_review": True,
            "adjacency_notes": [guidance],
            "contradictions_found": validation_result["warnings"],
        }

    return {
        "raw_consolidated_score": f"{adjusted_score:.1f}",
        "warnings": [],
        "requires_human_review": False,
        "adjacency_notes": [validator.get_boundary_guidance(adjusted_score)],
        "contradictions_found": ["None"],
    }


def human_like_adjustment(score: float, content_type: str) -> Dict[str, Union[float, str, List[str]]]:
    """
    Applies human-like heuristics to adjust scores based on content type.

    Args:
        score: Current decimal score to adjust
        content_type: Type of content (tweet, blog, paper etc)

    Returns:
        Dict containing adjusted score and reasoning
    """
    original_score = score
    adjustments = []

    # Content type specific caps
    content_caps = {"tweet": 7.5, "blog": 8.5, "paper": 10.0, "chart": 6.0}

    if content_type in content_caps and score > content_caps[content_type]:
        score = content_caps[content_type]
        adjustments.append(f"{content_type} cannot exceed {content_caps[content_type]}")

    return {
        "final_score": round(score, 1),
        "original_score": original_score,
        "adjustments": adjustments,
        "adjustment_magnitude": round(original_score - score, 2),
    }


def validate_rule_citations(agent_outputs: Dict) -> Dict:
    """Verify that all agent decisions cite valid rules from SST."""
    try:
        # Load SST rules
        with open("path/to/sst_rules.txt", "r", encoding="utf-8") as f:
            sst_rules = f.read()

        violations = []
        for agent_name, output in agent_outputs.items():
            if "cited_rules" not in output:
                violations.append(
                    {
                        "agent": agent_name,
                        "type": "missing_citation",
                        "description": "No rules cited",
                    }
                )
            else:
                for rule_id in output["cited_rules"]:
                    if rule_id not in sst_rules:
                        violations.append(
                            {
                                "agent": agent_name,
                                "type": "invalid_citation",
                                "rule_id": rule_id,
                                "description": "Cited rule not found in SST",
                            }
                        )

        return {
            "total_checked": len(agent_outputs),
            "violations": violations,
            "status": "FAILED" if violations else "PASSED",
        }
    except Exception as e:
        return {"error": f"Failed to validate citations: {str(e)}"}


def check_fact_checker_override(outputs: Dict) -> Dict:
    """Check if fact checker findings require score override."""
    try:
        fact_check = outputs.get("fact_check_results", {})
        final_score = outputs.get("consolidated_score", {}).get("score", 0)

        violations = []
        if fact_check.get("severe_misinformation", False) and final_score > 2:
            violations.append(
                {
                    "type": "score_override",
                    "description": "Severe misinformation requires score ≤ 2",
                    "current_score": final_score,
                    "max_allowed": 2,
                    "rule_id": "1.3",
                }
            )

        return {
            "violations": violations,
            "status": "FAILED" if violations else "PASSED",
            "adjusted_score": min(final_score, 2) if violations else final_score,
        }
    except Exception as e:
        return {"error": f"Failed to check fact override: {str(e)}"}


def validate_adjacency_rules(outputs: Dict) -> Dict:
    """Validate that scores maintain allowed differences."""
    try:
        violations = []

        # Check depth vs relevance
        depth = outputs.get("depth_analysis", {}).get("score", 0)
        relevance = outputs.get("relevance_assessment", {}).get("score", 0)

        if abs(depth - relevance) > 3:
            violations.append(
                {
                    "type": "adjacency_violation",
                    "scores": {"depth": depth, "relevance": relevance},
                    "description": "Depth and relevance scores differ by >3 points",
                    "rule_id": "2.1",
                }
            )

        # Check fact check impact
        fact_check = outputs.get("fact_check_results", {})
        if fact_check.get("reliability") == "low" and depth > 5:
            violations.append(
                {
                    "type": "reliability_conflict",
                    "description": "Low reliability content cannot have high depth score",
                    "rule_id": "2.3",
                }
            )

        return {
            "violations": violations,
            "status": "FAILED" if violations else "PASSED",
        }
    except Exception as e:
        return {"error": f"Failed to validate adjacency: {str(e)}"}


def extract_urls(content: str) -> list:
    """
    Extract URLs from tweet content using regex pattern matching.

    Args:
        content (str): The tweet content to extract URLs from

    Returns:
        list: List of extracted URLs
    """
    # Regex pattern for URLs
    url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"

    # Find all URLs in the content
    urls = re.findall(url_pattern, content)

    # Remove any duplicates while preserving order
    unique_urls = list(dict.fromkeys(urls))

    return unique_urls


def fetch_source_content(urls: list) -> str:
    """
    Fetch content from provided URLs.

    Args:
        urls (list): List of URLs to fetch content from

    Returns:
        str: Combined content from all URLs
    """
    import requests
    from bs4 import BeautifulSoup

    all_content = []

    for url in urls:
        try:
            # Make request with timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Truncate if too long (e.g., first 1000 characters)
            text = text[:1000] + "..." if len(text) > 1000 else text

            all_content.append(text)

        except Exception as e:
            print(f"Error fetching content from {url}: {str(e)}")
            all_content.append(f"[Error fetching content from {url}]")

    return "\n\n".join(all_content)
